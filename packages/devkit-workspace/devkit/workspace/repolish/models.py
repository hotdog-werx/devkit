from pydantic import Field
from repolish import BaseContext, BaseInputs


class WorkspaceProviderContext(BaseContext):
    """Context for the WorkspaceProvider."""

    devkit_ref: str = 'master'
    enable_docs: bool = False
    has_python: bool | None = None
    manage_workflows: bool = True
    python_operating_systems: list[str] = Field(
        default_factory=lambda: ['ubuntu-latest'],
    )
    python_codecov: bool = False


class WorkspaceProviderInputs(BaseInputs):
    """Inputs for the WorkspaceProvider (no cross-provider inputs used)."""
