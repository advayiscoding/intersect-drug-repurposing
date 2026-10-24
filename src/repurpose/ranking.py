"""Deterministic typed paths with sanitized-graph degree normalization."""
from __future__ import annotations

import math
import networkx as nx


def related(graph, node, relation):
    return {other for other, edge in graph[node].items() if relation in edge["relations"]} if node in graph else set()


def score_candidates(graph: nx.Graph, nodes: dict, targets: set[int], candidates: list[int]):
    disease_genes = {d: related(graph, d, "disease_protein") for d in targets}
    degrees = dict(graph.degree())
    ranked = []
    for drug in candidates:
        paths = []
        drug_genes = related(graph, drug, "drug_protein")
        for disease, associated in disease_genes.items():
            for gene in sorted(drug_genes):
                if gene in associated:
                    paths.append([drug, gene, disease])
                for bridge in sorted(related(graph, gene, "protein_protein") & associated - {gene}):
                    paths.append([drug, gene, bridge, disease])
        scored = []
        for path in paths:
            # Uniform edge evidence weight: PrimeKG has no per-edge confidence here.
            # Penalize hubs and longer paths without fitting to held-out labels.
            score = 0.5 ** (len(path) - 3)
            score /= math.sqrt(max(1, degrees.get(drug, 0)))
            for intermediate in path[1:-1]:
                score /= math.sqrt(max(1, degrees[intermediate]))
            scored.append((score, path))
        scored.sort(key=lambda item: (-item[0], item[1]))
        # Fixed top-10 aggregation bounds effects of redundant biological routes.
        score = sum(s for s, _ in scored[:10])
        explanations = []
        for path_score, path in scored[:5]:
            explanations.append({"score": path_score,
                "nodes": [nodes[i] for i in path],
                "edges": [{"source": u, "target": v, **graph[u][v]} for u, v in zip(path, path[1:])],
                "direction": "direction unknown"})
        ranked.append({"drug_id": drug, "name": nodes[drug]["name"],
            "source_id": nodes[drug]["source_id"], "path_score": score,
            "degree": degrees.get(drug, 0), "path_count": len(scored),
            "in_subgraph": drug in graph, "paths": explanations,
            "embedding_score": None, "lincs_score": None, "combined_score": None,
            "signal_weights": {"path": 1.0, "embedding": "unavailable", "lincs": "unavailable"}})
    # SHA-256 tie order avoids favoring low database IDs. Shared across baselines.
    ranked.sort(key=lambda row: (-row["path_score"], tie_key(row["drug_id"])))
    for rank, row in enumerate(ranked, 1):
        row["rank"] = rank
    return ranked


def tie_key(drug: int) -> str:
    import hashlib
    return hashlib.sha256(f"repurpose-fixed-tie-v1:{drug}".encode()).hexdigest()
