"""
Phase 5: Knowledge Graph — Analyzer

High-level analysis classes that combine multiple algorithms into
actionable supply chain intelligence reports.

BlastRadiusAnalyzer: Given a list of at-risk nodes (from Phase 4),
  runs blast radius analysis on each and ranks by total business impact.

DependencyAnalyzer: Builds a full dependency report for any node —
  ancestors, descendants, centrality, and path to all products.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import networkx as nx

from app.graph.algorithms import GraphAlgorithms

logger = logging.getLogger("graph.analyzer")

_algo = GraphAlgorithms()


class BlastRadiusAnalyzer:
    """
    Analyzes the blast radius across the entire supply chain from
    multiple disrupted nodes simultaneously.

    Used by GraphAgent.execute() to generate the graph_snapshot.blast_radius_report.
    """

    def analyze_all(
        self,
        G: nx.DiGraph,
        disrupted_nodes: Optional[List[str]] = None,
        max_depth: int = 4,
        top_n: int = 10,
    ) -> Dict[str, Any]:
        """
        Run blast radius analysis on multiple disrupted nodes.

        If disrupted_nodes is None, automatically selects nodes with
        risk_score >= 67 (HIGH or CRITICAL).

        Returns:
            {
              "disrupted_nodes_count": int,
              "total_nodes_impacted": int,
              "unique_products_at_risk": [...],
              "unique_suppliers_at_risk": [...],
              "blast_radius_reports": [...],
              "worst_case_node": str,
            }
        """
        # Auto-select high-risk nodes if not provided
        if disrupted_nodes is None:
            disrupted_nodes = [
                nid for nid, attrs in G.nodes(data=True)
                if attrs.get("risk_score", 0.0) >= 67.0
            ]

        if not disrupted_nodes:
            return {
                "disrupted_nodes_count": 0,
                "total_nodes_impacted": 0,
                "blast_radius_reports": [],
                "message": "No high-risk nodes found",
            }

        reports = []
        all_impacted: set = set()
        products_at_risk: set = set()
        suppliers_at_risk: set = set()

        for node_id in disrupted_nodes[:top_n]:  # limit to avoid O(n^2) slowdown
            if not G.has_node(node_id):
                continue

            report = _algo.blast_radius(G, node_id, max_depth=max_depth)
            reports.append(report)

            for imp in report.get("direct_impacts", []) + report.get("indirect_impacts", []):
                all_impacted.add(imp["node_id"])
                if imp["node_type"] == "product":
                    products_at_risk.add(imp["node_id"])
                elif imp["node_type"] == "supplier":
                    suppliers_at_risk.add(imp["node_id"])

        # Sort by blast_radius_score descending
        reports.sort(key=lambda r: r.get("blast_radius_score", 0), reverse=True)

        worst_case = reports[0]["disrupted_node"] if reports else None

        return {
            "disrupted_nodes_count":   len(disrupted_nodes),
            "total_nodes_impacted":    len(all_impacted),
            "unique_products_at_risk": list(products_at_risk),
            "unique_suppliers_at_risk": list(suppliers_at_risk),
            "blast_radius_reports":    reports,
            "worst_case_node":         worst_case,
            "worst_case_score":        reports[0].get("blast_radius_score", 0) if reports else 0,
        }


class DependencyAnalyzer:
    """
    Full dependency analysis for any given node in the supply chain graph.

    Combines:
      - Ancestors (upstream dependencies)
      - Descendants (downstream impacts)
      - Centrality score
      - Dijkstra paths to all product nodes
    """

    def analyze_node(
        self,
        G: nx.DiGraph,
        node_id: str,
    ) -> Dict[str, Any]:
        """
        Complete dependency report for a single node.

        Returns:
            {
              "node_id": str,
              "node_info": {...},
              "ancestors": [...],
              "descendants": [...],
              "centrality": float,
              "is_spof": bool,
              "paths_to_products": [...],
            }
        """
        if not G.has_node(node_id):
            return {"error": f"Node '{node_id}' not found"}

        node_info = dict(G.nodes[node_id])

        # Ancestors and descendants
        anc_result  = _algo.ancestors(G, node_id)
        desc_result = _algo.descendants(G, node_id)

        # Centrality
        centrality_result = _algo.degree_centrality(G, top_n=G.number_of_nodes(), spof_threshold=0.15)
        node_centrality   = next(
            (n["centrality"] for n in centrality_result.get("top_nodes", []) if n["node_id"] == node_id),
            0.0
        )
        is_spof = node_centrality >= 0.15

        # Paths to all product nodes
        product_nodes = [
            nid for nid, attrs in G.nodes(data=True)
            if attrs.get("node_type") == "product"
        ]
        paths_to_products = []
        for prod_id in product_nodes:
            path_result = _algo.dijkstra_path(G, node_id, prod_id)
            if path_result.get("reachable"):
                paths_to_products.append({
                    "product_id":    prod_id,
                    "product_label": G.nodes[prod_id].get("label", prod_id),
                    "path_length":   path_result["hop_count"],
                    "path_cost":     path_result["total_cost"],
                    "path_nodes":    path_result["path"],
                })

        return {
            "node_id":            node_id,
            "node_info":          node_info,
            "ancestors":          anc_result.get("ancestors", []),
            "ancestor_count":     anc_result.get("total_ancestors", 0),
            "descendants":        desc_result.get("descendants", []),
            "descendant_count":   desc_result.get("total_descendants", 0),
            "centrality":         node_centrality,
            "is_spof":            is_spof,
            "paths_to_products":  paths_to_products,
            "products_reachable": len(paths_to_products),
        }
