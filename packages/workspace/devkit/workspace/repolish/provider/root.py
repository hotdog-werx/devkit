from typing_extensions import override

from repolish import ModeHandler, Symlink

from devkit.workspace.repolish.models import WorkspaceProviderContext, WorkspaceProviderInputs


class WorkspaceRootHandler(ModeHandler[WorkspaceProviderContext, WorkspaceProviderInputs]):
    """Provider behavior specific to root-mode workspaces."""

    @override
    def create_default_symlinks(
        self,
    ) -> list[Symlink]:
        """Return symlinks to create in root workspaces."""
        return [
            Symlink(
                source='configs/.editorconfig',
                target='.editorconfig',
            ),
        ]
