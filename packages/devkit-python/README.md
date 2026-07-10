# devkit-python

Repolish provider for Python tooling: ruff, ty, complexipy, pydoclint,
pytest/coverage config, and the Python CI check workflow.

This package ships:

- `devkit.python` — a [repolish](https://pypi.org/project/repolish/) provider
  (`PythonProvider`) that pushes Python dev-tooling config templates
  (`ruff.toml`, `coveragerc.toml`, `pydoclint.toml`) and the shared
  `_ci-checks.yaml` reusable workflow into consumer repos. Type checking uses
  `ty` (latest version) only — `pyright`/`basedpyright` are not used.
- [`toolbelt`](https://pypi.org/project/tbelt/) profile configs
  (`toolbelt/python.yaml`, `toolbelt/python-dev.yaml`) that batch format/check
  commands per file type.

Note: `devkit.workspace` (package `devkit-workspace`) applies first in any
consumer repo and owns repo-wide concerns like `dprint`/`.editorconfig`; this
provider only covers Python-specific tooling.

## Provider

`devkit.python.repolish.provider.PythonProvider` detects the consumer's
`project_source` (`src` by default) from `[tool.uv.build-backend] module-name`
metadata in the consumer's own `pyproject.toml`, then maps template resources to
destination paths in the consumer repo.

## Development

This package is part of the `devkit` uv workspace. See the repo root `README.md`
for shared workspace tooling.
