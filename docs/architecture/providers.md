# Providers

Each devkit package (`devkit-workspace`, `devkit-python`, `devkit-releez`)
implements a `repolish.Provider` subclass. A provider has three jobs:

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
      workspace_ref: v1
      python_ref: v1
  python:
    cli: devkit-python-link
  releez:
    cli: devkit-releez-link

providers_order: [workspace, python, releez]
```

`cli: devkit-<name>-link` tells repolish to resolve the provider from an
installed package's console-script entry point (see
[Adopting Devkit](../adopting-devkit.md) for how that package actually gets
installed). Devkit's own repo dogfoods its providers differently — via
`provider_root: ./packages/devkit-<name>/...` pointing directly at the package
source, since there's nothing to "install" when you _are_ the provider.

## `devkit-workspace`

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
  `workspace:repolish:link`, `workspace:docs:dev`, `workspace:docs:build`,
  `workspace:docs:clean`, plus the `workspace:setup-hook`/
  `workspace:pnpm-install` file-tasks

Context detection: `owner`/`repo` from `git remote get-url origin`, `has_python`
from `pyproject.toml`'s `[build-system]` presence, `has_docs`/`enable_docs` from
`zensical.toml` presence.

## `devkit-python`

Python dev tooling — ruff, ty, complexipy, pydoclint, pytest/coverage:

- `ruff.toml` / `pydoclint.toml` — **referenced in place**, not rendered (see
  [Mise Tasks](./mise-tasks.md#referenced-in-place-not-copy-pasted))
- `coveragerc.toml` doesn't exist as a file at all — its settings are plain
  `[tool.coverage.*]` tables, folded straight into the consumer's own
  `pyproject.toml` (see the `pyproject-fragments/python.toml` reference doc
  shipped in the package)
- mise tasks: `python:format`, `python:check:ruff`, `python:check:ty`,
  `python:check:complexity`, `python:check:pydoclint`, `python:uv-sync` (all
  referenced in place), plus `python:check:coverage` (rendered per-repo — see
  below)

`create_context()` returns an empty context — this provider has no per-repo
template variables left to resolve, now that `check-coverage`/
`check-complexity` detect their own targets at runtime instead (see
[Mise Tasks](./mise-tasks.md#runtime-detection-over-render-time-templating)).

## `devkit-releez`

Release/publish/changelog automation:

- `cliff.toml` — rendered per-repo (owner/repo substituted into
  `[remote.github]`)
- `finalize-release.yaml` / `lint-pr-title.yaml` / `validate-release.yaml` —
  thin wrappers around `__releez_publish.yaml` / `__releez_lint-pr-title.yaml` /
  `__releez_validate-release.yaml`
- No mise tasks at all — releez itself already handles tag-pulling before a
  release, and `uv build`/`uv publish` need no wrapper (see
  [Reusable Workflows](../ci/reusable-workflows.md#__releez_publishyaml))

`use_self_action` is auto-detected from `action.yaml`/`action.yml` presence in
the consumer repo — a repo that hosts its own `action.yaml` _is_ releez itself,
and should dogfood its local action (`uses: ./`) instead of the published
`hotdog-werx/releez@v1`. No manual override needed.
