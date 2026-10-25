"""Plain-language mode must be simpler without becoming a second set of claims."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

# Words that would turn a research hypothesis into a medical claim. Checked against
# the plain copy, where a careless simplification is most likely to slip through.
BANNED = (
    "cure", "cures", "treats", "treatment for", "will help", "helps patients",
    "proven", "proves", "guarantee", "guaranteed", "breakthrough", "miracle",
    "you should take", "we recommend", "recommended dose", "dose of",
    "is safe", "safely", "side effects are", "no side effects",
    "works for", "the drug works", "this drug works", "medicine works",
    "effective for", "efficacy in patients",
)
# Allowed only in an explicit negation, e.g. "Nothing here says a medicine is safe".
NEGATION = ("not ", "nothing ", "does not", "cannot", "never ", "no one ")


@pytest.fixture(scope="module")
def copy():
    from repurpose.plain_language import build
    return build(ROOT)


def _sentences(copy):
    from repurpose.plain_language import sentences
    return sentences(copy)


def test_plain_copy_is_generated_from_the_audited_artifact(copy):
    audited = json.loads((ROOT / "artifacts/audited_validation.json").read_text())
    strict = audited["diseases"]["alzheimers"]["strict"]
    path = strict["methods"]["path_only"]
    assert copy["numbers"]["strict_hits"] == path["metrics"]["hits_at_20"]
    assert copy["numbers"]["strict_labels"] == strict["heldout_count"]
    # The two modes must quote the same figures.
    assert str(copy["numbers"]["strict_hits"]) in " ".join(copy["how_well_it_did"]["body"])
    assert str(copy["numbers"]["strict_labels"]) in " ".join(copy["how_well_it_did"]["body"])


def test_plain_copy_contains_no_banned_claim(copy):
    offences = []
    for text in _sentences(copy):
        lowered = text.casefold()
        for phrase in BANNED:
            for match in re.finditer(re.escape(phrase), lowered):
                window = lowered[max(0, match.start() - 40):match.start()]
                if any(negator in window for negator in NEGATION):
                    continue
                offences.append(f"{phrase!r} in: {text[:110]}")
    assert not offences, "plain copy overclaims:\n" + "\n".join(offences)


def test_plain_copy_keeps_the_disclaimer_and_the_limits(copy):
    assert "not medical advice" in copy["disclaimer"]
    assert "doctor or pharmacist" in copy["disclaimer"]
    limits = " ".join(copy["what_it_does_not_mean"]["body"]).casefold()
    assert "does not mean it worked" in limits
    assert "small test" in limits


def test_plain_copy_reports_the_negative_second_disease(copy):
    body = " ".join(copy["second_disease"]["body"]).casefold()
    assert "did not work" in body
    assert str(copy["numbers"]["parkinsons_labels"]) in body


def test_plain_copy_reads_below_the_target_grade():
    from reading_level import TARGET_GRADE, report
    result = report(ROOT)
    assert result["overall_grade"] is not None
    assert result["overall_grade"] <= TARGET_GRADE, result["worst"][:3]
    assert not result["over_target"], [s["text"][:80] for s in result["over_target"]]


def test_the_detailed_ui_still_carries_the_hypothesis_banner():
    source = (ROOT / "web/src/main.jsx").read_text()
    assert "Research hypothesis, not medical advice" in source
    assert "hypothesis-banner" in source
