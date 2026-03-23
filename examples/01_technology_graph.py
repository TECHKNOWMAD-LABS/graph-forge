"""Example 1 — Build a technology knowledge graph.

Demonstrates the core GraphForge workflow:
  1. Load a domain config from YAML
  2. Extract entities and relationships from structured records
  3. Build a NetworkX DiGraph
  4. Query neighbours, shortest paths, and centrality
"""

from __future__ import annotations

from graphforge.builder import GraphBuilder
from graphforge.domains import DomainLoader
from graphforge.extractor import GraphExtractor

# ---------------------------------------------------------------------------
# 1. Load the technology domain configuration
# ---------------------------------------------------------------------------
loader = DomainLoader()
tech_domain = loader.load("technology")
print(f"Domain      : {tech_domain.name}")
print(f"Entity types: {tech_domain.entity_types}")
print(f"Rel types   : {tech_domain.relation_types}")
print()

# ---------------------------------------------------------------------------
# 2. Extract entities and relationships from structured records
# ---------------------------------------------------------------------------
extractor = GraphExtractor(tech_domain.to_extractor_config())

records = [
    {"id": "python",   "label": "Python",     "type": "software"},
    {"id": "django",   "label": "Django",      "type": "software"},
    {"id": "flask",    "label": "Flask",       "type": "software"},
    {"id": "psf",      "label": "PSF",         "type": "organization"},
    {"id": "postgres", "label": "PostgreSQL",  "type": "software"},
    # Relationships
    {"source": "django",   "target": "python",   "relation": "depends_on", "weight": 1.0},
    {"source": "flask",    "target": "python",   "relation": "depends_on", "weight": 1.0},
    {"source": "python",   "target": "psf",      "relation": "developed_by"},
    {"source": "django",   "target": "postgres", "relation": "depends_on", "weight": 0.8},
]

entities, relationships = extractor.from_dict(records)
print(f"Extracted: {len(entities)} entities, {len(relationships)} relationships")

# Validate against the domain schema
errors = extractor.validate(entities, relationships)
if errors:
    print(f"Validation errors: {errors}")
else:
    print("Validation: OK — all types conform to the technology domain")
print()

# ---------------------------------------------------------------------------
# 3. Build the graph
# ---------------------------------------------------------------------------
builder = GraphBuilder()
builder.build(entities, relationships)

print(f"Graph: {builder.node_count} nodes, {builder.edge_count} edges")
print()

# ---------------------------------------------------------------------------
# 4. Query the graph
# ---------------------------------------------------------------------------
# Neighbours (successors)
python_neighbors = builder.get_neighbors("python")
print(f"Nodes Python points to   : {python_neighbors}")

django_preds = builder.get_predecessors("python")
print(f"Nodes that depend on Python: {django_preds}")

# Shortest path
path = builder.shortest_path("django", "psf")
print(f"Shortest path django → psf: {path}")

# Software nodes
software_nodes = builder.find_by_type("software")
print(f"All software nodes: {software_nodes}")

# Degree centrality
centrality = builder.degree_centrality()
most_central = max(centrality, key=centrality.get)
print(f"Most central node: '{most_central}' (score={centrality[most_central]:.3f})")
print()

# ---------------------------------------------------------------------------
# 5. Serialise and restore
# ---------------------------------------------------------------------------
graph_dict = builder.to_dict()
restored = GraphBuilder.from_dict(graph_dict)
assert restored.node_count == builder.node_count
assert restored.edge_count == builder.edge_count
print(f"Serialisation round-trip: OK ({restored.node_count} nodes, {restored.edge_count} edges)")
