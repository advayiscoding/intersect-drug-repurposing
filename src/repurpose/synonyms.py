"""Build an offline synonym map for the graph's drug nodes from PubChem.

PubChem data is in the public domain (U.S. National Library of Medicine); see
ASSUMPTIONS.md. Every response is cached to disk, so the map is rebuilt without
network access and the UI looks synonyms up entirely offline.

Ambiguous synonyms retain all matching nodes for an explicit user choice, never an
arbitrary resolution. A synonym never overrides another node's primary name.
"""
from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

import requests

from .data import write_json
from .resolve import normalize

PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
SOURCE = {"name": "PubChem", "publisher": "U.S. National Library of Medicine",
          "url": "https://pubchem.ncbi.nlm.nih.gov/",
          "license": "Public domain (NLM); see https://www.ncbi.nlm.nih.gov/home/about/policies/"}
MAX_PER_DRUG = 25
MIN_LEN, MAX_LEN = 3, 60
THROTTLE_SECONDS = 0.22  # PubChem asks for no more than 5 requests/second.


def _usable(synonym: str) -> bool:
    """Drop registry numbers, catalogue codes and other non-names."""
    if not (MIN_LEN <= len(synonym) <= MAX_LEN):
        return False
    text = normalize(synonym)
    if not text or not any(ch.isalpha() for ch in text):
        return False
    digits = sum(ch.isdigit() for ch in text)
    if digits > len(text) / 2:
        return False
    # CAS numbers, UNII codes, supplier catalogue ids, SMILES-ish strings.
    if any(token in synonym for token in ("=", "#", "[", "]", "@")):
        return False
    return True


_ticket = threading.Lock()
_next_slot = [0.0]


def _throttle() -> None:
    """Shared token bucket: the whole pool stays under PubChem's 5 requests/second."""
    with _ticket:
        now = time.monotonic()
        wait = max(0.0, _next_slot[0] - now)
        _next_slot[0] = max(now, _next_slot[0]) + THROTTLE_SECONDS
    if wait:
        time.sleep(wait)


def fetch_synonyms(root: Path, name: str, session: requests.Session) -> list[str]:
    cache_dir = root / "data/cache/pubchem"
    cache = cache_dir / f"{normalize(name).replace(' ', '_')[:80]}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    url = f"{PUBCHEM}/compound/name/{quote(name)}/synonyms/JSON"
    try:
        _throttle()
        response = session.get(url, timeout=20)
        if response.status_code == 404:
            found = []
        else:
            response.raise_for_status()
            info = response.json().get("InformationList", {}).get("Information", [{}])[0]
            found = list(info.get("Synonym", []))[:200]
    except Exception:
        return []  # a miss is recorded as "no synonyms", never as a wrong match
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(found))
    return found


def build(root: Path, limit: int | None = None) -> dict:
    nodes = json.loads((root / "data/processed/nodes.json").read_text())
    drugs = [n for n in nodes if n["type"] == "drug"][:limit]
    primary = {normalize(d["name"]) for d in drugs}
    claims: dict[str, set[int]] = {}
    session = requests.Session()
    session.headers["User-Agent"] = "alzheimers-repurpose/0.1 (research prototype)"

    done = [0]
    lock = threading.Lock()

    def collect(drug):
        found = fetch_synonyms(root, drug["name"], session)
        kept = []
        for synonym in found:
            if len(kept) >= MAX_PER_DRUG or not _usable(synonym):
                continue
            key = normalize(synonym)
            # Never shadow another node's own name, and skip this node's own name.
            if key and key not in primary:
                kept.append(key)
        with lock:
            for key in kept:
                claims.setdefault(key, set()).add(drug["id"])
            done[0] += 1
            if done[0] % 500 == 0:
                print(f"{done[0]}/{len(drugs)} drugs, {len(claims)} candidate synonyms", flush=True)

    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(collect, drugs))

    # Ambiguous synonyms are KEPT with every candidate. The UI asks the user which
    # drug they meant; nothing is ever resolved silently to one of several nodes.
    mapping = {key: sorted(ids) for key, ids in claims.items()}
    unique = sum(1 for ids in mapping.values() if len(ids) == 1)
    report = {"source": {**SOURCE, "accessed": time.strftime("%Y-%m-%d")},
              "drug_nodes": len(drugs), "synonyms": len(mapping),
              "unique_synonyms": unique, "ambiguous_synonyms": len(mapping) - unique,
              "policy": f"Exact normalized matches only. At most {MAX_PER_DRUG} synonyms per "
                        "drug. A synonym equal to another node's primary name is never "
                        "recorded. A synonym claimed by several drug nodes is kept with all "
                        "candidates and offered as a choice, never resolved silently.",
              "map": mapping}
    write_json(root / "data/synonyms.json", report)
    print(json.dumps({k: v for k, v in report.items() if k != "map"}, indent=2))
    return report
