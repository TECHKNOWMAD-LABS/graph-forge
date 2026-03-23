"""Property-based tests using Hypothesis — Cycle 6.

Tests core invariants:
1. Serialisation round-trips are preserved (GraphBuilder to_dict/from_dict)
2. Entity/Relationship constructors never crash on valid string inputs
3. validate() never crashes on any combination of entities and relationships
4. from_dict() output count is monotonically bounded by input record count
5. Graph node/edge counts are consistent after build()
6. No crashes on any random valid text input to from_text()
7. find_by_type returns subset of actual node IDs
"""

from __future__ import annotations

import string

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from graphforge.builder import GraphBuilder
from graphforge.extractor import GraphExtractor
from graphforge.models import Entity, Relationship

# ---------------------------------------------------------------------------
# Strategy helpers
# ---------------------------------------------------------------------------

_PRINTABLE = string.printable
_SAFE_TEXT = st.text(
    alphabet=string.ascii_letters + string.digits + " _-.", min_size=1, max_size=64
)
_ENTITY_TYPES = st.sampled_from(["software", "organization", "person", "dataset", "model"])
_REL_TYPES = st.sampled_from(["depends_on", "developed_by", "uses", "cites", "follows"])


def _entity_strategy():
    return st.builds(
        Entity,
        id=_SAFE_TEXT,
        label=_SAFE_TEXT,
        entity_type=_ENTITY_TYPES,
        properties=st.fixed_dictionaries({}),
    )


def _relationship_strategy(entity_ids: list[str]):
    id_st = st.sampled_from(entity_ids)
    return st.builds(
        Relationship,
        source_id=id_st,
        target_id=id_st,
        relation_type=_REL_TYPES,
        weight=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        properties=st.fixed_dictionaries({}),
    )


# ---------------------------------------------------------------------------
# Invariant 1: Serialisation round-trips
# ---------------------------------------------------------------------------


@given(entities=st.lists(_entity_strategy(), min_size=1, max_size=30, unique_by=lambda e: e.id))
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_roundtrip_node_count_preserved(entities):
    """GraphBuilder.to_dict → from_dict preserves node count."""
    b = GraphBuilder()
    b.add_entities(entities)
    restored = GraphBuilder.from_dict(b.to_dict())
    assert restored.node_count == b.node_count


@given(entities=st.lists(_entity_strategy(), min_size=2, max_size=20, unique_by=lambda e: e.id))
@settings(max_examples=40, suppress_health_check=[HealthCheck.too_slow])
def test_roundtrip_edge_count_preserved(entities):
    """Serialisation round-trip preserves edge count."""
    b = GraphBuilder()
    b.add_entities(entities)
    ids = [e.id for e in entities]
    rels = [
        Relationship(source_id=ids[i], target_id=ids[(i + 1) % len(ids)], relation_type="uses")
        for i in range(min(len(ids), 5))
    ]
    b.add_relationships(rels)
    restored = GraphBuilder.from_dict(b.to_dict())
    assert restored.edge_count == b.edge_count


# ---------------------------------------------------------------------------
# Invariant 2: Entity/Relationship construction never crashes
# ---------------------------------------------------------------------------


@given(eid=_SAFE_TEXT, label=_SAFE_TEXT, etype=_ENTITY_TYPES)
@settings(max_examples=100)
def test_entity_construction_never_crashes(eid, label, etype):
    """Entity always constructable from valid strings."""
    e = Entity(id=eid, label=label, entity_type=etype)
    assert e.id == eid
    assert e.label == label


@given(
    src=_SAFE_TEXT,
    tgt=_SAFE_TEXT,
    rtype=_REL_TYPES,
    weight=st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100)
def test_relationship_construction_never_crashes(src, tgt, rtype, weight):
    """Relationship always constructable from valid inputs."""
    r = Relationship(source_id=src, target_id=tgt, relation_type=rtype, weight=weight)
    assert r.source_id == src
    assert r.weight == weight


# ---------------------------------------------------------------------------
# Invariant 3: validate() never crashes
# ---------------------------------------------------------------------------


@given(
    entities=st.lists(_entity_strategy(), min_size=0, max_size=20, unique_by=lambda e: e.id),
    extra_rel_type=_REL_TYPES,
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_validate_never_crashes(entities, extra_rel_type):
    """GraphExtractor.validate never raises for any entity/rel combination."""
    ext = GraphExtractor()
    ids = [e.id for e in entities]
    rels = []
    if len(ids) >= 2:
        rels = [
            Relationship(
                source_id=ids[0], target_id=ids[1], relation_type=extra_rel_type
            )
        ]
    errors = ext.validate(entities, rels)
    assert isinstance(errors, list)


# ---------------------------------------------------------------------------
# Invariant 4: from_dict output bounded by input count
# ---------------------------------------------------------------------------


@given(
    n_entities=st.integers(min_value=0, max_value=50),
    n_rels=st.integers(min_value=0, max_value=50),
)
@settings(max_examples=60)
def test_from_dict_count_bounded(n_entities, n_rels):
    """Output entity+rel counts do not exceed input record count."""
    ext = GraphExtractor()
    records = (
        [{"id": f"e{i}", "label": f"Entity {i}", "type": "software"} for i in range(n_entities)]
        + [{"source": f"e{i}", "target": f"e{(i+1)%max(n_entities,1)}", "relation": "uses"}
           for i in range(n_rels)]
    )
    entities, rels = ext.from_dict(records)
    assert len(entities) <= len(records)
    assert len(rels) <= len(records)
    assert len(entities) + len(rels) <= len(records)


# ---------------------------------------------------------------------------
# Invariant 5: Graph counts consistent after build
# ---------------------------------------------------------------------------


@given(entities=st.lists(_entity_strategy(), min_size=0, max_size=30, unique_by=lambda e: e.id))
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_build_node_count_matches(entities):
    """node_count == len(unique entities) after build."""
    b = GraphBuilder()
    b.add_entities(entities)
    assert b.node_count == len(entities)


@given(entities=st.lists(_entity_strategy(), min_size=2, max_size=20, unique_by=lambda e: e.id))
@settings(max_examples=40, suppress_health_check=[HealthCheck.too_slow])
def test_find_by_type_returns_subset(entities):
    """find_by_type always returns a subset of actual node IDs."""
    b = GraphBuilder()
    b.add_entities(entities)
    all_ids = set(e.id for e in entities)
    for etype in set(e.entity_type for e in entities):
        result = b.find_by_type(etype)
        assert set(result).issubset(all_ids)


# ---------------------------------------------------------------------------
# Invariant 6: from_text never crashes on valid string input
# ---------------------------------------------------------------------------


@given(text=st.text(min_size=0, max_size=500))
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_from_text_never_crashes(text):
    """from_text with no patterns never raises for any string input."""
    ext = GraphExtractor()
    entities, rels = ext.from_text(text)
    assert isinstance(entities, list)
    assert isinstance(rels, list)


# ---------------------------------------------------------------------------
# Invariant 7: Entity hash/equality contract
# ---------------------------------------------------------------------------


@given(eid=_SAFE_TEXT, label=_SAFE_TEXT)
@settings(max_examples=100)
def test_entity_hash_equality_contract(eid, label):
    """Two entities with the same id are equal and have the same hash."""
    e1 = Entity(id=eid, label=label, entity_type="software")
    e2 = Entity(id=eid, label="different_label", entity_type="hardware")
    assert e1 == e2
    assert hash(e1) == hash(e2)


@given(
    id1=_SAFE_TEXT,
    id2=_SAFE_TEXT,
)
@settings(max_examples=100)
def test_entity_inequality_different_ids(id1, id2):
    """Entities with different ids are not equal."""
    assume(id1 != id2)
    e1 = Entity(id=id1, label="X", entity_type="t")
    e2 = Entity(id=id2, label="X", entity_type="t")
    assert e1 != e2
