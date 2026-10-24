from repurpose.selection import choose_weight, combined_scores, ordered


def test_weight_selection_receives_only_tuning_labels_and_prefers_path_on_tie():
    scores = {i: float(100-i) for i in range(100)}
    weight, _ = choose_weight(scores, scores, {1, 2}, list(scores), [0, .25, .5, .75, 1])
    assert weight == 0
    assert ordered(combined_scores(scores, scores, 0), list(scores)) == ordered(scores, list(scores))


def test_weight_can_improve_tuning_recall_without_any_test_label_input():
    path = {i: float(100-i) for i in range(100)}
    embedding = {i: float(i) for i in range(100)}
    weight, _ = choose_weight(path, embedding, {98, 99}, list(path), [0, 1])
    assert weight == 1
