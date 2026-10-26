from pathlib import Path
from typing import Any, ClassVar, override

from devkit.workspace.repolish.models import (
    WorkspaceProviderContext,
    WorkspaceProviderInputs,
)
from devkit.workspace.repolish.provider._shared import _SharedWorkspaceBehavior
from devkit.workspace.repolish.provider.facets import GitignoreFacet
from repolish import Provider, ProviderFacet


class WorkspaceProvider(
    Provider[WorkspaceProviderContext, WorkspaceProviderInputs],
):
    """WorkspaceProvider repolish provider."""

    root_mode = _SharedWorkspaceBehavior
    standalone_mode = _SharedWorkspaceBehavior

    facets: ClassVar[list[type[ProviderFacet[Any, Any]]] | None] = [
        GitignoreFacet,
    ]

    @override
    def create_context(self) -> WorkspaceProviderContext:
        """Build the context for this provider.

        Note: create_context() is never mode-dispatched (it has no
        ModeHandler equivalent) — it always runs here directly, regardless
        of root/member/standalone mode.
        """
        # Presence of zensical's native zensical.toml config is what actually
        # indicates docs tooling is set up (more reliable than checking for a
        # docs/ directory, which may not exist yet even when docs are
        # enabled, or may exist for unrelated reasons). Still overridable via
        # context_overrides if needed.
        enable_docs = Path('zensical.toml').exists()

        return WorkspaceProviderContext(
            enable_docs=enable_docs,
        )
