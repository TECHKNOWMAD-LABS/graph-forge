"""GraphBuilder — construct and query NetworkX knowledge graphs."""

from __future__ import annotations

from typing import Any

import networkx as nx

from graphforge.models import Entity, Relationship


class GraphBuilder:
    """Build and manage a NetworkX DiGraph from entities and relationships."""

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def graph(self) -> nx.DiGraph:
        """The underlying NetworkX DiGraph."""
        return self._graph

    @property
    def node_count(self) -> int:
        return self._graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self._graph.number_of_edges()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def add_entity(self, entity: Entity) -> None:
        """Add a single entity as a graph node."""
        self._graph.add_node(
            entity.id,
            label=entity.label,
            entity_type=entity.entity_type,
            **entity.properties,
        )

    def add_entities(self, entities: list[Entity]) -> None:
        for entity in entities:
            self.add_entity(entity)

    def add_relationship(self, rel: Relationship) -> None:
        """Add a single relationship as a directed edge."""
        self._graph.add_edge(
            rel.source_id,
            rel.target_id,
            relation_type=rel.relation_type,
            weight=rel.weight,
            **rel.properties,
        )

    def add_relationships(self, relationships: list[Relationship]) -> None:
        for rel in relationships:
            self.add_relationship(rel)

    def build(
        self, entities: list[Entity], relationships: list[Relationship]
    ) -> nx.DiGraph:
        """Build the full graph and return it."""
        self.add_entities(entities)
        self.add_relationships(relationships)
        return self._graph

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        if node_id in self._graph:
            return dict(self._graph.nodes[node_id])
        return None

    def get_neighbors(self, node_id: str) -> list[str]:
        if node_id not in self._graph:
            return []
        return list(self._graph.successors(node_id))

    def get_predecessors(self, node_id: str) -> list[str]:
        if node_id not in self._graph:
            return []
        return list(self._graph.predecessors(node_id))

    def find_by_type(self, entity_type: str) -> list[str]:
        """Return node IDs whose entity_type matches."""
        return [
            n
            for n, data in self._graph.nodes(data=True)
            if data.get("entity_type") == entity_type
        ]

    def shortest_path(self, source: str, target: str) -> list[str]:
        """Return shortest path between two nodes, or empty list if none."""
        try:
            return nx.shortest_path(self._graph, source=source, target=target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def subgraph(self, node_ids: list[str]) -> nx.DiGraph:
        """Return an induced subgraph for the given node IDs."""
        return self._graph.subgraph(node_ids).copy()

    def degree_centrality(self) -> dict[str, float]:
        return nx.degree_centrality(self._graph)

    def clear(self) -> None:
        self._graph.clear()

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise the graph to a plain dict."""
        return nx.node_link_data(self._graph, edges="links")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphBuilder:
        builder = cls()
        builder._graph = nx.node_link_graph(data, directed=True, edges="links")
        return builder
