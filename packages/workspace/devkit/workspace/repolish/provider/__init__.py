from repolish import Provider

from devkit.workspace.repolish.models import (
    WorkspaceProviderContext,
    WorkspaceProviderInputs,
)
from devkit.workspace.repolish.provider.member import WorkspaceMemberHandler
from devkit.workspace.repolish.provider.root import WorkspaceRootHandler
from devkit.workspace.repolish.provider.standalone import WorkspaceStandaloneHandler


class WorkspaceProvider(Provider[WorkspaceProviderContext, WorkspaceProviderInputs]):
    """WorkspaceProvider repolish provider."""

    root_mode = WorkspaceRootHandler
    member_mode = WorkspaceMemberHandler
    standalone_mode = WorkspaceStandaloneHandler
