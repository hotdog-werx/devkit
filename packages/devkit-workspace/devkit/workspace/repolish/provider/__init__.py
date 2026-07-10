import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from devkit.workspace.repolish.models import (
    WorkspaceProviderContext,
    WorkspaceProviderInputs,
)
from devkit.workspace.repolish.provider.member import WorkspaceMemberHandler
from devkit.workspace.repolish.provider.root import WorkspaceRootHandler
from devkit.workspace.repolish.provider.standalone import (
    WorkspaceStandaloneHandler,
)
from repolish import Provider
from typing_extensions import override

_GITHUB_REMOTE_RE = re.compile(
    r'(?:https://(?:[^/]+@)?github\.com/|git@github\.com:)([^/]+)/([^.]+)(?:\.git)?$',
)


def _detect_owner_repo() -> tuple[str, str]:
    """Best-effort detection of the GitHub owner/repo from the git remote.

    Falls back to empty strings when there is no git remote configured
    (e.g. a fresh scratch repo used in tests) or when the remote URL does
    not match the expected GitHub formats.
    """
    try:
        url = subprocess.check_output(
            ['git', 'remote', 'get-url', 'origin'],
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return '', ''

    match = _GITHUB_REMOTE_RE.search(url)
    if not match:
        return '', ''
    return match.group(1), match.group(2)


class WorkspaceProvider(
    Provider[WorkspaceProviderContext, WorkspaceProviderInputs],
):
    """WorkspaceProvider repolish provider."""

    root_mode = WorkspaceRootHandler
    member_mode = WorkspaceMemberHandler
    standalone_mode = WorkspaceStandaloneHandler

    @override
    def create_context(self) -> WorkspaceProviderContext:
        """Build the context for this provider.

        Note: create_context() is never mode-dispatched (it has no
        ModeHandler equivalent) — it always runs here directly, regardless
        of root/member/standalone mode.
        """
        owner, repo = _detect_owner_repo()
        year = str(datetime.now(UTC).year)

        pyproject = Path('pyproject.toml')
        has_python = pyproject.exists() and '[build-system]' in pyproject.read_text()

        # Presence of zensical's native zensical.toml config is what actually
        # indicates docs tooling is set up (more reliable than checking for a
        # docs/ directory, which may not exist yet even when docs are
        # enabled, or may exist for unrelated reasons). Still overridable via
        # context_overrides if needed.
        enable_docs = Path('zensical.toml').exists()

        return WorkspaceProviderContext(
            owner=owner,
            repo=repo,
            year=year,
            has_python=has_python,
            enable_docs=enable_docs,
        )
