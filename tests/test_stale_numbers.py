"""Fail the build if prose still quotes a figure the artifacts no longer support.

Numbers in this project have been revised more than once. A reader who sees a stale
headline in the README, the dashboard or the plain-language text has been misled,
even if every artifact on disk is correct. This test is the backstop.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

# A line may quote a retired figure when it is explicitly flagged as historical.
MARKERS = ("superseded", "historical", "retired", "no longer", "previously",
           "was reported", "stale", "earlier claim", "before the strict",
           "pre-strict", "raw-label era")

# Prose a reader can actually see.
CORPUS = [
    "README.md",
    "docs/METHODOLOGY.md", "docs/DEMO.md", "docs/FINAL_PLAN.md",
    "docs/PARKINSONS_CHECKPOINT.md", "docs/PARKINSONS_PLAN.md",
    "docs/LABEL_AUDIT.md", "docs/HUMAN_CHECKS.md",
    "docs/STRICT_LABEL_PROTOCOL.md", "docs/ALZHEIMERS_ADJUDICATION.md",
    "docs/PARKINSONS_ADJUDICATION.md",
    "web/src/main.jsx",
]


def _headline_report():
    from headline_numbers import collect
    return collect(ROOT)


def _candidate_files():
    found = [ROOT / name for name in CORPUS]
    found += sorted((ROOT / "docs").glob("*_QA*.md"))
    found += sorted((ROOT / "docs").glob("*PLAIN*.md"))
    return [p for p in dict.fromkeys(found) if p.exists()]


def test_the_generator_runs_and_names_its_retired_figures():
    report = _headline_report()
    assert report["live_figures"], "no live figures found; artifacts missing?"
    assert isinstance(report["retired_figures"], list)


@pytest.mark.parametrize("path", _candidate_files(), ids=lambda p: p.name)
def test_no_document_quotes_a_retired_figure_unmarked(path):
    retired = _headline_report()["retired_figures"]
    if not retired:
        pytest.skip("nothing retired yet")
    offences = []
    patterns = {f: re.compile(r"(?<![\w./])" + re.escape(f.casefold()) + r"(?![\w/])")
                for f in retired}
    section_exempt = False
    for number, line in enumerate(path.read_text().splitlines(), 1):
        lowered = line.casefold()
        # A heading marked historical exempts its whole section until the next heading.
        if lowered.lstrip().startswith("#"):
            section_exempt = any(marker in lowered for marker in MARKERS)
        if section_exempt or any(marker in lowered for marker in MARKERS):
            continue
        for figure, pattern in patterns.items():
            if pattern.search(lowered):
                offences.append(f"{path.name}:{number} quotes retired {figure!r}: {line.strip()[:120]}")
    assert not offences, (
        "Retired figures still appear in prose. Either update the text to the current "
        "numbers, or mark the line historical with one of "
        f"{MARKERS}.\n" + "\n".join(offences))


def test_the_dashboard_reads_its_numbers_from_artifacts_not_literals():
    """The UI must render figures from the API payload, never hardcode them."""
    source = (ROOT / "web/src/main.jsx").read_text()
    # A bare percentage literal in JSX text is the shape we are guarding against.
    literals = re.findall(r">\s*\d+\.\d+%\s*<", source)
    assert not literals, f"hardcoded percentages in the dashboard: {literals}"


def test_headline_numbers_artifact_matches_a_fresh_generation():
    """A committed artifact that disagrees with the generator is itself stale."""
    path = ROOT / "artifacts/headline_numbers.json"
    if not path.exists():
        pytest.skip("headline_numbers.json not generated yet")
    stored = json.loads(path.read_text())
    fresh = _headline_report()
    assert stored["live_figures"] == fresh["live_figures"]
    assert stored["retired_figures"] == fresh["retired_figures"]


def test_the_generator_is_runnable_as_a_script():
    result = subprocess.run([sys.executable, "scripts/headline_numbers.py", "--check"],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
