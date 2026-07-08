from repolish import BaseContext, BaseInputs


class ReleezContext(BaseContext):
    """Context for the ReleezProvider."""

    owner: str = 'hotdog-werx'
    repo: str = ''
    build_command: str = 'mise run build'
    publish_command: str = 'mise run publish'
    releez_action_version: str = 'v1'
    use_self_action: bool = False


class ReleezInputs(BaseInputs):
    """Inputs for the ReleezProvider (no cross-provider inputs used yet)."""
