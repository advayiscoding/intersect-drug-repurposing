import numpy as np

from repurpose.embeddings import FilteredSampler


def test_negative_sampling_excludes_forward_reverse_heldout_pairs_and_known_triples():
    # local entities: drugs 0,1; target disease 2; other diseases 3,4
    triples = np.array([[0, 0, 3], [1, 0, 4]])
    sampler = FilteredSampler(triples, {0: (np.array([0, 1]), np.array([2, 3, 4]))},
                              ["drug", "drug", "disease", "disease", "disease"], {2}, 5, 1)
    assert sampler.forbidden(np.array([[0, 0, 2], [2, 0, 0], [1, 0, 2], [2, 0, 1]])).all()
    negatives = sampler.sample(triples, count=500)
    assert not sampler.forbidden(negatives).any()
    assert set(map(tuple, negatives)) == {(0, 0, 4), (1, 0, 3)}
