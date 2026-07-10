# devkit-releez

Repolish provider: release, publish, and changelog automation for hotdog-werx
repos.

This package wires up [`releez`](https://github.com/hotdog-werx/releez) and
[`git-cliff`](https://git-cliff.org) via a
[`repolish`](https://pypi.org/project/repolish/) provider, pushing:

- `cliff.toml` — git-cliff configuration
- `.github/workflows/finalize-release.yaml` — reusable finalize/build/publish
  workflow that calls the `releez` GitHub Action

## Usage

Add `devkit.releez` as a provider in your `repolish.yaml` configuration. See the
`repolish` documentation for details on wiring providers into a consumer repo.
