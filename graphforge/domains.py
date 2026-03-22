"""Domain configuration loader — reads YAML files from the domains/ directory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_DEFAULT_DOMAINS_DIR = Path(__file__).parent.parent / "domains"


class DomainConfig:
    """Holds the configuration for a single knowledge domain."""

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self._config = config

    @property
    def entity_types(self) -> list[str]:
        return list(self._config.get("entity_types", {}).keys())

    @property
    def relation_types(self) -> list[str]:
        return list(self._config.get("relation_types", {}).keys())

    @property
    def description(self) -> str:
        return str(self._config.get("description", ""))

    def get_entity_schema(self, entity_type: str) -> dict[str, Any]:
        return dict(self._config.get("entity_types", {}).get(entity_type, {}))

    def get_relation_schema(self, relation_type: str) -> dict[str, Any]:
        return dict(self._config.get("relation_types", {}).get(relation_type, {}))

    def to_extractor_config(self) -> dict[str, Any]:
        """Return a config dict compatible with GraphExtractor."""
        return {
            "entity_types": self.entity_types,
            "relation_types": self.relation_types,
        }

    def __repr__(self) -> str:
        return f"DomainConfig(name={self.name!r}, entities={self.entity_types})"


class DomainLoader:
    """Load one or more domain YAML files."""

    def __init__(self, domains_dir: str | Path | None = None) -> None:
        self._dir = Path(domains_dir) if domains_dir else _DEFAULT_DOMAINS_DIR

    @property
    def domains_dir(self) -> Path:
        return self._dir

    def load(self, domain_name: str) -> DomainConfig:
        """Load a single domain by name (looks for <name>.yaml)."""
        path = self._dir / f"{domain_name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Domain config not found: {path}")
        with path.open() as fh:
            raw = yaml.safe_load(fh) or {}
        return DomainConfig(name=domain_name, config=raw)

    def load_all(self) -> dict[str, DomainConfig]:
        """Load every .yaml file in the domains directory."""
        configs: dict[str, DomainConfig] = {}
        if not self._dir.exists():
            return configs
        for yaml_path in sorted(self._dir.glob("*.yaml")):
            name = yaml_path.stem
            with yaml_path.open() as fh:
                raw = yaml.safe_load(fh) or {}
            configs[name] = DomainConfig(name=name, config=raw)
        return configs

    def list_domains(self) -> list[str]:
        """Return names of available domains."""
        if not self._dir.exists():
            return []
        return sorted(p.stem for p in self._dir.glob("*.yaml"))
