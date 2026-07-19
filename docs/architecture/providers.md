# Providers

Each devkit package (`hotdogwerx-devkit-workspace`, `hotdogwerx-devkit-python`,
`hotdogwerx-devkit-releez`) implements a `repolish.Provider` subclass. A
provider has three jobs:

- **`create_context()`** — build a Pydantic context object with whatever values
  templates need (detected from the consumer's repo, or defaulted).
- **`create_file_mappings(context)`** — return a `dict[dest_path, source]` for
  files that need per-repo templating (Jinja variables, conditional inclusion).
  Files under `templates/repolish/` with no explicit mapping are
  **auto-discovered** and copied/rendered as-is.
- **`create_anchors(context)` / `create_default_symlinks()`** — see
  [Repolish Mechanics](./repolish-mechanics.md).

A consumer's `repolish.yaml` lists which providers to use and in what order:

```yaml
providers:
  workspace:
    cli: devkit-workspace-link
    context_overrides:
      workspace_ref: <immutable-tag-or-sha>
  python:
    cli: devkit-python-link
    context_overrides:
      python_ref: <immutable-tag-or-sha>
  releez:
    cli: devkit-releez-link
    context_overrides:
      releez_ref: <immutable-tag-or-sha>

providers_order: [workspace, python, releez]
```

`cli: devkit-<name>-link` tells repolish to resolve the provider from an
installed package's console-script entry point (see
[Adopting Devkit](../adopting-devkit.md) for how that package actually gets
installed). Devkit's own repo dogfoods its providers differently — via
`provider_root: ./packages/devkit-<name>/...` pointing directly at the package
source, since there's nothing to "install" when you _are_ the provider.

## `hotdogwerx-devkit-workspace`

Repo-agnostic concerns any repo benefits from, regardless of language:

- `.editorconfig` / `dprint.json` — **symlinked**, not rendered (see
  [Repolish Mechanics](./repolish-mechanics.md#symlinks-vs-rendered-files))
- `ci-checks.yaml` — thin wrapper calling `__workspace_repo-checks.yaml` and (if
  `has_python`) `__python_python-checks.yaml`, with a keep-block for
  consumer-specific jobs
- `deploy-docs.yaml` — thin wrapper calling `__workspace_deploy-docs.yaml`,
  rendered only when `enable_docs` is true
- mise tasks: `workspace:dprint:format`, `workspace:dprint:check`,
  `workspace:actionlint:check`, `workspace:repolish:check`,
  `workspace:repolish:link`, `workspace:uv-toolbox-lock:check`,
  `workspace:docs:dev`, `workspace:docs:build`, `workspace:docs:clean`, plus the
  `workspace:setup-hook`/`workspace:pnpm-install` file-tasks

Context detection: `has_python` comes from the loaded provider set and
`enable_docs` from `zensical.toml` presence. Repository identity and year come
from repolish's built-in global context rather than provider-specific Git
subprocesses.

## `hotdogwerx-devkit-python`

Python dev tooling — ruff, ty, complexipy, pydoclint, pytest/coverage:

- `ruff.toml` / `pydoclint.toml` — **referenced in place**, not rendered (see
  [Mise Tasks](./mise-tasks.md#referenced-in-place-not-copy-pasted))
- `coveragerc.toml` doesn't exist as a file at all — its settings are plain
  `[tool.coverage.*]` tables, folded straight into the consumer's own
  `pyproject.toml` (see the `pyproject-fragments/python.toml` reference doc
  shipped in the package)
- mise tasks: `python:format`, `python:check:ruff`, `python:check:ty`,
  `python:check:complexity`, `python:check:pydoclint`, `python:check:coverage`,
  and `python:uv-sync`, all referenced in place

The Python provider owns `python_ref` and emits it through Repolish's typed
provider-input exchange. The workspace provider receives that value when it
composes the optional `python-checks` job; this keeps Python's package-specific
ref out of workspace configuration. Other Python tooling has no per-repo
template variables because `check-coverage`/`check-complexity` detect their
targets at runtime (see
[Mise Tasks](./mise-tasks.md#runtime-detection-over-render-time-templating)).

## `hotdogwerx-devkit-releez`

Release/publish/changelog automation:

- `cliff.toml` — rendered per-repo (owner/repo substituted into
  `[remote.github]`)
- `finalize-release.yaml` / `lint-pr-title.yaml` / `validate-release.yaml` —
  thin wrappers around `__releez_publish.yaml` / `__releez_lint-pr-title.yaml` /
  `__releez_validate-release.yaml`
- No mise tasks at all — releez itself already handles tag-pulling before a
  release, and `uv build`/`uv publish` need no wrapper (see
  [Reusable Workflows](../ci/reusable-workflows.md#__releez_publishyaml))

`use_self_action` defaults to false. Releez itself explicitly sets it to true to
dogfood its local action; other GitHub Action repositories are therefore not
mistaken for releez merely because they contain `action.yaml`.
