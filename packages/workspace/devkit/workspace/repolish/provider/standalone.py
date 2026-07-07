from typing_extensions import override

from repolish import ModeHandler, Symlink

from devkit.workspace.repolish.models import WorkspaceProviderContext, WorkspaceProviderInputs


class WorkspaceStandaloneHandler(ModeHandler[WorkspaceProviderContext, WorkspaceProviderInputs]):
    """Provider behavior specific to standalone workspaces."""

    @override
    def create_default_symlinks(
        self,
    ) -> list[Symlink]:
        """Return symlinks to create in standalone workspaces."""
        return [
            Symlink(
                source='configs/.editorconfig',
                target='.editorconfig',
            ),
        ]
