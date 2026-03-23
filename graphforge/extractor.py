"""GraphExtractor — extract entities and relationships from structured data or text."""

from __future__ import annotations

import re
from typing import Any

from graphforge.models import Entity, Relationship

# Maximum allowed string length to guard against extremely large inputs
_MAX_TEXT_LENGTH = 1_000_000
_MAX_RECORDS = 100_000


class GraphExtractor:
    """Extract entities and relationships from various data sources."""

    def __init__(self, domain_config: dict[str, Any] | None = None) -> None:
        self._domain_config = domain_config or {}
        self._entity_types: set[str] = set(
            self._domain_config.get("entity_types", [])
        )
        self._relation_types: set[str] = set(
            self._domain_config.get("relation_types", [])
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def from_dict(
        self, records: list[dict[str, Any]] | None
    ) -> tuple[list[Entity], list[Relationship]]:
        """Extract entities and relationships from a list of record dicts.

        Each record may contain:
          - id, label, type → becomes an Entity
          - source, target, relation → becomes a Relationship

        Args:
            records: List of record dicts. None or empty list returns empty output.

        Raises:
            TypeError: If records is not a list (after None check).
            ValueError: If the list exceeds _MAX_RECORDS entries.
        """
        if records is None:
            return [], []
        if not isinstance(records, list):
            raise TypeError(f"records must be a list, got {type(records).__name__}")
        if len(records) > _MAX_RECORDS:
            raise ValueError(
                f"records list too large: {len(records)} entries (max {_MAX_RECORDS})"
            )

        entities: list[Entity] = []
        relationships: list[Relationship] = []

        for rec in records:
            if not isinstance(rec, dict):
                continue  # skip non-dict entries gracefully
            if "source" in rec and "target" in rec:
                rel = Relationship(
                    source_id=str(rec["source"]),
                    target_id=str(rec["target"]),
                    relation_type=str(rec.get("relation", "related_to")),
                    properties={
                        k: v
                        for k, v in rec.items()
                        if k not in {"source", "target", "relation"}
                    },
                    weight=float(rec.get("weight", 1.0)),
                )
                relationships.append(rel)
            elif "id" in rec:
                ent = Entity(
                    id=str(rec["id"]),
                    label=str(rec.get("label", rec["id"])),
                    entity_type=str(rec.get("type", "unknown")),
                    properties={
                        k: v for k, v in rec.items() if k not in {"id", "label", "type"}
                    },
                )
                entities.append(ent)

        return entities, relationships

    def from_text(
        self, text: str | None, entity_patterns: dict[str, str] | None = None
    ) -> tuple[list[Entity], list[Relationship]]:
        """Extract entities from free text using regex patterns.

        Args:
            text: Input text to process. None or empty string returns empty output.
            entity_patterns: Mapping of entity_type → regex pattern.

        Returns:
            Tuple of (entities, relationships).  Relationships extracted from
            "X [relation] Y" constructs where known relation types appear.

        Raises:
            TypeError: If text is not a string (after None check).
            ValueError: If text exceeds _MAX_TEXT_LENGTH characters.
        """
        if text is None:
            return [], []
        if not isinstance(text, (str, bytes)):
            raise TypeError(f"text must be a string, got {type(text).__name__}")
        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="replace")
        if len(text) > _MAX_TEXT_LENGTH:
            raise ValueError(
                f"text too large: {len(text)} chars (max {_MAX_TEXT_LENGTH})"
            )
        if not text.strip():
            return [], []
        patterns = entity_patterns or {}
        entities: list[Entity] = []
        seen_ids: set[str] = set()

        for etype, pattern in patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                raw = match.group(0).strip()
                eid = f"{etype}:{raw.lower().replace(' ', '_')}"
                if eid not in seen_ids:
                    seen_ids.add(eid)
                    entities.append(
                        Entity(id=eid, label=raw, entity_type=etype)
                    )

        relationships = self._extract_text_relationships(text, entities)
        return entities, relationships

    def validate(
        self,
        entities: list[Entity] | None,
        relationships: list[Relationship] | None,
    ) -> list[str]:
        """Return a list of validation error strings (empty means valid).

        Args:
            entities: List of Entity objects. None treated as empty list.
            relationships: List of Relationship objects. None treated as empty list.
        """
        entities = entities or []
        relationships = relationships or []
        errors: list[str] = []
        entity_ids = {e.id for e in entities}

        if self._entity_types:
            for ent in entities:
                if ent.entity_type not in self._entity_types:
                    errors.append(
                        f"Entity '{ent.id}' has unknown type '{ent.entity_type}'"
                    )

        if self._relation_types:
            for rel in relationships:
                if rel.relation_type not in self._relation_types:
                    errors.append(
                        f"Relation '{rel.relation_type}' is not in allowed types"
                    )

        for rel in relationships:
            if rel.source_id not in entity_ids:
                errors.append(
                    f"Relationship source '{rel.source_id}' references unknown entity"
                )
            if rel.target_id not in entity_ids:
                errors.append(
                    f"Relationship target '{rel.target_id}' references unknown entity"
                )

        return errors

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_text_relationships(
        self, text: str, entities: list[Entity]
    ) -> list[Relationship]:
        """Simple co-occurrence relationship extraction."""
        relations: list[Relationship] = []
        if len(entities) < 2:
            return relations

        # Build a quick label → entity map for lookup
        label_map = {e.label.lower(): e for e in entities}
        words = re.findall(r"\b\w+\b", text.lower())

        found: list[Entity] = []
        for w in words:
            if w in label_map and (not found or found[-1].id != label_map[w].id):
                found.append(label_map[w])

        for i in range(len(found) - 1):
            rel = Relationship(
                source_id=found[i].id,
                target_id=found[i + 1].id,
                relation_type="co_occurs_with",
            )
            if rel not in relations:
                relations.append(rel)

        return relations
