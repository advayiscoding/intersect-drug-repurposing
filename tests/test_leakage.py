import pandas as pd
import pytest

from repurpose.graph import remove_target_drug_edges, neighborhood, build_graph, assert_no_leakage
from repurpose.ranking import score_candidates


def test_removes_all_relations_and_reverse_copies_before_graph_and_degree():
    nodes = {1: {"id": 1, "name": "AD", "type": "disease"},
             2: {"id": 2, "name": "held-out", "type": "drug", "source_id": "D2"},
             3: {"id": 3, "name": "gene", "type": "gene/protein"}}
    clean = [(1, 3, "disease_protein"), (2, 3, "drug_protein")]
    injected = [(1, 2, "indication"), (2, 1, "indication"),
                (1, 2, "off-label use"), (2, 1, "contraindication")]
    frame = lambda rows: pd.DataFrame(rows, columns=["x_index", "y_index", "relation"])
    sanitized, removed = remove_target_drug_edges(frame(clean + injected), {1}, {2})
    assert len(removed) == 4
    assert_no_leakage(sanitized, {1}, {2})
    with pytest.raises(ValueError, match="leakage"):
        assert_no_leakage(frame(clean + injected), {1}, {2})
    # Training triples, node selection, degrees, and rankings all invariant to labels.
    expected = neighborhood(frame(clean), {1})
    actual = neighborhood(sanitized, {1})
    pd.testing.assert_frame_equal(expected, actual)
    a, b = build_graph(expected, nodes), build_graph(actual, nodes)
    assert dict(a.degree()) == dict(b.degree()) == {1: 1, 3: 2, 2: 1}
    assert score_candidates(a, nodes, {1}, [2]) == score_candidates(b, nodes, {1}, [2])


def test_label_edge_cannot_select_an_isolated_drug_into_neighborhood():
    edges = pd.DataFrame([(1, 3, "disease_protein"), (1, 2, "indication")],
                         columns=["x_index", "y_index", "relation"])
    clean, _ = remove_target_drug_edges(edges, {1}, {2})
    subgraph = neighborhood(clean, {1})
    assert 2 not in set(subgraph.x_index) | set(subgraph.y_index)
