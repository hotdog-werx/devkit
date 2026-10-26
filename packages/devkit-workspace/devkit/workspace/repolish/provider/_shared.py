from collections.abc import Sequence

from devkit.workspace.repolish.models import (
    WorkspaceProviderContext,
    WorkspaceProviderInputs,
)
from devkit.workspace.repolish.provider.facets.gitignore import GitignoreInputs
from repolish import (
    BaseInputs,
    FinalizeContextOptions,
    ModeHandler,
    ProvideInputsOptions,
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
    def provide_inputs(
        self,
        opt: ProvideInputsOptions[WorkspaceProviderContext],
    ) -> Sequence[BaseInputs]:
        """State which files the workspace itself wants ignored.

        The baseline is not baked into the gitignore facet: this payload
        routes back to this provider's own facet (a provider's emitted
        inputs are delivered to every matching provider, itself included),
        so the baseline renders as the provider's own labeled section and
        the facet stays generic — it renders whatever it receives, and
        what a provider wants ignored lives with the provider. In a repo
        without the workspace provider the payload simply routes nowhere.
        """
        return [
            GitignoreInputs(
                entries=[
                    '.DS_Store',
                    'scratch/**',
                    'mise.local.toml',
                    'tmp*',
                    '.tmp*',
                    '/.editorconfig',
                ],
            ),
        ]

    @override
    def finalize_context(
        self,
        opt: FinalizeContextOptions[
            WorkspaceProviderContext,
            WorkspaceProviderInputs,
        ],
    ) -> WorkspaceProviderContext:
        """Detect whether Python support is enabled for the workspace."""
        updates: dict[str, object] = {}
        if opt.own_context.has_python is None:
            updates['has_python'] = any(
                entry.alias == 'python'
                or (entry.inst_type is not None and entry.inst_type.__module__.startswith('devkit.python.'))
                or (
                    entry.context_type is not None
                    and entry.context_type.__module__.startswith(
                        'devkit.python.',
                    )
                )
                for entry in opt.all_providers
            )

        return opt.own_context.model_copy(update=updates)

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
        #
        # The workflow mappings are the devkit CI treatment (reusable
        # workflows expecting devkit mise task names); a repo that runs its
        # own CI (e.g. repolish) sets manage_workflows: false and this
        # provider claims only the gitignore facet's file. The sources are
        # `_repolish.`-prefixed (staging-only, same convention as the
        # gitignore facet): when the mappings opt out, unmapped conditional
        # templates are never staged, so the files can't surface through
        # auto-staging either.
        if not context.manage_workflows:
            return {}
        return {
            '.github/workflows/ci-checks.yaml': ('.github/workflows/_repolish.ci-checks.yaml'),
            '.github/workflows/deploy-docs.yaml': (
                '.github/workflows/_repolish.deploy-docs.yaml' if context.enable_docs else None
            ),
        }
