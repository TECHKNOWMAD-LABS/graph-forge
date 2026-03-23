"""Security tests — Cycle 4.

Checks: path traversal, injection guards, no hardcoded secrets.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from graphforge.domains import DomainLoader
from graphforge.extractor import GraphExtractor

# ---------------------------------------------------------------------------
# Security scan: no hardcoded secrets in source files
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent
_SECRET_PATTERNS = [
    # AWS
    r"AKIA[0-9A-Z]{16}",
    # Generic high-entropy password assignment
    r'(?i)(password|passwd|secret|api_key|apikey|token)\s*=\s*["\'][^"\']{8,}["\']',
    # GitHub PATs
    r"ghp_[A-Za-z0-9]{36}",
    r"ghs_[A-Za-z0-9]{36}",
    # OpenAI keys
    r"sk-[A-Za-z0-9]{20,}",
    # Private keys
    r"-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----",
]
_COMPILED = [re.compile(p) for p in _SECRET_PATTERNS]

_SOURCE_FILES = list((_REPO_ROOT / "graphforge").rglob("*.py"))


def _scan_file(path: Path) -> list[str]:
    """Return list of findings (pattern, line) for a file."""
    findings = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings
    for lineno, line in enumerate(content.splitlines(), start=1):
        for pat in _COMPILED:
            if pat.search(line):
                findings.append(f"{path.relative_to(_REPO_ROOT)}:{lineno}: {pat.pattern}")
    return findings


class TestNoHardcodedSecrets:
    def test_no_secrets_in_source(self):
        """Zero secret patterns found across all source .py files."""
        all_findings = []
        for src in _SOURCE_FILES:
            all_findings.extend(_scan_file(src))
        assert all_findings == [], (
            "Potential secrets found:\n" + "\n".join(all_findings)
        )


# ---------------------------------------------------------------------------
# Path traversal prevention in DomainLoader
# ---------------------------------------------------------------------------


class TestPathTraversal:
    def test_traversal_via_dotdot_raises(self, tmp_path):
        loader = DomainLoader(domains_dir=tmp_path)
        with pytest.raises(ValueError, match="path separator"):
            loader.load("../etc/passwd")

    def test_traversal_via_slash_raises(self, tmp_path):
        loader = DomainLoader(domains_dir=tmp_path)
        with pytest.raises(ValueError, match="path separator"):
            loader.load("subdir/evil")

    def test_traversal_via_backslash_raises(self, tmp_path):
        loader = DomainLoader(domains_dir=tmp_path)
        with pytest.raises(ValueError, match="path separator"):
            loader.load("subdir\\evil")

    def test_empty_domain_name_raises(self, tmp_path):
        loader = DomainLoader(domains_dir=tmp_path)
        with pytest.raises(ValueError):
            loader.load("")

    def test_valid_domain_name_accepted(self):
        """A valid, safe domain name does not raise ValueError."""
        loader = DomainLoader()
        cfg = loader.load("technology")
        assert cfg.name == "technology"


# ---------------------------------------------------------------------------
# Injection vectors in GraphExtractor
# ---------------------------------------------------------------------------


class TestInjectionVectors:
    def test_sql_like_payload_in_id(self):
        """SQL injection payload in record id is stored as-is — no DB interaction."""
        ext = GraphExtractor()
        payload = "'; DROP TABLE entities; --"
        entities, _ = ext.from_dict([{"id": payload, "label": "evil", "type": "t"}])
        assert entities[0].id == payload  # stored literally, no execution

    def test_path_payload_in_text(self):
        """Path traversal payload in text processed as plain text — no filesystem ops."""
        ext = GraphExtractor()
        entities, _ = ext.from_text(
            "../../etc/passwd", {"path": r"\.\./\.\./etc/passwd"}
        )
        # No exception raised; entities may or may not match depending on regex
        assert isinstance(entities, list)

    def test_large_unicode_payload_does_not_crash(self):
        """Very long unicode string within limit should not crash."""
        ext = GraphExtractor()
        text = "安全テスト" * 10_000  # 50k unicode chars — within 1M limit
        entities, _ = ext.from_text(text)
        assert entities == []

    def test_null_bytes_in_record_handled(self):
        """Null bytes in string fields are stored/handled without crash."""
        ext = GraphExtractor()
        entities, _ = ext.from_dict([{"id": "x\x00y", "label": "null\x00byte", "type": "t"}])
        assert len(entities) == 1

    def test_deeply_nested_properties_do_not_crash(self):
        """Deeply nested dict in properties field is stored without recursion error."""
        ext = GraphExtractor()
        nested: dict = {}
        current = nested
        for _ in range(50):
            current["child"] = {}
            current = current["child"]
        records = [{"id": "deep", "label": "Deep", "type": "t", "data": nested}]
        entities, _ = ext.from_dict(records)
        assert entities[0].properties["data"] is nested
