"""The gitignore facet: everything about `.gitignore` lives in this leaf.

A facet is a leaf connected to the provider through the `facets` class
attribute; its context model, input model, and facet class are defined
here, not in the provider's models module. Senders that want ignore
entries import `GitignoreInputs` from this module.
"""

import logging

from pydantic import BaseModel, Field
from repolish import (
    BaseContext,
    BaseInputs,
    FacetFinalizeOptions,
    FacetSpec,
    FacetSpecOptions,
    ProviderFacet,
)
from typing_extensions import override

logger = logging.getLogger(__name__)


class GitignoreSection(BaseModel):
    """One provider's block of ignore entries in the rendered .gitignore."""

    name: str
    """Section header text; rendered as ``## <name>`` so every entry is
    attributable to the provider that requested it."""

    entries: list[str] = Field(default_factory=list)


class GitignoreFacetContext(BaseContext):
    """Context for the workspace provider's gitignore facet."""

    sections: list[GitignoreSection] = Field(
        default_factory=lambda: [
            GitignoreSection(
                name='workspace',
                entries=[
                    '.DS_Store',
                    'scratch/**',
                    'mise.local.toml',
                    'tmp*',
                    '.tmp*',
                    '/.editorconfig',
                ],
            ),
        ],
    )
    """The rendered .gitignore's provider sections, in order: the workspace
    baseline first, then one section per provider that sent GitignoreInputs.
    Each section renders under a ``## <name>`` header so it is always
    clear why an entry is there. Note ``.repolish`` needs no entry here:
    repolish drops a ``.gitignore`` inside the folder itself."""


class GitignoreInputs(BaseInputs):
    """Ignore entries a provider asks the workspace to add to .gitignore.

    The framework stamps each routed payload with the emitting provider's
    identity (``payload.sender``), so the facet renders the entries under
    ``## <sender.alias>`` in the consuming repo's .gitignore. The sender
    declares only what it wants ignored, never how it is labeled.
    """

    entries: list[str] = Field(default_factory=list)


class GitignoreFacet(ProviderFacet[GitignoreFacetContext, GitignoreInputs]):
    """Owns `.gitignore` for the workspace provider.

    The rendered head carries one labeled section per provider: the
    workspace baseline first, then one section per sender of GitignoreInputs
    (exact-schema routing delivers them here), labeled with the sender's
    framework-stamped `payload.sender.alias`. Everything below the
    `## repo-overrides` keep-rest marker stays repo-owned, so a repo can
    keep its own entries and even negate a provider entry (e.g.
    `!/.editorconfig` after the workspace section ignores `/.editorconfig`).
    """

    name = 'gitignore'

    @override
    def finalize_context(
        self,
        opt: FacetFinalizeOptions[GitignoreFacetContext, GitignoreInputs],
    ) -> GitignoreFacetContext:
        """Merge the received payloads into one section per sender."""
        merged = [section.model_copy(deep=True) for section in opt.own_context.sections]
        for payload in opt.received_inputs:
            name = payload.sender.alias if payload.sender is not None else ''
            if not name:
                # A routed payload always carries the sender stamp; one
                # without it was hand-built. Skipping keeps the rendered
                # file free of nameless sections instead of guessing a label.
                logger.warning(
                    'gitignore input without a sender stamp, skipping (facet=%s)',
                    self.name,
                )
                continue
            target = next(
                (s for s in merged if s.name == name),
                None,
            )
            if target is None:
                target = GitignoreSection(name=name)
                merged.append(target)
            for entry in payload.entries:
                if entry not in target.entries:
                    target.entries.append(entry)
        return opt.own_context.model_copy(update={'sections': merged})

    @override
    def create_spec(
        self,
        opt: FacetSpecOptions[GitignoreFacetContext],
    ) -> FacetSpec:
        return FacetSpec(
            file_mappings={'.gitignore': '_repolish.gitignore'},
        )
