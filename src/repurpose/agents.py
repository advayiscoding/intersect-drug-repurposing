"""Evidence agents over retrieved PubMed records.

Five roles: the retriever (pubmed.retrieve, deterministic), a mechanism analyst, a
safety analyst, a skeptic and a synthesiser. Every agent must attach a verbatim
quote and PMID to each claim; citations.verify_all then decides what the UI may
show as supported. Agent output never feeds back into the ranking or validation.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .citations import MAX_WORDS, MIN_WORDS, verify_all
from .env import credential, offline

MODEL = "claude-sonnet-5"
MAX_ABSTRACT_CHARS = 900

BANNER = (
    "You are part of a research hypothesis workbench for Alzheimer's drug repurposing. "
    "Everything you produce is a research hypothesis, never medical advice, and you must "
    "never state or imply that a drug is effective, works, treats, or benefits patients. "
    "Describe what the cited records report, not what is true."
)

CLAIM_RULES = (
    f"Every claim MUST be an object with: text (your sentence), pmid (a PMID from the records "
    f"below, digits only), quote (a VERBATIM span of {MIN_WORDS}-{MAX_WORDS} words copied exactly "
    "from that PMID's title or abstract, no ellipsis, no paraphrase), and evidence_type (one of "
    "human trial, animal, in vitro, review, other). Copy the quote character for character. "
    "If you cannot support a sentence with such a quote, omit the sentence. Never invent a PMID. "
    "Give at most 4 claims and keep every summary under 90 words."
)

ROLES = {
    "mechanism_analyst": (
        "You are the mechanism analyst. Using only the records, describe what is reported about "
        "how this drug family relates to the biology named in the graph path. State the direction "
        "of any reported effect only if a record states it; otherwise say 'direction unknown'. "
        "Return JSON: {\"summary\": str, \"direction\": str, \"claims\": [claim, ...]}"),
    "safety_analyst": (
        "You are the safety analyst. Using only the records, note reported adverse effects, "
        "tolerability, dosing or population cautions relevant to older adults. Absence of reported "
        "harm is not evidence of safety; say so when the records are silent. "
        "Return JSON: {\"summary\": str, \"claims\": [claim, ...]}"),
    "skeptic": (
        "You are the skeptic. Argue against the repurposing hypothesis using only the records: "
        "null or negative results, small samples, surrogate endpoints, confounding, population "
        "mismatch, or the absence of Alzheimer-specific evidence. "
        "Return JSON: {\"counter_evidence\": str, \"claims\": [claim, ...]}"),
}

SYNTHESIS = (
    "You are the synthesiser. You receive the mechanism, safety and skeptic outputs and the same "
    "records. Write a short neutral summary of what the retrieved literature does and does not "
    "establish about this drug family in Alzheimer's disease, and list the open questions. Make no "
    "efficacy claim and do not recommend use. "
    "Return JSON: {\"summary\": str, \"open_questions\": [str, ...], \"claims\": [claim, ...]}")


def available(root: Path) -> bool:
    return not offline() and bool(credential("ANTHROPIC_API_KEY", root))


def _records_block(records: dict) -> str:
    lines = []
    for pmid, record in records.items():
        abstract = (record.get("abstract") or "")[:MAX_ABSTRACT_CHARS]
        lines.append(f"PMID {pmid} ({record.get('year','?')}, {record.get('journal','')}; "
                     f"{', '.join(record.get('publication_types', [])[:3])})\n"
                     f"TITLE: {record.get('title','')}\nABSTRACT: {abstract}")
    return "\n\n".join(lines) or "No records were retrieved."


def _parse(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError(f"agent returned no JSON object: {text[:300]!r}")
    return json.loads(match.group(0))


def _call(client, system: str, prompt: str, max_tokens: int = 8000, timeout: float = 180.0) -> dict:
    message = client.messages.create(
        model=MODEL, max_tokens=max_tokens, timeout=timeout, system=system,
        messages=[{"role": "user", "content": prompt}])
    if message.stop_reason == "max_tokens":
        raise ValueError("agent output was truncated; raise max_tokens")
    return _parse("".join(block.text for block in message.content if block.type == "text"))


def run_family(root: Path, family: dict, retrieval: dict, client=None) -> dict:
    """Run every role for one family and verify each claim before returning."""
    if offline():
        raise RuntimeError("Offline mode: live agents are disabled")
    if client is None:
        import anthropic
        client = anthropic.Anthropic(api_key=credential("ANTHROPIC_API_KEY", root))
    records = retrieval["records"]
    default_context = "drug - protein - disease associations in PrimeKG; edge direction is unknown"
    members = ", ".join(m["name"] for m in family["members"])
    context = (f"DRUG FAMILY: {family['name']}\n"
               f"MEMBERS: {members}\n"
               f"GRAPH PATH CONTEXT: {family.get('path_context') or default_context}\n\n"
               f"RECORDS:\n{_records_block(records)}")
    system = f"{BANNER}\n\n{CLAIM_RULES}\nRespond with JSON only."

    outputs, failures, total = {}, 0, 0
    for role, instruction in ROLES.items():
        raw = _call(client, system, f"{instruction}\n\n{context}")
        checked = verify_all(raw.get("claims"), records)
        total += len(checked)
        failures += sum(1 for c in checked if not c["verified"])
        outputs[role] = {**raw, "claims": checked}

    digest = json.dumps({role: {k: v for k, v in out.items() if k != "claims"} |
                         {"verified_claims": [c["text"] for c in out["claims"] if c["verified"]]}
                         for role, out in outputs.items()}, indent=1)
    raw = _call(client, system, f"{SYNTHESIS}\n\nAGENT OUTPUTS:\n{digest}\n\n{context}")
    checked = verify_all(raw.get("claims"), records)
    total += len(checked)
    failures += sum(1 for c in checked if not c["verified"])
    outputs["synthesizer"] = {**raw, "claims": checked}

    evidence_types = sorted({c.get("evidence_type", "other") for out in outputs.values()
                             for c in out["claims"] if c["verified"]})
    return {
        "family_id": family["id"], "family_name": family["name"],
        "members": [m["name"] for m in family["members"]],
        "model": MODEL,
        "retrieval": {"query": retrieval["query"], "pmids": retrieval["pmids"],
                      "retrieved_count": retrieval["retrieved_count"], "source": retrieval["source"]},
        "records": {pmid: {k: record[k] for k in ("pmid", "title", "journal", "year", "url")}
                    for pmid, record in records.items()},
        "mechanism": outputs["mechanism_analyst"],
        "safety": outputs["safety_analyst"],
        "skeptic": outputs["skeptic"],
        "synthesis": outputs["synthesizer"],
        "evidence_types": evidence_types,
        "direction": outputs["mechanism_analyst"].get("direction") or "direction unknown",
        "claim_counts": {"total": total, "verified": total - failures, "failed": failures},
        "verification": {"method": "span-level: PMID must be in the retrieved set and the quote "
                                  "must appear verbatim in that record's title or abstract",
                         "min_quote_words": MIN_WORDS, "max_quote_words": MAX_WORDS},
        "scope": "Literature review only. Agent output never enters the ranking or the validation "
                 "metrics, which cover the graph ranking alone.",
        "disclaimer": "Research hypothesis, not medical advice. Trial participation and reported "
                      "associations do not establish efficacy.",
    }
