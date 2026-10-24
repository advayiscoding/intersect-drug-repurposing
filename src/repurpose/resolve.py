"""Resolve untrusted drug and disease text against the graph's own vocabulary.

User text is only ever used to LOOK UP a node. Everything downstream — the agent
prompts and the PubMed query — uses the canonical name taken from the graph, so a
user cannot inject instructions or widen a retrieval query through this path.
"""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
from pathlib import Path

MAX_INPUT = 100
SUPPORTED_DISEASES = {"alzheimer", "alzheimers", "alzheimer disease", "alzheimers disease",
                      "alzheimer's disease", "alzheimer s disease", "ad",
                      "late onset alzheimer disease", "dementia of the alzheimer type"}


def sanitize(text: str, limit: int = MAX_INPUT) -> str:
    """Strip to a conservative character set and cap the length."""
    text = unicodedata.normalize("NFKC", str(text or ""))
    text = "".join(ch for ch in text if ch.isprintable() and ch not in "\r\n\t")
    text = re.sub(r"[^A-Za-z0-9 ,.'()\-+/]", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def normalize(text: str) -> str:
    text = sanitize(text).casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text)).strip()


def is_supported_disease(text: str) -> bool:
    return normalize(text) in SUPPORTED_DISEASES


class DrugIndex:
    """Case- and punctuation-insensitive index over every drug node in the graph."""

    def __init__(self, drugs: list[dict], synonyms: dict | None = None):
        self.drugs = drugs
        self.by_name: dict[str, dict] = {}
        self.by_id: dict[int, dict] = {}
        for drug in drugs:
            self.by_name.setdefault(normalize(drug["name"]), drug)
            self.by_id[drug["id"]] = drug
            source_id = str(drug.get("source_id", "")).strip().casefold()
            if source_id:
                self.by_name.setdefault(source_id, drug)
        # Synonyms never override a primary name: they are a fallback layer only.
        # A synonym may carry several candidates; those are offered, never chosen.
        self.synonyms: dict[str, list[int]] = {}
        for key, ids in (synonyms or {}).items():
            if key in self.by_name:
                continue
            known = [i for i in (ids if isinstance(ids, list) else [ids]) if i in self.by_id]
            if known:
                self.synonyms[key] = known

    @classmethod
    def load(cls, root: Path) -> "DrugIndex":
        path = root / "artifacts/drug_index.json"
        if not path.exists():
            path = root / "data/processed/nodes.json"
        nodes = json.loads(path.read_text())
        path = root / "data/synonyms.json"
        synonyms = json.loads(path.read_text()).get("map", {}) if path.exists() else {}
        return cls([n for n in nodes if n["type"] == "drug"], synonyms)

    def match(self, text: str) -> dict | None:
        """Resolve to a node and say HOW it matched, so the UI can show it."""
        key = normalize(text)
        if not key:
            return None
        hit = self.by_name.get(key) or self.by_name.get(sanitize(text).strip().casefold())
        if hit:
            how = "identifier" if key == str(hit.get("source_id", "")).casefold() else "exact"
            return {"node": hit, "match_type": how, "matched_on": text.strip()}
        if key in self.synonyms:
            candidates = [self.by_id[i] for i in self.synonyms[key]]
            if len(candidates) > 1:
                return {"node": None, "match_type": "ambiguous_synonym",
                        "matched_on": text.strip(), "candidates": candidates}
            return {"node": candidates[0], "match_type": "synonym", "matched_on": text.strip()}
        # Synonyms are matched exactly only. A salt or formulation suffix still
        # resolves when the leading words name a node exactly.
        words = key.split()
        for size in range(len(words) - 1, 0, -1):
            prefix = " ".join(words[:size])
            if prefix in self.by_name:
                return {"node": self.by_name[prefix], "match_type": "prefix", "matched_on": prefix}
        return None

    def resolve(self, text: str) -> dict | None:
        found = self.match(text)
        return found["node"] if found else None

    def suggestions(self, text: str, limit: int = 5) -> list[str]:
        key = normalize(text)
        if not key:
            return []
        names = list(self.by_name)
        close = difflib.get_close_matches(key, names, n=limit, cutoff=0.72)
        starts = [n for n in names if n.startswith(key[:4])][:limit] if len(key) >= 4 else []
        contains = [n for n in names if key in n][:limit] if len(key) >= 4 else []
        ordered, seen = [], set()
        for name in close + contains + starts:
            drug = self.by_name[name]
            if drug["name"] not in seen:
                seen.add(drug["name"])
                ordered.append(drug["name"])
        return ordered[:limit]
