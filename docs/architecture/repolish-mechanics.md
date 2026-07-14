# Repolish Mechanics

Repolish supports several distinct mechanisms for customizing rendered files.
They look similar (marker comments in the template) but behave very differently,
and picking the wrong one causes real bugs.

## Symlinks vs. rendered files

Files with **zero per-repo templating** (no Jinja variables at all) should be
symlinked via `create_default_symlinks()`, not rendered via
`create_file_mappings()`. Devkit uses this for `.editorconfig`/`dprint.json`
only — everything else (`ruff.toml`, `pydoclint.toml`, mise tasks) that's also
fully static is instead **referenced in place** via the
whole-resources-directory symlink `repolish link` creates (see
[Mise Tasks](./mise-tasks.md)), which achieves the same "no physical copy" goal
without a per-file symlink.

## Anchors: provider-computed, not preserved

```
## repolish-start[additional-deploy-jobs]
## post-deploy jobs — add your custom jobs here
## repolish-end[additional-deploy-jobs]
```

A plain anchor's replacement value comes from the provider's `create_anchors()`
— repolish always substitutes whatever that method returns, **every time**,
regardless of what's currently between the markers in the consumer's file. This
is correct for a static placeholder comment (which is all `create_anchors()`
typically returns), but it means anchors **cannot preserve arbitrary content a
consumer wrote there** — a real job definition placed between anchor markers
gets silently discarded on the next `repolish apply`.

## Keep-block / keep-rest: preserves local content

For content that genuinely needs to survive re-applies — most notably,
`ci-checks.yaml`'s consumer-specific jobs (GitHub Actions `needs:` only resolves
within one file, so a job depending on `repo-checks`/ `python-checks` can't live
in a separate workflow file) — use a keep directive instead:

```
## repolish-keep-block[custom-ci-checks]: start="  ## start-custom-ci-checks" end="  ## end-custom-ci-checks"
  ## start-custom-ci-checks
  ## default placeholder text, only used if no local match is found
  ## end-custom-ci-checks
```

Unlike an anchor, a keep-block/keep-rest directive reads the **consumer's
existing file** and, if it finds matching marker(s), preserves that content
verbatim — falling back to the template's own default only when no local match
exists. `keep-block` uses a start+end marker pair; `keep-rest` uses a single
marker and preserves everything from that line to end-of-file.

### The dprint-indentation gotcha

Repolish's marker matching is an **exact string match with no whitespace
normalization** (`line.rstrip('\r\n') == marker`). This caused a real,
hard-to-spot failure: dprint's YAML formatter pulls a comment sitting directly
before an indented job key to match that indent (2 spaces, in `ci-checks.yaml`'s
case), but leaves a comment at true end-of-file alone — so a start marker and an
end marker that started out identically unindented could drift **out of sync
with each other** after a single `dprint fmt` pass:

```yaml
## start-custom-ci-checks    # dprint indented this one (precedes a job key)
test-action:
  ...
## end-custom-ci-checks        # dprint left this one alone (nothing indented follows)
```

Once that happens, repolish's exact-match lookup for the _end_ marker silently
fails, the keep-block falls back to the template's own default placeholder, and
the consumer's real content is gone on the next apply — with
`repolish apply --check` reporting drift, and even a real `apply` believing
there's nothing local to preserve.

**Fix:** declare both markers with the _same_ indentation dprint's own formatter
will stably settle on for that position, and keep both marker lines out of any
content that might make dprint reindent one but not the other. Verify by running
the full `dprint fmt` → `repolish apply` → `repolish apply --check` cycle at
least twice in a row and confirming the custom content survives byte-for-byte
each time — a single verification pass isn't enough to catch this, since the
drift only appears after formatting has actually touched the file.

### Verifying keep-block content survives

Any time you touch a keep-block-carrying file (or the devkit template that
defines its markers), re-verify preservation explicitly — don't assume it
survived just because an earlier check passed:

```bash
grep -c "your-custom-marker-content" path/to/file.yaml
mise exec -- uv-toolbox exec --env repolish -- repolish apply
grep -c "your-custom-marker-content" path/to/file.yaml  # should be unchanged
```
