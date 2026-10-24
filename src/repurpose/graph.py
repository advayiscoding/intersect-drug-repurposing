"""Leakage-safe graph preparation shared by scoring and future embeddings."""
from __future__ import annotations

import networkx as nx
import pandas as pd

RELATIONS = {"drug_protein", "protein_protein", "disease_protein", "pathway_protein",
             "indication", "off-label use", "contraindication"}


def target_diseases(nodes: dict) -> set[int]:
    return {i for i, n in nodes.items() if n["type"] == "disease"
            and "alzheimer" in n["name"].casefold()
            and "non-alzheimer" not in n["name"].casefold()}


def remove_target_drug_edges(edges: pd.DataFrame, targets: set[int], drugs: set[int]):
    """Remove BOTH orientations and EVERY relation for supplied pairs.

    Production supplies all drugs, a stronger restriction than just held-out drugs.
    No trial labels are needed to construct the sanitized training graph.
    """
    mask = ((edges.x_index.isin(targets) & edges.y_index.isin(drugs))
            | (edges.y_index.isin(targets) & edges.x_index.isin(drugs)))
    return edges.loc[~mask].copy(), edges.loc[mask].copy()


def neighborhood(edges: pd.DataFrame, targets: set[int], hops: int = 3):
    if hops not in (2, 3):
        raise ValueError("Only approved 2–3 hop neighborhoods are supported")
    edges = edges.loc[edges.relation.isin(RELATIONS)].copy()
    seen = set(targets)
    frontier = set(targets)
    for _ in range(hops):
        incident = edges.loc[edges.x_index.isin(frontier) | edges.y_index.isin(frontier)]
        reached = set(incident.x_index) | set(incident.y_index)
        frontier = reached - seen
        seen.update(reached)
    selected = edges.loc[edges.x_index.isin(seen) & edges.y_index.isin(seen)].copy()
    # PrimeKG publishes reciprocal copies. Collapse only identical relation pairs.
    selected["u"] = selected[["x_index", "y_index"]].min(axis=1)
    selected["v"] = selected[["x_index", "y_index"]].max(axis=1)
    return selected.drop_duplicates(["u", "v", "relation"]).reset_index(drop=True)


def build_graph(edges: pd.DataFrame, nodes: dict) -> nx.Graph:
    graph = nx.Graph()
    for row in edges.itertuples(index=False):
        u, v = int(row.u), int(row.v)
        if not graph.has_edge(u, v):
            graph.add_edge(u, v, relations=[], direction="direction unknown", source="PrimeKG")
        graph[u][v]["relations"].append(str(row.relation))
    nx.set_node_attributes(graph, {i: nodes[i] for i in graph})
    return graph


def assert_no_leakage(edges: pd.DataFrame, targets: set[int], heldout: set[int]):
    _, forbidden = remove_target_drug_edges(edges, targets, heldout)
    if not forbidden.empty:
        raise ValueError(f"Validation leakage: {len(forbidden)} target-drug rows remain")


def eligible_drugs(edges: pd.DataFrame, nodes: dict, targets: set[int]) -> list[int]:
    """Fixed full-source universe with a non-target indication; no trial-label use."""
    other = edges.loc[(edges.relation == "indication")
                      & ~edges.x_index.isin(targets) & ~edges.y_index.isin(targets)]
    ids = set(other.x_index) | set(other.y_index)
    return sorted(i for i in ids if nodes[i]["type"] == "drug")
