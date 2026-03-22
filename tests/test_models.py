"""Tests for Entity and Relationship models."""

from graphforge.models import Entity, Relationship


def test_entity_creation():
    e = Entity(id="e1", label="Python", entity_type="software")
    assert e.id == "e1"
    assert e.label == "Python"
    assert e.entity_type == "software"
    assert e.properties == {}


def test_entity_with_properties():
    e = Entity(id="e2", label="Linux", entity_type="software", properties={"version": "6.0"})
    assert e.properties["version"] == "6.0"


def test_entity_equality():
    e1 = Entity(id="x", label="A", entity_type="t")
    e2 = Entity(id="x", label="B", entity_type="t")
    assert e1 == e2


def test_entity_hashable():
    e1 = Entity(id="x", label="A", entity_type="t")
    e2 = Entity(id="y", label="B", entity_type="t")
    s = {e1, e2}
    assert len(s) == 2


def test_relationship_creation():
    r = Relationship(source_id="a", target_id="b", relation_type="depends_on")
    assert r.source_id == "a"
    assert r.target_id == "b"
    assert r.relation_type == "depends_on"
    assert r.weight == 1.0


def test_relationship_equality():
    r1 = Relationship(source_id="a", target_id="b", relation_type="r")
    r2 = Relationship(source_id="a", target_id="b", relation_type="r")
    assert r1 == r2


def test_relationship_hashable():
    r1 = Relationship(source_id="a", target_id="b", relation_type="r")
    r2 = Relationship(source_id="a", target_id="c", relation_type="r")
    s = {r1, r2}
    assert len(s) == 2
