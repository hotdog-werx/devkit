from repolish import BaseContext, BaseInputs


class WorkspaceProviderContext(BaseContext):
    """Context for the WorkspaceProvider."""

    owner: str = ''
    repo: str = ''
    year: str = ''
    workspace_ref: str = 'master'
    python_ref: str = 'master'
    enable_docs: bool = False
    has_python: bool = False
    python_operating_systems: str = '["ubuntu-latest"]'
    python_codecov: bool = False


class WorkspaceProviderInputs(BaseInputs):
    """Inputs for the WorkspaceProvider.

    Fields declared here can be populated by other providers via
    ``provide_inputs`` and delivered to this provider's ``finalize_context``.
    """
