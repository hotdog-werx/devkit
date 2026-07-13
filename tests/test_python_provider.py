import tomllib
from pathlib import Path

from devkit.python.repolish.models import PythonProviderContext
from devkit.python.repolish.provider import (
    PythonProvider,
    _detect_project_source,
)
from repolish.testing import ProviderTestBed

_RESOURCES = Path(__file__).parents[1] / 'packages/devkit-python/devkit/python/resources'
_RUFF_TOML = (_RESOURCES / 'configs/ruff.toml').read_text()
_PYDOCLINT_TOML = (_RESOURCES / 'configs/pydoclint.toml').read_text()


def test_detect_project_source_falls_back_to_src_without_pyproject(
    tmp_path,
    monkeypatch,
):
    """With no pyproject.toml at all, the fallback source dir is 'src'."""
    monkeypatch.chdir(tmp_path)
    assert _detect_project_source() == 'src'


def test_detect_project_source_reads_module_name_string(tmp_path, monkeypatch):
    """module-name as a bare string is used directly as the source dir."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'pyproject.toml').write_text(
        '[tool.uv.build-backend]\nmodule-name = "releez"\n',
    )
    assert _detect_project_source() == 'releez'


def test_detect_project_source_reads_module_name_list(tmp_path, monkeypatch):
    """uv-toolbox's real pyproject.toml uses a list, not a bare string, here."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'pyproject.toml').write_text(
        '[tool.uv.build-backend]\nmodule-name = ["uv_toolbox"]\n',
    )
    assert _detect_project_source() == 'uv_toolbox'


def test_render_all_excludes_static_configs():
    """Static configs are referenced directly, not rendered as copies.

    ruff.toml/pydoclint.toml/uv-sync are static and referenced directly from
    the provider's linked resources directory instead of being rendered as
    physical copies; coveragerc.toml doesn't exist at all anymore (folded
    into the consumer's own pyproject.toml). check-coverage is unrelated to
    this and is still expected (it needs this repo's own project_source, so
    it's rendered per-repo rather than referenced in place).
    """
    bed = ProviderTestBed(
        PythonProvider,
        PythonProviderContext(project_source='src'),
    )
    rendered = bed.render_all()
    assert 'ruff.toml' not in rendered
    assert 'coveragerc.toml' not in rendered
    assert 'pydoclint.toml' not in rendered
    assert 'mise-tasks/python/uv-sync' not in rendered
    assert 'mise-tasks/python/check-coverage' in rendered


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
