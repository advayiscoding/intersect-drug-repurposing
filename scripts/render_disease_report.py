"""Render the Stage 1 checkpoint from cached numbers, without running the pipeline."""
import argparse
from html import escape
import json
from pathlib import Path


def render_report(report, manifest):
    def pct(value):
        return f"{100 * value:.2f}%"

    def cell(method, k):
        metrics = method["metrics"]
        value = pct(metrics[f"recall_at_{k}"])
        ci = method["exact_95_ci"]
        if ci is None:
            return f"{value}<small>exact random expectation</small>"
        lo, hi = ci[f"recall_at_{k}"]
        return (f'{metrics[f"hits_at_{k}"]}/{report["heldout_count"]} · {value}'
                f'<small>95% CI {pct(lo)}–{pct(hi)}</small>')

    rows = []
    for key, name in (("path_only", "Fixed path-only"), ("popularity_only", "Popularity"), ("random", "Random")):
        method = report["methods"][key]
        cells = "".join(f"<td>{cell(method, k)}</td>" for k in (10, 20, 50, 100))
        rows.append(f"<tr><th scope='row'>{name}</th>{cells}</tr>")
    path = report["methods"]["path_only"]
    lift = path["lift"]["20"]
    family_rows = "".join(
        f'<tr><th scope="row">{k}</th><td>{path["distinct_families_at_k"][k]}</td>'
        f'<td>{r["observed"]}</td><td>{r["p_value_one_sided"]:.3f}</td></tr>'
        for k, r in report["family_permutation"]["results"].items())
    rr_rows = "".join(
        f'<tr><th scope="row">{escape(name)}</th><td>{r["metrics"]["mrr"]:.5f}</td>'
        f'<td>{r["metrics"]["mean_reciprocal_heldout_rank"]:.5f}</td></tr>'
        for name, r in report["methods"].items())
    audit = ("The frozen registry rules include healthy-volunteer and interaction-probe studies. "
             "Acetaminophen (one top-50 path hit) appears in NCT02305017, a healthy-volunteer "
             "interaction study. Caffeine (the popularity hit) appears in NCT03970798 as an "
             "index substrate. These labels do not establish testing for benefit in Parkinson patients. "
             "Labels and scoring were not changed after viewing the results."
             if report["disease_id"] == "parkinsons" else
             "The small Alzheimer sample is concentrated in insulin variants and choline. "
             "This is a replay, not new independent validation.")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(report['disease_name'])} · Stage 1 checkpoint</title>
<style>
body{{margin:0;background:#f1f4f5;color:#172b35;font:16px/1.5 system-ui,sans-serif}}
main{{max-width:1180px;margin:32px auto;padding:0 24px 40px}}h1{{font-size:32px;margin:8px 0}}
h2{{font-size:21px;margin:0 0 12px}}p{{margin:10px 0}}.eyebrow{{letter-spacing:.12em;font-size:13px}}
.banner{{background:#172b35;color:white;padding:16px 20px;border-radius:8px}}
section{{background:white;border:1px solid #ced9df;border-radius:8px;padding:22px;margin-top:20px}}
.warning{{border-left:5px solid #955600;background:#fff8e9}}small{{display:block;color:#405965;font-size:13px}}
table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;text-align:left}}
th,td{{padding:12px 10px;border-bottom:1px solid #dce3e6;vertical-align:top}}thead th{{background:#edf3f5}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}.scroll{{overflow-x:auto}}
@media(max-width:850px){{.grid{{display:block}}main{{padding:0 12px}}}}
</style></head><body><main>
<div class="eyebrow">INTERSECT / FIXED-METHOD PILOT / STAGE 1</div>
<h1>{escape(report['disease_name'])}: lift over baselines</h1>
<div class="banner">{escape(report['disclaimer'])}</div>
<p>{report['candidate_count']:,} discovery drugs · {report['family_count']:,} candidate families ·
{report['heldout_count']} registry-labeled drugs / {report['positive_family_count']} labeled families ·
{report['known_controls_excluded']} known controls excluded from the candidate pool.</p>
<section><h2>Primary endpoints: recall at 10 and 20 drugs</h2>
<div class="scroll"><table><thead><tr><th>Ranking</th><th>Recall@10 · primary</th><th>Recall@20 · primary</th>
<th>Recall@50 · secondary</th><th>Recall@100 · secondary</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p>At 20: {lift['vs_random_ratio']:.2f}× random expectation;
{lift['vs_popularity_percentage_points']:+.2f} percentage points versus popularity.</p>
<small>Exact Clopper–Pearson intervals describe label recovery, not clinical outcomes. Random recall is analytical k/N;
it has no fitted binomial interval. Variants may be correlated; examine family results too.</small></section>
<section class="warning"><h2>What these labels do—and do not—mean</h2><p>{escape(audit)}</p>
<p>Trial participation does not establish efficacy. The sample is small, labels are incomplete,
and this is a retrospective graph holdout, not a temporal test. Secondary endpoints cannot replace the primary result.</p></section>
<div class="grid"><section><h2>Distinct family recovery</h2><table><thead><tr><th>k</th>
<th>Within top-k drugs</th><th>Top-k collapsed family cards</th><th>Permutation p</th></tr></thead>
<tbody>{family_rows}</tbody></table><small>Different ranking units: collapsing variants can move a label into the first
20 family cards despite no hit in the first 20 drugs. 10,000 permutations; k=20 primary family test;
k=10/50 exploratory, unadjusted.</small></section>
<section><h2>Reciprocal rank</h2><table><thead><tr><th>Ranking</th><th>Single-query MRR</th>
<th>All-label mean</th></tr></thead><tbody>{rr_rows}</tbody></table>
<small>Single-query MRR is 1 / first label rank. All-label mean averages 1 / rank over every label.
Random values average 1,000 permutations.</small></section></div>
<section><h2>Fixed protocol and remaining limits</h2><p>No label-fitted hyperparameters or disease-specific tuning.
Fresh pandas load → both-direction target/drug removal → three-hop graph → fixed degree-normalized path score.</p>
<p>{manifest['removed_target_drug_rows']} source rows removed across {len(manifest['guard_target_ids'])} guarded targets;
{manifest['graph_nodes']:,} graph nodes. Direction unknown. {escape(report['embedding_note'])} LINCS unavailable.</p>
<small>Inputs and scoring hashes: manifest.json / frozen_inputs.json. Numbers: primary_validation.json.
Stage 1 checkpoint only; the product UI and evidence remain Alzheimer-only.</small></section>
</main></body></html>"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    report = json.loads((args.folder / "primary_validation.json").read_text())
    manifest = json.loads((args.folder / "manifest.json").read_text())
    destination = args.folder / "report.html"
    destination.write_text(render_report(report, manifest))
    print(destination)
