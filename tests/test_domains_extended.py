"""Extended tests for DomainLoader and DomainConfig."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from graphforge.domains import DomainConfig, DomainLoader


def test_domain_config_repr():
    """Line 46: __repr__ of DomainConfig."""
    cfg = DomainConfig("test", {"entity_types": {"person": {}}, "relation_types": {}})
    r = repr(cfg)
    assert "test" in r
    assert "person" in r


def test_get_relation_schema():
    """Line 36: get_relation_schema."""
    cfg = DomainConfig(
        "test",
        {
            "entity_types": {},
            "relation_types": {"knows": {"description": "A knows B"}},
        },
    )
    schema = cfg.get_relation_schema("knows")
    assert schema["description"] == "A knows B"


def test_get_relation_schema_missing():
    """get_relation_schema for unknown type returns empty dict."""
    cfg = DomainConfig("test", {"relation_types": {}})
    assert cfg.get_relation_schema("no_such") == {}


def test_load_all_empty_dir():
    """Line 72: load_all on an empty directory returns empty dict."""
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = DomainLoader(domains_dir=tmpdir)
        result = loader.load_all()
        assert result == {}


def test_list_domains_nonexistent_dir():
    """Line 83: list_domains when dir doesn't exist."""
    loader = DomainLoader(domains_dir="/nonexistent_path_xyz")
    assert loader.list_domains() == []


def test_load_all_nonexistent_dir():
    """load_all when dir doesn't exist returns empty dict."""
    loader = DomainLoader(domains_dir="/nonexistent_path_xyz")
    assert loader.load_all() == {}


def test_custom_domains_dir():
    """Line 57: load domain from a custom directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        domain_data = {
            "description": "Custom test domain",
            "entity_types": {"widget": {"description": "A widget"}},
            "relation_types": {"contains": {"description": "Contains"}},
        }
        yaml_path = Path(tmpdir) / "custom.yaml"
        with yaml_path.open("w") as f:
            yaml.dump(domain_data, f)

        loader = DomainLoader(domains_dir=tmpdir)
        cfg = loader.load("custom")
        assert cfg.name == "custom"
        assert "widget" in cfg.entity_types
        assert "contains" in cfg.relation_types
        assert cfg.description == "Custom test domain"


def test_domain_loader_domains_dir_property():
    """Line 57: domains_dir property returns path."""
    loader = DomainLoader()
    assert loader.domains_dir.exists()
