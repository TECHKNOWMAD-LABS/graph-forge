# GraphForge

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#quick-start)

Knowledge graph construction toolkit — extract entities and relationships from structured records or free text, build queryable directed graphs, and enrich them with network metrics.

---

## Features

- **Dual-mode extraction** — parse entities and relationships from dict records or unstructured text via configurable regex patterns
- **Domain configuration** — define entity types, relationship types, and validation rules in YAML; swap domains without touching code
- **Graph querying** — find nodes by type, compute shortest paths, list neighbors/predecessors, and extract subgraphs
- **Network enrichment** — compute PageRank, degree centrality, clustering coefficient, and normalize edge weights in one call
- **Community detection** — partition graphs using greedy modularity optimization (NetworkX)
- **Portable serialization** — round-trip graphs to/from plain dicts via node-link format

---

## Quick Start

```bash
pip install graph-forge
```

```python
from graphforge import GraphBuilder, GraphExtractor, GraphEnricher
from graphforge.models import Entity, Relationship

# Build a graph manually
builder = GraphBuilder()
alice = Entity(id="alice", type="person", properties={"name": "Alice"})
bob   = Entity(id="bob",   type="person", properties={"name": "Bob"})
rel   = Relationship(source="alice", target="bob", type="knows", weight=1.0)

builder.add_entity(alice)
builder.add_entity(bob)
builder.add_relationship(rel)

# Query
print(builder.get_neighbors("alice"))   # ['bob']
print(builder.get_shortest_path("alice", "bob"))

# Extract from records
extractor = GraphExtractor()
records = [{"id": "p1", "type": "paper", "cites": "p2"}]
entities, relationships = extractor.extract_from_records(records)

# Enrich with metrics
enricher = GraphEnricher(builder.graph)
enricher.compute_centrality()
enricher.compute_pagerank()
enricher.detect_communities()
```

---

## Architecture

```
graph-forge/
├── graphforge/
│   ├── models.py      # Entity and Relationship dataclasses
│   ├── domains.py     # DomainLoader — reads YAML domain configs
│   ├── builder.py     # GraphBuilder — constructs and queries DiGraph
│   ├── extractor.py   # GraphExtractor — parses records and free text
│   └── enricher.py    # GraphEnricher — computes network metrics
├── domains/
│   ├── technology.yaml
│   ├── science.yaml
│   └── social.yaml
└── tests/             # pytest suite, one file per module
```

**Data flow:**

```
Raw data (dicts / text)
        │
   GraphExtractor        ← domain YAML controls entity/rel types
        │
   GraphBuilder          ← NetworkX DiGraph under the hood
        │
   GraphEnricher         ← PageRank, centrality, communities
        │
   Serialized dict / downstream query
```

---

## Development

```bash
git clone https://github.com/techknowmad/graph-forge.git
cd graph-forge
pip install -e ".[dev]"

# Lint
ruff check .

# Test
pytest -v
```

All tests must pass and `ruff check` must be clean before opening a PR.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch conventions, commit style, and the PR checklist.

---

## License

[MIT](LICENSE)

---

<sub>Built by [TechKnowMad Labs](https://techknowmad.ai)</sub>
