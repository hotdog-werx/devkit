# hotdogwerx-devkit-python

Repolish provider for Python tooling: ruff, ty, complexipy, pydoclint,
pytest/coverage config, and the Python CI check workflow.

This package ships:

- `devkit.python` — a [repolish](https://pypi.org/project/repolish/) provider.
- Static ruff and pydoclint configuration referenced through the provider's
  linked resources directory.
- Cross-platform mise tasks for ruff, ty, complexipy, pydoclint, formatting,
  dependency sync, and pytest/coverage.
- A reference `pyproject.toml` fragment for settings that must remain in each
  consumer's own project configuration.

Note: `devkit.workspace` (package `hotdogwerx-devkit-workspace`) applies first
in any consumer repo and owns repo-wide concerns like `dprint`/`.editorconfig`;
this provider only covers Python-specific tooling.

## Provider

`PythonProvider` renders no files. Static resources are linked and referenced in
place; tasks that need repository-specific values detect them when they run and
provide environment-variable overrides for exceptional layouts.

## Development

This package is part of the `devkit` uv workspace. See the repo root `README.md`
for shared workspace tooling.
