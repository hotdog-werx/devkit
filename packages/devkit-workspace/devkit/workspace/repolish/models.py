from pydantic import Field, computed_field
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
    python_mustard: bool = False
    # Mustard flag for the Python upload. Empty keeps Mustard's `default` flag.
    python_mustard_flag: str = ''

    # devkit's own repository calls its reusable workflows from the same
    # commit (`uses: ./.github/workflows/...`) so a PR tests its own workflow
    # changes instead of whatever devkit_ref points at. Only valid in devkit.
    devkit_local_workflows: bool = False

    @computed_field
    @property
    def devkit_workflow_prefix(self) -> str:
        """Return the reusable-workflow path prefix for `uses:` lines."""
        if self.devkit_local_workflows:
            return './.github/workflows/'
        return 'hotdog-werx/devkit/.github/workflows/'

    @computed_field
    @property
    def devkit_workflow_suffix(self) -> str:
        """Return the `@ref` suffix, empty for same-commit local workflows."""
        return '' if self.devkit_local_workflows else f'@{self.devkit_ref}'


class WorkspaceProviderInputs(BaseInputs):
    """Inputs for the WorkspaceProvider (no cross-provider inputs used)."""
