"""
Phase 5: Knowledge Graph — React Flow Serializer

Converts a NetworkX DiGraph into the exact JSON format consumed by
React Flow (frontend graph visualization library).

React Flow format:
  nodes: [{ id, type, position, data: {...} }]
  edges: [{ id, source, target, type, label, data: {...} }]

Node types map to custom React Flow node components:
  supplier   → "supplierNode"
  component  → "componentNode"
  product    → "productNode"
  country    → "countryNode"
  risk_event → "riskEventNode"

Position layout uses a layered left-to-right strategy:
  Layer 0: Countries
  Layer 1: Suppliers
  Layer 2: Components
  Layer 3: Products
  Layer 4: Risk Events
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional

import networkx as nx

logger = logging.getLogger("graph.serializer")

# ── Layout constants ──────────────────────────────────────────────────────────
LAYER_X: Dict[str, int] = {
    "country":     0,
    "supplier":    300,
    "component":   600,
    "product":     900,
    "risk_event":  1200,
}
NODE_Y_SPACING = 120   # vertical gap between nodes in the same layer
NODE_X_JITTER  = 50    # slight X variation within a layer


class ReactFlowSerializer:
    """
    Converts a NetworkX DiGraph into a React Flow-compatible JSON structure.

    Usage:
        serializer = ReactFlowSerializer()
        rf_data = serializer.serialize(G)
        # rf_data = {"nodes": [...], "edges": [...], "metadata": {...}}
    """

    def serialize(
        self,
        G: nx.DiGraph,
        filter_node_types: Optional[List[str]] = None,
        max_nodes: int = 200,
    ) -> Dict[str, Any]:
        """
        Serialize the full graph to React Flow JSON.

        Args:
            filter_node_types: If set, only include nodes of these types.
            max_nodes: Hard limit on nodes returned (prevents UI crash on huge graphs).

        Returns:
            {"nodes": [...], "edges": [...], "metadata": {...}}
        """
        # ── Filter and limit nodes ────────────────────────────────────────────
        all_nodes = list(G.nodes(data=True))

        if filter_node_types:
            all_nodes = [
                (nid, attrs) for nid, attrs in all_nodes
                if attrs.get("node_type", "") in filter_node_types
            ]

        # Sort by risk_score descending so highest-risk nodes are included first
        all_nodes.sort(key=lambda x: x[1].get("risk_score", 0), reverse=True)
        all_nodes = all_nodes[:max_nodes]
        included_ids = {nid for nid, _ in all_nodes}

        # ── Compute layout positions ──────────────────────────────────────────
        positions = self._compute_layout(all_nodes)

        # ── Build React Flow nodes ────────────────────────────────────────────
        rf_nodes = []
        for nid, attrs in all_nodes:
            x, y = positions.get(nid, (0, 0))
            node_type = attrs.get("node_type", "unknown")
            risk_score = attrs.get("risk_score", 0.0)

            rf_nodes.append({
                "id":       nid,
                "type":     self._rf_node_type(node_type),
                "position": {"x": x, "y": y},
                "data": {
                    "node_id":      nid,
                    "label":        attrs.get("label", nid),
                    "node_type":    node_type,
                    "risk_score":   round(risk_score, 2),
                    "risk_level":   self._score_to_level(risk_score),
                    "status":       attrs.get("status", "active"),
                    "tier":         attrs.get("tier"),
                    "country_code": attrs.get("country_code"),
                    "metadata":     attrs.get("metadata", {}),
                    "color":        self._risk_color(risk_score),
                },
                "style": {
                    "border": f"2px solid {self._risk_color(risk_score)}",
                },
            })

        # ── Build React Flow edges ────────────────────────────────────────────
        rf_edges = []
        for src, tgt, edata in G.edges(data=True):
            if src not in included_ids or tgt not in included_ids:
                continue

            edge_type = edata.get("edge_type", "unknown")
            risk_weight = edata.get("risk_weight", 0.5)
            edge_id = f"edge-{src[:20]}-{tgt[:20]}"

            rf_edges.append({
                "id":         edge_id,
                "source":     src,
                "target":     tgt,
                "type":       "smoothstep",
                "label":      edata.get("label", edge_type),
                "animated":   risk_weight >= 0.5,   # animate high-risk edges
                "style": {
                    "stroke":      self._edge_color(edge_type, risk_weight),
                    "strokeWidth": self._edge_width(risk_weight),
                },
                "data": {
                    "edge_type":   edge_type,
                    "weight":      edata.get("weight", 1.0),
                    "risk_weight": round(risk_weight, 3),
                },
            })

        # ── Metadata ──────────────────────────────────────────────────────────
        metadata = {
            "total_nodes": len(rf_nodes),
            "total_edges": len(rf_edges),
            "graph_version": G.graph.get("version", "unknown"),
            "truncated": len(list(G.nodes())) > max_nodes,
        }

        return {
            "nodes":    rf_nodes,
            "edges":    rf_edges,
            "metadata": metadata,
        }

    def serialize_subgraph(
        self,
        G: nx.DiGraph,
        center_node: str,
        radius: int = 2,
    ) -> Dict[str, Any]:
        """
        Serialize only the neighborhood of `center_node` within `radius` hops.
        Ideal for focused "node detail" views in the React UI.
        """
        within_radius = {center_node}
        frontier = {center_node}
        for _ in range(radius):
            next_frontier = set()
            for node in frontier:
                if G.has_node(node):
                    next_frontier.update(G.successors(node))
                    next_frontier.update(G.predecessors(node))
            within_radius.update(next_frontier)
            frontier = next_frontier

        sub = G.subgraph(within_radius)
        return self.serialize(sub)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _compute_layout(
        self, nodes: List[tuple]
    ) -> Dict[str, tuple]:
        """
        Layered left-to-right layout.
        Groups nodes by node_type, positions each layer at a fixed X,
        distributes nodes vertically within each layer.
        """
        layer_buckets: Dict[str, List[str]] = {}
        for nid, attrs in nodes:
            nt = attrs.get("node_type", "unknown")
            if nt not in layer_buckets:
                layer_buckets[nt] = []
            layer_buckets[nt].append(nid)

        positions: Dict[str, tuple] = {}
        for node_type, node_ids in layer_buckets.items():
            x_base = LAYER_X.get(node_type, 1500)
            for i, nid in enumerate(node_ids):
                # Center the column vertically
                y_offset = (i - len(node_ids) / 2) * NODE_Y_SPACING
                positions[nid] = (x_base, int(y_offset))

        return positions

    def _rf_node_type(self, node_type: str) -> str:
        """Map NodeType value to React Flow custom node component name."""
        return {
            "supplier":   "supplierNode",
            "component":  "componentNode",
            "product":    "productNode",
            "country":    "countryNode",
            "risk_event": "riskEventNode",
        }.get(node_type, "default")

    def _score_to_level(self, score: float) -> str:
        if score >= 85:   return "CRITICAL"
        if score >= 67:   return "HIGH"
        if score >= 33:   return "MEDIUM"
        return "LOW"

    def _risk_color(self, score: float) -> str:
        """Return hex color based on risk score for node border/fill."""
        if score >= 85:   return "#ef4444"   # red-500
        if score >= 67:   return "#f97316"   # orange-500
        if score >= 33:   return "#eab308"   # yellow-500
        return "#22c55e"                      # green-500

    def _edge_color(self, edge_type: str, risk_weight: float) -> str:
        """Color edges by type and risk."""
        if edge_type == "affected_by":
            return "#ef4444"
        if risk_weight >= 0.6:
            return "#f97316"
        if risk_weight >= 0.3:
            return "#eab308"
        return "#94a3b8"   # slate-400

    def _edge_width(self, risk_weight: float) -> int:
        if risk_weight >= 0.7: return 3
        if risk_weight >= 0.4: return 2
        return 1


# Module-level singleton
react_flow_serializer = ReactFlowSerializer()
