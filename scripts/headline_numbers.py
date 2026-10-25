"""Generate the canonical headline numbers from artifacts, and name the retired ones.

One source of truth for every figure quoted in prose. Run it after any evaluation
changes; `tests/test_stale_numbers.py` then fails the build if a document, the
dashboard, the Q&A or the plain-language text still quotes a figure this script
says is retired.

    PYTHONPATH=src python3 scripts/headline_numbers.py          # write + print
    PYTHONPATH=src python3 scripts/headline_numbers.py --check  # print only

A figure is "live" if it appears in the current artifacts. A figure is "retired" if
it was once a headline and no longer matches any artifact. Retired figures may still
be quoted on a line explicitly marked historical — see MARKERS in the test.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# Figures that have been published as headlines at some point in this project's life.
# Nothing is deleted from this list; the generator decides which are still live.
HISTORICAL_HEADLINES = [
    "4/44", "9.09%", "8.15x", "8.05x", "8.62x", "16.09x", "2.53%", "21.67%",
    "13.64%", "6/44", "0.080", "0.0799", "2 of 41", "0/39", "1/39", "4/39", "6/39",
    "9.03%", "0.356", "8.33%", "10.42%", "5/48", "4/48",
]


def _pct(value: float) -> list[str]:
    """Every spelling of a proportion we might reasonably write."""
    return [f"{value * 100:.2f}%", f"{value * 100:.1f}%", f"{round(value * 100):g}%"]


def collect(root: Path) -> dict:
    live: set[str] = set()
    report: dict = {"diseases": {}, "strict": {}}

    for folder in sorted((root / "artifacts/diseases").glob("*")):
        path = folder / "primary_validation.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        total = data.get("heldout_count")
        entry = {"labels": total, "candidates": data.get("candidate_count"),
                 "families": data.get("family_count"),
                 "positive_families": data.get("positive_family_count")}
        # Every method, not just the primary one: popularity and random figures are
        # quoted in prose too, and a figure we fail to emit looks falsely retired.
        for method, block in (data.get("methods") or {}).items():
            metrics, ci = block["metrics"], block.get("exact_95_ci") or {}
            for k in (10, 20, 50, 100):
                hits = metrics.get(f"hits_at_{k}")
                recall = metrics.get(f"recall_at_{k}")
                if hits is None or recall is None:
                    continue
                if method == "path_only":
                    entry[f"hits_at_{k}"] = hits
                    entry[f"recall_at_{k}"] = recall
                if float(hits).is_integer():
                    live.add(f"{int(hits)}/{total}")
                live.update(_pct(recall))
                enrichment = metrics.get(f"enrichment_at_{k}")
                if enrichment:
                    live.add(f"{enrichment:.2f}x")
                if ci.get(f"recall_at_{k}"):
                    low, high = ci[f"recall_at_{k}"]
                    live.update(_pct(low) + _pct(high))
            families = block.get("distinct_families_at_k") or {}
            for k, count in families.items():
                if isinstance(count, int):
                    live.add(f"{count} of {data.get('positive_family_count')}")
                    live.add(f"{count}/{data.get('positive_family_count')}")
            if method == "path_only":
                entry["enrichment_at_20"] = metrics.get("enrichment_at_20")
                entry["distinct_families_at_20"] = families.get("20")
        permutation = (data.get("family_permutation") or {}).get("results", {})
        for k, value in permutation.items():
            p = value["p_value_one_sided"]
            live.update({f"{p:.3f}", f"{p:.4f}", f"{p:.2f}"})
            if k == "20":
                entry["permutation_p_at_20"] = p
        report["diseases"][folder.name] = entry

    audited = root / "artifacts/audited_validation.json"
    if audited.exists():
        data = json.loads(audited.read_text())
        for disease, value in data.get("diseases", {}).items():
            section = {}
            for name in ("strict", "strict_sensitivity", "raw"):
                block = value.get(name)
                if not block or not block.get("methods"):
                    continue
                path_only = block["methods"].get("path_only")
                if not path_only:
                    continue
                total = block.get("heldout_count")
                figures = {"labels": total,
                           "positive_families": block.get("positive_family_count"),
                           "sample_note": block.get("sample_note")}
                for k in (10, 20):
                    hits = path_only["metrics"][f"hits_at_{k}"]
                    figures[f"hits_at_{k}"] = hits
                    figures[f"recall_at_{k}"] = path_only["metrics"][f"recall_at_{k}"]
                    live.add(f"{hits}/{total}")
                    live.update(_pct(path_only["metrics"][f"recall_at_{k}"]))
                    ci = (path_only.get("exact_95_ci") or {}).get(f"recall_at_{k}")
                    if ci:
                        live.update(_pct(ci[0]) + _pct(ci[1]))
                section[name] = figures
            report["strict"][disease] = section

    report["live_figures"] = sorted(live)
    report["retired_figures"] = sorted(f for f in HISTORICAL_HEADLINES if f not in live)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--check", action="store_true", help="print without writing")
    args = parser.parse_args()
    report = collect(args.root)
    if not args.check:
        destination = args.root / "artifacts/headline_numbers.json"
        destination.write_text(json.dumps(report, indent=2) + "\n")
        print(f"wrote {destination}")
    print(json.dumps({"live": len(report["live_figures"]),
                      "retired": report["retired_figures"]}, indent=2))


if __name__ == "__main__":
    main()
