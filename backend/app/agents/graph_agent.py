"""
GraphAgent — Phase 5: Knowledge Graph Agent (REAL implementation)

Replaces GraphAgentStub. Runs the full graph pipeline:
  1. Build DiGraph (seed + risk_assessments overlay + news_events overlay)
  2. Run all algorithms (BFS, DFS, Dijkstra, Centrality, Blast Radius)
  3. Serialize for React Flow UI
  4. Update in-memory graph_store singleton
  5. Persist graph_snapshot to DB
  6. Return graph_snapshot dict to WorkflowState

Data contract (WorkflowState.graph_snapshot):
  {
    "execution_id":       str,
    "updated_at":         str (ISO),
    "graph_stats":        dict,   # node/edge counts, density, DAG check
    "react_flow":         dict,   # nodes + edges for UI
    "centrality":         dict,   # SPOF detection results
    "betweenness":        dict,   # bottleneck detection
    "blast_radius_report": dict,  # multi-node blast analysis
    "top_risk_nodes":     list,   # top 10 highest-risk nodes
    "spof_nodes":         list,   # single points of failure
    "critical_paths":     list,   # key Dijkstra paths
  }
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.orchestrator.state import WorkflowState

logger = logging.getLogger("agent.graph")


class GraphAgent(BaseAgent):
    """
    Phase 5 Knowledge Graph Agent.

    Consumes:
      - state["risk_assessments"]  (Phase 4 output)
      - state["news_events"]       (Phase 3 output)

    Produces:
      - state["graph_snapshot"]    (DiGraph analysis for Phase 6+)
    """

    agent_id    = "graph_agent"
    description = (
        "Builds a NetworkX DiGraph of Supplier → Component → Product dependencies. "
        "Runs BFS blast-radius tracing, DFS dependency traversal, Dijkstra critical-path, "
        "degree centrality SPOF detection, and betweenness bottleneck analysis. "
        "Serializes the graph to React Flow JSON for the UI."
    )
    version = "1.0.0"  # Phase 5 real implementation

    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Run the complete graph pipeline.

        Returns a partial WorkflowState dict updating graph_snapshot.
        """
        from app.graph.builder import SupplyChainGraphBuilder
        from app.graph.algorithms import GraphAlgorithms
        from app.graph.analyzer import BlastRadiusAnalyzer
        from app.graph.serializer import ReactFlowSerializer
        from app.graph.snapshot import graph_store

        risk_assessments: List[Dict[str, Any]] = state.get("risk_assessments", [])
        news_events:      List[Dict[str, Any]] = state.get("news_events", [])
        execution_id:     str                  = state.get("execution_id", "")

        logger.info(
            f"[graph_agent] Building graph — "
            f"risk_assessments={len(risk_assessments)}, news_events={len(news_events)}"
        )

        # ── Step 1: Build DiGraph ─────────────────────────────────────────────
        builder = SupplyChainGraphBuilder()
        G = builder.build(
            risk_assessments=risk_assessments,
            news_events=news_events,
        )

        # ── Step 2: Run algorithms ────────────────────────────────────────────
        algo = GraphAlgorithms()

        graph_stats    = algo.graph_stats(G)
        centrality     = algo.degree_centrality(G, top_n=20, spof_threshold=0.15)
        betweenness    = algo.betweenness_centrality(G, top_n=10)

        # ── Step 3: Blast radius on top high-risk nodes ───────────────────────
        blast_analyzer = BlastRadiusAnalyzer()
        blast_report   = blast_analyzer.analyze_all(G, max_depth=4, top_n=10)

        # ── Step 4: Key critical paths (Supplier → Product) ───────────────────
        critical_paths = self._compute_key_critical_paths(G, algo)

        # ── Step 5: React Flow serialization ──────────────────────────────────
        serializer  = ReactFlowSerializer()
        react_flow  = serializer.serialize(G, max_nodes=150)

        # ── Step 6: Update in-memory store ────────────────────────────────────
        snapshot: Dict[str, Any] = {
            "execution_id":        execution_id,
            "updated_at":          datetime.now(timezone.utc).isoformat(),
            "graph_stats":         graph_stats,
            "react_flow":          react_flow,
            "centrality":          centrality,
            "betweenness":         betweenness,
            "blast_radius_report": blast_report,
            "top_risk_nodes":      graph_stats.get("top_risk_nodes", []),
            "spof_nodes":          centrality.get("spof_nodes", []),
            "critical_paths":      critical_paths,
            "node_count":          G.number_of_nodes(),
            "edge_count":          G.number_of_edges(),
        }

        await graph_store.update(G, execution_id, snapshot)

        # ── Step 7: Persist to DB ─────────────────────────────────────────────
        self._persist_snapshot(snapshot)

        logger.info(
            f"[graph_agent] Done — "
            f"nodes={G.number_of_nodes()}, edges={G.number_of_edges()}, "
            f"spof_count={centrality.get('spof_count', 0)}, "
            f"blast_impacted={blast_report.get('total_nodes_impacted', 0)}"
        )

        return {
            "graph_snapshot":   snapshot,
            "completed_agents": ["graph_agent"],
            "failed_agents":    [],
            "errors":           [],
            "agent_results": [{
                "agent_id": "graph_agent",
                "status":   "success",
                "data": {
                    "node_count":         G.number_of_nodes(),
                    "edge_count":         G.number_of_edges(),
                    "spof_count":         centrality.get("spof_count", 0),
                    "blast_impacted":     blast_report.get("total_nodes_impacted", 0),
                    "critical_paths":     len(critical_paths),
                    "risk_distribution":  graph_stats.get("risk_score_distribution", {}),
                },
                "error":       None,
                "duration_ms": 0,
                "retry_count": 0,
                "timestamp":   datetime.now(timezone.utc).isoformat(),
            }],
        }

    def _compute_key_critical_paths(
        self, G: Any, algo: Any
    ) -> List[Dict[str, Any]]:
        """
        Compute Dijkstra critical paths for the most important
        supplier → product pairs. Returns top 5 paths.
        """
        key_pairs = [
            ("supplier::TSMC",    "product::SMARTPHONE"),
            ("supplier::TSMC",    "product::SERVER"),
            ("supplier::CATL",    "product::EV_CAR"),
            ("supplier::BOSCH",   "product::EV_CAR"),
            ("supplier::SAMSUNG", "product::LAPTOP"),
        ]
        paths = []
        for src, tgt in key_pairs:
            result = algo.dijkstra_path(G, src, tgt, weight="risk_weight")
            if result.get("reachable"):
                paths.append({
                    "source":      src,
                    "target":      tgt,
                    "source_label": G.nodes[src].get("label", src) if G.has_node(src) else src,
                    "target_label": G.nodes[tgt].get("label", tgt) if G.has_node(tgt) else tgt,
                    "path":        result.get("path", []),
                    "path_labels": result.get("path_labels", []),
                    "total_cost":  result.get("total_cost", 0),
                    "hop_count":   result.get("hop_count", 0),
                })
        return paths

    def _persist_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """
        Persist graph snapshot summary to PostgreSQL.
        Uses the graph_snapshots table (graceful no-op if table doesn't exist yet).
        """
        try:
            from app.db.session import SessionLocal
            from app.db.models.graph_snapshot import GraphSnapshot

            db = SessionLocal()
            try:
                row = GraphSnapshot(
                    execution_id=    snapshot.get("execution_id", ""),
                    node_count=      snapshot.get("node_count", 0),
                    edge_count=      snapshot.get("edge_count", 0),
                    spof_count=      len(snapshot.get("spof_nodes", [])),
                    blast_impacted=  snapshot.get("blast_radius_report", {}).get("total_nodes_impacted", 0),
                    critical_paths=  len(snapshot.get("critical_paths", [])),
                    react_flow_json= snapshot.get("react_flow"),
                    centrality_json= snapshot.get("centrality"),
                    blast_radius_json= snapshot.get("blast_radius_report"),
                    graph_stats_json= snapshot.get("graph_stats"),
                )
                db.add(row)
                db.commit()
                logger.info(f"[graph_agent] Persisted snapshot to DB")
            except Exception as e:
                logger.warning(f"[graph_agent] DB persist failed (non-fatal): {e}")
                try:
                    db.rollback()
                except Exception:
                    pass
            finally:
                db.close()
        except ImportError:
            logger.debug("[graph_agent] DB model not available yet — skipping persistence")
