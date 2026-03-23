"""Extended tests for GraphExtractor — edge cases and uncovered branches."""

from __future__ import annotations

import pytest

from graphforge.extractor import GraphExtractor
from graphforge.models import Entity, Relationship


@pytest.fixture()
def extractor():
    return GraphExtractor()


def test_from_text_single_entity(extractor):
    """Line 139: _extract_text_relationships returns [] for <2 entities."""
    text = "Python is great."
    patterns = {"software": r"Python"}
    entities, rels = extractor.from_text(text, patterns)
    assert len(entities) == 1
    assert rels == []


def test_from_text_no_patterns(extractor):
    """from_text with no patterns returns empty entities."""
    entities, rels = extractor.from_text("some text here")
    assert entities == []
    assert rels == []


def test_from_text_cooccurrence(extractor):
    """_extract_text_relationships creates co_occurs_with edges."""
    text = "Alice knows Bob. Alice is friends with Carol."
    patterns = {"person": r"Alice|Bob|Carol"}
    entities, rels = extractor.from_text(text, patterns)
    rel_types = {r.relation_type for r in rels}
    assert "co_occurs_with" in rel_types


def test_from_dict_default_label_from_id(extractor):
    """from_dict uses id as label when label key is absent."""
    records = [{"id": "mynode", "type": "software"}]
    entities, _ = extractor.from_dict(records)
    assert entities[0].label == "mynode"


def test_from_dict_default_relation_type(extractor):
    """from_dict uses 'related_to' when relation key is absent."""
    records = [{"source": "a", "target": "b"}]
    _, rels = extractor.from_dict(records)
    assert rels[0].relation_type == "related_to"


def test_from_dict_default_entity_type(extractor):
    """from_dict uses 'unknown' when type key is absent."""
    records = [{"id": "x"}]
    entities, _ = extractor.from_dict(records)
    assert entities[0].entity_type == "unknown"


def test_from_dict_extra_properties_stored(extractor):
    """Extra fields in entity record go into properties."""
    records = [{"id": "e1", "label": "Test", "type": "widget", "color": "blue"}]
    entities, _ = extractor.from_dict(records)
    assert entities[0].properties["color"] == "blue"


def test_from_dict_relationship_extra_properties(extractor):
    """Extra fields in relationship record go into properties."""
    records = [{"source": "a", "target": "b", "relation": "r", "since": 2020}]
    _, rels = extractor.from_dict(records)
    assert rels[0].properties["since"] == 2020


def test_validate_invalid_relation_type():
    """validate flags unknown relation type."""
    extractor = GraphExtractor(
        domain_config={
            "entity_types": ["software"],
            "relation_types": ["depends_on"],
        }
    )
    entities = [Entity(id="e1", label="E1", entity_type="software")]
    rels = [Relationship(source_id="e1", target_id="e1", relation_type="unknown_rel")]
    errors = extractor.validate(entities, rels)
    assert any("unknown_rel" in err or "not in allowed" in err for err in errors)


def test_from_dict_empty_list(extractor):
    """from_dict with empty input returns empty lists."""
    entities, rels = extractor.from_dict([])
    assert entities == []
    assert rels == []


def test_from_text_dedup_entities(extractor):
    """Each unique match should only produce one Entity."""
    text = "Python Python Python"
    patterns = {"software": r"Python"}
    entities, _ = extractor.from_text(text, patterns)
    assert len(entities) == 1


def test_validate_no_domain_config(extractor):
    """With no domain restrictions, validate only checks dangling refs."""
    entities = [Entity(id="e1", label="L", entity_type="anything")]
    rels = [Relationship(source_id="e1", target_id="e1", relation_type="whatever")]
    errors = extractor.validate(entities, rels)
    assert errors == []
