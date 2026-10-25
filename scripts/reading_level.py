"""Flesch–Kincaid grade level for the plain-language copy.

A plain-language mode that reads like the methodology section is not plain language.
This scores every reader-facing sentence and reports the worst offenders so they can
be rewritten rather than quietly shipped.

    PYTHONPATH=src python3 scripts/reading_level.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VOWELS = "aeiouy"
TARGET_GRADE = 9.0


def syllables(word: str) -> int:
    word = re.sub(r"[^a-z]", "", word.casefold())
    if not word:
        return 0
    count, previous_vowel = 0, False
    for char in word:
        vowel = char in VOWELS
        if vowel and not previous_vowel:
            count += 1
        previous_vowel = vowel
    if word.endswith("e") and count > 1 and not word.endswith(("le", "ee")):
        count -= 1
    return max(1, count)


def grade(text: str) -> float | None:
    """Flesch–Kincaid grade level. None when there is nothing to score."""
    parts = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    words = re.findall(r"[A-Za-z']+", text)
    if not parts or not words:
        return None
    total = sum(syllables(w) for w in words)
    return 0.39 * (len(words) / len(parts)) + 11.8 * (total / len(words)) - 15.59


def report(root: Path) -> dict:
    sys.path.insert(0, str(root / "src"))
    from repurpose.plain_language import sentences
    copy = json.loads((root / "artifacts/plain_language.json").read_text())
    scored = []
    for text in sentences(copy):
        value = grade(text)
        if value is not None:
            scored.append({"grade": round(value, 2), "text": text})
    scored.sort(key=lambda item: -item["grade"])
    whole = grade(" ".join(sentences(copy)))
    return {"target_grade": TARGET_GRADE, "overall_grade": round(whole, 2) if whole else None,
            "worst": scored[:8], "count": len(scored),
            "over_target": [s for s in scored if s["grade"] > TARGET_GRADE]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    result = report(args.root)
    print(json.dumps(result, indent=2))
    if result["over_target"]:
        print(f"\n{len(result['over_target'])} sentence(s) above grade {TARGET_GRADE}")


if __name__ == "__main__":
    main()
