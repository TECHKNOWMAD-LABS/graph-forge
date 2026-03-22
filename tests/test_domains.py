"""Tests for DomainLoader and DomainConfig."""

import pytest

from graphforge.domains import DomainLoader


@pytest.fixture()
def loader():
    return DomainLoader()


def test_list_domains(loader):
    domains = loader.list_domains()
    assert "technology" in domains
    assert "science" in domains
    assert "social" in domains


def test_load_technology(loader):
    cfg = loader.load("technology")
    assert cfg.name == "technology"
    assert "software" in cfg.entity_types
    assert "depends_on" in cfg.relation_types


def test_load_science(loader):
    cfg = loader.load("science")
    assert "researcher" in cfg.entity_types
    assert "cites" in cfg.relation_types


def test_load_social(loader):
    cfg = loader.load("social")
    assert "person" in cfg.entity_types
    assert "follows" in cfg.relation_types


def test_load_all(loader):
    all_configs = loader.load_all()
    assert len(all_configs) >= 3


def test_domain_description(loader):
    cfg = loader.load("technology")
    assert len(cfg.description) > 0


def test_to_extractor_config(loader):
    cfg = loader.load("technology")
    ec = cfg.to_extractor_config()
    assert "entity_types" in ec
    assert "relation_types" in ec
    assert "software" in ec["entity_types"]


def test_get_entity_schema(loader):
    cfg = loader.load("technology")
    schema = cfg.get_entity_schema("software")
    assert isinstance(schema, dict)


def test_missing_domain_raises(loader):
    with pytest.raises(FileNotFoundError):
        loader.load("nonexistent_domain_xyz")
