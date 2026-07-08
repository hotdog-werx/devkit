# devkit-workspace

Repolish provider: repo-agnostic scaffolding (editorconfig, dprint, mise base,
generic CI) for hotdog-werx repos.

## What it provides

- `.editorconfig`
- `dprint.json`
- Generic reusable CI workflow pieces (`_deploy-docs.yaml`, `deploy-docs.yaml`)
  when the consumer repo has a `docs/` directory
- Base `mise.toml` task fragments (`format-dprint`, `check-dprint`,
  `check-actionlint`, `dev-docs`, `build-docs`, `clean-docs`, `setup`) and
  file-tasks (`pnpm-install`, `setup-hook`) for later integration

## Usage

Add `devkit-workspace` as a repolish provider dependency and reference the
`devkit.workspace` provider module in your `repolish.yaml` configuration.
