"""Prepare graph evidence for an offline UI; no generated biological claims."""
import json
from pathlib import Path

import pandas as pd

from .data import write_json, digest
from .graph import build_graph, assert_no_leakage
from .links import external_link
from .ranking import score_candidates, related


def prepare_ui(root: Path):
    out = root / "artifacts"
    read = lambda name: json.loads((out/name).read_text())
    manifest, rows = read("manifest.json"), read("discovery_rankings.json")
    training = root / "data/processed/training_edges.parquet"
    if digest(training) != manifest["training_edges_sha256"]:
        raise ValueError("Training graph changed")
    nodes = {n["id"]:n for n in json.loads((root/"data/processed/nodes.json").read_text())}
    targets = {n["id"] for n in manifest["target_diseases"]}
    edges = pd.read_parquet(training)
    assert_no_leakage(edges, targets, {i for i,n in nodes.items() if n["type"]=="drug"})
    graph = build_graph(edges, nodes)
    ranked = score_candidates(graph, nodes, targets, [r["drug_id"] for r in rows])
    original = {r["drug_id"]:r for r in rows}
    labels = {r["drug_id"]:r for r in read("trial_labels.json")["labels"]}
    details = {}
    for row in ranked:
        drug = row["drug_id"]
        if row["path_score"] != original[drug]["path_score"]:
            raise ValueError("UI score disagrees with frozen path score")
        graph_nodes, graph_edges = {drug:nodes[drug]}, {}
        for path in row["paths"]:
            graph_nodes.update({n["id"]:n for n in path["nodes"]})
            for edge in path["edges"]:
                u,v = sorted([edge["source"],edge["target"]])
                graph_edges[f"{u}-{v}"] = {**edge, "id":f"{u}-{v}", "context":False}
        proteins = [i for i,n in graph_nodes.items() if n["type"]=="gene/protein"]
        for gene in proteins:
            # At most one real pathway membership per displayed protein; context only.
            pathways = sorted(related(graph,gene,"pathway_protein"), key=lambda i:nodes[i]["name"])
            if pathways:
                pathway = pathways[0]
                graph_nodes[pathway] = nodes[pathway]
                u,v = sorted([gene,pathway])
                graph_edges[f"{u}-{v}"] = {"id":f"{u}-{v}", "source":gene,"target":pathway,
                    **graph[gene][pathway],"context":True}
        linked = [{**n, "url": external_link(n)} for n in graph_nodes.values()]
        details[str(drug)] = {"drug_id":drug,"paths":row["paths"],
            "graph":{"nodes":linked,"edges":list(graph_edges.values())},
            "trials":list({t["nct_id"]:t for t in labels.get(drug,{}).get("trials",[])}.values()),
            "evidence_status":"graph_only", "literature":[],
            "note":"Pathway branches are sourced context, not part of the ranking score. Biological direction is unknown. Literature agents are pending stage 4."}
    write_json(out/"explorer_details.json",details)
    print(f"Cached graph detail for {len(details)} drugs; every displayed edge is from the sanitized PrimeKG subgraph.")
