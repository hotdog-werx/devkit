import re
import subprocess


def get_owner_repo() -> tuple[str, str]:
    """Get the owner and repository name from the git remote URL.

    Returns:
        A tuple containing the owner and repository name.
    """
    git_remote = subprocess.check_output(
        ['git', 'remote', 'get-url', 'origin'],  # noqa: S607 - running git
        text=True,
    ).strip()

    match = re.search(
        r'(?:https://(?:[^/]+@)?github\.com/|git@github\.com:)([^/]+)/([^.]+)(?:\.git)?$',
        git_remote,
    )
    if match:
        owner, repo = match.groups()
        return owner, repo

    msg = f'No owner/repo found in git remote URL: {git_remote}'
    raise ValueError(msg)
