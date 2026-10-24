"""Deterministic span-level citation verification.

A claim is supported only if it carries a PMID that is in the retrieved set for
that family and a verbatim quote of 8-40 words that actually appears in that
record's title or abstract. Nothing here calls a model: this is the check that
decides whether generated text may be shown as supported.
"""
from __future__ import annotations

import re
import unicodedata

MIN_WORDS, MAX_WORDS = 8, 40

# Unicode punctuation that models routinely substitute for ASCII.
_PUNCTUATION = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-",
    "―": "-", "−": "-", "…": "...", " ": " ",
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = "".join(_PUNCTUATION.get(ch, ch) for ch in text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def word_count(quote: str) -> int:
    return len(normalize(quote).split())


def verify_claim(claim: dict, retrieved: dict) -> dict:
    """Return the claim with a verified flag and, when it fails, the reason.

    `retrieved` maps PMID -> record with title/abstract, as returned by the
    retriever for this family. A PMID outside that mapping never verifies, even
    if it exists in PubMed: the agent may only cite what it was shown.
    """
    pmid = str(claim.get("pmid", "")).strip()
    quote = claim.get("quote", "") or ""
    result = {**claim, "pmid": pmid, "verified": False, "failure": None}
    count = word_count(quote)
    if not pmid:
        result["failure"] = "no pmid"
    elif pmid not in retrieved:
        result["failure"] = "pmid not in retrieved set"
    elif count < MIN_WORDS:
        result["failure"] = f"quote too short ({count} words, minimum {MIN_WORDS})"
    elif count > MAX_WORDS:
        result["failure"] = f"quote too long ({count} words, maximum {MAX_WORDS})"
    else:
        record = retrieved[pmid]
        haystack = normalize(f"{record.get('title','')} {record.get('abstract','')}")
        if normalize(quote) in haystack:
            result["verified"] = True
        else:
            result["failure"] = "quote not found in the cited record"
    return result


def verify_all(claims: list[dict], retrieved: dict) -> list[dict]:
    return [verify_claim(claim, retrieved) for claim in claims or []]
