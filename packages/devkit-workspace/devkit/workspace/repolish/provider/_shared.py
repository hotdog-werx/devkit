from typing_extensions import override

from repolish import ModeHandler, Symlink, TemplateMapping

from devkit.workspace.repolish.models import (
    WorkspaceProviderContext,
    WorkspaceProviderInputs,
)


class _SharedWorkspaceBehavior(
    ModeHandler[WorkspaceProviderContext, WorkspaceProviderInputs],
):
    """Behavior shared by root- and standalone-mode workspaces.

    Member mode gets none of this (see member.py) — consumer repos in this
    org are never repolish workspace *members* themselves.
    """

    @override
    def create_default_symlinks(self) -> list[Symlink]:
        return [
            Symlink(source='configs/.editorconfig', target='.editorconfig'),
            Symlink(source='configs/dprint.json', target='dprint.json'),
        ]

    @override
    def create_file_mappings(
        self,
        context: WorkspaceProviderContext,
    ) -> dict[str, str | TemplateMapping | None]:
        # TODO: mise.toml base-scaffold merging is a follow-up, not blocking.
        # LICENSE and README.md also need anchor-based merging into
        # potentially-existing files and are likewise deferred.
        return {
            '.github/workflows/ci-checks.yaml': '.github/workflows/ci-checks.yaml',
            '.github/workflows/deploy-docs.yaml': (
                '.github/workflows/deploy-docs.yaml' if context.enable_docs else None
            ),
        }

    @override
    def create_anchors(
        self,
        context: WorkspaceProviderContext,  # noqa: ARG002
    ) -> dict[str, str]:
        return {
            'additional-ci-jobs': '## post-check jobs — add your custom jobs here',
            'additional-deploy-jobs': '## post-deploy jobs — add your custom jobs here',
        }
