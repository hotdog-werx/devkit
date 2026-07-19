# Reusable Workflows

Every `__*.yaml` file in `.github/workflows/` is a reusable workflow
(`on: workflow_call`), hand-maintained directly in devkit's own repo (not
repolish-rendered — a consumer's own thin wrapper _calls into_ these, it doesn't
carry their logic). Consumers reference them with
`uses: hotdog-werx/devkit/.github/workflows/__<name>.yaml@<ref>`.

## `__workspace_repo-checks.yaml`

Runs dprint, actionlint, repolish drift, conditional `uv-toolbox.lock`
validation, and (if `enable-docs` is true) the docs build. Every check step is
`if: always() && !cancelled()` so one failure does not hide the others.

```yaml
inputs:
  enable-docs:
    type: boolean
    default: false
```

## `__python_python-checks.yaml`

Split into two jobs:

- **`lint`** — `check-python` (ruff check + format check), `check-ty`,
  `check-complexity`, `check-pydoclint` (the last is `continue-on-error: true`,
  since pydoclint's arg-type-hint checks are stricter than most codebases
  currently satisfy). Always runs once on `ubuntu-latest` — lint checks are
  OS-independent, so matrixing them would just waste CI minutes.
- **`test`** — `check-coverage`, matrixed across `operating-systems`, with an
  optional Codecov upload.

```yaml
inputs:
  operating-systems:
    description: 'JSON array of operating systems to run pytest/coverage on'
    type: string
    default: '["ubuntu-latest"]'
  codecov:
    description: 'Whether to generate a coverage XML report and upload to Codecov'
    type: boolean
    default: false
secrets:
  CODECOV_TOKEN:
    required: false
```

A consumer opts into a full OS matrix + Codecov via its own `repolish.yaml`:

```yaml
providers:
  workspace:
    context_overrides:
      python_operating_systems: [ubuntu-latest, windows-latest]
      python_codecov: true
```

This absorbed what used to be releez's own hand-maintained `tests` job (a
Linux+Windows matrix with Codecov upload, duplicated per-consumer) — after this
change, releez's `ci-checks.yaml` keep-block only needs to carry the
`test-action` job (the `act`-driven GitHub Actions test suite), which genuinely
can't be shared since it drives releez's own `action.yaml`.

**Note on `check-format`:** an earlier version of this workflow had a separate
`check-format` step running `ruff format --check .` — this was pure duplication,
since `check-python` (`python:check:ruff`) already runs `ruff format --check .`
as its second command. Removed entirely; nothing else referenced it.

## `__workspace_deploy-docs.yaml`

Two jobs: `check-docs` (detects `zensical.toml` presence, gates the second job
on it) and `build-and-deploy` (installs deps, builds via `workspace:docs:build`,
deploys to GitHub Pages). No lint/check steps — deploying docs doesn't need to
re-run Python lint checks, that's CI's job.

## `__releez_publish.yaml` / `__releez_lint-pr-title.yaml` / `__releez_validate-release.yaml`

Each accepts a `use-self-action` boolean input, since GitHub Actions' `uses:`
field **cannot reference a dynamic expression** — it must be a static string.
This is worked around with two mutually-exclusive steps, each with a static
`uses:`:

```yaml
- name: Releez finalize (published action)
  if: '!inputs.use-self-action'
  uses: hotdog-werx/releez@v1
  with:
    mode: finalize

- name: Releez finalize (self action)
  if: inputs.use-self-action
  uses: ./
  with:
    mode: finalize
```

Outputs from whichever step actually ran are merged with `||`:
`${{ steps.releez-published.outputs.x || steps.releez-self.outputs.x }}`.

The publish and validate workflows also accept `project`, defaulting to `''`.
They forward it to the Releez action; an empty value uses release-branch
detection.

`__releez_publish.yaml`'s `build-command`/`publish-command` inputs default to
plain `uv build`/`uv publish` commands (`uv build --no-sources`,
`uv publish dist/*`) — no mise task wrapper. `--no-sources` verifies that the
distribution can build from its published metadata rather than relying on
workspace-only source overrides.

For a monorepo release, the workflow reads the single `project` and singular
`pep440-version` emitted by Releez finalize. It passes that project to
`uv version --package`; single-project repositories retain the normal root
project behavior. A monorepo can customize `build-command` to build the selected
package using the exported `PROJECT` environment variable. When Releez project
IDs differ from Python distribution names, `package-prefix` is prepended for
`uv version`; the same `PACKAGE_PREFIX` value is exported to custom build
commands.

## Reusable-workflow permission ceilings

A called reusable workflow's `permissions:` can never exceed what the
**calling** wrapper grants at its own top level, regardless of what the reusable
workflow itself declares. Every thin-wrapper template
(`lint-pr-title.yaml.jinja`, `validate-release.yaml.jinja`, etc.) must
explicitly declare the `permissions:` block its called workflow needs — this was
caught via a real CI failure ("requesting 'pull-requests: write', but is only
allowed 'pull-requests: none'") after a template was missing one.
