"""Performance tests — Cycle 3.

Measures sequential vs parallel batch parsing and async node enrichment.
These tests validate correctness; timing is logged but not asserted
(CI machines have variable performance).
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import pytest

from graphforge.async_builder import build_graph_parallel, enrich_nodes_parallel
from graphforge.builder import GraphBuilder
from tests.conftest import make_entity, make_relationship

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_batch(n: int, offset: int = 0) -> list[dict[str, Any]]:
    """Create n entity records starting at id offset."""
    return [
        {"id": f"node_{offset + i}", "label": f"Node {offset + i}", "type": "software"}
        for i in range(n)
    ]


def _make_large_graph(n_nodes: int, n_edges: int) -> GraphBuilder:
    b = GraphBuilder()
    entities = [make_entity(f"n{i}", entity_type="software") for i in range(n_nodes)]
    rels = [
        make_relationship(f"n{i % n_nodes}", f"n{(i + 1) % n_nodes}")
        for i in range(n_edges)
    ]
    b.build(entities, rels)
    return b


# ---------------------------------------------------------------------------
# Parallel batch parsing
# ---------------------------------------------------------------------------


class TestParallelBatchParsing:
    """L4/conjecture: parallelising N batches will yield ~Nx speedup vs sequential."""

    def test_parallel_batch_parsing_correct(self):
        """Parallel build produces same entity counts as sequential."""
        batches = [_make_batch(50, offset=i * 50) for i in range(4)]

        results = asyncio.run(build_graph_parallel(batches, concurrency=4))

        assert len(results) == 4
        for r in results:
            assert r.entity_count == 50
            assert r.relationship_count == 0

    def test_parallel_batch_all_batches_returned(self):
        """All batch indices are present in results."""
        batches = [_make_batch(10, offset=i * 10) for i in range(8)]
        results = asyncio.run(build_graph_parallel(batches, concurrency=4))
        indices = {r.batch_index for r in results}
        assert indices == set(range(8))

    def test_parallel_batch_empty_input(self):
        """Empty batch list returns empty results."""
        results = asyncio.run(build_graph_parallel([]))
        assert results == []

    def test_parallel_batch_invalid_concurrency(self):
        with pytest.raises(ValueError, match="concurrency"):
            asyncio.run(build_graph_parallel([_make_batch(5)], concurrency=0))

    def test_parallel_timing_logged(self):
        """Sequential vs parallel timing — log result, assert parallel is not slower by >20x."""
        batches = [_make_batch(200, offset=i * 200) for i in range(10)]

        from graphforge.extractor import GraphExtractor

        extractor = GraphExtractor()

        t0 = time.perf_counter()
        for b in batches:
            extractor.from_dict(b)
        seq_s = time.perf_counter() - t0

        t0 = time.perf_counter()
        asyncio.run(build_graph_parallel(batches, concurrency=4))
        par_s = time.perf_counter() - t0

        # Parallel should not be dramatically slower than sequential
        # (overhead acceptable up to 20x on a test machine)
        assert par_s < seq_s * 20 + 1.0, (
            f"Parallel ({par_s:.3f}s) unexpectedly much slower than "
            f"sequential ({seq_s:.3f}s)"
        )
        print(f"\n[perf] sequential={seq_s:.4f}s  parallel={par_s:.4f}s  "
              f"ratio={seq_s/par_s:.2f}x")


# ---------------------------------------------------------------------------
# Parallel node enrichment
# ---------------------------------------------------------------------------


class TestParallelNodeEnrichment:
    """enrich_nodes_parallel applies async enricher to every node concurrently."""

    def test_enrich_nodes_parallel_applies_updates(self):
        builder = _make_large_graph(50, 0)

        async def async_enricher(node_id: str, data: dict) -> dict:
            await asyncio.sleep(0)  # yield to event loop
            return {"enriched": True, "computed_len": len(node_id)}

        results = asyncio.run(enrich_nodes_parallel(builder, async_enricher))

        assert len(results) == 50
        for nid in [f"n{i}" for i in range(50)]:
            assert builder.graph.nodes[nid].get("enriched") is True

    def test_enrich_nodes_parallel_empty_graph(self):
        builder = GraphBuilder()

        async def async_enricher(node_id, data):
            return {}

        results = asyncio.run(enrich_nodes_parallel(builder, async_enricher))
        assert results == {}

    def test_enrich_nodes_parallel_invalid_concurrency(self):
        builder = _make_large_graph(5, 0)

        async def async_enricher(nid, data):
            return {}

        with pytest.raises(ValueError, match="concurrency"):
            asyncio.run(enrich_nodes_parallel(builder, async_enricher, concurrency=0))

    def test_enrich_nodes_parallel_respects_semaphore(self):
        """Runs successfully with concurrency=1 (maximally restricted)."""
        builder = _make_large_graph(10, 0)
        call_count = 0

        async def counter_enricher(nid, data):
            nonlocal call_count
            call_count += 1
            return {"visited": True}

        asyncio.run(enrich_nodes_parallel(builder, counter_enricher, concurrency=1))
        assert call_count == 10

    def test_enrich_nodes_parallel_timing(self):
        """Parallel enrichment with I/O sleep is faster than equivalent sequential."""
        builder = _make_large_graph(30, 0)

        async def slow_enricher(nid, data):
            await asyncio.sleep(0.01)  # simulate 10ms I/O
            return {"done": True}

        async def sequential_enricher():
            for nid, data in builder.graph.nodes(data=True):
                await asyncio.sleep(0.01)
                data["done_seq"] = True

        t0 = time.perf_counter()
        asyncio.run(sequential_enricher())
        seq_s = time.perf_counter() - t0

        t0 = time.perf_counter()
        asyncio.run(enrich_nodes_parallel(builder, slow_enricher, concurrency=30))
        par_s = time.perf_counter() - t0

        speedup = seq_s / par_s if par_s > 0 else 1.0
        print(f"\n[perf] sequential={seq_s:.3f}s  parallel={par_s:.3f}s  "
              f"speedup={speedup:.1f}x")
        # Expect meaningful speedup for I/O-bound tasks
        assert speedup > 2.0, f"Expected speedup >2x, got {speedup:.2f}x"


# ---------------------------------------------------------------------------
# GraphBuilder version tracking
# ---------------------------------------------------------------------------


class TestBuilderVersionTracking:
    """Ensure _version increments on structural changes."""

    def test_version_increments_on_add_entity(self):
        b = GraphBuilder()
        v0 = b._version
        b.add_entity(make_entity("x"))
        assert b._version == v0 + 1

    def test_version_increments_on_add_relationship(self):
        b = GraphBuilder()
        b.add_entity(make_entity("a"))
        b.add_entity(make_entity("b"))
        v0 = b._version
        b.add_relationship(make_relationship("a", "b"))
        assert b._version == v0 + 1

    def test_version_increments_on_clear(self):
        b = GraphBuilder()
        b.add_entity(make_entity("x"))
        v0 = b._version
        b.clear()
        assert b._version == v0 + 1
