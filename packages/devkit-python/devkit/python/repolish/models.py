from repolish import BaseContext, BaseInputs


class PythonProviderContext(BaseContext):
    """Context for the PythonProvider."""

    python_ref: str = 'master'


class PythonWorkflowInputs(BaseInputs):
    """Python workflow settings supplied to composing providers."""

    python_ref: str
