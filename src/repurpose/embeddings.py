"""Fixed-budget DistMult on sanitized PrimeKG triples, with filtered negatives."""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.nn import functional as F

from .data import digest, write_json
from .graph import assert_no_leakage

SCHEMA = {"drug_protein": ("drug", "gene/protein"),
          "protein_protein": ("gene/protein", "gene/protein"),
          "disease_protein": ("disease", "gene/protein"),
          "pathway_protein": ("pathway", "gene/protein"),
          "indication": ("drug", "disease"), "off-label use": ("drug", "disease"),
          "contraindication": ("drug", "disease")}


def encode(triples, n_entities, n_relations):
    return (triples[:, 0] * n_relations + triples[:, 1]) * n_entities + triples[:, 2]


class FilteredSampler:
    def __init__(self, triples, pools, entity_types, target_ids, n_entities, n_relations, seed=20261024):
        self.pools = pools
        self.entity_types = np.array(entity_types)
        self.target_ids = np.array(sorted(target_ids), dtype=np.int64)
        self.n, self.r = n_entities, n_relations
        self.rng = np.random.default_rng(seed)
        reverse = triples[:, [2, 1, 0]]
        self.known = np.unique(encode(np.concatenate([triples, reverse]), self.n, self.r))
        self.rejected = 0

    def forbidden(self, rows):
        codes = encode(rows, self.n, self.r)
        positions = np.searchsorted(self.known, codes)
        known = self.known[np.minimum(positions, len(self.known) - 1)] == codes
        # Exclude ALL target/drug pairs, including held-out positives, either direction
        # and regardless of relation. No test labels are needed by the sampler.
        target_drug = ((np.isin(rows[:, 0], self.target_ids) & (self.entity_types[rows[:, 2]] == "drug"))
                       | (np.isin(rows[:, 2], self.target_ids) & (self.entity_types[rows[:, 0]] == "drug")))
        return known | target_drug | (rows[:, 0] == rows[:, 2])

    def sample(self, positive, count=4):
        source = np.repeat(positive, count, axis=0)
        result = source.copy()
        pending = np.arange(len(result))
        for _ in range(100):
            if not len(pending):
                return result
            corrupt_head = self.rng.random(len(pending)) < .5
            for relation in np.unique(source[pending, 1]):
                for side, mask in ((0, corrupt_head), (2, ~corrupt_head)):
                    indices = pending[(source[pending, 1] == relation) & mask]
                    result[indices] = source[indices]
                    pool = self.pools[int(relation)][0 if side == 0 else 1]
                    result[indices, side] = self.rng.choice(pool, len(indices))
            invalid = self.forbidden(result[pending])
            self.rejected += int(invalid.sum())
            pending = pending[invalid]
        raise RuntimeError("Negative filtering exhausted retries; do not train on forbidden negatives")


class DistMult(nn.Module):
    def __init__(self, n_entities, n_relations, dim):
        super().__init__()
        self.entities = nn.Embedding(n_entities, dim, sparse=True)
        self.relations = nn.Embedding(n_relations, dim, sparse=True)
        nn.init.uniform_(self.entities.weight, -.1, .1)
        nn.init.uniform_(self.relations.weight, -.1, .1)

    def forward(self, rows):
        h, r, t = self.entities(rows[:, 0]), self.relations(rows[:, 1]), self.entities(rows[:, 2])
        return (h * r * t).sum(-1), (h.square().mean() + r.square().mean() + t.square().mean())


def train(root: Path):
    start = time.monotonic()
    out, processed = root / "artifacts", root / "data/processed"
    if (out / "embedding_run.json").exists():
        raise ValueError("A fitted experiment exists; preserve it and do not retune after test results")
    protocol = json.loads((out / "protocol.json").read_text())
    training = processed / "training_edges.parquet"
    if digest(training) != protocol["training_edges_sha256"]:
        raise ValueError("Sanitized training hash changed")
    config = {"model": "DistMult", "dimension": 64, "epochs": 40, "batch_size": 2048,
              "negatives_per_positive": 4, "lr": .003, "regularization": .0001,
              "max_per_relation_per_epoch": 30000, "seed": 20261024,
              "wall_time_limit_seconds": 10800, "device": "cpu", "torch_threads": 2,
              "selection": "Fixed configuration, no test-based model selection or early stopping",
              "target_aggregation": "max indication score over resolved Alzheimer disease nodes",
              "protocol_sha256": digest(out / "protocol.json")}
    write_json(out / "embedding_config.json", config)
    edges = pd.read_parquet(training)
    nodes = {n["id"]: n for n in json.loads((processed / "nodes.json").read_text())}
    targets = {d["id"] for d in json.loads((out / "manifest.json").read_text())["target_diseases"]}
    assert_no_leakage(edges, targets, set(protocol["tuning_ids"] + protocol["test_ids"]))
    assert_no_leakage(edges, targets, {i for i, n in nodes.items() if n["type"] == "drug"})
    ids = sorted(set(edges.u) | set(edges.v))
    mapping = {int(i): j for j, i in enumerate(ids)}
    relations = sorted(edges.relation.astype(str).unique())
    relation_map = {r: i for i, r in enumerate(relations)}
    rows = []
    for row in edges.itertuples(index=False):
        h, t = int(row.u), int(row.v)
        htype, ttype = SCHEMA[row.relation]
        if nodes[h]["type"] != htype or nodes[t]["type"] != ttype:
            h, t = t, h
        if nodes[h]["type"] != htype or nodes[t]["type"] != ttype:
            raise ValueError(f"Schema mismatch in {row.relation}")
        rows.append((mapping[h], relation_map[row.relation], mapping[t]))
    triples = np.array(rows, dtype=np.int64)
    types = [nodes[i]["type"] for i in ids]
    pools = {ri: (np.flatnonzero(np.array(types) == SCHEMA[r][0]),
                  np.flatnonzero(np.array(types) == SCHEMA[r][1])) for r, ri in relation_map.items()}
    sampler = FilteredSampler(triples, pools, types, {mapping[i] for i in targets if i in mapping},
                              len(ids), len(relations))
    torch.manual_seed(config["seed"])
    torch.set_num_threads(config["torch_threads"])
    torch.use_deterministic_algorithms(True)
    model = DistMult(len(ids), len(relations), config["dimension"])
    optimizer = torch.optim.SparseAdam(model.parameters(), lr=config["lr"])
    rng = np.random.default_rng(config["seed"])
    grouped = [np.flatnonzero(triples[:, 1] == ri) for ri in range(len(relations))]
    history, seen = [], 0
    for epoch in range(config["epochs"]):
        indices = np.concatenate([rng.choice(g, min(len(g), config["max_per_relation_per_epoch"]), replace=False) for g in grouped])
        rng.shuffle(indices)
        losses = []
        for offset in range(0, len(indices), config["batch_size"]):
            if time.monotonic() - start > config["wall_time_limit_seconds"]:
                break
            positive = triples[indices[offset:offset + config["batch_size"]]]
            negatives = sampler.sample(positive, config["negatives_per_positive"])
            optimizer.zero_grad()
            pos_score, pos_reg = model(torch.from_numpy(positive))
            neg_score, neg_reg = model(torch.from_numpy(negatives))
            loss = .5 * (F.softplus(-pos_score).mean() + F.softplus(neg_score).mean())
            loss += config["regularization"] * (pos_reg + neg_reg)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
            seen += len(positive)
        history.append({"epoch": epoch + 1, "loss": float(np.mean(losses)) if losses else None,
                        "elapsed_seconds": round(time.monotonic() - start, 2)})
        print(json.dumps(history[-1]), flush=True)
        if time.monotonic() - start > config["wall_time_limit_seconds"]:
            break
    model.eval()
    scores = {}
    target_local = [mapping[i] for i in sorted(targets) if i in mapping]
    candidates = json.loads((out / "rankings.json").read_text())
    with torch.no_grad():
        for row in candidates:
            drug = row["drug_id"]
            if drug not in mapping:
                scores[str(drug)] = None
                continue
            queries = torch.tensor([[mapping[drug], relation_map["indication"], t] for t in target_local])
            scores[str(drug)] = float(model(queries)[0].max())
    checkpoint = processed / "distmult.pt"
    torch.save({"state_dict": model.state_dict(), "entity_ids": ids,
                "relations": relations, "config": config}, checkpoint)
    write_json(out / "embedding_scores.json", scores)
    write_json(out / "embedding_run.json", {"config": config, "history": history,
        "training_triples": len(triples), "positive_presentations": seen,
        "filtered_negative_rejections": sampler.rejected,
        "negative_policy": "Type-constrained corruption; reject known triples and reverses, self-pairs, and ALL Alzheimer/drug pairs for all relations",
        "no_heldout_training_edges": True, "no_heldout_negative_pairs": True,
        "elapsed_seconds": time.monotonic() - start, "torch_version": torch.__version__,
        "training_edges_sha256": digest(training), "model_sha256": digest(checkpoint),
        "scores_sha256": digest(out / "embedding_scores.json"),
        "test_labels_used_for_training_or_selection": False,
        "note": "Source graph is undirected/unsigned; DistMult does not infer activation or inhibition."})
