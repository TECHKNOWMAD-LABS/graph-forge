# Changelog

All notable changes to GraphForge are documented in this file.

## [0.1.0] — 2026-03-23

### Summary
First release following 8 autonomous Edgecraft iteration cycles.

### Cycle 1 — Test Coverage
- Added `tests/conftest.py` with shared fixtures (`make_entity`, `make_relationship`,
  `triangle_builder`, `tech_extractor`).
- Added extended test files for all 5 source modules (builder, enricher, extractor,
  domains, models), targeting previously uncovered branches.
- Fixed `ModuleNotFoundError` for `numpy` and `scipy` (added to project dependencies).
- Coverage improved from 89% to **100%** across all 6 source modules.
- Total tests: 92 passing.

### Cycle 2 — Error Hardening
- `GraphExtractor.from_dict`: `None` returns `([], [])`, `TypeError` for non-list,
  `ValueError` for >100k records, non-dict entries silently skipped.
- `GraphExtractor.from_text`: `None`/empty/whitespace returns `([], [])`, `bytes` are
  decoded to UTF-8, `ValueError` guard for >1M chars.
- `GraphExtractor.validate`: `None` inputs treated as empty lists.
- `GraphBuilder.add_entity/add_relationship`: `TypeError` on wrong type.
- `GraphBuilder.add_entities/add_relationships`: `None` is a no-op.
- `GraphBuilder.get_node/get_neighbors/get_predecessors/find_by_type`: all `None`-safe.
- `GraphEnricher.add_node_property`: `None` node_id returns `False`; empty key raises.
- `GraphEnricher.bulk_enrich_nodes`: `None`/empty dict returns `[]` early.
- Tests: 27 new hardening tests. Total: 119 passing.

### Cycle 3 — Performance
- Added `graphforge/async_builder.py` with:
  - `enrich_nodes_parallel`: `asyncio.gather` with semaphore for parallel node enrichment.
  - `build_graph_parallel`: parallel record-batch parsing via `run_in_executor`.
  - `measure_sequential_vs_parallel`: benchmark utility.
- `GraphBuilder._version`: cache-invalidation counter bumped on every structural change.
- Measured **30.4x speedup** for I/O-bound enrichment (30 nodes, 10ms each).
- Tests: 13 new performance tests. Total: 132 passing.

### Cycle 4 — Security
- Security scan: 0 real findings across 6 source files, 7 secret patterns.
- Fixed **CWE-22 path traversal** in `DomainLoader.load`: domain name validated
  against `/`, `\\`, `..`; `Path.resolve()` + `relative_to()` ensures path stays
  within domains directory.
- Tests: 11 new security tests. Total: 143 passing.

### Cycle 5 — CI/CD
- Added `.github/workflows/ci.yml`: checkout, Python 3.12, uv sync, ruff check,
  pytest with `--cov-fail-under=95`, coverage artifact upload.
- Added `.pre-commit-config.yaml`: ruff + ruff-format, trailing-whitespace,
  end-of-file-fixer, check-yaml, detect-private-key, check-merge-conflict.
- Applied `ruff --fix` to all source and test files (22 auto-fixed lint issues).

### Cycle 6 — Property-Based Testing
- Added `tests/test_property_based.py` with 11 Hypothesis property tests:
  1. Serialisation round-trips preserve node/edge counts.
  2. Entity/Relationship construction stable on any valid strings.
  3. `validate()` never crashes on any entity/rel combination.
  4. `from_dict()` output counts bounded by input record count.
  5. `build()` node count equals unique entity count.
  6. `from_text()` never crashes on any string ≤500 chars.
  7. Entity hash/equality contract holds for all distinct IDs.
- Hypothesis found **no failures** across all strategies.

### Cycle 7 — Examples + Docs
- Added `examples/01_technology_graph.py`: full workflow example.
- Added `examples/02_text_extraction.py`: regex NER + graph enrichment.
- Added `examples/03_async_parallel_enrichment.py`: parallel batch + async enrichment.
- Fixed bug: `weight` key now excluded from `Relationship.properties` in `from_dict`
  (prevented `TypeError: multiple values for keyword argument 'weight'`).
- Added missing docstrings to `GraphBuilder` public methods.

### Cycle 8 — Release Engineering
- Updated `pyproject.toml`: author, readme, keywords, classifiers.
- Added `CHANGELOG.md` (this file).
- Added `Makefile` with `test`, `lint`, `format`, `security`, `clean` targets.
- Added `AGENTS.md` documenting the Edgecraft autonomous development protocol.
- Added `EVOLUTION.md` with per-cycle timestamps and findings.
- Tagged `v0.1.0`.
