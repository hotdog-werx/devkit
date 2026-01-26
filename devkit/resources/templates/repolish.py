from datetime import UTC, datetime
from typing import Any

from devkit.github_utils import get_owner_repo


def create_context() -> dict[str, Any]:
    """Base context for repolish."""
    owner, repo = get_owner_repo()
    return {
        'owner': owner,
        'repo': repo,
        'year': str(datetime.now(tz=UTC).year),
        # Repos need to define this key, an array of objects with 'name', 'ref' and 'runs_on' keys
        'devkits': [[]]
    }
