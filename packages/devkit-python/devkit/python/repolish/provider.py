import tomllib
from pathlib import Path

from devkit.python.repolish.models import (
    PythonProviderContext,
    PythonProviderInputs,
)
from repolish import Provider, TemplateMapping
from typing_extensions import override


def _detect_project_source() -> str:
    """Detect the consumer's project source directory.

    Reads the consumer's own ``pyproject.toml`` looking for
    ``[tool.uv.build-backend] module-name``, which in a flat (non-src)
    layout is also the on-disk source directory name (e.g. ``uv_toolbox``).
    ``module-name`` may be a string or a list of strings (uv supports both);
    the first entry is used when it's a list. Falls back to ``'src'`` if the
    file is missing, unreadable, malformed, or the key isn't present.

    Returns:
        The detected project source directory, or ``'src'`` as a fallback.
    """
    pyproject_path = Path('pyproject.toml')
    if not pyproject_path.exists():
        return 'src'

    try:
        data = tomllib.loads(pyproject_path.read_text())
        module_name = data['tool']['uv']['build-backend']['module-name']
    except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError):
        return 'src'

    if isinstance(module_name, list):
        return module_name[0] if module_name else 'src'
    return module_name


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
            A `PythonProviderContext` with `project_source` detected from the
            consumer's `pyproject.toml`, and all other fields left at their
            Pydantic defaults.
        """
        return PythonProviderContext(project_source=_detect_project_source())

    @override
    def create_file_mappings(
        self,
        context: PythonProviderContext,
    ) -> dict[str, str | TemplateMapping | None]:
        """Build the destination -> template source mappings.

        Returns:
            Mapping of destination paths in the consumer repo to template
            source strings.
        """
        # NOTE: The mise `[tasks]` fragment for Python tasks (format-python,
        # check-python, check-format, check-ty, check-complexity,
        # check-pydoclint, check-coverage, uv-sync) isn't auto-merged into
        # the consumer's mise.toml (anchor-based TOML merging isn't built
        # yet) — it's hand-copied from
        # resources/templates/mise-fragments/python-tasks.toml.
        return {
            'ruff.toml': 'ruff.toml',
            'coveragerc.toml': 'coveragerc.toml',
            'pydoclint.toml': 'pydoclint.toml',
        }
