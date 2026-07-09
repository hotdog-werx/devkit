import tomllib

from repolish.testing import ProviderTestBed

from devkit.releez.repolish.models import ReleezProviderContext
from devkit.releez.repolish.provider import ReleezProvider

# NOTE: create_file_mappings() references these without the .jinja suffix
# (correct for the real CLI, which resolves that automatically); render_all()
# doesn't do the same fallback for dest-mapped entries, so these tests call
# bed.render() directly with the literal on-disk .jinja-suffixed path.
FINALIZE_RELEASE_TEMPLATE = '.github/workflows/finalize-release.yaml.jinja'
LINT_PR_TITLE_TEMPLATE = '.github/workflows/lint-pr-title.yaml.jinja'
VALIDATE_RELEASE_TEMPLATE = '.github/workflows/validate-release.yaml.jinja'
CLIFF_TOML_TEMPLATE = 'cliff.toml.jinja'


def test_finalize_release_uses_published_action_ref_by_default():
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext(repo='uv-toolbox', use_self_action=False))
    workflow = bed.render(FINALIZE_RELEASE_TEMPLATE)
    assert "releez-action-ref: 'hotdog-werx/releez@v1'" in workflow
    assert "releez-action-ref: './'" not in workflow


def test_finalize_release_uses_self_action_when_enabled():
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext(repo='releez', use_self_action=True))
    workflow = bed.render(FINALIZE_RELEASE_TEMPLATE)
    assert "releez-action-ref: './'" in workflow
    assert "releez-action-ref: 'hotdog-werx/releez@v1'" not in workflow


def test_finalize_release_uses_mise_tasks_for_build_and_publish():
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext(repo='example'))
    workflow = bed.render(FINALIZE_RELEASE_TEMPLATE)
    assert 'build-command: mise run build' in workflow
    assert 'publish-command: mise run publish' in workflow


def test_finalize_release_references_releez_ref_reusable_workflow():
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext(releez_ref='topic/repolish'))
    workflow = bed.render(FINALIZE_RELEASE_TEMPLATE)
    assert '__releez_publish.yaml@topic/repolish' in workflow


def test_finalize_release_publish_package_defaults_true():
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext())
    workflow = bed.render(FINALIZE_RELEASE_TEMPLATE)
    assert 'publish-package: true' in workflow


def test_finalize_release_publish_package_can_be_disabled():
    """devkit itself (a bare workspace container with no installable root
    package) needs tagging/changelog/GitHub Release without a PyPI build+
    publish step — publish_package=False must render `false` for that input.
    """
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext(publish_package=False))
    workflow = bed.render(FINALIZE_RELEASE_TEMPLATE)
    assert 'publish-package: false' in workflow


def test_lint_pr_title_references_releez_ref_reusable_workflow():
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext(releez_ref='topic/repolish'))
    workflow = bed.render(LINT_PR_TITLE_TEMPLATE)
    assert '__releez_lint-pr-title.yaml@topic/repolish' in workflow


def test_lint_pr_title_uses_self_action_when_enabled():
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext(use_self_action=True))
    workflow = bed.render(LINT_PR_TITLE_TEMPLATE)
    assert "releez-action-ref: './'" in workflow


def test_validate_release_references_releez_ref_reusable_workflow():
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext(releez_ref='topic/repolish'))
    workflow = bed.render(VALIDATE_RELEASE_TEMPLATE)
    assert '__releez_validate-release.yaml@topic/repolish' in workflow


def test_validate_release_uses_published_action_ref_by_default():
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext(use_self_action=False))
    workflow = bed.render(VALIDATE_RELEASE_TEMPLATE)
    assert "releez-action-ref: 'hotdog-werx/releez@v1'" in workflow


def test_cliff_toml_is_valid_toml_and_preserves_tera_syntax():
    """The body template is Tera syntax (git-cliff's own engine), not Jinja.

    It must survive Jinja rendering completely unprocessed via {% raw %},
    while the [remote.github] owner/repo *are* real Jinja substitutions.
    Regression test for the raw-block boundary being drawn in the right
    place.
    """
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext(owner='hotdog-werx', repo='releez'))
    content = bed.render(CLIFF_TOML_TEMPLATE)
    parsed = tomllib.loads(content)

    assert parsed['remote']['github']['owner'] == 'hotdog-werx'
    assert parsed['remote']['github']['repo'] == 'releez'
    # Tera syntax must remain literal, not be interpreted as Jinja:
    assert '{{ version | trim_start_matches' in parsed['changelog']['body']
    assert '{% if commit.scope %}' in parsed['changelog']['body']


def test_no_pyright_references():
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
