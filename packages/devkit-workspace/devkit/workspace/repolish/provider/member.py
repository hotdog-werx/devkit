from devkit.workspace.repolish.models import (
    WorkspaceProviderContext,
    WorkspaceProviderInputs,
)
from repolish import ModeHandler


class WorkspaceMemberHandler(
    ModeHandler[WorkspaceProviderContext, WorkspaceProviderInputs],
):
    """Provider behavior specific to member-mode workspaces."""
