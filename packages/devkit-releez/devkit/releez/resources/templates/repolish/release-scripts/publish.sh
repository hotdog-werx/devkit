#!/usr/bin/env bash
set -euo pipefail

if [ -z "${VERSION:-}" ]; then
  echo "ERROR: VERSION must be set in environment" >&2
  exit 1
fi
if [ -z "${PYPI_TOKEN:-}" ]; then
  echo "ERROR: PYPI_TOKEN must be set in environment" >&2
  exit 1
fi
IS_RELEASE="${IS_RELEASE:-false}"

if [ "${IS_RELEASE}" != "true" ]; then
  echo "IS_RELEASE is not true, skipping publish (dry run)"
  exit 0
fi

echo "Publishing version ${VERSION} to PyPI..."
UV_PUBLISH_TOKEN="${PYPI_TOKEN}" uv publish dist/*
echo "Publish complete."
