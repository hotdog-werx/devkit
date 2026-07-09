import re
import subprocess
from typing import TYPE_CHECKING

from typing_extensions import override

from repolish import Provider

from devkit.releez.repolish.models import ReleezProviderContext, ReleezProviderInputs

if TYPE_CHECKING:
    from repolish import TemplateMapping

_GITHUB_REMOTE_PATTERN = re.compile(
    r'(?:https://(?:[^/]+@)?github\.com/|git@github\.com:)([^/]+)/([^.]+)(?:\.git)?$',
)


def _detect_repo() -> str:
    """Derive the repo name from the `origin` git remote, if possible."""
    try:
        remote_url = subprocess.check_output(
            ['git', 'remote', 'get-url', 'origin'],
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, OSError):
        return ''

    match = _GITHUB_REMOTE_PATTERN.search(remote_url)
    if not match:
        return ''
    return match.group(2)


class ReleezProvider(Provider[ReleezProviderContext, ReleezProviderInputs]):
    """Repolish provider for release, publish, and changelog automation."""

    @override
    def create_context(self) -> ReleezProviderContext:
        return ReleezProviderContext(repo=_detect_repo())

    @override
    def create_file_mappings(
        self,
        context: ReleezProviderContext,
    ) -> dict[str, 'str | TemplateMapping | None']:
        # TODO: the mise `[tasks]` fragment (regen-changelog, release-start,
        # build, publish) still needs anchor-based merging into the
        # consumer's `mise.toml` — deferred. Content lives at
        # resources/templates/mise-fragments/releez-tasks.toml for now.
        return {
            'cliff.toml': 'cliff.toml',
            '.github/workflows/finalize-release.yaml': '.github/workflows/finalize-release.yaml',
            '.github/workflows/lint-pr-title.yaml': '.github/workflows/lint-pr-title.yaml',
            '.github/workflows/validate-release.yaml': '.github/workflows/validate-release.yaml',
        }

    @override
    def create_anchors(self, context: ReleezProviderContext) -> dict[str, str]:
        return {
            'additional-jobs': '## post-release jobs — add your custom jobs here',
            'additional-lint-pr-title-jobs': '## post-lint-pr-title jobs — add your custom jobs here',
            'additional-validate-release-jobs': '## post-validate-release jobs — add your custom jobs here',
        }
