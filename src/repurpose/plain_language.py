"""Plain-language copy, generated from the same artifacts the detailed view uses.

Simple mode must never be a second set of numbers. Every figure here is read out of
`artifacts/audited_validation.json`, so the two modes cannot drift apart. The words
are short on purpose; `scripts/reading_level.py` checks them and
`tests/test_plain_language.py` forbids the vocabulary that would overclaim.
"""
from __future__ import annotations

import json
from pathlib import Path

from .data import write_json

DISCLAIMER = ("This is a research idea, not medical advice. It does not tell anyone "
              "what to take. Talk to a doctor or pharmacist about any medicine.")


def _primary(disease: dict) -> tuple[dict, dict]:
    block = disease["strict"]
    return block, block["methods"]["path_only"]


def build(root: Path) -> dict:
    audited = json.loads((root / "artifacts/audited_validation.json").read_text())
    alz, alz_path = _primary(audited["diseases"]["alzheimers"])
    par, par_path = _primary(audited["diseases"]["parkinsons"])
    raw = audited["diseases"]["alzheimers"]["raw"]
    sensitivity = audited["diseases"]["alzheimers"]["strict_sensitivity"]
    sens_path = sensitivity["methods"]["path_only"]

    hits = alz_path["metrics"]["hits_at_20"]
    labels = alz["heldout_count"]
    low, high = alz_path["exact_95_ci"]["recall_at_20"]

    copy = {
        "disclaimer": DISCLAIMER,
        "what_this_is": {
            "title": "What this is",
            "body": [
                "This is a research tool. It reads a large map of biology and guesses "
                "which existing medicines might be worth studying for Alzheimer's.",
                "It does not test medicines. It does not know if any of them work. "
                "It points at connections a researcher could go and check.",
            ],
        },
        "how_it_works": {
            "title": "How it works",
            "body": [
                "The map links a drug to the proteins it acts on, and links those "
                "proteins to the disease. A short chain of links scores higher than a "
                "long one, and links through very busy proteins count for less.",
                "The map does not say which way an effect goes. A drug can be linked "
                "to the right protein and still push the wrong way.",
            ],
        },
        "how_well_it_did": {
            "title": "How well it did",
            "body": [
                f"We checked the ranking against {labels} trials that we read one by "
                f"one to be sure they really tested the drug in people with the "
                f"disease. The ranking put {hits} of those {labels} in its top 20.",
                f"That is {alz_path['metrics']['recall_at_20'] * 100:.0f} in 100. The "
                f"true number could be anywhere from {low * 100:.0f} to "
                f"{high * 100:.0f} in 100, because the sample is tiny.",
                f"The one it found is an insulin. Two more insulins were too unclear "
                f"to count, and we counted them separately: that gives "
                f"{sens_path['metrics']['hits_at_20']} of "
                f"{sensitivity['heldout_count']}.",
                f"Before we read the trials, a looser list of {raw['heldout_count']} "
                f"trials gave {raw['methods']['path_only']['metrics']['hits_at_20']} "
                f"hits. Reading them carefully removed most of that.",
            ],
        },
        "what_it_does_not_mean": {
            "title": "What this does not mean",
            "body": [
                "A drug being tested in a trial does not mean it worked. Many trials "
                "fail, and some never report results.",
                "Nothing here says a medicine is safe or effective for anyone.",
                "This was one small test on one disease. It does not show the method "
                "would work again.",
            ],
        },
        "second_disease": {
            "title": "We tried it on a second disease",
            "body": [
                f"We ran the same method, unchanged, on Parkinson's. It found "
                f"{par_path['metrics']['hits_at_20']} of {par['heldout_count']} "
                f"checked trials in its top 20.",
                "We are reporting that because it did not work, not because it did.",
            ],
        },
        "about_the_reading": {
            "title": "About the reading agents",
            "body": [
                "For the top candidates, a set of agents reads real papers. "
                "The papers come from PubMed. The agents write a short summary. "
                "One writes a safety note. One argues against the idea.",
                "Every sentence they show has to quote the paper word for word, and we "
                "check the quote is really there. Anything we cannot check is marked "
                "unverified and is not shown as support.",
            ],
        },
        "numbers": {
            "strict_hits": hits, "strict_labels": labels,
            "strict_recall_percent": round(alz_path["metrics"]["recall_at_20"] * 100, 2),
            "sensitivity_hits": sens_path["metrics"]["hits_at_20"],
            "sensitivity_labels": sensitivity["heldout_count"],
            "raw_hits": raw["methods"]["path_only"]["metrics"]["hits_at_20"],
            "raw_labels": raw["heldout_count"],
            "parkinsons_hits": par_path["metrics"]["hits_at_20"],
            "parkinsons_labels": par["heldout_count"],
        },
    }
    write_json(root / "artifacts/plain_language.json", copy)
    return copy


def sentences(copy: dict) -> list[str]:
    """Every reader-facing sentence, for the reading-level and banned-copy checks."""
    found = []
    for key, section in copy.items():
        if key == "numbers":
            continue
        if isinstance(section, str):
            found.append(section)
        elif isinstance(section, dict):
            found.append(section["title"])
            found.extend(section["body"])
    return found
