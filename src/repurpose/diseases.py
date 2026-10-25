"""Explicit disease inputs; scoring constants are deliberately not configurable."""
import json
import re
from pathlib import Path

DISCLAIMER = ("Research hypothesis, not medical advice. This tool does not tell anyone "
              "what to take. Talk to a doctor or pharmacist about any medicine.")


def load_config(root: Path, disease: str) -> dict:
    registry = json.loads((root / "config/diseases.json").read_text())
    if disease not in registry["diseases"] or not re.fullmatch(r"[a-z][a-z0-9_-]*", disease):
        raise ValueError("Unknown configured disease")
    config = registry["diseases"][disease]
    if config["id"] != disease or config["radius"] not in (2, 3):
        raise ValueError("Invalid disease ID or neighborhood radius")
    if config["label_source"]["provider"] != "ClinicalTrials.gov":
        raise ValueError("Only the existing ClinicalTrials.gov label protocol is implemented")
    re.compile(config["label_source"]["condition_pattern"])
    if "controls_file" in config:
        config["controls"] = json.loads((root / config["controls_file"]).read_text())
    return config


def resolve_targets(config: dict, nodes: dict) -> set[int]:
    targets = set()
    for expected in config["targets"]:
        node = nodes.get(expected["id"])
        if node is None or node["type"] != "disease" or node["name"] != expected["name"]:
            raise ValueError(f"Disease target mismatch: {expected}")
        targets.add(expected["id"])
    if not targets:
        raise ValueError("Disease config has no targets")
    return targets
