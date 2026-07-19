from devkit.python.repolish.models import (
    PythonProviderContext,
    PythonWorkflowInputs,
)
from repolish import BaseInputs, ProvideInputsOptions, Provider, TemplateMapping
from typing_extensions import override


class PythonProvider(Provider[PythonProviderContext, BaseInputs]):
    """Repolish provider for Python dev tooling.

    Covers ruff, ty, complexipy, pydoclint, and pytest/coverage config.

    Note:
        ``devkit.workspace`` owns the combined `ci-checks.yaml` entry point
        (it decides whether to include a `python-checks` job based on its
        own `has_python` detection) and the underscore-prefixed callable
        `__python_python-checks.yaml` workflow is hand-maintained directly
        in devkit's own repo, not rendered per-consumer here — this
        provider only pushes Python tooling *config*.
    """

    @override
    def create_context(self) -> PythonProviderContext:
        """Build the context for this provider.

        Returns:
            PythonProviderContext: Python-owned provider settings at their
            defaults, including the reusable-workflow ref.
        """
        return PythonProviderContext()

    @override
    def provide_inputs(
        self,
        opt: ProvideInputsOptions[PythonProviderContext],
    ) -> list[BaseInputs]:
        """Supply the Python reusable-workflow ref to composing providers."""
        return [PythonWorkflowInputs(python_ref=opt.own_context.python_ref)]

    @override
    def create_file_mappings(
        self,
        context: PythonProviderContext,
    ) -> dict[str, str | TemplateMapping | None]:
        """Build the destination -> template source mappings.

        Args:
            context (PythonProviderContext): Unused, kept for hook signature
                consistency.

        Returns:
            dict[str, str | TemplateMapping | None]: Empty — every file this
            provider ships (ruff.toml, pydoclint.toml, and the mise tasks
            under resources/mise-tasks/) is fully static (no per-repo
            templating), so nothing needs rendering as a physical copy.
            They're referenced directly from `.repolish/hotdogwerx-devkit-python/`
            (the whole-resources-directory symlink `repolish link` already
            creates) via mise's `task_config.includes` and `[tool.ruff]
            extend`/pydoclint's `--config` flag. coveragerc.toml doesn't
            exist at all; its settings live in the consumer's own
            pyproject.toml `[tool.coverage.*]` tables. See
            resources/templates/pyproject-fragments/python.toml.
        """
        return {}
