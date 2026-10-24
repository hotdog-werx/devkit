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


class ReleezProviderInputs(BaseInputs):
    """Inputs for the ReleezProvider (no cross-provider inputs used yet)."""
