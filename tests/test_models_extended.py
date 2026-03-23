"""Extended tests for Entity and Relationship models — edge cases."""

from __future__ import annotations

from graphforge.models import Entity, Relationship

# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------


def test_entity_not_equal_to_non_entity():
    """Line 21: __eq__ returns NotImplemented for non-Entity."""
    e = Entity(id="x", label="X", entity_type="t")
    result = e.__eq__("not an entity")
    assert result is NotImplemented


def test_entity_equal_same_id_different_attrs():
    """Entities with same id but different label/type are equal."""
    e1 = Entity(id="shared", label="Alpha", entity_type="software")
    e2 = Entity(id="shared", label="Beta", entity_type="hardware")
    assert e1 == e2


def test_entity_hash_consistent():
    """hash(entity) is deterministic across calls."""
    e = Entity(id="stable", label="L", entity_type="t")
    assert hash(e) == hash(e)


def test_entity_hash_in_set():
    """Entities with same id de-duplicate in a set."""
    e1 = Entity(id="dup", label="A", entity_type="t")
    e2 = Entity(id="dup", label="B", entity_type="t")
    assert len({e1, e2}) == 1


# ---------------------------------------------------------------------------
# Relationship
# ---------------------------------------------------------------------------


def test_relationship_not_equal_to_non_relationship():
    """Line 40: __eq__ returns NotImplemented for non-Relationship."""
    r = Relationship(source_id="a", target_id="b", relation_type="r")
    result = r.__eq__("not a relationship")
    assert result is NotImplemented


def test_relationship_equality_ignores_weight():
    """Two Relationships with same src/tgt/type but different weight are equal."""
    r1 = Relationship(source_id="a", target_id="b", relation_type="r", weight=1.0)
    r2 = Relationship(source_id="a", target_id="b", relation_type="r", weight=99.0)
    assert r1 == r2


def test_relationship_different_type_not_equal():
    r1 = Relationship(source_id="a", target_id="b", relation_type="r1")
    r2 = Relationship(source_id="a", target_id="b", relation_type="r2")
    assert r1 != r2


def test_relationship_with_properties():
    r = Relationship(
        source_id="a", target_id="b", relation_type="r", properties={"since": 2020}
    )
    assert r.properties["since"] == 2020


def test_relationship_hash_consistent():
    r = Relationship(source_id="a", target_id="b", relation_type="r")
    assert hash(r) == hash(r)
