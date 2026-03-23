"""Extended tests for GraphEnricher — targeting uncovered branches."""

from __future__ import annotations

import pytest

from graphforge.builder import GraphBuilder
from graphforge.enricher import GraphEnricher
from tests.conftest import make_entity, make_relationship


@pytest.fixture()
def linear_builder() -> GraphBuilder:
    """GraphBuilder with a simple A→B→C linear chain."""
    b = GraphBuilder()
    b.build(
        [make_entity("A"), make_entity("B"), make_entity("C")],
        [make_relationship("A", "B", weight=1.0), make_relationship("B", "C", weight=3.0)],
    )
    return b


def test_add_edge_property_missing(linear_builder):
    """Line 65: add_edge_property returns False for unknown edge."""
    enricher = GraphEnricher(linear_builder)
    result = enricher.add_edge_property("A", "C", "key", "val")  # no direct edge
    assert result is False


def test_enrich_clustering(linear_builder):
    """Lines 89-92: clustering coefficient enrichment."""
    enricher = GraphEnricher(linear_builder)
    enricher.enrich_clustering()
    for nid in ["A", "B", "C"]:
        assert "clustering" in enricher.graph.nodes[nid]


def test_enrich_community_labels(linear_builder):
    """Lines 98-105: community label enrichment."""
    enricher = GraphEnricher(linear_builder)
    label_map = enricher.enrich_community_labels()
    assert isinstance(label_map, dict)
    for nid in ["A", "B", "C"]:
        assert nid in label_map
        assert isinstance(label_map[nid], int)
        assert "community" in enricher.graph.nodes[nid]


def test_normalize_weights_single_weight():
    """Line 119: normalize_weights with all equal weights (spread=1 fallback)."""
    b = GraphBuilder()
    b.build(
        [make_entity("X"), make_entity("Y"), make_entity("Z")],
        [
            make_relationship("X", "Y", weight=5.0),
            make_relationship("Y", "Z", weight=5.0),
        ],
    )
    enricher = GraphEnricher(b)
    enricher.normalize_weights()
    for _, _, d in enricher.graph.edges(data=True):
        assert d["weight_normalized"] == 0.0  # (5-5)/1 = 0


def test_normalize_weights_empty_graph():
    """normalize_weights on graph with no edges should not raise."""
    b = GraphBuilder()
    b.add_entity(make_entity("solo"))
    enricher = GraphEnricher(b)
    enricher.normalize_weights()  # should not raise


def test_enrich_pagerank_custom_attr(linear_builder):
    """enrich_pagerank with custom attribute name."""
    enricher = GraphEnricher(linear_builder)
    enricher.enrich_pagerank(attr_name="pr_score")
    for nid in ["A", "B", "C"]:
        assert "pr_score" in enricher.graph.nodes[nid]


def test_tag_nodes_with_custom_value(linear_builder):
    """tag_nodes with non-default value."""
    enricher = GraphEnricher(linear_builder)
    enricher.tag_nodes(["A"], "priority", value=5)
    assert enricher.graph.nodes["A"]["priority"] == 5


def test_tag_nodes_missing_node_ignored(linear_builder):
    """tag_nodes should silently ignore missing node IDs."""
    enricher = GraphEnricher(linear_builder)
    enricher.tag_nodes(["ghost_node"], "x")  # should not raise


def test_bulk_enrich_nodes_all_found(linear_builder):
    """bulk_enrich_nodes with no missing nodes returns empty list."""
    enricher = GraphEnricher(linear_builder)
    missing = enricher.bulk_enrich_nodes({"A": {"score": 1}, "B": {"score": 2}})
    assert missing == []
    assert enricher.graph.nodes["A"]["score"] == 1
