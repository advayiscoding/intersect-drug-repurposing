import pytest

from repurpose.links import external_link

CASES = [
    ({"type": "pathway", "source": "REACTOME", "source_id": "R-HSA-629597"},
     "https://reactome.org/content/detail/R-HSA-629597"),
    ({"type": "gene/protein", "source": "NCBI", "source_id": "1141"},
     "https://www.ncbi.nlm.nih.gov/gene/1141"),
    ({"type": "drug", "source": "DrugBank", "source_id": "DB00657"},
     "https://go.drugbank.com/drugs/DB00657"),
    ({"type": "disease", "source": "MONDO", "source_id": "11401"},
     "https://monarchinitiative.org/MONDO:0011401"),
    ({"type": "effect/phenotype", "source": "HPO", "source_id": "1507"},
     "https://monarchinitiative.org/HP:0001507"),
    ({"type": "biological_process", "source": "GO", "source_id": "51581"},
     "https://amigo.geneontology.org/amigo/term/GO:0051581"),
    ({"type": "anatomy", "source": "UBERON", "source_id": "2"},
     "http://purl.obolibrary.org/obo/UBERON_0000002"),
]


@pytest.mark.parametrize("node,expected", CASES)
def test_every_linkable_node_type_resolves_to_its_own_page(node, expected):
    assert external_link(node) == expected


def test_already_prefixed_identifiers_are_not_double_prefixed():
    assert external_link({"source": "MONDO", "source_id": "MONDO:0011401"}) == \
        "https://monarchinitiative.org/MONDO:0011401"


@pytest.mark.parametrize("node", [
    # Grouped MONDO nodes collapse many terms and have no single page.
    {"type": "disease", "source": "MONDO_grouped", "source_id": "11913_7088_11743"},
    {"type": "exposure", "source": "CTD", "source_id": "C092102"},
    {"type": "drug", "source": "SomethingNew", "source_id": "X1"},
    {"type": "gene/protein", "source": "NCBI", "source_id": "not-a-number"},
    {"type": "drug", "source": "DrugBank", "source_id": "12345"},
    {"type": "disease", "source": "MONDO", "source_id": ""},
    {"type": "pathway"},
])
def test_unknown_or_unreliable_sources_return_no_link(node):
    assert external_link(node) is None
