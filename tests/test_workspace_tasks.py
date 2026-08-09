import runpy
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

LOCK_CHECK_TASK = (
    Path(__file__).parents[1]
    / 'packages/devkit-workspace/devkit/workspace/resources/mise-tasks'
    / 'workspace/uv-toolbox-lock/check'
)


def test_uv_toolbox_lock_check_skips_repo_without_lock(
    tmp_path: Path,
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repositories that do not opt into a lockfile pass without invoking uv-toolbox."""
    monkeypatch.chdir(tmp_path)
    run_mock = mocker.patch('subprocess.run')

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(LOCK_CHECK_TASK), run_name='__main__')

    assert exc_info.value.code == 0
    run_mock.assert_not_called()


def test_uv_toolbox_lock_check_forwards_command_and_exit_code(
    tmp_path: Path,
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repositories with a lock run `uv-toolbox lock --check` and preserve failures."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'uv-toolbox.lock').touch()
    run_mock = mocker.patch('subprocess.run')
    run_mock.return_value.returncode = 7

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(LOCK_CHECK_TASK), run_name='__main__')

    assert exc_info.value.code == 7
    run_mock.assert_called_once_with(
        ['uv-toolbox', 'lock', '--check'],
        check=False,
    )
