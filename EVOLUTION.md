# EVOLUTION.md — Edgecraft 8-Cycle Autonomous Development Log

Repository: `TECHKNOWMAD-LABS/graph-forge`
Protocol: Edgecraft v4.0
Date: 2026-03-23
Agent: Claude Sonnet 4.6

---

## Cycle 1 — Test Coverage
**Timestamp**: 2026-03-23T00:00

### Findings
- `graphforge/builder.py` lines 85, 89-91, 110, 116 at 0% coverage.
- `graphforge/enricher.py` lines 65, 89-92, 98-105, 119 at 0%.
- `graphforge/models.py` lines 21, 40 (`NotImplemented` branches) at 0%.
- Missing `numpy` + `scipy` deps caused `test_enrich_pagerank` to fail.

### Actions
- Added `tests/conftest.py` with `make_entity`, `make_relationship` factories
  and 5 shared fixtures.
- Added 5 extended test files (50 new tests) covering every previously uncovered branch.
- Added `numpy>=2.4.3` and `scipy>=1.17.1` to project dependencies.

### Result
- **92 tests passing** | **100% coverage** across all 6 source modules.

---

## Cycle 2 — Error Hardening
**Timestamp**: 2026-03-23T00:15

### Findings
- `from_dict(None)` → `AttributeError` on `.items()`.
- `from_text(b"bytes")` → `TypeError` (bytes not str).
- `add_entity("string")` → `AttributeError` on `.id`.
- `bulk_enrich_nodes({})` iterated unnecessarily.
- `find_by_type("")` matched nodes with empty `entity_type` attr.
- `from_dict([None, 42, "str"])` → `AttributeError` on `.get()`.

### Actions
- Added `None`/type guards to `from_dict`, `from_text`, `validate`.
- Added `TypeError` guards to `add_entity`, `add_relationship`.
- Added `None`-safe returns to `get_node`, `get_neighbors`, `get_predecessors`.
- Added early-exit for empty inputs in `bulk_enrich_nodes`.
- Bytes auto-decoded to UTF-8 in `from_text`.

### Result
- **119 tests passing** | All hardening tests pass.

---

## Cycle 3 — Performance
**Timestamp**: 2026-03-23T00:30

### Conjecture
Parallelising N I/O-bound node enrichment calls will yield ~Nx speedup.

### Actions
- Added `graphforge/async_builder.py`:
  - `enrich_nodes_parallel(builder, enricher_fn, *, concurrency=16)`
  - `build_graph_parallel(record_batches, *, concurrency=16)`
  - `measure_sequential_vs_parallel()` benchmark utility.
- Added `_version` counter to `GraphBuilder` for cache-invalidation support.

### Result (measured on test machine)
- **Sequential**: 0.331s (30 nodes × 10ms I/O)
- **Parallel**: 0.011s (concurrency=30)
- **Speedup**: **30.4x**
- Pattern applicable to: `tkm-enhance`, `cortex-research-suite` enrichment pipelines.

---

## Cycle 4 — Security
**Timestamp**: 2026-03-23T00:45

### Scan Results
- Files scanned: 6 Python source files.
- Patterns checked: AWS AKIA, GitHub PATs (ghp_, ghs_), OpenAI (sk-), SSH/RSA private keys,
  generic `password=` assignments.
- **Real findings: 0**
- False positives: 1 (`_MAX_TEXT_LENGTH = 1_000_000` matched a broad numeric pattern).

### Actions
- Fixed **CWE-22 path traversal** in `DomainLoader.load`:
  - Reject domain names containing `/`, `\\`, or `..`.
  - `Path.resolve()` + `relative_to()` verifies path stays within `domains_dir`.

---

## Cycle 5 — CI/CD
**Timestamp**: 2026-03-23T01:00

### Actions
- `.github/workflows/ci.yml`: Python 3.12, uv, ruff check, pytest 95% coverage gate.
- `.pre-commit-config.yaml`: ruff + ruff-format, trailing-whitespace, check-yaml,
  detect-private-key, check-merge-conflict.
- Applied `ruff --fix`: 22 auto-fixed issues (unused imports, f-string prefix, import order).

---

## Cycle 6 — Property-Based Testing
**Timestamp**: 2026-03-23T01:15

### Invariants Tested
1. `to_dict()` → `from_dict()` preserves node and edge counts.
2. `Entity`/`Relationship` construction stable for all valid strings.
3. `validate()` never raises for any entity/rel combination.
4. `from_dict()` output bounded by input record count.
5. `build()` node_count equals unique entity count.
6. `from_text()` never crashes for any string ≤500 chars.
7. Entity hash/equality contract for all distinct IDs.

### Hypothesis Results
- **No failures found** across 11 property tests and 7 strategies.
- Total Hypothesis examples run: ~870.

---

## Cycle 7 — Examples + Docs
**Timestamp**: 2026-03-23T01:30

### Actions
- `examples/01_technology_graph.py` — domain load → extract → build → query → serialise.
- `examples/02_text_extraction.py` — regex NER, PageRank, community detection.
- `examples/03_async_parallel_enrichment.py` — parallel batch + async enrichment (17x speedup).
- **Bug fixed**: `weight` key excluded from `Relationship.properties` in `from_dict`
  (prevented `TypeError: multiple values for keyword argument 'weight'`).
- Added docstrings to all undocumented public methods in `GraphBuilder`.

---

## Cycle 8 — Release Engineering
**Timestamp**: 2026-03-23T01:45

### Actions
- Updated `pyproject.toml`: author, readme, keywords, PyPI classifiers.
- Created `CHANGELOG.md` with all cycle improvements.
- Created `Makefile` with `test`, `lint`, `format`, `security`, `clean` targets.
- Created `AGENTS.md` documenting the Edgecraft protocol.
- Created `EVOLUTION.md` (this file).
- Tagged `v0.1.0`.

---

## Final State

| Metric | Value |
|--------|-------|
| Total tests | 154 |
| Coverage | 100% |
| Cycles completed | 8 |
| Security findings | 0 |
| Property strategies | 7 |
| Examples | 3 |
| Max speedup measured | 30.4x |
| Commits | ~16 |
