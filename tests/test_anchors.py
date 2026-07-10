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
from repolish.testing import ProviderTestBed


def test_workspace_ci_checks_anchor_marker_is_replaceable():
    bed = ProviderTestBed(
        WorkspaceProvider,
        WorkspaceProviderContext(has_python=True, enable_docs=False),
    )
    content = bed.render('.github/workflows/ci-checks.yaml.jinja')

    # The rendered file must still contain the literal marker text (anchor
    # substitution is a separate preprocessing pass the CLI runs before
    # Jinja in the real pipeline; ProviderTestBed only does the Jinja pass).
    assert '## repolish-start[additional-ci-jobs]' in content
    assert '## repolish-end[additional-ci-jobs]' in content

    replaced = replace_tags_in_content(
        content,
        {'additional-ci-jobs': 'custom-job:\n  runs-on: ubuntu-latest'},
    )
    assert 'custom-job:' in replaced
    assert '## repolish-start[additional-ci-jobs]' not in replaced
    assert '## repolish-end[additional-ci-jobs]' not in replaced


def test_workspace_deploy_docs_anchor_marker_is_replaceable():
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


def test_anchor_content_with_github_actions_expressions_survives_raw_wrapping():
    """A ${{ }} expression injected via an anchor must not be swallowed by Jinja.

    This mirrors releez's real repolish.yaml, where the additional-ci-jobs
    anchor value itself contains {% raw %}-wrapped ${{ matrix.os }} etc.
    Anchor substitution runs before Jinja, so the anchor's own value is
    re-processed by Jinja along with the rest of the file — if it isn't
    wrapped, rendering fails with an "undefined" error.
    """
    bed = ProviderTestBed(
        WorkspaceProvider,
        WorkspaceProviderContext(has_python=True),
    )
    content = bed.render('.github/workflows/ci-checks.yaml.jinja')

    anchor_value = '  tests:\n    runs-on: {% raw %}${{ matrix.os }}{% endraw %}\n'
    substituted = replace_tags_in_content(
        content,
        {'additional-ci-jobs': anchor_value.rstrip('\n')},
    )

    # Re-render the substituted content through Jinja exactly as the real
    # apply pipeline does — this is the step that previously blew up with
    # "'matrix' is undefined" when the ${{ }} wasn't raw-wrapped.
    env = Environment(undefined=StrictUndefined, keep_trailing_newline=True)
    final = env.from_string(substituted).render()
    assert '${{ matrix.os }}' in final
