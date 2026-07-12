"""
Phase 5: Knowledge Graph — DiGraph Builder

Constructs and maintains the NetworkX DiGraph from:
  1. Seed topology (SEED_NODES / SEED_EDGES from nodes.py)
  2. Phase 4 risk_assessments — adds RiskEvent nodes and AFFECTED_BY edges
  3. Phase 3 news_events — updates node risk_scores from live news

Graph design:
  - One DiGraph per workflow run (built fresh + seeded, then layered with live data)
  - Node attributes stored as dict on each NetworkX node:
      G.nodes[node_id] = {"node_type": ..., "risk_score": ..., ...}
  - Edge attributes stored as dict on each NetworkX edge:
      G.edges[src, tgt] = {"edge_type": ..., "weight": ..., "risk_weight": ...}
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import networkx as nx

from app.graph.nodes import (
    SEED_EDGES,
    SEED_NODES,
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeStatus,
    NodeType,
)

logger = logging.getLogger("graph.builder")


class SupplyChainGraphBuilder:
    """
    Builds a NetworkX DiGraph representing the full supply chain dependency network.

    Usage:
        builder = SupplyChainGraphBuilder()
        G = builder.build(risk_assessments=..., news_events=...)
        stats = builder.stats(G)
    """

    def build(
        self,
        risk_assessments: Optional[List[Dict[str, Any]]] = None,
        news_events: Optional[List[Dict[str, Any]]] = None,
    ) -> nx.DiGraph:
        """
        Construct the full DiGraph.

        Steps:
          1. Create empty DiGraph
          2. Add all seed nodes (suppliers, components, products, countries)
          3. Add all seed edges (dependency relationships)
          4. Overlay Phase 4 risk assessments (update risk_scores, add RiskEvent nodes)
          5. Overlay Phase 3 news events (fine-tune risk_scores from live data)
          6. Classify node statuses based on final risk_scores

        Returns:
            nx.DiGraph with all nodes and edges populated
        """
        G = nx.DiGraph()
        G.graph["name"] = "SupplyChield AI — Supply Chain Graph"
        G.graph["version"] = "phase5"

        # ── Step 2: Seed nodes ────────────────────────────────────────────────
        self._add_seed_nodes(G)

        # ── Step 3: Seed edges ────────────────────────────────────────────────
        self._add_seed_edges(G)

        # ── Step 4: Risk assessment overlay ──────────────────────────────────
        if risk_assessments:
            self._overlay_risk_assessments(G, risk_assessments)

        # ── Step 5: News event overlay ────────────────────────────────────────
        if news_events:
            self._overlay_news_events(G, news_events)

        # ── Step 6: Classify node statuses ────────────────────────────────────
        self._classify_statuses(G)

        logger.info(
            f"[graph_builder] Built graph: "
            f"{G.number_of_nodes()} nodes, {G.number_of_edges()} edges"
        )
        return G

    # ── Private helpers ───────────────────────────────────────────────────────

    def _add_seed_nodes(self, G: nx.DiGraph) -> None:
        for node in SEED_NODES:
            G.add_node(node.node_id, **node.to_dict())

    def _add_seed_edges(self, G: nx.DiGraph) -> None:
        for edge in SEED_EDGES:
            if G.has_node(edge.source_id) and G.has_node(edge.target_id):
                G.add_edge(
                    edge.source_id,
                    edge.target_id,
                    **edge.to_dict(),
                )
            else:
                logger.debug(
                    f"[graph_builder] Skipping edge {edge.source_id} → {edge.target_id} "
                    f"(missing node)"
                )

    def _overlay_risk_assessments(
        self, G: nx.DiGraph, risk_assessments: List[Dict[str, Any]]
    ) -> None:
        """
        For each risk assessment:
          1. Add a RiskEvent node with the assessment data
          2. Link it to AFFECTED_BY edges on matching suppliers/countries
          3. Update the risk_score on matching country/supplier nodes
        """
        for ra in risk_assessments:
            assessment_id = ra.get("assessment_id", "")
            risk_score    = float(ra.get("risk_score", 0.0))
            risk_level    = ra.get("risk_level", "LOW")
            title         = ra.get("title", "Unknown Event")[:80]
            event_type    = ra.get("event_type", "UNKNOWN")
            countries     = ra.get("countries", []) or []
            industries    = ra.get("industries", []) or []

            if not assessment_id:
                continue

            # Add RiskEvent node
            risk_node_id = f"risk::{assessment_id[:16]}"
            G.add_node(
                risk_node_id,
                node_id=risk_node_id,
                node_type=NodeType.RISK_EVENT.value,
                label=title,
                risk_score=risk_score,
                risk_level=risk_level,
                event_type=event_type,
                tier=None,
                country_code=countries[0] if countries else None,
                status=(
                    NodeStatus.CRITICAL.value if risk_score >= 85
                    else NodeStatus.AT_RISK.value if risk_score >= 33
                    else NodeStatus.ACTIVE.value
                ),
                metadata={"assessment_id": assessment_id, "industries": industries},
            )

            # ── Update risk_scores on affected country nodes ───────────────────
            for iso_code in countries:
                country_node_id = f"country::{iso_code.upper()}"
                if G.has_node(country_node_id):
                    existing = G.nodes[country_node_id].get("risk_score", 0.0)
                    # Take the max of existing vs incoming
                    G.nodes[country_node_id]["risk_score"] = max(existing, risk_score)

                    # Add AFFECTED_BY edge
                    G.add_edge(
                        country_node_id,
                        risk_node_id,
                        source_id=country_node_id,
                        target_id=risk_node_id,
                        edge_type=EdgeType.AFFECTED_BY.value,
                        weight=1.0,
                        risk_weight=risk_score / 100.0,
                        label=f"risk:{risk_level}",
                        metadata={},
                    )

            # ── Propagate risk to suppliers located in affected countries ──────
            for node_id, attrs in list(G.nodes(data=True)):
                if attrs.get("node_type") != NodeType.SUPPLIER.value:
                    continue
                supplier_country = attrs.get("country_code", "")
                if supplier_country.upper() in [c.upper() for c in countries]:
                    existing = attrs.get("risk_score", 0.0)
                    # Supplier risk = max(existing, 70% of event risk)
                    propagated = risk_score * 0.70
                    if propagated > existing:
                        G.nodes[node_id]["risk_score"] = round(propagated, 2)
                    # Add AFFECTED_BY edge to RiskEvent
                    if not G.has_edge(node_id, risk_node_id):
                        G.add_edge(
                            node_id, risk_node_id,
                            source_id=node_id,
                            target_id=risk_node_id,
                            edge_type=EdgeType.AFFECTED_BY.value,
                            weight=1.0,
                            risk_weight=risk_score / 100.0,
                            label=f"risk:{risk_level}",
                            metadata={},
                        )

    def _overlay_news_events(
        self, G: nx.DiGraph, news_events: List[Dict[str, Any]]
    ) -> None:
        """
        Gently update node risk_scores from news event severity,
        keeping the Phase 4 risk_assessment values as the primary source.
        """
        for event in news_events:
            severity_score = float(event.get("severity_score", 0.0))
            if severity_score < 5.0:
                continue  # Only apply significant events

            countries = event.get("countries") or event.get("country_codes") or []
            for iso_code in countries:
                country_node_id = f"country::{iso_code.upper()}"
                if G.has_node(country_node_id):
                    existing = G.nodes[country_node_id].get("risk_score", 0.0)
                    news_score = severity_score * 10  # 0-10 → 0-100
                    if news_score > existing:
                        G.nodes[country_node_id]["risk_score"] = round(news_score, 2)

    def _classify_statuses(self, G: nx.DiGraph) -> None:
        """Update the status attribute on every node based on final risk_score."""
        for node_id in G.nodes:
            risk_score = G.nodes[node_id].get("risk_score", 0.0)
            if risk_score >= 85:
                G.nodes[node_id]["status"] = NodeStatus.CRITICAL.value
            elif risk_score >= 67:
                G.nodes[node_id]["status"] = NodeStatus.AT_RISK.value
            elif risk_score >= 33:
                G.nodes[node_id]["status"] = NodeStatus.ACTIVE.value
            else:
                G.nodes[node_id]["status"] = NodeStatus.ACTIVE.value

    def add_node(self, G: nx.DiGraph, node: GraphNode) -> None:
        """Add or update a single node."""
        G.add_node(node.node_id, **node.to_dict())

    def add_edge(self, G: nx.DiGraph, edge: GraphEdge) -> None:
        """Add a single edge (both nodes must exist)."""
        if G.has_node(edge.source_id) and G.has_node(edge.target_id):
            G.add_edge(edge.source_id, edge.target_id, **edge.to_dict())

    def stats(self, G: nx.DiGraph) -> Dict[str, Any]:
        """Return basic graph statistics."""
        node_type_counts: Dict[str, int] = {}
        edge_type_counts: Dict[str, int] = {}

        for _, attrs in G.nodes(data=True):
            nt = attrs.get("node_type", "unknown")
            node_type_counts[nt] = node_type_counts.get(nt, 0) + 1

        for _, _, attrs in G.edges(data=True):
            et = attrs.get("edge_type", "unknown")
            edge_type_counts[et] = edge_type_counts.get(et, 0) + 1

        return {
            "total_nodes":       G.number_of_nodes(),
            "total_edges":       G.number_of_edges(),
            "is_directed":       nx.is_directed(G),
            "is_dag":            nx.is_directed_acyclic_graph(G),
            "node_type_counts":  node_type_counts,
            "edge_type_counts":  edge_type_counts,
            "weakly_connected":  nx.number_weakly_connected_components(G),
        }
