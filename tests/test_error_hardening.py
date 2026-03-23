"""Tests for input validation and error hardening — Cycle 2."""

from __future__ import annotations

import pytest

from graphforge.builder import GraphBuilder
from graphforge.enricher import GraphEnricher
from graphforge.extractor import GraphExtractor
from tests.conftest import make_entity

# ---------------------------------------------------------------------------
# GraphExtractor — empty / None / malformed inputs
# ---------------------------------------------------------------------------


class TestExtractorInputValidation:
    def test_from_dict_none_returns_empty(self):
        """None input returns ([], []) without raising."""
        ext = GraphExtractor()
        entities, rels = ext.from_dict(None)
        assert entities == []
        assert rels == []

    def test_from_dict_not_a_list_raises_type_error(self):
        ext = GraphExtractor()
        with pytest.raises(TypeError, match="list"):
            ext.from_dict("not a list")  # type: ignore[arg-type]

    def test_from_dict_skips_non_dict_entries(self):
        """Non-dict entries in list are silently skipped."""
        ext = GraphExtractor()
        records = [None, "string", 42, {"id": "ok", "label": "OK", "type": "software"}]
        entities, rels = ext.from_dict(records)  # type: ignore[arg-type]
        assert len(entities) == 1

    def test_from_dict_huge_list_raises(self):
        ext = GraphExtractor()
        big = [{"id": str(i), "type": "t"} for i in range(100_001)]
        with pytest.raises(ValueError, match="too large"):
            ext.from_dict(big)

    def test_from_text_none_returns_empty(self):
        ext = GraphExtractor()
        entities, rels = ext.from_text(None)
        assert entities == [] and rels == []

    def test_from_text_empty_string_returns_empty(self):
        ext = GraphExtractor()
        entities, rels = ext.from_text("")
        assert entities == [] and rels == []

    def test_from_text_whitespace_only_returns_empty(self):
        ext = GraphExtractor()
        entities, rels = ext.from_text("   \n\t  ")
        assert entities == [] and rels == []

    def test_from_text_not_string_raises_type_error(self):
        ext = GraphExtractor()
        with pytest.raises(TypeError, match="string"):
            ext.from_text(12345)  # type: ignore[arg-type]

    def test_from_text_huge_string_raises(self):
        ext = GraphExtractor()
        with pytest.raises(ValueError, match="too large"):
            ext.from_text("x" * 1_000_001)

    def test_from_text_bytes_decoded(self):
        """Bytes input is decoded to string."""
        ext = GraphExtractor()
        entities, _ = ext.from_text(b"Python is great", {"software": r"Python"})
        assert len(entities) == 1

    def test_from_text_unicode_content(self):
        """Unicode text should not crash the extractor."""
        ext = GraphExtractor()
        entities, _ = ext.from_text("日本語テスト — no patterns match", {"software": r"Python"})
        assert entities == []

    def test_from_text_malformed_regex_raises(self):
        """A malformed regex in patterns should raise re.error."""
        import re

        ext = GraphExtractor()
        with pytest.raises(re.error):
            ext.from_text("some text", {"bad": r"[invalid"})

    def test_validate_none_inputs(self):
        ext = GraphExtractor()
        errors = ext.validate(None, None)
        assert errors == []


# ---------------------------------------------------------------------------
# GraphBuilder — empty / None / wrong-type inputs
# ---------------------------------------------------------------------------


class TestBuilderInputValidation:
    def test_add_entity_wrong_type_raises(self):
        b = GraphBuilder()
        with pytest.raises(TypeError, match="Entity"):
            b.add_entity("not an entity")  # type: ignore[arg-type]

    def test_add_relationship_wrong_type_raises(self):
        b = GraphBuilder()
        with pytest.raises(TypeError, match="Relationship"):
            b.add_relationship({"source": "a", "target": "b"})  # type: ignore[arg-type]

    def test_add_entities_none_noop(self):
        b = GraphBuilder()
        b.add_entities(None)  # type: ignore[arg-type]
        assert b.node_count == 0

    def test_add_relationships_none_noop(self):
        b = GraphBuilder()
        b.add_relationships(None)  # type: ignore[arg-type]
        assert b.edge_count == 0

    def test_build_none_inputs(self):
        b = GraphBuilder()
        g = b.build(None, None)
        assert g.number_of_nodes() == 0

    def test_get_node_none_returns_none(self):
        b = GraphBuilder()
        assert b.get_node(None) is None

    def test_get_neighbors_none_returns_empty(self):
        b = GraphBuilder()
        assert b.get_neighbors(None) == []

    def test_get_predecessors_none_returns_empty(self):
        b = GraphBuilder()
        assert b.get_predecessors(None) == []

    def test_find_by_type_none_returns_empty(self):
        b = GraphBuilder()
        b.add_entity(make_entity("x", entity_type="foo"))
        assert b.find_by_type(None) == []

    def test_find_by_type_empty_string_returns_empty(self):
        b = GraphBuilder()
        b.add_entity(make_entity("x", entity_type="foo"))
        assert b.find_by_type("") == []


# ---------------------------------------------------------------------------
# GraphEnricher — empty / None inputs
# ---------------------------------------------------------------------------


class TestEnricherInputValidation:
    def test_add_node_property_none_node_id(self, triangle_builder):
        enricher = GraphEnricher(triangle_builder)
        assert enricher.add_node_property(None, "key", "val") is False

    def test_add_node_property_empty_key_raises(self, triangle_builder):
        enricher = GraphEnricher(triangle_builder)
        with pytest.raises(ValueError, match="key"):
            enricher.add_node_property("A", "", "val")

    def test_bulk_enrich_none_returns_empty(self, triangle_builder):
        enricher = GraphEnricher(triangle_builder)
        missing = enricher.bulk_enrich_nodes(None)  # type: ignore[arg-type]
        assert missing == []

    def test_bulk_enrich_empty_dict_returns_empty(self, triangle_builder):
        enricher = GraphEnricher(triangle_builder)
        missing = enricher.bulk_enrich_nodes({})
        assert missing == []
