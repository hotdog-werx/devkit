"""Regression tests for the repolish-start/repolish-end anchor mechanism.

These exist because the anchor marker syntax was initially written wrong
(`## repolish-anchor[tag]: start` instead of the real
`## repolish-start[tag]` / `## repolish-end[tag]`), which silently never
matched repolish's substitution regex — the default anchor text just sat in
every rendered file unreplaced. Confirming the *real* marker + substitution
behavior here catches that class of bug for every template that uses anchors.
"""

from devkit.releez.repolish.models import ReleezProviderContext
from devkit.releez.repolish.provider import ReleezProvider
from devkit.workspace.repolish.models import WorkspaceProviderContext
from devkit.workspace.repolish.provider import WorkspaceProvider
from jinja2 import Environment, StrictUndefined
from repolish.preprocessors.anchors import replace_tags_in_content
from repolish.preprocessors.keep import KeepBlockSpec, apply_keep_replacements
from repolish.testing import ProviderTestBed


def test_workspace_ci_checks_keep_block_preserves_local_custom_jobs():
    """The custom-ci-checks keep-block preserves whatever the consumer already wrote.

    Unlike a plain anchor (always reset to a provider-computed value), a
    keep-block is what lets consumers add jobs that must live in the same
    file as repo-checks/python-checks (GitHub Actions `needs:` only works
    within one file) without repolish clobbering them on the next apply.
    """
    bed = ProviderTestBed(
        WorkspaceProvider,
        WorkspaceProviderContext(has_python=True, enable_docs=False),
    )
    content = bed.render('.github/workflows/ci-checks.yaml.jinja')

    # The rendered file must still contain the literal directive + marker
    # text (keep-block substitution is a separate preprocessing pass the
    # CLI runs before Jinja in the real pipeline; ProviderTestBed only does
    # the Jinja pass).
    assert 'repolish-keep-block[custom-ci-checks]' in content
    assert '## start-custom-ci-checks' in content
    assert '## end-custom-ci-checks' in content

    local_content = '## start-custom-ci-checks\ntests:\n  runs-on: ubuntu-latest\n## end-custom-ci-checks\n'
    result = apply_keep_replacements(
        content,
        {
            'custom-ci-checks': KeepBlockSpec(
                start='## start-custom-ci-checks',
                end='## end-custom-ci-checks',
            ),
        },
        {},
        {},
        local_content,
    )
    assert 'tests:\n  runs-on: ubuntu-latest' in result
    assert 'repolish-keep-block' not in result


def test_workspace_deploy_docs_anchor_marker_is_replaceable():
    """The additional-deploy-jobs anchor in deploy-docs.yaml accepts a real substitution."""
    bed = ProviderTestBed(
        WorkspaceProvider,
        WorkspaceProviderContext(enable_docs=True),
    )
    content = bed.render('.github/workflows/deploy-docs.yaml.jinja')

    assert '## repolish-start[additional-deploy-jobs]' in content
    assert '## repolish-end[additional-deploy-jobs]' in content

    replaced = replace_tags_in_content(
        content,
        {'additional-deploy-jobs': 'notify-slack:\n  runs-on: ubuntu-latest'},
    )
    assert 'notify-slack:' in replaced


def test_releez_finalize_release_anchor_marker_is_replaceable():
    """The additional-jobs anchor in finalize-release.yaml accepts a real substitution."""
    bed = ProviderTestBed(
        ReleezProvider,
        ReleezProviderContext(repo='example', use_self_action=False),
    )
    content = bed.render('.github/workflows/finalize-release.yaml.jinja')

    assert '## repolish-start[additional-jobs]' in content
    assert '## repolish-end[additional-jobs]' in content

    replaced = replace_tags_in_content(
        content,
        {'additional-jobs': 'notify:\n  runs-on: ubuntu-latest'},
    )
    assert 'notify:' in replaced


def test_releez_lint_pr_title_anchor_marker_is_replaceable():
    """The additional-lint-pr-title-jobs anchor in lint-pr-title.yaml accepts a real substitution."""
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext(repo='example'))
    content = bed.render('.github/workflows/lint-pr-title.yaml.jinja')

    assert '## repolish-start[additional-lint-pr-title-jobs]' in content
    assert '## repolish-end[additional-lint-pr-title-jobs]' in content

    replaced = replace_tags_in_content(
        content,
        {'additional-lint-pr-title-jobs': 'notify:\n  runs-on: ubuntu-latest'},
    )
    assert 'notify:' in replaced


def test_releez_validate_release_anchor_marker_is_replaceable():
    """The additional-validate-release-jobs anchor in validate-release.yaml accepts a real substitution."""
    bed = ProviderTestBed(ReleezProvider, ReleezProviderContext(repo='example'))
    content = bed.render('.github/workflows/validate-release.yaml.jinja')

    assert '## repolish-start[additional-validate-release-jobs]' in content
    assert '## repolish-end[additional-validate-release-jobs]' in content

    replaced = replace_tags_in_content(
        content,
        {
            'additional-validate-release-jobs': 'notify:\n  runs-on: ubuntu-latest',
        },
    )
    assert 'notify:' in replaced


def test_keep_block_content_with_github_actions_expressions_survives_raw_wrapping():
    """A ${{ }} expression injected via a keep-block must not be swallowed by Jinja.

    This mirrors releez's real ci-checks.yaml, where the custom-ci-checks
    keep-block's local content contains {% raw %}-wrapped ${{ matrix.os }}
    etc. Keep-block substitution runs before Jinja, so the injected local
    content is re-processed by Jinja along with the rest of the file — if
    it isn't wrapped, rendering fails with an "undefined" error.
    """
    bed = ProviderTestBed(
        WorkspaceProvider,
        WorkspaceProviderContext(has_python=True),
    )
    content = bed.render('.github/workflows/ci-checks.yaml.jinja')

    local_content = (
        '## start-custom-ci-checks\n'
        '  tests:\n'
        '    runs-on: {% raw %}${{ matrix.os }}{% endraw %}\n'
        '## end-custom-ci-checks\n'
    )
    substituted = apply_keep_replacements(
        content,
        {
            'custom-ci-checks': KeepBlockSpec(
                start='## start-custom-ci-checks',
                end='## end-custom-ci-checks',
            ),
        },
        {},
        {},
        local_content,
    )

    # Re-render the substituted content through Jinja exactly as the real
    # apply pipeline does — this is the step that previously blew up with
    # "'matrix' is undefined" when the ${{ }} wasn't raw-wrapped.
    env = Environment(undefined=StrictUndefined, keep_trailing_newline=True)
    final = env.from_string(substituted).render()
    assert '${{ matrix.os }}' in final
