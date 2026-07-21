# Adopting Devkit

Steps for a new repo to start consuming devkit's providers.

## 1. Add a `uv-toolbox.yaml` "repolish" environment

Devkit's providers, and `repolish` itself, live in their own
[uv-toolbox](https://github.com/hotdog-werx/uv-toolbox)-managed environment —
never in the consumer's own `.venv`, and never installed as a plain mise-managed
tool. This matters: `repolish` genuinely needs to be part of a uv-toolbox
environment alongside the provider packages it loads, or the whole provisioning
order breaks (see [Postinstall hooks](#3-wire-up-postinstall-hooks)).

```yaml
# uv-toolbox.yaml
environments:
  - name: repolish
    requirements: |
      repolish
      hotdogwerx-devkit-workspace
      hotdogwerx-devkit-python
      hotdogwerx-devkit-releez
    executables:
      - repolish
      - devkit-workspace-link
      - devkit-python-link
      - devkit-releez-link
```

Pin each provider package and its reusable workflows to matching immutable
versions/refs. They are separate distributions even when a devkit release
publishes all three together.

After editing `uv-toolbox.yaml`, regenerate and verify the lockfile:

```bash
uv-toolbox lock
uv-toolbox lock --check
uv-toolbox install
```

## 2. Add `repolish.yaml`

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

post_process:
  - mise run workspace:dprint:format
```

`post_process` must go through `mise run`, not a bare `dprint fmt` —
post-process commands run with `cwd` set to repolish's internal staging
directory, not the project root, and aren't shell-interpreted (no `$VAR`
expansion). `mise run` does its own upward search for `mise.toml` (the same way
git finds `.git`), so it resolves correctly from deep inside the staging
directory; a bare `dprint` can't find the real `dprint.json`.

## 3. Wire up postinstall hooks

```toml
# mise.toml
[[hooks.postinstall]]
run = "uv-toolbox install"

[[hooks.postinstall]]
run = "uv-toolbox exec --env repolish -- repolish link"

[[hooks.postinstall]]
run = "mise run workspace:setup-hook"
```

**Use `[[hooks.postinstall]]` (array-of-tables), not a flat
`postinstall = ["...", "..."]` array.** Newer mise releases (2026.7.5+) silently
run only the _last_ entry of the flat-array form, dropping the earlier steps —
this broke CI in a way that was invisible locally, since the local mise version
at the time still ran all entries correctly. There is no warning when this
happens; the flat form should be treated as unreliable for sequential hooks
going forward.

`repolish link` (not `repolish apply`) is what belongs in a postinstall hook —
it only materializes the whole-resources-directory symlinks
(`.repolish/hotdogwerx-devkit-<name>/`, used by every referenced-in-place mise
task) and the static config symlinks (`.editorconfig`, `dprint.json`). It's safe
to run on every `mise install` without review. `repolish apply` actually
writes/regenerates tracked files and should stay a manual, reviewed operation
(`mise run workspace:repolish:check`/an explicit `repolish
apply`), not
something that runs silently on every install.

## 4. Add `[task_config] includes`

```toml
[task_config]
includes = [
  "mise-tasks",
  ".repolish/hotdogwerx-devkit-workspace/mise-tasks",
  ".repolish/hotdogwerx-devkit-workspace/mise-tasks.toml",
  ".repolish/hotdogwerx-devkit-python/mise-tasks",
]
```

See [Mise Tasks](./architecture/mise-tasks.md) for why `"mise-tasks"` has to be
listed explicitly, and why this is enough to get every devkit task without
copy-pasting any task definitions.

## 5. Add the `[tool.ruff]`/`[tool.coverage.*]` pyproject.toml fragment

Copy `resources/templates/pyproject-fragments/python.toml` from the
`hotdogwerx-devkit-python` package into your own `pyproject.toml` — this is a
reference doc, not auto-merged, so it needs a one-time manual copy. Adjust the
`[tool.ruff] extend` path if you're dogfooding hotdogwerx-devkit-python locally
via `provider_root:` instead of consuming it as a package (see that file's own
comments for the local-path variant).

## 6. Run `mise install` and verify

```bash
rm -f .editorconfig dprint.json  # simulate a fresh checkout
mise install
mise run workspace:repolish:check   # should report zero drift
mise run workspace:uv-toolbox-lock:check
mise run repo-checks                # dprint/actionlint/repolish, all clean
```

If you're adding a keep-block-carrying file (most likely `ci-checks.yaml`, for a
consumer-specific job that must live in the same file as
`repo-checks`/`python-checks`), read
[Repolish Mechanics](./architecture/repolish-mechanics.md#keep-block--keep-rest-preserves-local-content)
first — the dprint-indentation gotcha there is easy to hit and easy to miss in a
single verification pass.
