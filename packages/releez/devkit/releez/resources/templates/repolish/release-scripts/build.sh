#!/usr/bin/env bash
set -euo pipefail

if [ -z "${VERSION:-}" ]; then
  echo "ERROR: VERSION must be set in environment" >&2
  exit 1
fi

IS_RELEASE="${IS_RELEASE:-false}"
echo "Building version: ${VERSION} (IS_RELEASE: ${IS_RELEASE})"

if [ -d dist ]; then
  rm -rf dist
fi

echo "Setting version with uv..."
uv version "${VERSION}" --frozen

echo "Building package..."
uv build

echo "Build complete: dist/ contains build artifacts"
ls -lh dist/
