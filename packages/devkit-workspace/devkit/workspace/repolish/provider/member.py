from repolish import ModeHandler

from devkit.workspace.repolish.models import WorkspaceProviderContext, WorkspaceProviderInputs


class WorkspaceMemberHandler(ModeHandler[WorkspaceProviderContext, WorkspaceProviderInputs]):
    """Provider behavior specific to member-mode workspaces."""
