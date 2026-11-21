from pydantic import computed_field
from repolish import BaseContext, BaseInputs


class ReleezProviderContext(BaseContext):
    """Context for the ReleezProvider."""

    devkit_ref: str = 'master'
    build_command: str = 'uv build --no-sources'
    publish_command: str = 'uv publish dist/*'
    package_prefix: str = ''
    use_self_action: bool = False
    # Some consumers only want tagging/changelog/GitHub Release behavior,
    # without a Python package build and publish step.
    publish_package: bool = True

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


class ReleezProviderInputs(BaseInputs):
    """Inputs for the ReleezProvider (no cross-provider inputs used yet)."""
