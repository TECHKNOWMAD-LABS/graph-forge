"""Example 3 — Parallel async node enrichment.

Demonstrates:
  1. Building a large graph from multiple record batches in parallel
  2. Using enrich_nodes_parallel to apply async enrichment to all nodes
  3. Measuring sequential vs parallel timing
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from graphforge.async_builder import build_graph_parallel, enrich_nodes_parallel
from graphforge.builder import GraphBuilder


# ---------------------------------------------------------------------------
# 1. Build graph from parallel batches
# ---------------------------------------------------------------------------
async def main() -> None:
    # Generate 5 batches of 20 nodes each
    batches = [
        [
            {"id": f"node_{batch}_{i}", "label": f"Node {batch}.{i}", "type": "software"}
            for i in range(20)
        ]
        for batch in range(5)
    ]

    print("Building graph from 5 parallel batches (20 nodes each)...")
    t0 = time.perf_counter()
    results = await build_graph_parallel(batches, concurrency=5)
    elapsed = time.perf_counter() - t0

    total_entities = sum(r.entity_count for r in results)
    print(f"  Parsed {total_entities} entities across {len(results)} batches in {elapsed:.4f}s")
    print()

    # Assemble a single builder from all batch results
    builder = GraphBuilder()
    for result in results:
        builder.add_entities(result.entities)
    print(f"Graph built: {builder.node_count} nodes")

    # ---------------------------------------------------------------------------
    # 2. Parallel async node enrichment
    # ---------------------------------------------------------------------------
    async def compute_importance(node_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Simulate an async enrichment (e.g. API call) per node."""
        await asyncio.sleep(0.005)  # simulate 5ms I/O
        return {"importance": len(node_id), "processed": True}

    print(f"\nEnriching {builder.node_count} nodes (simulated 5ms I/O each)...")

    # Sequential timing
    t0 = time.perf_counter()
    for node_id, data in builder.graph.nodes(data=True):
        await asyncio.sleep(0.005)
        data["seq_done"] = True
    seq_time = time.perf_counter() - t0

    # Parallel timing
    t0 = time.perf_counter()
    enriched = await enrich_nodes_parallel(builder, compute_importance, concurrency=20)
    par_time = time.perf_counter() - t0

    speedup = seq_time / par_time if par_time > 0 else float("inf")
    print(f"  Sequential: {seq_time:.3f}s")
    print(f"  Parallel  : {par_time:.3f}s")
    print(f"  Speedup   : {speedup:.1f}x")
    print(f"  Enriched nodes: {len(enriched)}")

    # Verify enrichment was applied
    sample_node = next(iter(builder.graph.nodes()))
    node_data = builder.graph.nodes[sample_node]
    assert node_data.get("processed") is True, "Enrichment was not applied!"
    print(f"\nSample node '{sample_node}': importance={node_data['importance']}")
    print("Parallel enrichment example complete.")


if __name__ == "__main__":
    asyncio.run(main())
