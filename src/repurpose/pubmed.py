"""Throttled, disk-cached PubMed retrieval through NCBI E-utilities.

Every response is written to data/cache/pubmed before use, so a cached run needs
no network. On timeout or error the cache is used if present and the failure is
reported rather than silently producing an empty retrieved set.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

from .env import credential

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL = {"tool": "alzheimers-repurpose", "email": "research@example.org"}
_last_call = [0.0]


def _throttle(has_key: bool) -> None:
    # E-utilities allows 10 requests/second with an API key, 3 without.
    minimum = 0.11 if has_key else 0.34
    wait = minimum - (time.monotonic() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    _last_call[0] = time.monotonic()


def _cache_path(root: Path, kind: str, key: str) -> Path:
    digest = hashlib.sha256(key.encode()).hexdigest()[:24]
    return root / "data/cache/pubmed" / f"{kind}-{digest}.json"


def _request(root: Path, kind: str, endpoint: str, params: dict, timeout: float = 25.0) -> tuple[str, str]:
    """Return (payload, source) where source is 'live' or 'cache'."""
    key = credential("NCBI_API_KEY", root)
    cache = _cache_path(root, kind, json.dumps(params, sort_keys=True))
    if cache.exists():
        return json.loads(cache.read_text())["payload"], "cache"
    query = {**TOOL, **params}
    if key:
        query["api_key"] = key
    try:
        _throttle(bool(key))
        response = requests.get(f"{BASE}/{endpoint}", params=query, timeout=timeout)
        response.raise_for_status()
    except Exception as error:  # network, HTTP or timeout
        raise RuntimeError(f"PubMed {endpoint} failed with no cached copy: {error}") from error
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"params": params, "payload": response.text}))
    return response.text, "live"


def search(root: Path, term: str, retmax: int = 8) -> tuple[list[str], str]:
    payload, origin = _request(root, "esearch", "esearch.fcgi",
                               {"db": "pubmed", "term": term, "retmax": retmax,
                                "retmode": "json", "sort": "relevance"})
    data = json.loads(payload)
    return list(data.get("esearchresult", {}).get("idlist", [])), origin


def _text(node) -> str:
    return re.sub(r"\s+", " ", "".join(node.itertext())).strip() if node is not None else ""


def fetch(root: Path, pmids: list[str]) -> tuple[dict, str]:
    if not pmids:
        return {}, "cache"
    payload, origin = _request(root, "efetch", "efetch.fcgi",
                               {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"})
    records = {}
    for article in ET.fromstring(payload).iter("PubmedArticle"):
        pmid = _text(article.find(".//PMID"))
        if not pmid:
            continue
        abstract = " ".join(_text(part) for part in article.findall(".//Abstract/AbstractText"))
        year = _text(article.find(".//PubDate/Year")) or _text(article.find(".//PubDate/MedlineDate"))[:4]
        types = sorted({_text(t) for t in article.findall(".//PublicationType")})
        records[pmid] = {
            "pmid": pmid,
            "title": _text(article.find(".//ArticleTitle")),
            "abstract": abstract,
            "journal": _text(article.find(".//Journal/ISOAbbreviation")),
            "year": year,
            "publication_types": types,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        }
    return records, origin


def retrieve(root: Path, drug_names: list[str], retmax: int = 8) -> dict:
    """Retriever agent: one relevance-ranked PubMed query per drug family."""
    names = " OR ".join(f'"{name}"' for name in drug_names)
    term = f"({names}) AND (Alzheimer OR dementia OR \"cognitive impairment\")"
    pmids, search_origin = search(root, term, retmax=retmax)
    records, fetch_origin = fetch(root, pmids)
    return {"query": term, "pmids": pmids, "records": records,
            "source": "cache" if search_origin == fetch_origin == "cache" else "live",
            "retrieved_count": len(records)}
