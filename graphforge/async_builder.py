"""Async-capable parallel enrichment utilities for GraphForge.

Provides asyncio-based parallel node enrichment with a configurable
concurrency semaphore so heavy per-node computations can be parallelised
without overwhelming the event loop.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Coroutine
from typing import Any

from graphforge.builder import GraphBuilder

# Default maximum number of concurrent enrichment coroutines
_DEFAULT_CONCURRENCY = 16


async def enrich_nodes_parallel(
    builder: GraphBuilder,
    enricher_fn: Callable[[str, dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]],
    *,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> dict[str, dict[str, Any]]:
    """Enrich all graph nodes in parallel using an async enricher function.

    The *enricher_fn* is called with (node_id, node_data) and must return
    a coroutine that resolves to a dict of new attributes to merge into the
    node.  A semaphore limits the number of concurrent coroutines to
    ``concurrency``.

    Args:
        builder: The GraphBuilder whose nodes will be enriched.
        enricher_fn: Async function ``(node_id, node_data) → dict``.
        concurrency: Maximum number of simultaneous coroutines (default 16).

    Returns:
        Mapping of ``node_id → dict`` with the enrichment results that were
        applied to each node.
    """
    if concurrency < 1:
        raise ValueError(f"concurrency must be >= 1, got {concurrency}")

    sem = asyncio.Semaphore(concurrency)
    results: dict[str, dict[str, Any]] = {}

    async def _bounded(node_id: str, data: dict[str, Any]) -> None:
        async with sem:
            updates = await enricher_fn(node_id, data)
            if updates:
                data.update(updates)
                results[node_id] = updates

    nodes = list(builder.graph.nodes(data=True))
    await asyncio.gather(*(_bounded(nid, d) for nid, d in nodes))
    return results


async def build_graph_parallel(
    records_batches: list[list[dict[str, Any]]],
    *,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> list[BuildResult]:
    """Parse multiple batches of record dicts into (entities, rels) in parallel.

    Useful when records arrive as separate chunks (e.g. pages from an API).

    Args:
        records_batches: List of record-dict lists, one per batch.
        concurrency: Max simultaneous parse tasks.

    Returns:
        List of BuildResult named-tuples, one per batch, in original order.
    """
    from graphforge.extractor import GraphExtractor

    if concurrency < 1:
        raise ValueError(f"concurrency must be >= 1, got {concurrency}")

    sem = asyncio.Semaphore(concurrency)
    results: list[BuildResult | None] = [None] * len(records_batches)

    async def _parse_batch(idx: int, batch: list[dict[str, Any]]) -> None:
        async with sem:
            # GraphExtractor.from_dict is CPU-bound; run in executor to avoid
            # blocking the event loop on large batches.
            loop = asyncio.get_running_loop()
            extractor = GraphExtractor()
            entities, rels = await loop.run_in_executor(
                None, extractor.from_dict, batch
            )
            results[idx] = BuildResult(
                batch_index=idx,
                entity_count=len(entities),
                relationship_count=len(rels),
                entities=entities,
                relationships=rels,
            )

    await asyncio.gather(*(_parse_batch(i, b) for i, b in enumerate(records_batches)))
    return [r for r in results if r is not None]


class BuildResult:
    """Result container for a single parallel build batch."""

    __slots__ = ("batch_index", "entity_count", "relationship_count", "entities", "relationships")

    def __init__(
        self,
        batch_index: int,
        entity_count: int,
        relationship_count: int,
        entities: list,
        relationships: list,
    ) -> None:
        self.batch_index = batch_index
        self.entity_count = entity_count
        self.relationship_count = relationship_count
        self.entities = entities
        self.relationships = relationships

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"BuildResult(batch={self.batch_index}, "
            f"entities={self.entity_count}, rels={self.relationship_count})"
        )


def measure_sequential_vs_parallel(
    items: list[Any],
    sync_fn: Callable[[Any], Any],
    async_fn: Callable[[Any], Coroutine[Any, Any, Any]],
    *,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> dict[str, float]:
    """Benchmark sequential vs parallel execution of a function over items.

    Args:
        items: Items to process.
        sync_fn: Synchronous function applied to each item.
        async_fn: Async version of the same function.
        concurrency: Semaphore limit for parallel execution.

    Returns:
        Dict with keys ``sequential_s``, ``parallel_s``, ``speedup``.
    """

    async def _run_parallel() -> None:
        sem = asyncio.Semaphore(concurrency)

        async def _bounded(item: Any) -> Any:
            async with sem:
                return await async_fn(item)

        await asyncio.gather(*(_bounded(i) for i in items))

    t0 = time.perf_counter()
    for item in items:
        sync_fn(item)
    seq_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    asyncio.run(_run_parallel())
    par_time = time.perf_counter() - t0

    return {
        "sequential_s": round(seq_time, 6),
        "parallel_s": round(par_time, 6),
        "speedup": round(seq_time / par_time, 3) if par_time > 0 else float("inf"),
    }
