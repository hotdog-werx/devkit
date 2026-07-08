import tomllib

from repolish.testing import ProviderTestBed

from devkit.releez.repolish.models import ReleezProviderContext
from devkit.releez.repolish.provider import ReleezProvider

# NOTE: create_file_mappings() references these without the .jinja suffix
# (correct for the real CLI, which resolves that automatically); render_all()
# doesn't do the same fallback for dest-mapped entries, so these tests call
# bed.render() directly with the literal on-disk .jinja-suffixed path.
FINALIZE_RELEASE_TEMPLATE = '.github/workflows/finalize-release.yaml.jinja'
CLIFF_TOML_TEMPLATE = 'cliff.toml.jinja'


def test_render_all_succeeds_use_self_action_false():
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext(repo='uv-toolbox', use_self_action=False))
    workflow = bed.render(FINALIZE_RELEASE_TEMPLATE)
    assert 'uses: hotdog-werx/releez@v1' in workflow
    assert 'uses: ./' not in workflow


def test_render_all_succeeds_use_self_action_true():
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext(repo='releez', use_self_action=True))
    workflow = bed.render(FINALIZE_RELEASE_TEMPLATE)
    assert 'uses: ./' in workflow
    assert 'uses: hotdog-werx/releez@v1' not in workflow


def test_finalize_release_uses_mise_tasks_for_build_and_publish():
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext(repo='example'))
    workflow = bed.render(FINALIZE_RELEASE_TEMPLATE)
    assert 'run: mise run build' in workflow
    assert 'run: mise run publish' in workflow


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
            bed.render(CLIFF_TOML_TEMPLATE),
        ],
    )
    assert 'pyright' not in combined.lower()
