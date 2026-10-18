"""Tests for WorkspaceProvider."""

from devkit.workspace.repolish.models import WorkspaceProviderContext
from devkit.workspace.repolish.provider import WorkspaceProvider
from devkit.workspace.repolish.provider.facets import GitignoreFacet
from devkit.workspace.repolish.provider.facets.gitignore import (
    GitignoreFacetContext,
    GitignoreInputs,
    GitignoreSection,
)
from repolish import FacetFinalizeOptions, FacetSpecOptions, ProviderInfo
from repolish.testing import ProviderTestBed


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


class TestGitignoreFacet:
    """The gitignore facet owns .gitignore and merges received entries."""

    def test_provider_declares_the_facet(self) -> None:
        """WorkspaceProvider registers GitignoreFacet."""
        assert WorkspaceProvider.facets == [GitignoreFacet]

    def test_baseline_context(self) -> None:
        """create_context() starts from the labeled workspace baseline."""
        facet = GitignoreFacet()
        ctx = facet.create_context()
        assert isinstance(ctx, GitignoreFacetContext)
        assert ctx.sections == [
            GitignoreSection(
                name='workspace',
                entries=[
                    '.DS_Store',
                    'scratch/**',
                    'mise.local.toml',
                    'tmp*',
                    '.tmp*',
                    '/.editorconfig',
                ],
            ),
        ]

    def test_finalize_merges_received_entries_into_sender_sections(self) -> None:
        """Received payloads merge under their sender's section, deduplicated."""
        facet = GitignoreFacet()
        opt = FacetFinalizeOptions(
            own_context=GitignoreFacetContext(),
            received_inputs=[
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
            ('workspace', ['.DS_Store', 'scratch/**', 'mise.local.toml', 'tmp*', '.tmp*', '/.editorconfig']),
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
        assert [(s.name, s.entries) for s in final.sections] == [
            ('workspace', ['.DS_Store', 'scratch/**', 'mise.local.toml', 'tmp*', '.tmp*', '/.editorconfig']),
        ]

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
