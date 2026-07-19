from typing import TYPE_CHECKING

from devkit.releez.repolish.models import (
    ReleezProviderContext,
    ReleezProviderInputs,
)
from repolish import Provider
from typing_extensions import override

if TYPE_CHECKING:
    from repolish import TemplateMapping


class ReleezProvider(Provider[ReleezProviderContext, ReleezProviderInputs]):
    """Repolish provider for release, publish, and changelog automation."""

    @override
    def create_file_mappings(
        self,
        context: ReleezProviderContext,
    ) -> dict[str, 'str | TemplateMapping | None']:
        # No mise tasks: releez itself already handles tag-pulling, and
        # `uv build`/`uv publish` (see build_command/publish_command) need
        # no wrapper — running them directly is simpler than maintaining a
        # mise task that just forwards to the same command.
        return {
            'cliff.toml': 'cliff.toml',
            '.github/workflows/finalize-release.yaml': '.github/workflows/finalize-release.yaml',
            '.github/workflows/lint-pr-title.yaml': '.github/workflows/lint-pr-title.yaml',
            '.github/workflows/validate-release.yaml': '.github/workflows/validate-release.yaml',
        }
