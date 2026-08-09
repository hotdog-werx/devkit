import tomllib
from pathlib import Path

from devkit.python.repolish.models import PythonProviderContext
from devkit.python.repolish.provider import PythonProvider
from repolish.testing import ProviderTestBed

_RESOURCES = Path(__file__).parents[1] / 'packages/devkit-python/devkit/python/resources'
_RUFF_TOML = (_RESOURCES / 'configs/ruff.toml').read_text()
_PYDOCLINT_TOML = (_RESOURCES / 'configs/pydoclint.toml').read_text()


def test_render_all_is_empty():
    """Nothing is rendered — every file this provider ships is fully static.

    ruff.toml/pydoclint.toml/uv-sync/check-coverage/etc. are all referenced
    directly from the provider's linked resources directory instead of
    being rendered as physical copies; coveragerc.toml doesn't exist at all
    (folded into the consumer's own pyproject.toml).
    """
    bed = ProviderTestBed(PythonProvider, PythonProviderContext())
    assert bed.render_all() == {}


def test_ruff_toml_is_valid_toml():
    """The shared ruff.toml parses and sets the expected docstring convention."""
    parsed = tomllib.loads(_RUFF_TOML)
    assert parsed['lint']['pydocstyle']['convention'] == 'google'


def test_no_pyright_or_basedpyright_anywhere_in_static_configs():
    """pydoclint/ty replaced pyright entirely — regression test for that decision."""
    combined = f'{_RUFF_TOML}\n{_PYDOCLINT_TOML}'
    assert 'pyright' not in combined.lower()


def test_no_toolbelt_references_anywhere_in_static_configs():
    """toolbelt/tbelt was removed entirely in favor of native mise tasks."""
    combined = f'{_RUFF_TOML}\n{_PYDOCLINT_TOML}'
    assert 'toolbelt' not in combined.lower()
    assert 'tbelt' not in combined.lower()
