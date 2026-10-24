"""External pages for graph nodes, derived from the node's own source identifier.

PrimeKG stores ontology identifiers without their prefix and without zero padding,
so MONDO/HP/GO/UBERON ids are reconstructed before building a URL. Any node whose
source has no reliable per-entity page returns None; the UI then shows no link
rather than a wrong one.
"""
from __future__ import annotations

PRIMEKG_DOI = "https://doi.org/10.7910/DVN/IXA7BM"

# Zero-padded OBO-style identifiers: (prefix, width).
_OBO = {"MONDO": ("MONDO", 7), "HPO": ("HP", 7), "GO": ("GO", 7), "UBERON": ("UBERON", 7)}


def curie(source: str, source_id: str) -> str | None:
    prefix, width = _OBO[source]
    local = str(source_id).strip()
    if local.upper().startswith(f"{prefix}:"):
        local = local.split(":", 1)[1]
    if not local.isdigit():
        return None
    return f"{prefix}:{local.zfill(width)}"


def external_link(node: dict) -> str | None:
    """Return the entity's own page, or None when no reliable page exists."""
    source, source_id = node.get("source"), str(node.get("source_id", "")).strip()
    if not source or not source_id:
        return None
    if source == "REACTOME":
        return f"https://reactome.org/content/detail/{source_id}"
    if source == "NCBI":
        return f"https://www.ncbi.nlm.nih.gov/gene/{source_id}" if source_id.isdigit() else None
    if source == "DrugBank":
        return f"https://go.drugbank.com/drugs/{source_id}" if source_id.upper().startswith("DB") else None
    if source in ("MONDO", "HPO"):
        identifier = curie(source, source_id)
        return f"https://monarchinitiative.org/{identifier}" if identifier else None
    if source == "GO":
        identifier = curie(source, source_id)
        return f"https://amigo.geneontology.org/amigo/term/{identifier}" if identifier else None
    if source == "UBERON":
        identifier = curie(source, source_id)
        return f"http://purl.obolibrary.org/obo/{identifier.replace(':', '_')}" if identifier else None
    # MONDO_grouped collapses many ontology terms into one node, and CTD exposure
    # identifiers have no stable public page. Unknown sources fall through here too.
    return None
