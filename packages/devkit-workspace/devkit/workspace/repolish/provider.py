import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from typing_extensions import override

from repolish import Provider, TemplateMapping

from devkit.workspace.repolish.models import WorkspaceContext, WorkspaceInputs

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


class WorkspaceProvider(Provider[WorkspaceContext, WorkspaceInputs]):
    """Repo-agnostic scaffolding provider (editorconfig, dprint, mise base, generic CI)."""

    @override
    def create_context(self) -> WorkspaceContext:
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

        return WorkspaceContext(
            owner=owner,
            repo=repo,
            year=year,
            has_python=has_python,
            enable_docs=enable_docs,
        )

    @override
    def create_file_mappings(
        self,
        context: WorkspaceContext,
    ) -> dict[str, str | TemplateMapping | None]:
        # TODO: mise.toml base-scaffold merging is a follow-up, not blocking.
        # LICENSE and README.md also need anchor-based merging into
        # potentially-existing files and are likewise deferred.
        #
        # NOTE: the underscore-prefixed *callable* workflows this template
        # set references (__workspace_repo-checks.yaml,
        # __python_python-checks.yaml, __workspace_deploy-docs.yaml) are
        # NOT rendered here — they live only in devkit's own
        # .github/workflows/ (hand-maintained), since consumers reference
        # them remotely via `uses: hotdog-werx/devkit/.github/workflows/
        # <name>@ref` rather than needing a local copy. Only the thin,
        # event-driven wrapper files below get pushed to every consumer.
        return {
            '.editorconfig': '.editorconfig',
            'dprint.json': 'dprint.json',
            '.github/workflows/ci-checks.yaml': '.github/workflows/ci-checks.yaml',
            '.github/workflows/deploy-docs.yaml': (
                '.github/workflows/deploy-docs.yaml' if context.enable_docs else None
            ),
        }

    @override
    def create_anchors(self, context: WorkspaceContext) -> dict[str, str]:  # noqa: ARG002
        return {
            'additional-ci-jobs': '## post-check jobs — add your custom jobs here',
            'additional-deploy-jobs': '## post-deploy jobs — add your custom jobs here',
        }
