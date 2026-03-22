"""Tests for GraphExtractor."""

import pytest

from graphforge.extractor import GraphExtractor
from graphforge.models import Entity, Relationship


@pytest.fixture()
def extractor():
    return GraphExtractor()


@pytest.fixture()
def domain_extractor():
    return GraphExtractor(
        domain_config={
            "entity_types": ["software", "organization"],
            "relation_types": ["developed_by", "depends_on"],
        }
    )


def test_from_dict_entities(extractor):
    records = [{"id": "py", "label": "Python", "type": "software"}]
    entities, rels = extractor.from_dict(records)
    assert len(entities) == 1
    assert entities[0].id == "py"
    assert entities[0].entity_type == "software"
    assert rels == []


def test_from_dict_relationships(extractor):
    records = [{"source": "a", "target": "b", "relation": "depends_on"}]
    entities, rels = extractor.from_dict(records)
    assert len(rels) == 1
    assert rels[0].relation_type == "depends_on"
    assert entities == []


def test_from_dict_mixed(extractor):
    records = [
        {"id": "a", "label": "A", "type": "software"},
        {"id": "b", "label": "B", "type": "software"},
        {"source": "a", "target": "b", "relation": "depends_on"},
    ]
    entities, rels = extractor.from_dict(records)
    assert len(entities) == 2
    assert len(rels) == 1


def test_from_text_entities(extractor):
    text = "Python and Django are popular frameworks."
    patterns = {"software": r"Python|Django"}
    entities, _ = extractor.from_text(text, patterns)
    labels = {e.label for e in entities}
    assert "Python" in labels
    assert "Django" in labels


def test_validate_valid(domain_extractor):
    entities = [Entity(id="e1", label="E1", entity_type="software")]
    rels = [Relationship(source_id="e1", target_id="e1", relation_type="depends_on")]
    errors = domain_extractor.validate(entities, rels)
    assert errors == []


def test_validate_invalid_entity_type(domain_extractor):
    entities = [Entity(id="e1", label="E1", entity_type="unknown_type")]
    errors = domain_extractor.validate(entities, [])
    assert any("unknown type" in err for err in errors)


def test_validate_dangling_relationship(domain_extractor):
    rels = [Relationship(source_id="ghost", target_id="also_ghost", relation_type="depends_on")]
    errors = domain_extractor.validate([], rels)
    assert len(errors) >= 2
