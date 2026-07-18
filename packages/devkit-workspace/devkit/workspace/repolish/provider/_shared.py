from devkit.workspace.repolish.models import (
    WorkspaceProviderContext,
    WorkspaceProviderInputs,
)
from repolish import (
    FinalizeContextOptions,
    ModeHandler,
    Symlink,
    TemplateMapping,
)
from typing_extensions import override


class _SharedWorkspaceBehavior(
    ModeHandler[WorkspaceProviderContext, WorkspaceProviderInputs],
):
    """Behavior shared by root- and standalone-mode workspaces.

    Member mode uses the provider's no-op defaults; repository-wide files and
    tasks belong only at a workspace root or in a standalone repository.

    Note: these symlinks use an absolute path to their source, so they must
    never be committed to git (see .gitignore) — every environment (local
    dev, CI) is expected to run `repolish link` for itself (the
    workspace:repolish:link mise task), which recreates them fresh and
    correctly for that machine's checkout path.
    """

    @override
    def finalize_context(
        self,
        opt: FinalizeContextOptions[
            WorkspaceProviderContext,
            WorkspaceProviderInputs,
        ],
    ) -> WorkspaceProviderContext:
        """Derive Python support from provider composition unless overridden."""
        if opt.own_context.has_python is not None:
            return opt.own_context

        has_python = any(
            entry.alias == 'python'
            or (entry.inst_type is not None and entry.inst_type.__module__.startswith('devkit.python.'))
            or (entry.context_type is not None and entry.context_type.__module__.startswith('devkit.python.'))
            for entry in opt.all_providers
        )
        return opt.own_context.model_copy(update={'has_python': has_python})

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
        # NOTE: mise.toml base-scaffold merging isn't built yet. LICENSE and
        # README.md also need anchor-based merging into potentially-existing
        # files and are likewise not yet implemented.
        return {
            '.github/workflows/ci-checks.yaml': '.github/workflows/ci-checks.yaml',
            '.github/workflows/deploy-docs.yaml': (
                '.github/workflows/deploy-docs.yaml' if context.enable_docs else None
            ),
        }

    @override
    def create_anchors(
        self,
        context: WorkspaceProviderContext,
    ) -> dict[str, str]:
        # ci-checks.yaml's custom-job region is a repolish-keep-block
        # directive instead of a plain anchor (see the .jinja template) —
        # it preserves whatever job YAML the consumer already wrote there
        # across re-applies, rather than always resetting to a static
        # provider-computed placeholder.
        return {
            'additional-deploy-jobs': '## post-deploy jobs — add your custom jobs here',
        }
