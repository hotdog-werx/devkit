from repolish import BaseContext, BaseInputs


class WorkspaceContext(BaseContext):
    """Context for the WorkspaceProvider."""

    owner: str = ''
    repo: str = ''
    year: str = ''
    devkit_ref: str = 'master'
    enable_docs: bool = False
    has_python: bool = False


class WorkspaceInputs(BaseInputs):
    """Inputs for the WorkspaceProvider (no cross-provider inputs used yet)."""
