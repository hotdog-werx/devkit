"""The gitignore facet: everything about `.gitignore` lives in this leaf.

A facet is a leaf connected to the provider through the `facets` class
attribute; its context model, input model, and facet class are defined
here, not in the provider's models module. Senders that want ignore
entries import `GitignoreInputs` from this module.
"""

import logging
from typing import override

from pydantic import BaseModel, Field
from repolish import (
    BaseContext,
    BaseInputs,
    FacetFinalizeOptions,
    FacetSpec,
    FacetSpecOptions,
    ProviderFacet,
)

logger = logging.getLogger(__name__)


class GitignoreSection(BaseModel):
    """One provider's block of ignore entries in the rendered .gitignore."""

    name: str
    """Section header text; rendered as ``## <name>`` so every entry is
    attributable to the provider that requested it."""

    entries: list[str] = Field(default_factory=list)


class GitignoreFacetContext(BaseContext):
    """Context for the workspace provider's gitignore facet."""

    sections: list[GitignoreSection] = Field(default_factory=list)
    """The rendered .gitignore's provider sections, in received order.

    Sections start empty: every entry, the workspace baseline included,
    arrives as a routed ``GitignoreInputs`` payload (the workspace
    provider sends its own baseline through ``provide_inputs``, so a
    provider's ignores live with the provider, not baked into this
    facet). Each section renders under a ``## <sender.alias>`` header so
    it is always clear why an entry is there. Note ``.repolish`` needs
    no entry: repolish drops a ``.gitignore`` inside the folder itself.
    """


class GitignoreInputs(BaseInputs):
    """Ignore entries a provider asks the workspace to add to .gitignore.

    The framework stamps each routed payload with the emitting provider's
    identity (``payload.sender``), so the facet renders the entries under
    ``## <sender.alias>`` in the consuming repo's .gitignore. The sender
    declares only what it wants ignored, never how it is labeled.
    """

    entries: list[str] = Field(default_factory=list)


def _merge_into_section(
    merged: list[GitignoreSection],
    name: str,
    entries: list[str],
) -> None:
    """Add or extend *name*'s section with *entries* (order-preserving, dedup)."""
    target = next((s for s in merged if s.name == name), None)
    if target is None:
        target = GitignoreSection(name=name)
        merged.append(target)
    target.entries.extend(entry for entry in entries if entry not in target.entries)


class GitignoreFacet(ProviderFacet[GitignoreFacetContext, GitignoreInputs]):
    """Owns `.gitignore` for the workspace provider.

    The rendered head carries one labeled section per sender of
    GitignoreInputs (exact-schema routing delivers them here, including
    the workspace provider's own provide_inputs payload: a provider's
    emitted inputs route back to its facets, so no entry is special-cased
    in the facet), labeled with the sender's framework-stamped
    `payload.sender.alias`. Everything below the `## repo-overrides`
    keep-rest marker stays repo-owned, so a repo can keep its own entries
    and even negate a provider entry (e.g. `!/.editorconfig` after the
    workspace section ignores `/.editorconfig`).
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
            _merge_into_section(merged, name, payload.entries)
        return opt.own_context.model_copy(update={'sections': merged})

    @override
    def create_spec(
        self,
        opt: FacetSpecOptions[GitignoreFacetContext],
    ) -> FacetSpec:
        return FacetSpec(
            file_mappings={'.gitignore': '_repolish.gitignore'},
        )
