import tomllib

from devkit.python.repolish.models import PythonProviderContext
from devkit.python.repolish.provider import (
    PythonProvider,
    _detect_project_source,
)
from repolish.testing import ProviderTestBed


def test_detect_project_source_falls_back_to_src_without_pyproject(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    assert _detect_project_source() == 'src'


def test_detect_project_source_reads_module_name_string(tmp_path, monkeypatch):
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


def test_render_all_succeeds():
    bed = ProviderTestBed(
        PythonProvider,
        PythonProviderContext(project_source='src'),
    )
    rendered = bed.render_all()
    assert 'ruff.toml' in rendered
    assert 'coveragerc.toml' in rendered
    assert 'pydoclint.toml' in rendered


def test_ruff_toml_is_valid_toml():
    bed = ProviderTestBed(PythonProvider, PythonProviderContext())
    rendered = bed.render_all()
    parsed = tomllib.loads(rendered['ruff.toml'])
    assert parsed['lint']['pydocstyle']['convention'] == 'google'


def test_no_pyright_or_basedpyright_anywhere_in_rendered_output():
    """pydoclint/ty replaced pyright entirely — regression test for that decision."""
    bed = ProviderTestBed(PythonProvider, PythonProviderContext())
    rendered = bed.render_all()
    combined = '\n'.join(rendered.values())
    assert 'pyright' not in combined.lower()


def test_no_toolbelt_references_anywhere_in_rendered_output():
    """toolbelt/tbelt was removed entirely in favor of native mise tasks."""
    bed = ProviderTestBed(PythonProvider, PythonProviderContext())
    rendered = bed.render_all()
    combined = '\n'.join(rendered.values())
    assert 'toolbelt' not in combined.lower()
    assert 'tbelt' not in combined.lower()
