"""Tests for WorkspaceProvider."""

from devkit.workspace.repolish.models import WorkspaceProviderContext
from devkit.workspace.repolish.provider import WorkspaceProvider
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


class TestAnchors:
    """create_anchors() returns the expected shape."""

    def test_anchors_returns_dict(self) -> None:
        """anchors() returns a dict, regardless of content."""
        bed = ProviderTestBed(WorkspaceProvider)
        anchors = bed.anchors()
        assert isinstance(anchors, dict)
