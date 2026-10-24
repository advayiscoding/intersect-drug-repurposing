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

    def __init__(self, drugs: list[dict]):
        self.drugs = drugs
        self.by_name: dict[str, dict] = {}
        for drug in drugs:
            self.by_name.setdefault(normalize(drug["name"]), drug)
            source_id = str(drug.get("source_id", "")).strip().casefold()
            if source_id:
                self.by_name.setdefault(source_id, drug)

    @classmethod
    def load(cls, root: Path) -> "DrugIndex":
        nodes = json.loads((root / "data/processed/nodes.json").read_text())
        return cls([n for n in nodes if n["type"] == "drug"])

    def resolve(self, text: str) -> dict | None:
        key = normalize(text)
        if not key:
            return None
        hit = self.by_name.get(key) or self.by_name.get(sanitize(text).strip().casefold())
        if hit:
            return hit
        # A salt or formulation suffix ("insulin glargine injection") still resolves
        # when the leading words name a node exactly.
        words = key.split()
        for size in range(len(words) - 1, 0, -1):
            candidate = self.by_name.get(" ".join(words[:size]))
            if candidate:
                return candidate
        return None

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
