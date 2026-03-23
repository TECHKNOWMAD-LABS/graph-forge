"""Extended tests for GraphBuilder — targeting uncovered branches."""

from __future__ import annotations

import pytest

from graphforge.builder import GraphBuilder
from graphforge.models import Entity, Relationship
from tests.conftest import make_entity, make_relationship


def test_get_predecessors(triangle_builder):
    """Line 89-91: get_predecessors on existing and missing node."""
    preds = triangle_builder.get_predecessors("B")
    assert "A" in preds


def test_get_predecessors_missing():
    b = GraphBuilder()
    assert b.get_predecessors("ghost") == []


def test_subgraph(triangle_builder):
    """Line 110: subgraph extraction."""
    sg = triangle_builder.subgraph(["A", "B"])
    assert "A" in sg.nodes
    assert "B" in sg.nodes
    assert "C" not in sg.nodes


def test_clear(triangle_builder):
    """Line 116: clear empties the graph."""
    triangle_builder.clear()
    assert triangle_builder.node_count == 0
    assert triangle_builder.edge_count == 0


def test_add_entity_with_properties():
    b = GraphBuilder()
    e = make_entity("x", entity_type="org", version="1.0")
    b.add_entity(e)
    node = b.get_node("x")
    assert node is not None
    assert node["version"] == "1.0"


def test_add_relationship_properties():
    b = GraphBuilder()
    b.add_entity(make_entity("src"))
    b.add_entity(make_entity("tgt"))
    rel = make_relationship("src", "tgt", confidence=0.8)
    b.add_relationship(rel)
    edge_data = b.graph["src"]["tgt"]
    assert edge_data["confidence"] == 0.8


def test_graph_property(empty_builder):
    """Ensure .graph property returns DiGraph."""
    import networkx as nx

    assert isinstance(empty_builder.graph, nx.DiGraph)


def test_get_neighbors_missing_node():
    b = GraphBuilder()
    assert b.get_neighbors("no_such_node") == []


def test_find_by_type_no_match(triangle_builder):
    result = triangle_builder.find_by_type("nonexistent_type")
    assert result == []


def test_shortest_path_same_node(triangle_builder):
    """Path from a node to itself."""
    path = triangle_builder.shortest_path("A", "A")
    assert path == ["A"]


def test_from_dict_preserves_edge_weights():
    b = GraphBuilder()
    entities = [make_entity("x"), make_entity("y")]
    rels = [make_relationship("x", "y", weight=5.0)]
    b.build(entities, rels)
    d = b.to_dict()
    restored = GraphBuilder.from_dict(d)
    assert restored.graph["x"]["y"]["weight"] == 5.0


def test_degree_centrality_empty():
    b = GraphBuilder()
    centrality = b.degree_centrality()
    assert centrality == {}
