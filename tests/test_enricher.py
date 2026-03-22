"""Tests for GraphEnricher."""

import pytest

from graphforge.builder import GraphBuilder
from graphforge.enricher import GraphEnricher
from graphforge.models import Entity, Relationship


@pytest.fixture()
def builder():
    b = GraphBuilder()
    entities = [
        Entity(id="a", label="A", entity_type="t"),
        Entity(id="b", label="B", entity_type="t"),
        Entity(id="c", label="C", entity_type="t"),
    ]
    rels = [
        Relationship(source_id="a", target_id="b", relation_type="r", weight=2.0),
        Relationship(source_id="b", target_id="c", relation_type="r", weight=4.0),
    ]
    b.build(entities, rels)
    return b


@pytest.fixture()
def enricher(builder):
    return GraphEnricher(builder)


def test_add_node_property(enricher):
    result = enricher.add_node_property("a", "color", "red")
    assert result is True
    assert enricher.graph.nodes["a"]["color"] == "red"


def test_add_node_property_missing(enricher):
    result = enricher.add_node_property("ghost", "x", 1)
    assert result is False


def test_bulk_enrich_nodes(enricher):
    missing = enricher.bulk_enrich_nodes({"a": {"score": 10}, "ghost": {"score": 0}})
    assert missing == ["ghost"]
    assert enricher.graph.nodes["a"]["score"] == 10


def test_enrich_degree_centrality(enricher):
    enricher.enrich_degree_centrality()
    for nid in ["a", "b", "c"]:
        assert "degree_centrality" in enricher.graph.nodes[nid]


def test_enrich_pagerank(enricher):
    enricher.enrich_pagerank()
    for nid in ["a", "b", "c"]:
        assert "pagerank" in enricher.graph.nodes[nid]


def test_normalize_weights(enricher):
    enricher.normalize_weights()
    for _, _, d in enricher.graph.edges(data=True):
        assert 0.0 <= d["weight_normalized"] <= 1.0


def test_tag_nodes(enricher):
    enricher.tag_nodes(["a", "b"], "highlight")
    assert enricher.graph.nodes["a"]["highlight"] is True
    assert enricher.graph.nodes["b"]["highlight"] is True
    assert "highlight" not in enricher.graph.nodes["c"]


def test_apply_node_function(enricher):
    def fn(nid, data):
        return {"upper_id": nid.upper()}

    enricher.apply_node_function(fn)
    assert enricher.graph.nodes["a"]["upper_id"] == "A"


def test_add_edge_property(enricher):
    result = enricher.add_edge_property("a", "b", "label", "edge_ab")
    assert result is True
    assert enricher.graph["a"]["b"]["label"] == "edge_ab"
