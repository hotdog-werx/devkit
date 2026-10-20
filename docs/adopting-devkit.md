# Adopting Devkit

Steps for a new repo to start consuming devkit's providers.

## 1. Add a `uv-toolbox.yaml` "repolish" environment

Devkit's providers, and `repolish` itself, live in their own
[uv-toolbox](https://github.com/hotdog-werx/uv-toolbox)-managed environment —
never in the consumer's own `.venv`, and never installed as a plain mise-managed
tool. This matters: `repolish` genuinely needs to be part of a uv-toolbox
environment alongside the provider packages it loads, or the whole provisioning
order breaks (see [Postinstall hooks](#3-wire-up-the-postinstall-hooks)).

```yaml
# uv-toolbox.yaml
environments:
  - name: repolish
    dependencies:
      - repolish
      - hotdogwerx-devkit-workspace
      - hotdogwerx-devkit-python
      - hotdogwerx-devkit-releez
    sources:
      hotdogwerx-devkit-workspace:
        git: https://github.com/hotdog-werx/devkit
        tag: <immutable-devkit-tag>
        subdirectory: packages/devkit-workspace
      hotdogwerx-devkit-python:
        git: https://github.com/hotdog-werx/devkit
        tag: <immutable-devkit-tag>
        subdirectory: packages/devkit-python
      hotdogwerx-devkit-releez:
        git: https://github.com/hotdog-werx/devkit
        tag: <immutable-devkit-tag>
        subdirectory: packages/devkit-releez
```

The `dependencies`+`sources` form is uv-toolbox 0.4.1+ (the `requirements` key
it replaces is removed in 1.0); pin by `tag:` for an immutable release, or by
`rev:` when pointing at a raw commit sha.

Install every selected provider and reference every reusable workflow from one
immutable Devkit Git snapshot. Devkit releases and versions the three provider
packages together under one repository tag; it does not publish them to PyPI.

After editing `uv-toolbox.yaml`, regenerate and verify the lockfile:

```bash
uv-toolbox lock
uv-toolbox lock --check
uv-toolbox install
```

## 2. Add `repolish.yaml`

```yaml
module_links: true

providers:
  workspace:
    module: devkit.workspace
    context_overrides:
      devkit_ref: &devkit-ref <immutable-tag-or-sha>
  python:
    module: devkit.python
  releez:
    module: devkit.releez
    context_overrides:
      devkit_ref: *devkit-ref

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

## 3. Wire up the postinstall hooks

```toml
# mise.toml
[[hooks.postinstall]]
run = "mise run workspace:uv-toolbox-install"

[[hooks.postinstall]]
run = "mise run workspace:repolish:link"

[[hooks.postinstall]]
run = "mise run workspace:setup-hook"
```

Three entries, each a named task, so the hook stays dumb and behavior lives with
the tasks. The first two run in every environment: `uv-toolbox install`
provisions the envs (this is where consumer repos get repolish from), and
`repolish link` materializes the config symlinks (`.editorconfig`,
`dprint.json`) — never committed to git (absolute symlink sources are
machine-specific), so every environment links them fresh on every
`mise install`, CI runners included (mise-action's tool install fires these
hooks on every fresh runner), which is what keeps `workspace:dprint:check`
working there.

The third entry is the local-only gate over `setup`: it skips when `CI` is set,
because workflow jobs run their own targeted steps — python checks run
`python:uv-sync` themselves, the docs job has no Python to sync at all, so a
full sync there is wasted work. `setup` stays a local convenience, and what it
does is the providers' decision, not the hook's.

**Use the array-of-tables form, not a flat array.** Newer mise releases
(2026.7.5+) silently run only the _last_ entry of a multi-entry flat
`postinstall` array, dropping the earlier steps — this broke CI in a way that
was invisible locally, since the local mise version at the time still ran all
entries correctly. There is no warning when this happens.

`repolish link` (not `repolish apply`) is what belongs in a hook — it only
materializes the whole-resources-directory symlinks (`.repolish/devkit-<name>/`,
used by every referenced-in-place mise task) and the static config symlinks.
It's safe to run on every `mise install` without review. `repolish apply`
actually writes/regenerates tracked files and should stay a manual, reviewed
operation (`mise run workspace:repolish:check`/an explicit `repolish
apply`),
not something that runs silently on every install.

## 4. Add `[task_config] includes`

```toml
[task_config]
includes = [
  "mise-tasks",
  ".repolish/devkit-workspace/mise-tasks",
  ".repolish/devkit-workspace/mise-tasks.toml",
  ".repolish/devkit-python/mise-tasks",
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
[Repolish Mechanics](./architecture/repolish-mechanics.md#keep-block-keep-rest-preserves-local-content)
first — the dprint-indentation gotcha there is easy to hit and easy to miss in a
single verification pass.
