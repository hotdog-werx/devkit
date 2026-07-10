from repolish import BaseContext, BaseInputs


class PythonProviderContext(BaseContext):
    """Context for the PythonProvider."""

    project_source: str = 'src'
    complexipy_threshold: int = 10


class PythonProviderInputs(BaseInputs):
    """Inputs for the PythonProvider (no cross-provider inputs used yet)."""
