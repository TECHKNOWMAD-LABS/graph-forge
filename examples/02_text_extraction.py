"""Example 2 — Extract a knowledge graph from free text.

Demonstrates:
  1. Using regex patterns to extract named entities from text
  2. Auto-generated co-occurrence relationships
  3. Enriching the graph with PageRank and community labels
"""

from __future__ import annotations

from graphforge.builder import GraphBuilder
from graphforge.enricher import GraphEnricher
from graphforge.extractor import GraphExtractor

# ---------------------------------------------------------------------------
# 1. Define the text and entity patterns
# ---------------------------------------------------------------------------
text = """
Python is a programming language created by Guido van Rossum and maintained
by the Python Software Foundation. Django is a web framework built on Python.
Flask is another Python web framework. SQLAlchemy is an ORM used by both
Django and Flask. NumPy is a scientific computing library for Python.
"""

entity_patterns = {
    "software": r"\b(?:Python|Django|Flask|SQLAlchemy|NumPy)\b",
    "person": r"\b(?:Guido van Rossum)\b",
    "organization": r"\b(?:Python Software Foundation)\b",
}

# ---------------------------------------------------------------------------
# 2. Extract entities and relationships
# ---------------------------------------------------------------------------
extractor = GraphExtractor()
entities, relationships = extractor.from_text(text, entity_patterns)

print(f"Entities found ({len(entities)}):")
for e in entities:
    print(f"  [{e.entity_type}] {e.label!r}")

print(f"\nCo-occurrence relationships ({len(relationships)}):")
for r in relationships:
    print(f"  {r.source_id} --{r.relation_type}--> {r.target_id}")
print()

# ---------------------------------------------------------------------------
# 3. Build and enrich the graph
# ---------------------------------------------------------------------------
builder = GraphBuilder()
builder.build(entities, relationships)

enricher = GraphEnricher(builder)

# Add PageRank scores
enricher.enrich_pagerank()

# Detect communities
community_map = enricher.enrich_community_labels()
n_communities = len(set(community_map.values()))
print(f"Graph: {builder.node_count} nodes, {builder.edge_count} edges")
print(f"Communities detected: {n_communities}")
print()

# ---------------------------------------------------------------------------
# 4. Print enriched node data
# ---------------------------------------------------------------------------
print("Enriched nodes (PageRank, community):")
for node_id, data in builder.graph.nodes(data=True):
    pr = data.get("pagerank", 0.0)
    comm = data.get("community", -1)
    print(f"  {data.get('label', node_id):<30} PR={pr:.4f}  community={comm}")

# ---------------------------------------------------------------------------
# 5. Normalize edge weights
# ---------------------------------------------------------------------------
enricher.normalize_weights()
print("\nEdge weights normalized to [0, 1]")
for u, v, d in builder.graph.edges(data=True):
    print(f"  {u} → {v}: weight_normalized={d.get('weight_normalized', 'n/a'):.3f}")
