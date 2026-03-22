"""Tests for GraphBuilder."""

import pytest

from graphforge.builder import GraphBuilder
from graphforge.models import Entity, Relationship


@pytest.fixture()
def sample_entities():
    return [
        Entity(id="py", label="Python", entity_type="software"),
        Entity(id="dj", label="Django", entity_type="software"),
        Entity(id="psf", label="PSF", entity_type="organization"),
    ]


@pytest.fixture()
def sample_rels():
    return [
        Relationship(source_id="dj", target_id="py", relation_type="depends_on"),
        Relationship(source_id="py", target_id="psf", relation_type="developed_by"),
    ]


@pytest.fixture()
def built_graph(sample_entities, sample_rels):
    b = GraphBuilder()
    b.build(sample_entities, sample_rels)
    return b


def test_node_count(built_graph):
    assert built_graph.node_count == 3


def test_edge_count(built_graph):
    assert built_graph.edge_count == 2


def test_get_node(built_graph):
    node = built_graph.get_node("py")
    assert node is not None
    assert node["label"] == "Python"


def test_get_node_missing(built_graph):
    assert built_graph.get_node("nope") is None


def test_get_neighbors(built_graph):
    neighbors = built_graph.get_neighbors("dj")
    assert "py" in neighbors


def test_find_by_type(built_graph):
    software = built_graph.find_by_type("software")
    assert set(software) == {"py", "dj"}


def test_shortest_path(built_graph):
    path = built_graph.shortest_path("dj", "psf")
    assert path == ["dj", "py", "psf"]


def test_shortest_path_no_path(built_graph):
    path = built_graph.shortest_path("psf", "dj")
    assert path == []


def test_to_dict_roundtrip(built_graph):
    d = built_graph.to_dict()
    restored = GraphBuilder.from_dict(d)
    assert restored.node_count == built_graph.node_count
    assert restored.edge_count == built_graph.edge_count


def test_degree_centrality(built_graph):
    centrality = built_graph.degree_centrality()
    assert "py" in centrality
    assert centrality["py"] > 0
