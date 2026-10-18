"""Regression tests for Repolish keep-block preprocessing."""

from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import devkit.releez
import devkit.workspace
import pytest
from devkit.releez.repolish.models import ReleezProviderContext
from devkit.releez.repolish.provider import ReleezProvider
from devkit.workspace.repolish.models import WorkspaceProviderContext
from devkit.workspace.repolish.provider import WorkspaceProvider
from jinja2 import Environment, StrictUndefined
from repolish.directives.keep import KeepBlockSpec, KeepPatterns, apply_keep_replacements
from repolish.misc import ctx_to_dict
from repolish.testing import ProviderTestBed

_START_MARKER = '## start-custom-ci-checks'
_END_MARKER = '## end-custom-ci-checks'


def test_workspace_ci_checks_keep_block_preserves_local_custom_jobs():
    """The custom-ci-checks keep-block preserves whatever the consumer already wrote.

    Unlike a plain anchor (always reset to a provider-computed value), a
    keep-block is what lets consumers add jobs that must live in the same
    file as repo-checks/python-checks (GitHub Actions `needs:` only works
    within one file) without repolish clobbering them on the next apply.

    Marker values are indentation-neutral because Repolish strips surrounding
    whitespace when matching. The visible YAML comments may therefore remain
    indented under ``jobs`` and be reformatted without losing the block.
    """
    bed = ProviderTestBed(
        WorkspaceProvider,
        WorkspaceProviderContext(has_python=True, enable_docs=False),
    )
    content = bed.render('.github/workflows/_repolish.ci-checks.yaml.jinja')

    # The rendered file must still contain the literal directive + marker
    # text (keep-block substitution is a separate preprocessing pass the
    # CLI runs before Jinja in the real pipeline; ProviderTestBed only does
    # the Jinja pass).
    assert 'repolish-keep-block[custom-ci-checks]' in content
    assert f'  {_START_MARKER}' in content
    assert f'  {_END_MARKER}' in content

    local_content = f'  {_START_MARKER}\n  tests:\n    runs-on: ubuntu-latest\n  {_END_MARKER}\n'
    result = apply_keep_replacements(
        content,
        KeepPatterns(
            blocks={
                'custom-ci-checks': KeepBlockSpec(
                    start=_START_MARKER,
                    end=_END_MARKER,
                ),
            },
            rest={},
            header={},
        ),
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
            '.github/workflows/_repolish.deploy-docs.yaml.jinja',
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
    start_marker = f'## start-{tag}'
    end_marker = f'## end-{tag}'

    assert f'repolish-keep-block[{tag}]' in content
    assert f'  {start_marker}' in content
    assert f'  {end_marker}' in content

    local_content = f'  {start_marker}\n  notify:\n    runs-on: ubuntu-latest\n  {end_marker}\n'
    result = apply_keep_replacements(
        content,
        KeepPatterns(
            blocks={tag: KeepBlockSpec(start=start_marker, end=end_marker)},
            rest={},
            header={},
        ),
        local_content,
    )

    assert 'notify:\n    runs-on: ubuntu-latest' in result
    assert f'repolish-keep-block[{tag}]' not in result


@dataclass(frozen=True)
class KeepBlockTemplate:
    """A workflow template with a keep-block for consumer-owned jobs."""

    provider_type: type[WorkspaceProvider] | type[ReleezProvider]
    context: WorkspaceProviderContext | ReleezProviderContext
    package: ModuleType
    template_name: str
    tag: str

    @property
    def keep_spec(self) -> dict[str, KeepBlockSpec]:
        """The keep-block spec, as the CLI builds it from the directive.

        Returns:
            The spec keyed by the keep-block tag.
        """
        return KeepPatterns(
            blocks={self.tag: KeepBlockSpec(start=f'## start-{self.tag}', end=f'## end-{self.tag}')},
            rest={},
            header={},
        )

    def test_bed(self) -> ProviderTestBed:
        """A test bed for the template's provider.

        Returns:
            A ProviderTestBed for the provider and context.
        """
        return ProviderTestBed(self.provider_type, self.context)

    def render_like_cli(self, local_content: str) -> str:
        """Render in the real CLI order: keep-block substitution, then Jinja.

        ProviderTestBed renders Jinja first, which would hide the bug this
        guards against: in the real pipeline the consumer's preserved jobs
        become part of the template source before Jinja runs.

        Args:
            local_content: The consumer's existing file content.

        Returns:
            The rendered file.
        """
        templates = Path(self.package.__file__ or '').parent / 'resources' / 'templates' / 'repolish'
        template = (templates / self.template_name).read_text(encoding='utf-8')
        substituted = apply_keep_replacements(template, self.keep_spec, local_content)
        env = Environment(undefined=StrictUndefined, keep_trailing_newline=True)
        return env.from_string(substituted).render(**ctx_to_dict(self.test_bed().resolved_context))


_KEEP_BLOCK_TEMPLATES = [
    KeepBlockTemplate(
        WorkspaceProvider,
        WorkspaceProviderContext(has_python=True),
        devkit.workspace,
        '.github/workflows/_repolish.ci-checks.yaml.jinja',
        'custom-ci-checks',
    ),
    KeepBlockTemplate(
        WorkspaceProvider,
        WorkspaceProviderContext(enable_docs=True),
        devkit.workspace,
        '.github/workflows/_repolish.deploy-docs.yaml.jinja',
        'additional-deploy-jobs',
    ),
    *(
        KeepBlockTemplate(
            ReleezProvider,
            ReleezProviderContext(),
            devkit.releez,
            f'.github/workflows/{name}.yaml.jinja',
            tag,
        )
        for name, tag in [
            ('finalize-release', 'additional-jobs'),
            ('lint-pr-title', 'additional-lint-pr-title-jobs'),
            ('validate-release', 'additional-validate-release-jobs'),
        ]
    ),
]


def _template_id(template: KeepBlockTemplate) -> str:
    return Path(template.template_name).name.removesuffix('.yaml.jinja')


@pytest.mark.parametrize('template', _KEEP_BLOCK_TEMPLATES, ids=_template_id)
def test_keep_block_content_with_github_actions_expressions_is_preserved_verbatim(
    template: KeepBlockTemplate,
) -> None:
    """Consumer jobs using ${{ }} expressions survive without any escaping.

    Without the template's raw wrapping, Jinja reads ``${{ matrix.uv }}`` as
    ``$`` plus a Jinja expression and fails with "'matrix' is undefined".
    """
    custom_jobs = (
        f'  ## start-{template.tag}\n'
        '  uv-compatibility:\n'
        '    name: uv ${{ matrix.uv }}\n'
        '    strategy:\n'
        "      matrix:\n        uv: ['0.8.24', '0.12.24']\n"
        f'  ## end-{template.tag}\n'
    )

    rendered = template.render_like_cli(custom_jobs)

    assert rendered.endswith(custom_jobs)
    assert 'raw %}' not in rendered


@pytest.mark.parametrize('template', _KEEP_BLOCK_TEMPLATES, ids=_template_id)
def test_raw_wrapping_leaves_default_output_unchanged(template: KeepBlockTemplate) -> None:
    """With no local content, the output matches the Jinja-first render of the template default."""
    rendered = template.render_like_cli('')
    default = template.test_bed().render(template.template_name)

    assert rendered == apply_keep_replacements(default, template.keep_spec, '')
    assert rendered.endswith(f'  ## end-{template.tag}\n')
    assert 'raw %}' not in rendered
