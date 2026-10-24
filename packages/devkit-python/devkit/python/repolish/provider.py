from collections.abc import Sequence

from devkit.python.repolish.models import (
    PythonProviderContext,
    PythonProviderInputs,
)
from devkit.workspace.repolish.provider.facets.gitignore import GitignoreInputs
from repolish import BaseInputs, ProvideInputsOptions, Provider, TemplateMapping
from typing_extensions import override


class PythonProvider(Provider[PythonProviderContext, PythonProviderInputs]):
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
        defaults.
        """
        return PythonProviderContext()

    @override
    def create_file_mappings(
        self,
        context: PythonProviderContext,
    ) -> dict[str, str | TemplateMapping | None]:
        """Build the destination -> template source mappings.

        Args:
            context: Unused, kept for hook signature consistency.

        Returns:
            Empty — every file this provider ships (ruff.toml, pydoclint.toml, and the mise tasks
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

    @override
    def provide_inputs(
        self,
        opt: ProvideInputsOptions[PythonProviderContext],
    ) -> Sequence[BaseInputs]:
        """Tell the workspace provider which Python artifacts to ignore.

        The workspace gitignore facet collects these entries into the
        rendered .gitignore head, under this provider's own section (the
        framework stamps the payload with the sender's identity, so the
        facet labels the block from the provider alias, not from anything
        declared here). In a repo without the workspace provider the
        payload simply routes nowhere.
        """
        return [
            GitignoreInputs(
                entries=[
                    '.venv/',
                    '__pycache__/',
                    '*.pyc',
                    '*.egg-info/',
                    'build/',
                    'dist/',
                    '.coverage',
                    '.coverage.*',
                    '.coverage-files/',
                    'htmlcov/',
                    '.pytest_cache/',
                ],
            ),
        ]
