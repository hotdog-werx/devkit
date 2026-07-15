import os
import subprocess
from pathlib import Path

LOCK_CHECK_TASK = (
    Path(__file__).parents[1]
    / 'packages/devkit-workspace/devkit/workspace/resources/mise-tasks'
    / 'workspace/uv-toolbox-lock/check'
)


def test_uv_toolbox_lock_check_skips_repo_without_lock(tmp_path: Path) -> None:
    """Repositories that do not opt into a lockfile pass without invoking uv-toolbox."""
    result = subprocess.run(  # noqa: S603 - execute the checked-in task under test
        [LOCK_CHECK_TASK],
        cwd=tmp_path,
        check=False,
    )

    assert result.returncode == 0


def test_uv_toolbox_lock_check_forwards_command_and_exit_code(
    tmp_path: Path,
) -> None:
    """Repositories with a lock run `uv-toolbox lock --check` and preserve failures."""
    (tmp_path / 'uv-toolbox.lock').touch()
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    log_path = tmp_path / 'arguments.log'
    fake_uv_toolbox = bin_dir / 'uv-toolbox'
    fake_uv_toolbox.write_text(
        '#!/bin/sh\nprintf "%s\\n" "$@" > "$UV_TOOLBOX_LOG"\nexit 7\n',
    )
    fake_uv_toolbox.chmod(0o755)

    result = subprocess.run(  # noqa: S603 - execute the checked-in task under test
        [LOCK_CHECK_TASK],
        cwd=tmp_path,
        env={
            **os.environ,
            'PATH': f'{bin_dir}{os.pathsep}{os.environ["PATH"]}',
            'UV_TOOLBOX_LOG': str(log_path),
        },
        check=False,
    )

    assert result.returncode == 7
    assert log_path.read_text().splitlines() == ['lock', '--check']
