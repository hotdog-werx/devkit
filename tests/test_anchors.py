"""Regression tests for Repolish keep-block preprocessing."""

import pytest
from devkit.releez.repolish.models import ReleezProviderContext
from devkit.releez.repolish.provider import ReleezProvider
from devkit.workspace.repolish.models import WorkspaceProviderContext
from devkit.workspace.repolish.provider import WorkspaceProvider
from jinja2 import Environment, StrictUndefined
from repolish.preprocessors.keep import KeepBlockSpec, apply_keep_replacements
from repolish.testing import ProviderTestBed

_START_MARKER = '  ## start-custom-ci-checks'
_END_MARKER = '  ## end-custom-ci-checks'


def test_workspace_ci_checks_keep_block_preserves_local_custom_jobs():
    """The custom-ci-checks keep-block preserves whatever the consumer already wrote.

    Unlike a plain anchor (always reset to a provider-computed value), a
    keep-block is what lets consumers add jobs that must live in the same
    file as repo-checks/python-checks (GitHub Actions `needs:` only works
    within one file) without repolish clobbering them on the next apply.

    Both markers are declared at 2-space indent, matching what dprint's
    yaml formatter settles on for a comment sitting directly before/after
    an indented job key — repolish's marker lookup is an exact string
    match with no whitespace normalization, so if only one marker got
    reformatted (e.g. the end marker left at column 0 because nothing
    indented follows it), the lookup would silently stop matching.
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
    assert _START_MARKER in content
    assert _END_MARKER in content

    local_content = f'{_START_MARKER}\n  tests:\n    runs-on: ubuntu-latest\n{_END_MARKER}\n'
    result = apply_keep_replacements(
        content,
        {
            'custom-ci-checks': KeepBlockSpec(
                start=_START_MARKER,
                end=_END_MARKER,
            ),
        },
        {},
        {},
        local_content,
    )
    assert 'tests:\n    runs-on: ubuntu-latest' in result
    assert 'repolish-keep-block' not in result


@pytest.mark.parametrize(
    ('provider_type', 'context', 'template_name', 'tag'),
    [
        (
            WorkspaceProvider,
            WorkspaceProviderContext(enable_docs=True),
            '.github/workflows/deploy-docs.yaml.jinja',
            'additional-deploy-jobs',
        ),
        (
            ReleezProvider,
            ReleezProviderContext(),
            '.github/workflows/finalize-release.yaml.jinja',
            'additional-jobs',
        ),
        (
            ReleezProvider,
            ReleezProviderContext(),
            '.github/workflows/lint-pr-title.yaml.jinja',
            'additional-lint-pr-title-jobs',
        ),
        (
            ReleezProvider,
            ReleezProviderContext(),
            '.github/workflows/validate-release.yaml.jinja',
            'additional-validate-release-jobs',
        ),
    ],
)
def test_additional_job_keep_blocks_preserve_consumer_jobs(
    provider_type,
    context,
    template_name,
    tag,
):
    """Consumer-owned additional jobs survive re-rendering in every workflow."""
    content = ProviderTestBed(provider_type, context).render(template_name)
    start_marker = f'  ## start-{tag}'
    end_marker = f'  ## end-{tag}'

    assert f'repolish-keep-block[{tag}]' in content
    assert start_marker in content
    assert end_marker in content

    local_content = f'{start_marker}\n  notify:\n    runs-on: ubuntu-latest\n{end_marker}\n'
    result = apply_keep_replacements(
        content,
        {tag: KeepBlockSpec(start=start_marker, end=end_marker)},
        {},
        {},
        local_content,
    )

    assert 'notify:\n    runs-on: ubuntu-latest' in result
    assert f'repolish-keep-block[{tag}]' not in result


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
        f'{_START_MARKER}\n  tests:\n    runs-on: {{% raw %}}${{{{ matrix.os }}}}{{% endraw %}}\n{_END_MARKER}\n'
    )
    substituted = apply_keep_replacements(
        content,
        {
            'custom-ci-checks': KeepBlockSpec(
                start=_START_MARKER,
                end=_END_MARKER,
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
    final = env.from_string(substituted).render(
        secrets={'CODECOV_TOKEN': '${{ secrets.CODECOV_TOKEN }}'},
    )
    assert '${{ matrix.os }}' in final
