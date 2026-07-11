import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from devkit.releez.repolish.models import (
    ReleezProviderContext,
    ReleezProviderInputs,
)
from repolish import Provider
from typing_extensions import override

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


def _detect_self_action() -> bool:
    """Detect whether this repo hosts its own hotdog-werx/releez action.yaml.

    A repo that has one *is* releez — it should dogfood its own action
    (`uses: ./`) instead of the published `hotdog-werx/releez@v1`.
    """
    return Path('action.yaml').exists() or Path('action.yml').exists()


class ReleezProvider(Provider[ReleezProviderContext, ReleezProviderInputs]):
    """Repolish provider for release, publish, and changelog automation."""

    @override
    def create_context(self) -> ReleezProviderContext:
        return ReleezProviderContext(
            repo=_detect_repo(),
            use_self_action=_detect_self_action(),
        )

    @override
    def create_file_mappings(
        self,
        context: ReleezProviderContext,
    ) -> dict[str, 'str | TemplateMapping | None']:
        # NOTE: the mise `[tasks]` fragment (regen-changelog, release-start,
        # build, publish) isn't auto-merged into the consumer's `mise.toml`
        # (anchor-based TOML merging isn't built yet) — it's hand-copied
        # from resources/templates/mise-fragments/releez-tasks.toml.
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
