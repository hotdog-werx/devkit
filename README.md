# devkit

The base devkit for hotdog-werx repositories. Provides universal tooling, CI
orchestration, and templates to maintain consistent standards across projects.

## What it provides

- **Universal configs**: `.editorconfig`, markdown formatting (dprint).
- **CI orchestration**: Composable `ci-checks` workflow that dynamically
  includes checks from opted-in devkits.
- **Templates**: Repolish templates for consistent repo setup (gitignore,
  workflows, etc.).
- **Tooling**: Mise-managed tools for development and maintenance.

## Usage

Repos opt into devkits via repolish configuration. The base `devkit` ensures
every repo has essential checks and standards.

For more details, see the [docs](https://hotdog-werx.github.io/devkit/) (coming
soon).
