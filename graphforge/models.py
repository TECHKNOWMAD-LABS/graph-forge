"""Core data models for GraphForge."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Entity:
    """Represents a node in the knowledge graph."""

    id: str
    label: str
    entity_type: str
    properties: dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id


@dataclass
class Relationship:
    """Represents an edge in the knowledge graph."""

    source_id: str
    target_id: str
    relation_type: str
    properties: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0

    def __hash__(self) -> int:
        return hash((self.source_id, self.target_id, self.relation_type))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Relationship):
            return NotImplemented
        return (
            self.source_id == other.source_id
            and self.target_id == other.target_id
            and self.relation_type == other.relation_type
        )
