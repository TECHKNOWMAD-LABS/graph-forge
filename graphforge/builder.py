"""GraphBuilder — construct and query NetworkX knowledge graphs."""

from __future__ import annotations

from typing import Any

import networkx as nx

from graphforge.models import Entity, Relationship


class GraphBuilder:
    """Build and manage a NetworkX DiGraph from entities and relationships."""

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()
        # Cache invalidation counter — bumped on every structural change
        self._version: int = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def graph(self) -> nx.DiGraph:
        """The underlying NetworkX DiGraph."""
        return self._graph

    @property
    def node_count(self) -> int:
        """Number of nodes currently in the graph."""
        return self._graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        """Number of directed edges currently in the graph."""
        return self._graph.number_of_edges()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def add_entity(self, entity: Entity) -> None:
        """Add a single entity as a graph node.

        Args:
            entity: Entity to add. Must be an Entity instance.

        Raises:
            TypeError: If entity is not an Entity instance.
        """
        if not isinstance(entity, Entity):
            raise TypeError(f"Expected Entity, got {type(entity).__name__}")
        self._graph.add_node(
            entity.id,
            label=entity.label,
            entity_type=entity.entity_type,
            **entity.properties,
        )
        self._version += 1

    def add_entities(self, entities: list[Entity] | None) -> None:
        """Add multiple entities to the graph.

        Args:
            entities: List of Entity objects to add. None or empty list is a no-op.
        """
        if not entities:
            return
        for entity in entities:
            self.add_entity(entity)

    def add_relationship(self, rel: Relationship) -> None:
        """Add a single relationship as a directed edge.

        Args:
            rel: Relationship to add. Must be a Relationship instance.

        Raises:
            TypeError: If rel is not a Relationship instance.
        """
        if not isinstance(rel, Relationship):
            raise TypeError(f"Expected Relationship, got {type(rel).__name__}")
        self._graph.add_edge(
            rel.source_id,
            rel.target_id,
            relation_type=rel.relation_type,
            weight=rel.weight,
            **rel.properties,
        )
        self._version += 1

    def add_relationships(self, relationships: list[Relationship] | None) -> None:
        """Add multiple relationships to the graph.

        Args:
            relationships: List of Relationship objects. None or empty list is a no-op.
        """
        if not relationships:
            return
        for rel in relationships:
            self.add_relationship(rel)

    def build(
        self,
        entities: list[Entity] | None,
        relationships: list[Relationship] | None,
    ) -> nx.DiGraph:
        """Build the full graph and return it.

        Args:
            entities: Entities to add (None treated as empty).
            relationships: Relationships to add (None treated as empty).
        """
        self.add_entities(entities or [])
        self.add_relationships(relationships or [])
        return self._graph

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_node(self, node_id: str | None) -> dict[str, Any] | None:
        """Return node attribute dict or None if node_id is None/missing."""
        if not node_id:
            return None
        if node_id in self._graph:
            return dict(self._graph.nodes[node_id])
        return None

    def get_neighbors(self, node_id: str | None) -> list[str]:
        """Return successor node IDs. Returns [] if node_id is None or missing."""
        if not node_id or node_id not in self._graph:
            return []
        return list(self._graph.successors(node_id))

    def get_predecessors(self, node_id: str | None) -> list[str]:
        """Return predecessor node IDs. Returns [] if node_id is None or missing."""
        if not node_id or node_id not in self._graph:
            return []
        return list(self._graph.predecessors(node_id))

    def find_by_type(self, entity_type: str | None) -> list[str]:
        """Return node IDs whose entity_type matches. Empty string or None returns []."""
        if not entity_type:
            return []
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
        """Compute and return degree centrality for all nodes."""
        return nx.degree_centrality(self._graph)

    def clear(self) -> None:
        """Remove all nodes and edges from the graph."""
        self._graph.clear()
        self._version += 1

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise the graph to a plain dict."""
        return nx.node_link_data(self._graph, edges="links")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphBuilder:
        """Restore a GraphBuilder from a serialised dict (produced by to_dict).

        Args:
            data: Dict as returned by ``to_dict()``.

        Returns:
            New GraphBuilder with the graph restored.
        """
        builder = cls()
        builder._graph = nx.node_link_graph(data, directed=True, edges="links")
        return builder
