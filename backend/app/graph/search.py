"""
Phase 5: Knowledge Graph — Graph Search

Provides fast lookup and query capabilities over the supply chain DiGraph.

Supported searches:
  1. Node lookup by ID or label (fuzzy)
  2. Nodes by type filter
  3. Nodes by risk score range
  4. Subgraph extraction (neighborhood)
  5. Path existence check
  6. Find all paths between two nodes
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import networkx as nx

logger = logging.getLogger("graph.search")


class GraphSearch:
    """Fast search and query layer over the supply chain DiGraph."""

    def find_node(
        self,
        G: nx.DiGraph,
        query: str,
        search_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Find nodes by ID or label (case-insensitive, partial match on label).

        Args:
            query: Search term (matches node_id prefix or label substring)
            search_type: Optional filter by node_type

        Returns:
            {"matches": [...], "total": int}
        """
        query_lower = query.lower().strip()
        results = []

        for nid, attrs in G.nodes(data=True):
            nt = attrs.get("node_type", "")
            if search_type and nt != search_type:
                continue

            # Match on node_id or label
            label = attrs.get("label", "").lower()
            if query_lower in nid.lower() or query_lower in label:
                results.append({
                    "node_id":    nid,
                    "label":      attrs.get("label", nid),
                    "node_type":  nt,
                    "risk_score": attrs.get("risk_score", 0.0),
                    "status":     attrs.get("status", "unknown"),
                    "country_code": attrs.get("country_code"),
                    "tier":       attrs.get("tier"),
                })

        results.sort(key=lambda x: x["risk_score"], reverse=True)
        return {"matches": results, "total": len(results), "query": query}

    def get_nodes_by_type(
        self,
        G: nx.DiGraph,
        node_type: str,
        sort_by: str = "risk_score",
    ) -> List[Dict[str, Any]]:
        """Return all nodes of a given type, sorted by `sort_by` attr."""
        results = [
            {
                "node_id":    nid,
                "label":      attrs.get("label", nid),
                "node_type":  attrs.get("node_type"),
                "risk_score": attrs.get("risk_score", 0.0),
                "status":     attrs.get("status", "unknown"),
                "country_code": attrs.get("country_code"),
                "tier":       attrs.get("tier"),
                "metadata":   attrs.get("metadata", {}),
            }
            for nid, attrs in G.nodes(data=True)
            if attrs.get("node_type") == node_type
        ]
        results.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
        return results

    def get_high_risk_nodes(
        self,
        G: nx.DiGraph,
        min_risk_score: float = 67.0,
        node_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return all nodes with risk_score >= min_risk_score."""
        results = []
        for nid, attrs in G.nodes(data=True):
            if node_type and attrs.get("node_type") != node_type:
                continue
            rs = attrs.get("risk_score", 0.0)
            if rs >= min_risk_score:
                results.append({
                    "node_id":    nid,
                    "label":      attrs.get("label", nid),
                    "node_type":  attrs.get("node_type"),
                    "risk_score": rs,
                    "status":     attrs.get("status", "unknown"),
                    "country_code": attrs.get("country_code"),
                    "tier":       attrs.get("tier"),
                })
        results.sort(key=lambda x: x["risk_score"], reverse=True)
        return results

    def neighborhood_subgraph(
        self,
        G: nx.DiGraph,
        center_node: str,
        radius: int = 2,
    ) -> Dict[str, Any]:
        """
        Extract a subgraph centered on `center_node` within `radius` hops.
        Used to generate a focused React Flow visualization for one node.

        Returns:
            {"nodes": [...], "edges": [...]}
        """
        if not G.has_node(center_node):
            return {"error": f"Node '{center_node}' not found", "nodes": [], "edges": []}

        # BFS to collect nodes within radius
        within_radius = {center_node}
        frontier = {center_node}
        for _ in range(radius):
            next_frontier = set()
            for node in frontier:
                next_frontier.update(G.successors(node))
                next_frontier.update(G.predecessors(node))
            within_radius.update(next_frontier)
            frontier = next_frontier

        # Extract subgraph
        sub = G.subgraph(within_radius)

        nodes = [
            {
                "node_id":    nid,
                "label":      attrs.get("label", nid),
                "node_type":  attrs.get("node_type", "unknown"),
                "risk_score": attrs.get("risk_score", 0.0),
                "status":     attrs.get("status", "unknown"),
                "is_center":  nid == center_node,
            }
            for nid, attrs in sub.nodes(data=True)
        ]

        edges = [
            {
                "source_id":   src,
                "target_id":   tgt,
                "edge_type":   data.get("edge_type", "unknown"),
                "weight":      data.get("weight", 1.0),
                "risk_weight": data.get("risk_weight", 0.5),
            }
            for src, tgt, data in sub.edges(data=True)
        ]

        return {
            "center_node": center_node,
            "radius":      radius,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes":       nodes,
            "edges":       edges,
        }

    def find_paths(
        self,
        G: nx.DiGraph,
        source: str,
        target: str,
        max_paths: int = 5,
    ) -> Dict[str, Any]:
        """
        Find all simple paths between source and target (up to max_paths).

        Uses NetworkX all_simple_paths with cutoff to prevent exponential blowup.
        """
        if not G.has_node(source) or not G.has_node(target):
            return {"error": "Source or target not found", "paths": []}

        try:
            generator = nx.all_simple_paths(G, source, target, cutoff=6)
            paths = []
            for path in generator:
                paths.append(path)
                if len(paths) >= max_paths:
                    break

            return {
                "source":   source,
                "target":   target,
                "paths":    paths,
                "total":    len(paths),
                "reachable": len(paths) > 0,
            }
        except Exception as e:
            return {"error": str(e), "paths": []}


# Module-level singleton
graph_search = GraphSearch()
