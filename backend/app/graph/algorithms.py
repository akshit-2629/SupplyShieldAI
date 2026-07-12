"""
Phase 5: Knowledge Graph — Algorithm Implementations

All algorithms operate on a NetworkX DiGraph (G).
Each returns a structured dict suitable for JSON serialization.

Algorithms implemented:
  1.  BFS Tree           — bfs_tree(G, source)
  2.  DFS Tree           — dfs_tree(G, source)  
  3.  Dijkstra Path      — dijkstra_path(G, source, target, weight='risk_weight')
  4.  Dijkstra Length    — dijkstra_path_length(G, source, target, weight='risk_weight')
  5.  Degree Centrality  — degree_centrality(G)
  6.  In-Degree Centrality — in_degree_centrality(G)
  7.  Betweenness Centrality — betweenness_centrality(G)
  8.  Descendants        — descendants(G, node)
  9.  Ancestors          — ancestors(G, node)
  10. Blast Radius       — BFS from disrupted node → all downstream impacts
  11. Critical Path      — Dijkstra on risk-weighted graph (highest-risk path)
  12. SPOF Detection     — nodes with degree_centrality above threshold
  13. Shortest Path All  — all_shortest_paths(G, source, target)
  14. Strongly Connected — strongly_connected_components(G)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

logger = logging.getLogger("graph.algorithms")


class GraphAlgorithms:
    """
    All graph algorithm implementations for the supply chain DiGraph.

    All methods accept:
        G: nx.DiGraph  — the current supply chain graph
        ...parameters specific to each algorithm

    All methods return:
        Dict[str, Any]  — structured, JSON-serializable result
    """

    # ─────────────────────────────────────────────────────────────────────────
    # 1. BFS — Breadth-First Search tree from a source node
    # ─────────────────────────────────────────────────────────────────────────

    def bfs_tree(
        self,
        G: nx.DiGraph,
        source: str,
        max_depth: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Breadth-First Search tree rooted at `source`.

        Formula:
            BFS explores all nodes at distance k before distance k+1.
            Used for blast-radius tracing — "which nodes does a disruption
            at `source` reach, in order of proximity?"

        Returns:
            {
              "source": str,
              "visited_nodes": [{"node_id", "depth", "label", "risk_score", ...}],
              "tree_edges": [{"source", "target"}],
              "total_impacted": int,
              "max_depth_reached": int,
            }
        """
        if not G.has_node(source):
            return {"error": f"Node '{source}' not found in graph", "source": source}

        visited: Dict[str, int] = {}   # node_id → depth
        queue = [(source, 0)]
        tree_edges: List[Dict] = []

        while queue:
            node, depth = queue.pop(0)
            if node in visited:
                continue
            if max_depth is not None and depth > max_depth:
                continue

            visited[node] = depth

            for neighbor in G.successors(node):
                if neighbor not in visited:
                    tree_edges.append({"source": node, "target": neighbor})
                    queue.append((neighbor, depth + 1))

        visited_nodes = [
            {
                "node_id":    nid,
                "depth":      d,
                "label":      G.nodes[nid].get("label", nid) if G.has_node(nid) else nid,
                "node_type":  G.nodes[nid].get("node_type", "unknown") if G.has_node(nid) else "unknown",
                "risk_score": G.nodes[nid].get("risk_score", 0.0) if G.has_node(nid) else 0.0,
                "status":     G.nodes[nid].get("status", "unknown") if G.has_node(nid) else "unknown",
            }
            for nid, d in sorted(visited.items(), key=lambda x: x[1])
        ]

        max_depth_reached = max(visited.values()) if visited else 0

        return {
            "algorithm":        "BFS",
            "source":           source,
            "visited_nodes":    visited_nodes,
            "tree_edges":       tree_edges,
            "total_impacted":   len(visited),
            "max_depth_reached": max_depth_reached,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 2. DFS — Depth-First Search tree from a source node
    # ─────────────────────────────────────────────────────────────────────────

    def dfs_tree(
        self,
        G: nx.DiGraph,
        source: str,
        max_depth: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Depth-First Search tree rooted at `source`.

        Formula:
            DFS explores as deep as possible before backtracking.
            Used for dependency chain traversal — "what is the full
            depth of the dependency chain below this supplier?"

        Returns:
            {
              "source": str,
              "visited_nodes": [...],
              "tree_edges": [...],
              "total_reachable": int,
              "max_depth_reached": int,
            }
        """
        if not G.has_node(source):
            return {"error": f"Node '{source}' not found in graph", "source": source}

        visited: Dict[str, int] = {}
        stack = [(source, 0)]
        tree_edges: List[Dict] = []
        parent: Dict[str, str] = {}

        while stack:
            node, depth = stack.pop()
            if node in visited:
                continue
            if max_depth is not None and depth > max_depth:
                continue

            visited[node] = depth

            if node in parent:
                tree_edges.append({"source": parent[node], "target": node})

            for neighbor in reversed(list(G.successors(node))):
                if neighbor not in visited:
                    parent[neighbor] = node
                    stack.append((neighbor, depth + 1))

        visited_nodes = [
            {
                "node_id":    nid,
                "depth":      d,
                "label":      G.nodes[nid].get("label", nid) if G.has_node(nid) else nid,
                "node_type":  G.nodes[nid].get("node_type", "unknown") if G.has_node(nid) else "unknown",
                "risk_score": G.nodes[nid].get("risk_score", 0.0) if G.has_node(nid) else 0.0,
            }
            for nid, d in sorted(visited.items(), key=lambda x: x[1])
        ]

        return {
            "algorithm":         "DFS",
            "source":            source,
            "visited_nodes":     visited_nodes,
            "tree_edges":        tree_edges,
            "total_reachable":   len(visited),
            "max_depth_reached": max(visited.values()) if visited else 0,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Dijkstra — Critical Procurement Path (lowest risk-weighted path)
    # ─────────────────────────────────────────────────────────────────────────

    def dijkstra_path(
        self,
        G: nx.DiGraph,
        source: str,
        target: str,
        weight: str = "risk_weight",
    ) -> Dict[str, Any]:
        """
        Dijkstra's shortest (lowest risk-weight) path from source to target.

        Formula:
            Standard Dijkstra: greedily expands the lowest-cost frontier.
            edge weight = risk_weight (0.0 to 1.0, higher = riskier)
            The path returned is the SAFEST procurement route.

        Returns:
            {
              "source": str,
              "target": str,
              "path": [node_ids],
              "path_labels": [display_labels],
              "total_cost": float,
              "edge_details": [...],
              "reachable": bool,
            }
        """
        if not G.has_node(source):
            return {"error": f"Source '{source}' not found", "reachable": False}
        if not G.has_node(target):
            return {"error": f"Target '{target}' not found", "reachable": False}

        try:
            path = nx.dijkstra_path(G, source, target, weight=weight)
            length = nx.dijkstra_path_length(G, source, target, weight=weight)

            edge_details = []
            for i in range(len(path) - 1):
                src, tgt = path[i], path[i + 1]
                edge_attrs = G.edges.get((src, tgt), {})
                edge_details.append({
                    "from":        src,
                    "to":          tgt,
                    "from_label":  G.nodes[src].get("label", src),
                    "to_label":    G.nodes[tgt].get("label", tgt),
                    "edge_type":   edge_attrs.get("edge_type", "unknown"),
                    "weight":      edge_attrs.get("weight", 1.0),
                    "risk_weight": edge_attrs.get("risk_weight", 1.0),
                })

            return {
                "algorithm":   "Dijkstra",
                "source":      source,
                "target":      target,
                "path":        path,
                "path_labels": [G.nodes[n].get("label", n) for n in path if G.has_node(n)],
                "total_cost":  round(length, 4),
                "edge_details": edge_details,
                "hop_count":   len(path) - 1,
                "reachable":   True,
            }
        except nx.NetworkXNoPath:
            return {
                "algorithm": "Dijkstra",
                "source":    source,
                "target":    target,
                "reachable": False,
                "error":     f"No path exists from '{source}' to '{target}'",
            }
        except nx.NodeNotFound as e:
            return {"algorithm": "Dijkstra", "reachable": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Degree Centrality — SPOF (Single Point of Failure) Detection
    # ─────────────────────────────────────────────────────────────────────────

    def degree_centrality(
        self,
        G: nx.DiGraph,
        top_n: int = 15,
        spof_threshold: float = 0.15,
    ) -> Dict[str, Any]:
        """
        Compute degree centrality for all nodes.

        Formula:
            degree_centrality(v) = deg(v) / (n - 1)
            where deg(v) = number of edges (in + out), n = total nodes

            Nodes with high centrality = single points of failure (SPOF).
            A disruption at a high-centrality node cascades to many others.

        Args:
            top_n: Return only the top N most central nodes
            spof_threshold: Centrality above this = flagged as SPOF

        Returns:
            {
              "top_nodes": [{"node_id", "centrality", "is_spof", ...}],
              "spof_nodes": [...],
              "avg_centrality": float,
              "max_centrality": float,
            }
        """
        centrality     = nx.degree_centrality(G)
        in_centrality  = nx.in_degree_centrality(G)
        out_centrality = nx.out_degree_centrality(G)

        # Build sorted list
        all_nodes = [
            {
                "node_id":         nid,
                "label":           G.nodes[nid].get("label", nid),
                "node_type":       G.nodes[nid].get("node_type", "unknown"),
                "risk_score":      G.nodes[nid].get("risk_score", 0.0),
                "status":          G.nodes[nid].get("status", "unknown"),
                "centrality":      round(c, 4),
                "in_centrality":   round(in_centrality.get(nid, 0), 4),
                "out_centrality":  round(out_centrality.get(nid, 0), 4),
                "degree":          G.degree(nid),
                "in_degree":       G.in_degree(nid),
                "out_degree":      G.out_degree(nid),
                "is_spof":         c >= spof_threshold,
            }
            for nid, c in centrality.items()
            if G.has_node(nid)
        ]
        all_nodes.sort(key=lambda x: x["centrality"], reverse=True)

        top_nodes  = all_nodes[:top_n]
        spof_nodes = [n for n in all_nodes if n["is_spof"]]
        centrality_values = list(centrality.values())

        return {
            "algorithm":      "DegreeCentrality",
            "top_nodes":      top_nodes,
            "spof_nodes":     spof_nodes,
            "total_nodes":    G.number_of_nodes(),
            "spof_count":     len(spof_nodes),
            "avg_centrality": round(sum(centrality_values) / len(centrality_values), 4) if centrality_values else 0.0,
            "max_centrality": round(max(centrality_values), 4) if centrality_values else 0.0,
            "spof_threshold": spof_threshold,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Betweenness Centrality — Bottleneck / Chokepoint Detection
    # ─────────────────────────────────────────────────────────────────────────

    def betweenness_centrality(
        self,
        G: nx.DiGraph,
        top_n: int = 10,
        normalized: bool = True,
    ) -> Dict[str, Any]:
        """
        Betweenness centrality: fraction of all shortest paths passing through a node.

        Formula:
            BC(v) = Σ_{s≠v≠t} (σ_st(v) / σ_st)
            where σ_st = number of shortest paths from s to t,
                  σ_st(v) = those paths that pass through v.

            High BC = node is a chokepoint in the supply chain.
            Disrupting a high-BC node blocks many inter-supplier routes.

        Returns:
            Top N nodes by betweenness centrality + bottleneck classification.
        """
        bc = nx.betweenness_centrality(G, normalized=normalized, weight="risk_weight")

        nodes = [
            {
                "node_id":      nid,
                "label":        G.nodes[nid].get("label", nid),
                "node_type":    G.nodes[nid].get("node_type", "unknown"),
                "risk_score":   G.nodes[nid].get("risk_score", 0.0),
                "betweenness":  round(score, 4),
                "is_bottleneck": score >= 0.10,
            }
            for nid, score in bc.items()
        ]
        nodes.sort(key=lambda x: x["betweenness"], reverse=True)

        return {
            "algorithm":          "BetweennessCentrality",
            "top_nodes":          nodes[:top_n],
            "bottleneck_nodes":   [n for n in nodes if n["is_bottleneck"]],
            "bottleneck_count":   sum(1 for n in nodes if n["is_bottleneck"]),
            "normalized":         normalized,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Descendants — Full Impact Propagation
    # ─────────────────────────────────────────────────────────────────────────

    def descendants(
        self,
        G: nx.DiGraph,
        node: str,
    ) -> Dict[str, Any]:
        """
        All nodes reachable from `node` via directed edges.

        Formula:
            descendants(G, v) = all nodes reachable from v via directed paths.
            Uses NetworkX's built-in transitive closure (DFS-based).

            Used for: "If TSMC goes offline, which products are affected?"

        Returns:
            {
              "source": str,
              "descendants": [{"node_id", "node_type", "risk_score", "label"}],
              "total_descendants": int,
              "by_type": {node_type: count, ...},
            }
        """
        if not G.has_node(node):
            return {"error": f"Node '{node}' not found", "source": node}

        try:
            desc_set: Set[str] = nx.descendants(G, node)
        except Exception as e:
            return {"error": str(e), "source": node}

        desc_nodes = [
            {
                "node_id":    nid,
                "label":      G.nodes[nid].get("label", nid),
                "node_type":  G.nodes[nid].get("node_type", "unknown"),
                "risk_score": G.nodes[nid].get("risk_score", 0.0),
                "status":     G.nodes[nid].get("status", "unknown"),
            }
            for nid in desc_set if G.has_node(nid)
        ]
        desc_nodes.sort(key=lambda x: x["risk_score"], reverse=True)

        by_type: Dict[str, int] = {}
        for n in desc_nodes:
            nt = n["node_type"]
            by_type[nt] = by_type.get(nt, 0) + 1

        return {
            "algorithm":         "Descendants",
            "source":            node,
            "source_label":      G.nodes[node].get("label", node) if G.has_node(node) else node,
            "descendants":       desc_nodes,
            "total_descendants": len(desc_nodes),
            "by_type":           by_type,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 7. Ancestors — Upstream Dependency Tracing
    # ─────────────────────────────────────────────────────────────────────────

    def ancestors(
        self,
        G: nx.DiGraph,
        node: str,
    ) -> Dict[str, Any]:
        """
        All nodes from which `node` is reachable (upstream dependencies).

        Used for: "What does Product X depend on upstream?"

        Returns:
            {"source", "ancestors": [list], "total_ancestors": int, "by_type": {}}
        """
        if not G.has_node(node):
            return {"error": f"Node '{node}' not found", "source": node}

        try:
            anc_set: Set[str] = nx.ancestors(G, node)
        except Exception as e:
            return {"error": str(e), "source": node}

        anc_nodes = [
            {
                "node_id":    nid,
                "label":      G.nodes[nid].get("label", nid),
                "node_type":  G.nodes[nid].get("node_type", "unknown"),
                "risk_score": G.nodes[nid].get("risk_score", 0.0),
                "status":     G.nodes[nid].get("status", "unknown"),
            }
            for nid in anc_set if G.has_node(nid)
        ]
        anc_nodes.sort(key=lambda x: x["risk_score"], reverse=True)

        by_type: Dict[str, int] = {}
        for n in anc_nodes:
            nt = n["node_type"]
            by_type[nt] = by_type.get(nt, 0) + 1

        return {
            "algorithm":      "Ancestors",
            "source":         node,
            "source_label":   G.nodes[node].get("label", node) if G.has_node(node) else node,
            "ancestors":      anc_nodes,
            "total_ancestors": len(anc_nodes),
            "by_type":        by_type,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 8. Blast Radius Analysis — BFS + Risk Score Propagation
    # ─────────────────────────────────────────────────────────────────────────

    def blast_radius(
        self,
        G: nx.DiGraph,
        disrupted_node: str,
        max_depth: int = 5,
    ) -> Dict[str, Any]:
        """
        Full blast-radius analysis from a disrupted node.

        Algorithm:
            1. BFS from disrupted_node (up to max_depth hops)
            2. For each reachable node at depth d:
               impact_score = source_risk_score × decay_factor^d
               where decay_factor = 0.75 (25% decay per hop)
            3. Classify each impacted node as DIRECT (d=1) or INDIRECT (d>1)
            4. Sum total business impact = Σ impact_scores

        Returns:
            {
              "disrupted_node": str,
              "direct_impacts": [...],   # depth 1
              "indirect_impacts": [...], # depth 2+
              "total_nodes_impacted": int,
              "total_business_impact": float,
              "blast_radius_score": float,  # 0-100 severity
              "critical_downstream": [...], # risk_score > 70
            }
        """
        if not G.has_node(disrupted_node):
            return {"error": f"Node '{disrupted_node}' not found"}

        source_risk = G.nodes[disrupted_node].get("risk_score", 50.0)
        decay_factor = 0.75

        # BFS with depth tracking
        visited: Dict[str, int] = {disrupted_node: 0}
        queue = [(disrupted_node, 0)]

        while queue:
            node, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            for neighbor in G.successors(node):
                if neighbor not in visited:
                    visited[neighbor] = depth + 1
                    queue.append((neighbor, depth + 1))

        # Remove the source node itself
        visited.pop(disrupted_node, None)

        # Calculate impact for each node
        impacted_nodes = []
        total_impact = 0.0

        for nid, depth in visited.items():
            if not G.has_node(nid):
                continue
            node_attrs  = G.nodes[nid]
            node_risk   = node_attrs.get("risk_score", 0.0)
            impact_score = source_risk * (decay_factor ** depth)
            effective_risk = min(100.0, max(node_risk, impact_score))
            total_impact  += impact_score

            impacted_nodes.append({
                "node_id":       nid,
                "label":         node_attrs.get("label", nid),
                "node_type":     node_attrs.get("node_type", "unknown"),
                "depth":         depth,
                "impact_type":   "DIRECT" if depth == 1 else "INDIRECT",
                "base_risk":     round(node_risk, 2),
                "impact_score":  round(impact_score, 2),
                "effective_risk": round(effective_risk, 2),
                "status":        node_attrs.get("status", "unknown"),
            })

        impacted_nodes.sort(key=lambda x: x["impact_score"], reverse=True)

        direct_impacts   = [n for n in impacted_nodes if n["impact_type"] == "DIRECT"]
        indirect_impacts = [n for n in impacted_nodes if n["impact_type"] == "INDIRECT"]
        critical_downstream = [n for n in impacted_nodes if n["effective_risk"] >= 70.0]

        # Blast radius score: normalized (0–100)
        blast_radius_score = min(100.0, (total_impact / max(1, len(impacted_nodes))))

        return {
            "algorithm":             "BlastRadius",
            "disrupted_node":        disrupted_node,
            "disrupted_label":       G.nodes[disrupted_node].get("label", disrupted_node),
            "source_risk_score":     source_risk,
            "direct_impacts":        direct_impacts,
            "indirect_impacts":      indirect_impacts,
            "total_nodes_impacted":  len(impacted_nodes),
            "total_business_impact": round(total_impact, 2),
            "blast_radius_score":    round(blast_radius_score, 2),
            "critical_downstream":   critical_downstream,
            "max_depth":             max_depth,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 9. Critical Path — Highest-Risk Procurement Route
    # ─────────────────────────────────────────────────────────────────────────

    def critical_path(
        self,
        G: nx.DiGraph,
        source: str,
        target: str,
    ) -> Dict[str, Any]:
        """
        Identifies the critical (highest-risk-weight) path from source to target.

        Strategy:
            1. Run Dijkstra with inverted weights (1 - risk_weight) to find
               the MAX-risk path (the most dangerous procurement route).
            2. Also run standard Dijkstra to find the SAFEST route.
            3. Return both for comparison.

        Returns:
            {
              "critical_path": [...],       # highest-risk route nodes
              "safe_path": [...],           # lowest-risk route nodes
              "critical_path_score": float, # total risk weight of critical path
              "safe_path_score": float,
              "risk_difference": float,
            }
        """
        if not G.has_node(source) or not G.has_node(target):
            return {"error": "Source or target node not found", "reachable": False}

        # Add inverted weight to find max-risk path via Dijkstra
        G_inv = G.copy()
        for u, v, data in G_inv.edges(data=True):
            rw = data.get("risk_weight", 0.5)
            G_inv.edges[u, v]["inv_risk_weight"] = max(0.001, 1.0 - rw)

        try:
            # Safest path (lowest risk weight)
            safe_path   = nx.dijkstra_path(G, source, target, weight="risk_weight")
            safe_cost   = nx.dijkstra_path_length(G, source, target, weight="risk_weight")

            # Critical path (highest risk weight via inverted Dijkstra)
            crit_path   = nx.dijkstra_path(G_inv, source, target, weight="inv_risk_weight")
            crit_cost   = sum(
                G.edges[crit_path[i], crit_path[i + 1]].get("risk_weight", 0.5)
                for i in range(len(crit_path) - 1)
            )

            return {
                "algorithm":          "CriticalPath",
                "source":             source,
                "target":             target,
                "safe_path":          safe_path,
                "safe_path_labels":   [G.nodes[n].get("label", n) for n in safe_path if G.has_node(n)],
                "safe_path_cost":     round(safe_cost, 4),
                "critical_path":      crit_path,
                "critical_path_labels": [G.nodes[n].get("label", n) for n in crit_path if G.has_node(n)],
                "critical_path_cost": round(crit_cost, 4),
                "risk_difference":    round(abs(crit_cost - safe_cost), 4),
                "reachable":          True,
            }
        except nx.NetworkXNoPath:
            return {
                "algorithm": "CriticalPath",
                "source":    source,
                "target":    target,
                "reachable": False,
                "error":     "No path found",
            }

    # ─────────────────────────────────────────────────────────────────────────
    # 10. Supplier Connections — all direct connections of a supplier node
    # ─────────────────────────────────────────────────────────────────────────

    def supplier_connections(
        self,
        G: nx.DiGraph,
        supplier_node: str,
    ) -> Dict[str, Any]:
        """
        Full connection profile for a supplier node.

        Returns: upstream (what the supplier depends on) + downstream
                 (what depends on the supplier) + peer country nodes.
        """
        if not G.has_node(supplier_node):
            return {"error": f"Node '{supplier_node}' not found"}

        def node_info(nid: str) -> Dict:
            a = G.nodes.get(nid, {})
            return {
                "node_id":   nid,
                "label":     a.get("label", nid),
                "node_type": a.get("node_type", "unknown"),
                "risk_score": a.get("risk_score", 0.0),
                "status":    a.get("status", "unknown"),
            }

        downstream = [node_info(n) for n in G.successors(supplier_node)]
        upstream   = [node_info(n) for n in G.predecessors(supplier_node)]

        return {
            "algorithm":        "SupplierConnections",
            "supplier_node":    supplier_node,
            "supplier_label":   G.nodes[supplier_node].get("label", supplier_node),
            "risk_score":       G.nodes[supplier_node].get("risk_score", 0.0),
            "downstream":       downstream,
            "upstream":         upstream,
            "downstream_count": len(downstream),
            "upstream_count":   len(upstream),
            "total_connections": len(downstream) + len(upstream),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 11. Full Graph Statistics
    # ─────────────────────────────────────────────────────────────────────────

    def graph_stats(self, G: nx.DiGraph) -> Dict[str, Any]:
        """
        Compute a full statistical summary of the supply chain graph.

        Returns:
            {
              "total_nodes", "total_edges",
              "avg_degree", "density",
              "is_dag", "weakly_connected_components",
              "risk_score_distribution": {LOW/MED/HIGH/CRITICAL: count},
              "top_risk_nodes": top 5 by risk_score
            }
        """
        node_count = G.number_of_nodes()
        edge_count = G.number_of_edges()

        degrees = [d for _, d in G.degree()]
        avg_degree = sum(degrees) / len(degrees) if degrees else 0.0

        risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        all_nodes_sorted = []
        for nid, attrs in G.nodes(data=True):
            rs = attrs.get("risk_score", 0.0)
            if rs >= 85:
                risk_dist["CRITICAL"] += 1
            elif rs >= 67:
                risk_dist["HIGH"] += 1
            elif rs >= 33:
                risk_dist["MEDIUM"] += 1
            else:
                risk_dist["LOW"] += 1
            all_nodes_sorted.append({"node_id": nid, "label": attrs.get("label", nid), "risk_score": rs})

        all_nodes_sorted.sort(key=lambda x: x["risk_score"], reverse=True)

        return {
            "total_nodes":   node_count,
            "total_edges":   edge_count,
            "avg_degree":    round(avg_degree, 2),
            "density":       round(nx.density(G), 4),
            "is_directed":   nx.is_directed(G),
            "is_dag":        nx.is_directed_acyclic_graph(G),
            "weakly_connected_components": nx.number_weakly_connected_components(G),
            "risk_score_distribution": risk_dist,
            "top_risk_nodes": all_nodes_sorted[:5],
        }


# Module-level singleton
graph_algorithms = GraphAlgorithms()
