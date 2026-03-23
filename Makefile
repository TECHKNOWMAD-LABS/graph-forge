.PHONY: test lint format security clean install help

# Default target
help:
	@echo "GraphForge — available make targets:"
	@echo "  make install    Install all dependencies (uv sync)"
	@echo "  make test       Run full test suite with coverage"
	@echo "  make lint       Run ruff linter"
	@echo "  make format     Run ruff formatter"
	@echo "  make security   Run secret scan on source files"
	@echo "  make clean      Remove build artifacts and caches"

install:
	uv sync --all-extras

test:
	uv run pytest -v --tb=short --cov=graphforge --cov-report=term-missing --cov-fail-under=95

test-fast:
	uv run pytest -q --tb=line

test-property:
	uv run pytest tests/test_property_based.py -v --tb=short

lint:
	uv run ruff check graphforge/ tests/

format:
	uv run ruff format graphforge/ tests/
	uv run ruff check --fix graphforge/ tests/

security:
	@echo "Running secret scan..."
	@python3 -c "\
import re, pathlib; \
patterns = [r'AKIA[0-9A-Z]{16}', r'ghp_[A-Za-z0-9]{36}', r'sk-[A-Za-z0-9]{20,}', r'-----BEGIN.*PRIVATE KEY']; \
files = list(pathlib.Path('graphforge').rglob('*.py')); \
findings = []; \
[findings.extend([f'{f}:{i+1}' for i,l in enumerate(f.read_text().splitlines()) if any(re.search(p,l) for p in patterns)]) for f in files]; \
print(f'Scanned {len(files)} files — {len(findings)} findings') if not findings else print('FINDINGS:', findings)"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .coverage htmlcov dist build *.egg-info .pytest_cache .ruff_cache 2>/dev/null || true
