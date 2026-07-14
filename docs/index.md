# devkit

`devkit` is the shared home for repolish providers, mise tasks, and reusable
GitHub Actions workflows used across `hotdog-werx` repos. Instead of copying
config and CI boilerplate into every repo, a consumer installs one or more
devkit providers and gets config, mise tasks, and CI wiring pushed to it (and
kept in sync) by [`repolish`](https://github.com/hotdog-werx/repolish).

## What's in devkit

Three providers, each covering a distinct concern:

| Provider           | Package            | Covers                                                                                             |
| ------------------ | ------------------ | -------------------------------------------------------------------------------------------------- |
| `devkit-workspace` | `devkit.workspace` | `.editorconfig`, `dprint.json`, `ci-checks.yaml`, `deploy-docs.yaml`, dprint/actionlint/docs tasks |
| `devkit-python`    | `devkit.python`    | `ruff.toml`, `pydoclint.toml`, ruff/ty/complexipy/pydoclint/pytest tasks                           |
| `devkit-releez`    | `devkit.releez`    | `cliff.toml`, `finalize-release.yaml`, `lint-pr-title.yaml`, `validate-release.yaml`               |

A consumer repo picks the providers it needs in its own `repolish.yaml` — a CLI
tool (`releez`) doesn't need `devkit-workspace`'s docs-deploy job any more than
a docs-only repo needs `devkit-releez`.

## Documentation

- [Providers](./architecture/providers.md) — what each provider ships, and how
  `create_context`/`create_file_mappings`/`create_anchors` work
- [Mise Tasks](./architecture/mise-tasks.md) — how tasks are referenced in place
  instead of copy-pasted, naming conventions, and why every task is Python
  instead of bash
- [Repolish Mechanics](./architecture/repolish-mechanics.md) — anchors vs.
  keep-blocks vs. keep-rest, and the dprint-indentation gotcha that broke
  keep-blocks in practice
- [Reusable Workflows](./ci/reusable-workflows.md) — every `__*.yaml` reusable
  workflow, its inputs, and how consumers wire them up
- [Adopting Devkit](./adopting-devkit.md) — steps for a new repo to start
  consuming devkit's providers
