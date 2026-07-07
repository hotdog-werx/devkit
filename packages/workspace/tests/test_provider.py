"""Tests for WorkspaceProvider."""

from devkit.workspace.repolish.models import WorkspaceProviderContext
from devkit.workspace.repolish.provider import WorkspaceProvider
from repolish.testing import ProviderTestBed


class TestContext:
    def test_default_context(self) -> None:
        bed = ProviderTestBed(WorkspaceProvider)
        ctx = bed.resolved_context
        assert isinstance(ctx, WorkspaceProviderContext)


class TestFileMappings:
    def test_file_mappings_returns_dict(self) -> None:
        bed = ProviderTestBed(WorkspaceProvider)
        fm = bed.file_mappings()
        assert isinstance(fm, dict)


class TestAnchors:
    def test_anchors_returns_dict(self) -> None:
        bed = ProviderTestBed(WorkspaceProvider)
        anchors = bed.anchors()
        assert isinstance(anchors, dict)
