from repolish import BaseContext, BaseInputs


class PythonProviderContext(BaseContext):
    """Context for the PythonProvider."""

    project_source: str = 'src'
    ruff_version: str = '0.14.14'
    complexipy_threshold: int = 10
    pydoclint_version: str = 'latest'


class PythonProviderInputs(BaseInputs):
    """Inputs for the PythonProvider (no cross-provider inputs used yet)."""
