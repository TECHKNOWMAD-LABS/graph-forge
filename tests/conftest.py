"""Shared fixtures and mock helpers for the GraphForge test suite."""

from __future__ import annotations

import pytest

from graphforge.builder import GraphBuilder
from graphforge.enricher import GraphEnricher
from graphforge.extractor import GraphExtractor
from graphforge.models import Entity, Relationship

# ---------------------------------------------------------------------------
# Entity / Relationship factories
# ---------------------------------------------------------------------------


def make_entity(
    eid: str = "e1",
    label: str | None = None,
    entity_type: str = "software",
    **props,
) -> Entity:
    """Create a test Entity with sensible defaults."""
    return Entity(
        id=eid,
        label=label or eid.upper(),
        entity_type=entity_type,
        properties=props,
    )


def make_relationship(
    source: str = "a",
    target: str = "b",
    rel_type: str = "depends_on",
    weight: float = 1.0,
    **props,
) -> Relationship:
    """Create a test Relationship with sensible defaults."""
    return Relationship(
        source_id=source,
        target_id=target,
        relation_type=rel_type,
        weight=weight,
        properties=props,
    )


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def empty_builder() -> GraphBuilder:
    """A fresh, empty GraphBuilder."""
    return GraphBuilder()


@pytest.fixture()
def triangle_builder() -> GraphBuilder:
    """GraphBuilder with 3 nodes and 3 edges forming a triangle A→B→C→A."""
    b = GraphBuilder()
    entities = [
        make_entity("A", entity_type="node"),
        make_entity("B", entity_type="node"),
        make_entity("C", entity_type="node"),
    ]
    rels = [
        make_relationship("A", "B", weight=1.0),
        make_relationship("B", "C", weight=2.0),
        make_relationship("C", "A", weight=3.0),
    ]
    b.build(entities, rels)
    return b


@pytest.fixture()
def triangle_enricher(triangle_builder: GraphBuilder) -> GraphEnricher:
    """GraphEnricher wrapping the triangle_builder fixture."""
    return GraphEnricher(triangle_builder)


@pytest.fixture()
def base_extractor() -> GraphExtractor:
    """A plain GraphExtractor with no domain restrictions."""
    return GraphExtractor()


@pytest.fixture()
def tech_extractor() -> GraphExtractor:
    """A GraphExtractor configured with technology domain types."""
    return GraphExtractor(
        domain_config={
            "entity_types": ["software", "organization", "language"],
            "relation_types": ["depends_on", "developed_by", "uses"],
        }
    )


@pytest.fixture()
def sample_records() -> list[dict]:
    """Mixed list of entity and relationship records for extractor tests."""
    return [
        {"id": "py", "label": "Python", "type": "language"},
        {"id": "dj", "label": "Django", "type": "software"},
        {"id": "psf", "label": "PSF", "type": "organization"},
        {"source": "dj", "target": "py", "relation": "depends_on", "weight": 0.9},
        {"source": "py", "target": "psf", "relation": "developed_by"},
    ]
