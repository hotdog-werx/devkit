from repolish import BaseContext, BaseInputs


class ReleezProviderContext(BaseContext):
    """Context for the ReleezProvider."""

    owner: str = 'hotdog-werx'
    repo: str = ''
    releez_ref: str = 'master'
    build_command: str = 'mise run releez:build'
    publish_command: str = 'mise run releez:publish'
    use_self_action: bool = False
    # Some consumers (e.g. devkit itself, a uv workspace container with no
    # single installable package at its root) only want tagging/changelog/GH
    # release out of the finalize job, not a PyPI build+publish step.
    publish_package: bool = True


class ReleezProviderInputs(BaseInputs):
    """Inputs for the ReleezProvider (no cross-provider inputs used yet)."""
