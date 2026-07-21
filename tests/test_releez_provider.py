import tomllib
from pathlib import Path

from devkit.releez.repolish.models import ReleezProviderContext
from devkit.releez.repolish.provider import ReleezProvider
from repolish.testing import ProviderTestBed

# NOTE: create_file_mappings() references these without the .jinja suffix
# (correct for the real CLI, which resolves that automatically); render_all()
# doesn't do the same fallback for dest-mapped entries, so these tests call
# bed.render() directly with the literal on-disk .jinja-suffixed path.
FINALIZE_RELEASE_TEMPLATE = '.github/workflows/finalize-release.yaml.jinja'
LINT_PR_TITLE_TEMPLATE = '.github/workflows/lint-pr-title.yaml.jinja'
VALIDATE_RELEASE_TEMPLATE = '.github/workflows/validate-release.yaml.jinja'
CLIFF_TOML_TEMPLATE = 'cliff.toml.jinja'
REUSABLE_WORKFLOW_DIR = Path(__file__).parents[1] / '.github' / 'workflows'


def test_finalize_release_uses_published_action_by_default():
    """use_self_action=False renders the published-action input as false."""
    bed = ProviderTestBed(
        ReleezProvider,
        ReleezProviderContext(use_self_action=False),
    )
    workflow = bed.render(FINALIZE_RELEASE_TEMPLATE)
    assert 'use-self-action: false' in workflow


def test_finalize_release_uses_self_action_when_enabled():
    """use_self_action=True renders the self-action input as true."""
    bed = ProviderTestBed(
        ReleezProvider,
        ReleezProviderContext(use_self_action=True),
    )
    workflow = bed.render(FINALIZE_RELEASE_TEMPLATE)
    assert 'use-self-action: true' in workflow


def test_release_project_comes_from_finalize_output():
    """The publish workflow uses the project detected by Releez finalize."""
    publish = (REUSABLE_WORKFLOW_DIR / '__releez_publish.yaml').read_text()
    validate = (REUSABLE_WORKFLOW_DIR / '__releez_validate-release.yaml').read_text()

    expected = 'PROJECT: ${{ steps.releez-published.outputs.project || steps.releez-self.outputs.project }}'
    assert publish.count(expected) == 2
    assert 'inputs.project' not in publish
    assert 'project:' not in validate


def test_finalize_release_uses_direct_uv_commands_for_build_and_publish():
    """No mise task wrappers: uv build/publish need no indirection, and releez itself handles tag-pulling now."""
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext())
    workflow = bed.render(FINALIZE_RELEASE_TEMPLATE)
    assert 'build-command: uv build --no-sources' in workflow
    assert 'publish-command: uv publish dist/*' in workflow
    assert "package-prefix: ''" in workflow


def test_finalize_release_references_releez_ref_reusable_workflow():
    """The finalize-release workflow pins the reusable workflow to releez_ref."""
    bed = ProviderTestBed(
        ReleezProvider,
        ReleezProviderContext(releez_ref='releez-pin'),
    )
    workflow = bed.render(FINALIZE_RELEASE_TEMPLATE)
    assert '__releez_publish.yaml@releez-pin' in workflow


def test_finalize_release_publish_package_defaults_true():
    """publish_package defaults true — most consumers have a package to publish."""
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext())
    workflow = bed.render(FINALIZE_RELEASE_TEMPLATE)
    assert 'publish-package: true' in workflow


def test_finalize_release_publish_package_can_be_disabled():
    """publish_package=False must render `false` for the publish-package input.

    A docs-only consumer can still tag and create a GitHub Release without a
    PyPI build/publish step.
    """
    bed = ProviderTestBed(
        ReleezProvider,
        ReleezProviderContext(publish_package=False),
    )
    workflow = bed.render(FINALIZE_RELEASE_TEMPLATE)
    assert 'publish-package: false' in workflow


def test_lint_pr_title_references_releez_ref_reusable_workflow():
    """The lint-pr-title workflow pins the reusable workflow to releez_ref."""
    bed = ProviderTestBed(
        ReleezProvider,
        ReleezProviderContext(releez_ref='releez-pin'),
    )
    workflow = bed.render(LINT_PR_TITLE_TEMPLATE)
    assert '__releez_lint-pr-title.yaml@releez-pin' in workflow


def test_lint_pr_title_uses_self_action_when_enabled():
    """use_self_action=True renders the self-action input as true."""
    bed = ProviderTestBed(
        ReleezProvider,
        ReleezProviderContext(use_self_action=True),
    )
    workflow = bed.render(LINT_PR_TITLE_TEMPLATE)
    assert 'use-self-action: true' in workflow


def test_validate_release_references_releez_ref_reusable_workflow():
    """The validate-release workflow pins the reusable workflow to releez_ref."""
    bed = ProviderTestBed(
        ReleezProvider,
        ReleezProviderContext(releez_ref='releez-pin'),
    )
    workflow = bed.render(VALIDATE_RELEASE_TEMPLATE)
    assert '__releez_validate-release.yaml@releez-pin' in workflow


def test_validate_release_uses_published_action_by_default():
    """use_self_action=False renders the published-action input as false."""
    bed = ProviderTestBed(
        ReleezProvider,
        ReleezProviderContext(use_self_action=False),
    )
    workflow = bed.render(VALIDATE_RELEASE_TEMPLATE)
    assert 'use-self-action: false' in workflow


def test_cliff_toml_is_valid_toml_and_preserves_tera_syntax():
    """The body template is Tera syntax (git-cliff's own engine), not Jinja.

    It must survive Jinja rendering completely unprocessed via {% raw %},
    while the [remote.github] owner/repo *are* real Jinja substitutions.
    Regression test for the raw-block boundary being drawn in the right
    place.
    """
    bed = ProviderTestBed(
        ReleezProvider,
        ReleezProviderContext(
            repolish={
                'repo': {'owner': 'hotdog-werx', 'name': 'releez'},
            },
        ),
    )
    content = bed.render(CLIFF_TOML_TEMPLATE)
    parsed = tomllib.loads(content)

    assert parsed['remote']['github']['owner'] == 'test-owner'
    assert parsed['remote']['github']['repo'] == 'test-repo'
    # Tera syntax must remain literal, not be interpreted as Jinja:
    assert '{{ version | trim_start_matches' in parsed['changelog']['body']
    assert '{% if commit.scope %}' in parsed['changelog']['body']


def test_no_pyright_references():
    """pydoclint/ty replaced pyright entirely — regression test for that decision."""
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext())
    rendered = bed.render_all()
    combined = '\n'.join(
        [
            *rendered.values(),
            bed.render(FINALIZE_RELEASE_TEMPLATE),
            bed.render(LINT_PR_TITLE_TEMPLATE),
            bed.render(VALIDATE_RELEASE_TEMPLATE),
            bed.render(CLIFF_TOML_TEMPLATE),
        ],
    )
    assert 'pyright' not in combined.lower()
