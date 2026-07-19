# Mise Tasks

Every devkit-provided mise task is referenced in place — no consumer ever
copy-pastes a task definition into its own `mise.toml`. Future task changes in
devkit propagate to every consumer automatically the next time they refresh
their devkit pin.

## Referenced in place, not copy-pasted

This works via mise's
[`task_config.includes`](https://mise.jdx.dev/tasks/task-configuration.html#task-config-options)
setting, which tells mise to scan additional directories (or TOML files) for
task definitions, in addition to (or instead of) the default `mise-tasks/`
directory. A consumer's `mise.toml` looks like this:

```toml
[task_config]
includes = [
  "mise-tasks", # the default, kept explicitly
  ".repolish/hotdogwerx-devkit-workspace/mise-tasks",
  ".repolish/hotdogwerx-devkit-workspace/mise-tasks.toml",
  ".repolish/hotdogwerx-devkit-python/mise-tasks",
]
```

**`includes` _replaces_ the default file-task directories, it doesn't add to
them** — this is why `"mise-tasks"` has to be listed explicitly even though it's
mise's own default.

`.repolish/hotdogwerx-devkit-<name>/` is a whole-resources-directory symlink
that `repolish link` creates automatically for every installed provider,
populated on every `mise install` via a postinstall hook — no `repolish
apply`
required, just `repolish link` (a much lighter operation). Devkit's own repo
(which dogfoods its providers via `provider_root:` rather than installing them
as packages) points `includes` at the local package paths directly instead:

```toml
[task_config]
includes = [
  "mise-tasks",
  "packages/devkit-workspace/devkit/workspace/resources/mise-tasks",
  "packages/devkit-workspace/devkit/workspace/resources/mise-tasks.toml",
  "packages/devkit-python/devkit/python/resources/mise-tasks",
]
```

Two kinds of included content:

- **File-tasks** — executable scripts under a `mise-tasks/` tree, auto-named
  from their directory path (see [naming](#naming-colons-not-hyphens) below).
  Used for anything with real logic (conditionals, multiple steps).
- **A plain `mise-tasks.toml` file** — native `[tasks."name"]`/`["name"]`
  definitions for genuinely simple, single-command tasks (`dprint check`,
  `actionlint`, `zensical build --clean`). Note: an _included_ tasks file uses
  top-level `["name"]` tables, not `[tasks."name"]` — the `tasks.` prefix is
  implicit for included files.

## Naming: colons, not hyphens

Mise namespaces file-tasks from **directory nesting**, not from hyphens or
colons in the filename itself:

```
mise-tasks/python/uv-sync          → task `python:uv-sync`
mise-tasks/python/check/ruff       → task `python:check:ruff`   ✅
mise-tasks/python/check-ruff       → task `python:check-ruff`   ❌ (not check:ruff!)
```

This bit us twice this session — both `check-coverage` and the `check-*` scripts
were initially flat files (`check-ruff`, `check-format`, etc.) that registered
with a hyphen instead of the intended `python:check:ruff`-style colon namespace.
The fix is always to nest one more directory level, e.g.
`mise-tasks/python/check/ruff` instead of `mise-tasks/python/check-ruff`.

File-tasks must also be **executable** (`chmod +x`) — mise silently ignores
non-executable files when scanning `task_config.includes` directories, with no
warning that a task went missing.

## Every task is Python, not bash

Any task with real branching or multi-step logic is a Python script (with a
`#!/usr/bin/env python3` shebang), not bash — `if`/`rm -rf`/shell globs don't
work on Windows, and mise's file-task mechanism works identically regardless of
the script's language. Tasks that are a single direct binary invocation with no
shell scripting at all (`dprint check`, `actionlint`) stay as plain one-line
entries in the included `mise-tasks.toml`, since there's no bash-specific syntax
to be non-portable about.

### Passing `usage` arguments into a Python script

mise's [`usage`](https://mise.jdx.dev/tasks/toml-tasks.html#usage) spec works in
file-tasks via a `#USAGE` frontmatter comment on the second line (after the
shebang):

```python
#!/usr/bin/env python3
#USAGE arg "[files]" var=#true default="." help="Files to format"
import os
files = os.environ.get('usage_files', '.').split()
```

Each declared arg becomes an environment variable named `usage_<argname>` inside
the script — the same naming convention used for `${usage_files}` substitution
in native TOML `run =` strings, just read via `os.environ` instead of
shell-substituted.

**The `default=""` empty-string bug applies here too**: mise's usage engine
renders an empty-string default as the literal two-character string `''`, not a
true empty value. Work around it with a non-empty sentinel:

```python
extra = os.environ.get('usage_extra', '__NONE__')
extra_args = [] if extra == '__NONE__' else extra.split()
```

## Runtime detection over render-time templating

Early in this work, `check-coverage` and `check-complexity` needed per-repo
values (the `--cov=` target, a complexity threshold) — the initial approach
baked these in via Jinja at `repolish apply` time, which meant the files
couldn't be referenced in place (they needed rendering, so they were excluded
from the whole-directory symlink pattern).

The better fix: detect the value **at task execution time** instead, since the
detection logic (reading `pyproject.toml`) is just as cheap to run live as it is
to bake in at render time. Both scripts also support an env var override for the
rare repo where auto-detection isn't right:

- `check-coverage` auto-detects `--cov=<target>` from
  `[tool.uv.build-backend] module-name` in `pyproject.toml`, falling back to
  `src`. Override with `PYTEST_COV_TARGET` in `mise.toml`'s `[env]` — needed for
  devkit's own repo, a bare uv workspace container with no single `module-name`
  to detect (`PYTEST_COV_TARGET = "devkit"`).
- `check-complexity` defaults its `complexipy -mx` threshold to `10`. Override
  with `COMPLEXIPY_THRESHOLD`.

This removed `project_source`/`complexipy_threshold` from
`PythonProviderContext` entirely — nothing needs them anymore.

`check-coverage` is also referenced in place. It excludes
`@pytest.mark.slow`-marked tests by default (`pytest -m "not slow" ...`) and
detects its coverage target from the consumer's `pyproject.toml` each time it
runs, so no per-repository rendering is needed.

## Tool version pinning

Never pin a devkit-managed tool to `"latest"` — it resolves fresh on every CI
run, so "works locally" and "works in CI" can silently mean different tool
versions. This bit us for real: `ty` was pinned to `"latest"` everywhere,
drifted from a stale local cache (`0.0.14`) to whatever PyPI's actual latest was
at CI-run time (`0.0.59`), and the newer version's stricter handling of
invariant generics caught real type errors that had never been checked before.
Pin every tool to an exact version instead.
