# AGENTS.md — Edgecraft Autonomous Development Protocol

This repository was developed using the **Edgecraft Protocol**, an autonomous
multi-cycle development system that iterates through structured improvement layers.

## Protocol Overview

Edgecraft operates through 8 prescribed cycles, each targeting a specific quality
dimension. All cycles execute without human intervention; the agent fixes failures
and continues.

### Cycle Structure

| Cycle | Layer | Focus | Commit Prefix |
|-------|-------|-------|---------------|
| 1 | L1/detection → L5/action → L6/grounding | Test coverage | `L1/detection:`, `L5/action:`, `L6/grounding:` |
| 2 | L3/sub-noise → L5/action | Error hardening | `L3/sub-noise:`, `L5/action:` |
| 3 | L4/conjecture → L6/grounding → L7/flywheel | Performance | `L4/conjecture:`, `L6/grounding:`, `L7/flywheel:` |
| 4 | L2/noise → L5/action | Security | `L2/noise:`, `L5/action:` |
| 5 | L5/action | CI/CD | `L5/action:` |
| 6 | L3/sub-noise → L6/grounding | Property-based testing | `L3/sub-noise:`, `L6/grounding:` |
| 7 | L5/action | Examples + documentation | `L5/action:` |
| 8 | L5/action | Release engineering | `L5/action:` |

### Layer Semantics

- **L1/detection** — Identify what is missing or broken.
- **L2/noise** — Surface-level scan results (security, lint).
- **L3/sub-noise** — Subtle bugs, edge cases, property violations.
- **L4/conjecture** — Hypothesis about improvement potential.
- **L5/action** — Concrete implementation of the fix/feature.
- **L6/grounding** — Measured validation of the hypothesis.
- **L7/flywheel** — Pattern recognition for cross-repo applicability.

## What the Agent Does in Each Cycle

### Cycle 1 — Test Coverage
1. Run `pytest --cov` to find uncovered lines.
2. Write `conftest.py` with shared fixtures.
3. Write test files targeting every uncovered branch.
4. Fix any failing tests before committing.

### Cycle 2 — Error Hardening
1. Attempt to break the code with: `None`, empty strings, wrong types,
   malformed data, huge inputs, unicode.
2. Add input validation, graceful fallbacks, and type guards.

### Cycle 3 — Performance
1. Find sequential I/O-bound operations.
2. Parallelise with `asyncio.gather` + semaphore.
3. Measure and log actual speedup.

### Cycle 4 — Security
1. Scan for hardcoded secrets using 7+ patterns.
2. Check for injection vectors (path traversal, SQL, command).
3. Fix all real findings.

### Cycle 5 — CI/CD
1. Create GitHub Actions workflow with lint + test.
2. Create `.pre-commit-config.yaml` with ruff + hooks.

### Cycle 6 — Property-Based Testing
1. Write Hypothesis tests for core invariants.
2. If Hypothesis finds failures, fix the underlying code first.

### Cycle 7 — Examples + Docs
1. Create 2-3 working example scripts in `examples/`.
2. Test each example manually.
3. Add docstrings to all public functions.

### Cycle 8 — Release Engineering
1. Finalise `pyproject.toml` metadata.
2. Write `CHANGELOG.md`.
3. Create `Makefile`, `AGENTS.md`, `EVOLUTION.md`.
4. Tag `v0.1.0`.

## Absolute Rules

- Never ask questions. Never pause.
- Fix all test failures before committing.
- Every commit must have a meaningful diff.
- Push after each cycle.
- All commit messages start with the Edgecraft layer prefix.
