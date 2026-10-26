"""Tests for WorkspaceProvider."""

from typing import cast

from devkit.workspace.repolish.models import WorkspaceProviderContext
from devkit.workspace.repolish.provider import WorkspaceProvider
from devkit.workspace.repolish.provider.facets import GitignoreFacet
from devkit.workspace.repolish.provider.facets.gitignore import (
    GitignoreFacetContext,
    GitignoreInputs,
)
from repolish import (
    BaseInputs,
    FacetFinalizeOptions,
    FacetSpecOptions,
    ProvideInputsOptions,
    ProviderInfo,
)
from repolish.providers.models.provider import call_provider_method
from repolish.testing import ProviderTestBed

_WORKSPACE_BASELINE = [
    '.DS_Store',
    'scratch/**',
    'mise.local.toml',
    'tmp*',
    '.tmp*',
    '/.editorconfig',
]


def _provide_inputs(
    bed: ProviderTestBed,
) -> list[BaseInputs]:
    """Collect the bed's provider inputs through the real mode dispatch.

    The test bed has no provide_inputs() convenience, and calling
    provider.provide_inputs() directly would bypass mode-handler dispatch
    (the shared behavior lives on _SharedWorkspaceBehavior, not the
    provider class) — so route through call_provider_method, the same
    entry point the loader uses.
    """
    return cast(
        'list[BaseInputs]',
        call_provider_method(
            bed._instance,
            'provide_inputs',
            ProvideInputsOptions(
                own_context=bed.resolved_context,
                all_providers=[],
                provider_index=0,
            ),
        ),
    )


class TestContext:
    """create_context() resolves to a WorkspaceProviderContext."""

    def test_default_context(self) -> None:
        """With no overrides, resolved_context is still a WorkspaceProviderContext."""
        bed = ProviderTestBed(WorkspaceProvider)
        ctx = bed.resolved_context
        assert isinstance(ctx, WorkspaceProviderContext)


class TestFileMappings:
    """create_file_mappings() returns the expected shape."""

    def test_file_mappings_returns_dict(self) -> None:
        """file_mappings() returns a dict, regardless of content."""
        bed = ProviderTestBed(WorkspaceProvider)
        fm = bed.file_mappings()
        assert isinstance(fm, dict)

    def test_manage_workflows_false_claims_no_workflow(self) -> None:
        """A repo that runs its own CI keeps its workflow files."""
        bed = ProviderTestBed(
            WorkspaceProvider,
            context=WorkspaceProviderContext(manage_workflows=False),
        )
        assert bed.file_mappings() == {}


class TestAnchors:
    """create_anchors() returns the expected shape."""

    def test_anchors_returns_dict(self) -> None:
        """anchors() returns a dict, regardless of content."""
        bed = ProviderTestBed(WorkspaceProvider)
        anchors = bed.anchors()
        assert isinstance(anchors, dict)


class TestProvideInputs:
    """provide_inputs() sends the workspace baseline to its own facet."""

    def test_workspace_sends_gitignore_inputs_to_itself(self) -> None:
        """The baseline is a self-routed GitignoreInputs payload."""
        bed = ProviderTestBed(WorkspaceProvider)
        inputs = _provide_inputs(bed)
        assert len(inputs) == 1
        payload = inputs[0]
        assert isinstance(payload, GitignoreInputs)
        assert payload.entries == _WORKSPACE_BASELINE
        # The sender is never self-declared: the framework stamps the
        # payload at collection, so the facet labels this 'workspace'
        # the same as any other sender's section.
        assert payload.sender is None

    def test_member_mode_emits_nothing(self) -> None:
        """Member-mode workspaces have no repository-wide ignores."""
        bed = ProviderTestBed(WorkspaceProvider, mode='member')
        assert _provide_inputs(bed) == []


class TestGitignoreFacet:
    """The gitignore facet owns .gitignore and merges received entries."""

    def test_provider_declares_the_facet(self) -> None:
        """WorkspaceProvider registers GitignoreFacet."""
        assert WorkspaceProvider.facets == [GitignoreFacet]

    def test_baseline_context(self) -> None:
        """create_context() starts with no sections: every entry arrives as a routed payload.

        The workspace baseline included: it arrives via the provider's own
        provide_inputs payload, not baked into the facet.
        """
        facet = GitignoreFacet()
        ctx = facet.create_context()
        assert isinstance(ctx, GitignoreFacetContext)
        assert ctx.sections == []

    def test_finalize_merges_received_entries_into_sender_sections(
        self,
    ) -> None:
        """Received payloads merge under their sender's section, deduplicated."""
        facet = GitignoreFacet()
        opt = FacetFinalizeOptions(
            own_context=GitignoreFacetContext(),
            received_inputs=[
                GitignoreInputs(
                    sender=ProviderInfo(alias='workspace'),
                    entries=['.DS_Store', 'tmp*'],
                ),
                GitignoreInputs(
                    sender=ProviderInfo(alias='python'),
                    entries=['.venv/', '__pycache__/'],
                ),
                GitignoreInputs(
                    sender=ProviderInfo(alias='python'),
                    entries=['.venv/', 'dist/'],
                ),
                GitignoreInputs(
                    sender=ProviderInfo(alias='releez'),
                    entries=['.releez-cache/'],
                ),
            ],
            all_providers=[],
            provider_index=0,
        )
        final = facet.finalize_context(opt)
        assert [(s.name, s.entries) for s in final.sections] == [
            ('workspace', ['.DS_Store', 'tmp*']),
            ('python', ['.venv/', '__pycache__/', 'dist/']),
            ('releez', ['.releez-cache/']),
        ]

    def test_finalize_skips_unstamped_payloads(self) -> None:
        """A hand-built payload without a sender warns and is skipped."""
        facet = GitignoreFacet()
        opt = FacetFinalizeOptions(
            own_context=GitignoreFacetContext(),
            received_inputs=[GitignoreInputs(entries=['unlabeled/'])],
            all_providers=[],
            provider_index=0,
        )
        final = facet.finalize_context(opt)
        assert final.sections == []

    def test_spec_claims_gitignore(self) -> None:
        """create_spec() maps .gitignore from the conditional template."""
        facet = GitignoreFacet()
        spec = facet.create_spec(
            FacetSpecOptions(
                own_context=GitignoreFacetContext(),
                provider_context=WorkspaceProviderContext(),
            ),
        )
        assert spec.file_mappings == {'.gitignore': '_repolish.gitignore'}
