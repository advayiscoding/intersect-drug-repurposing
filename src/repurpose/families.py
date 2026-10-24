"""Explicit family grouping shared by ranking cards and evaluation."""
import json
from pathlib import Path


def family_for(row, config):
    name = row["name"].casefold()
    matches = [g for g in config["groups"] if name in g.get("names", [])
               or any(name.startswith(p) for p in g.get("prefixes", []))]
    if len(matches) > 1:
        raise ValueError(f"Ambiguous family for {name}")
    if matches:
        return matches[0]["id"], matches[0]["name"]
    return f"drug-{row['drug_id']}", row["name"]


def group_rankings(rows, config):
    families = {}
    for row in rows:
        key, name = family_for(row, config)
        families.setdefault(key, {"id": key, "name": name, "members": [],
                                 "representative_id": row["drug_id"], "score": row["path_score"]})
        families[key]["members"].append(row)
    return [{**family, "rank": rank} for rank, family in enumerate(families.values(), 1)]


def load_families(root: Path):
    config = json.loads((root / "config/drug_families.json").read_text())
    rows = json.loads((root / "artifacts/discovery_rankings.json").read_text())
    return config, rows, group_rankings(rows, config)
