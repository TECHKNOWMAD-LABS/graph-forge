"""GraphEnricher — add computed attributes and metadata to graph nodes/edges."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import networkx as nx

from graphforge.builder import GraphBuilder


class GraphEnricher:
    """Enrich graph nodes and edges with computed properties."""

    def __init__(self, builder: GraphBuilder) -> None:
        self._builder = builder

    @property
    def graph(self) -> nx.DiGraph:
        return self._builder.graph

    # ------------------------------------------------------------------
    # Node enrichment
    # ------------------------------------------------------------------

    def add_node_property(self, node_id: str, key: str, value: Any) -> bool:
        """Set a single property on a node.  Returns False if node not found."""
        if node_id not in self.graph:
            return False
        self.graph.nodes[node_id][key] = value
        return True

    def bulk_enrich_nodes(
        self, enrichments: dict[str, dict[str, Any]]
    ) -> list[str]:
        """Apply multiple property dicts keyed by node_id.

        Returns list of node_ids that were not found.
        """
        missing: list[str] = []
        for node_id, props in enrichments.items():
            if node_id not in self.graph:
                missing.append(node_id)
                continue
            self.graph.nodes[node_id].update(props)
        return missing

    def apply_node_function(
        self, fn: Callable[[str, dict[str, Any]], dict[str, Any]]
    ) -> None:
        """Call fn(node_id, node_data) → dict and merge result into each node."""
        for node_id, data in self.graph.nodes(data=True):
            updates = fn(node_id, data)
            data.update(updates)

    # ------------------------------------------------------------------
    # Edge enrichment
    # ------------------------------------------------------------------

    def add_edge_property(
        self, source: str, target: str, key: str, value: Any
    ) -> bool:
        if not self.graph.has_edge(source, target):
            return False
        self.graph[source][target][key] = value
        return True

    # ------------------------------------------------------------------
    # Computed metrics
    # ------------------------------------------------------------------

    def enrich_degree_centrality(self, attr_name: str = "degree_centrality") -> None:
        """Write degree centrality score to each node."""
        centrality = nx.degree_centrality(self.graph)
        for node_id, score in centrality.items():
            self.graph.nodes[node_id][attr_name] = score

    def enrich_pagerank(
        self, attr_name: str = "pagerank", **pagerank_kwargs: Any
    ) -> None:
        """Write PageRank score to each node."""
        scores = nx.pagerank(self.graph, **pagerank_kwargs)
        for node_id, score in scores.items():
            self.graph.nodes[node_id][attr_name] = score

    def enrich_clustering(self, attr_name: str = "clustering") -> None:
        """Write clustering coefficient to each node (undirected approximation)."""
        undirected = self.graph.to_undirected()
        clustering = nx.clustering(undirected)
        for node_id, score in clustering.items():
            self.graph.nodes[node_id][attr_name] = score

    def enrich_community_labels(
        self, attr_name: str = "community"
    ) -> dict[str, int]:
        """Assign community labels via greedy modularity (undirected)."""
        undirected = self.graph.to_undirected()
        communities = nx.community.greedy_modularity_communities(undirected)
        label_map: dict[str, int] = {}
        for idx, community in enumerate(communities):
            for node_id in community:
                self.graph.nodes[node_id][attr_name] = idx
                label_map[node_id] = idx
        return label_map

    def tag_nodes(self, node_ids: list[str], tag: str, value: Any = True) -> None:
        """Apply a tag attribute to a set of nodes."""
        for nid in node_ids:
            if nid in self.graph:
                self.graph.nodes[nid][tag] = value

    def normalize_weights(self) -> None:
        """Normalize edge weights to [0, 1] range."""
        weights = [
            d.get("weight", 1.0) for _, _, d in self.graph.edges(data=True)
        ]
        if not weights:
            return
        max_w = max(weights)
        min_w = min(weights)
        spread = max_w - min_w or 1.0
        for u, v, data in self.graph.edges(data=True):
            data["weight_normalized"] = (data.get("weight", 1.0) - min_w) / spread
