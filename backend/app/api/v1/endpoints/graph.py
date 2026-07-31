"""
Knowledge Graph REST API Endpoints — Phase 5.

12 endpoints covering the full graph surface area:

  GET  /graph/snapshot           — Latest graph snapshot (React Flow + stats)
  GET  /graph/stats              — Graph statistics summary
  GET  /graph/nodes              — All nodes (filterable by type/risk)
  GET  /graph/nodes/{node_id}    — Single node detail + dependency analysis
  GET  /graph/edges              — All edges (filterable by type)
  POST /graph/bfs                — BFS from a source node
  POST /graph/dfs                — DFS from a source node
  POST /graph/dijkstra           — Dijkstra path between two nodes
  POST /graph/blast-radius       — Blast radius from a disrupted node
  GET  /graph/centrality         — Degree centrality + SPOF list
  GET  /graph/betweenness        — Betweenness centrality + bottlenecks
  POST /graph/search             — Search nodes by name/type
  GET  /graph/critical-paths     — Pre-computed key supplier→product paths
  POST /graph/rebuild            — Rebuild graph from latest risk assessments
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import UserPrincipal, get_current_user

logger = logging.getLogger("api.graph")

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


# ─────────────────────────────────────────────────────────────────────────────
# Request schemas
# ─────────────────────────────────────────────────────────────────────────────

class BFSRequest(BaseModel):
    source:    str
    max_depth: int = 5

class DFSRequest(BaseModel):
    source:    str
    max_depth: int = 5

class DijkstraRequest(BaseModel):
    source: str
    target: str
    weight: str = "risk_weight"

class BlastRadiusRequest(BaseModel):
    disrupted_node: str
    max_depth:      int = 4

class SearchRequest(BaseModel):
    query:       str
    node_type:   Optional[str] = None

class RebuildRequest(BaseModel):
    supplier_tier: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Helper: get current graph (lazy-init if not yet built — never 503)
# ─────────────────────────────────────────────────────────────────────────────

import networkx as nx  # top-level import for lazy-init

def _get_graph() -> nx.DiGraph:
    """Return the live supply chain graph.

    If the in-memory store has not been populated yet (e.g., the orchestrator
    hasn't run since server start), we lazy-initialize an empty DiGraph so the
    snapshot endpoint can immediately run the auto-seeder against the DB rather
    than returning a 503 to the client.
    """
    from app.graph.snapshot import graph_store
    G = graph_store.get_graph()
    if G is None:
        # Initialize an empty directed graph so the seeder can populate it
        G = nx.DiGraph()
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(
                    graph_store.update(G, execution_id="lazy_init", snapshot_data={})
                )
            else:
                loop.run_until_complete(
                    graph_store.update(G, execution_id="lazy_init", snapshot_data={})
                )
        except Exception:
            # Fallback: set graph directly (safe for sync context)
            graph_store._graph = G
        logger.info("[graph] Lazy-initialized empty DiGraph — seeder will populate from DB")
    return G


# ─────────────────────────────────────────────────────────────────────────────
# 1. GET /graph/snapshot — Latest full React Flow snapshot
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/snapshot", summary="Get latest graph snapshot (React Flow JSON + stats)")
def get_graph_snapshot(
    filter_types: Optional[str] = Query(
        default=None,
        description="Comma-separated node types to include: COMPANY,FACTORY,WAREHOUSE,PRODUCT,COMPONENT,SUPPLIER,SHIPMENT,INCIDENT,RECOMMENDATION"
    ),
    max_nodes: int = Query(default=150, ge=10, le=500),
    db: Session = Depends(get_db),
    current_user: UserPrincipal = Depends(get_current_user),
) -> Dict[str, Any]:
    from app.graph.builder import SupplyChainGraphBuilder
    from app.graph.serializer import ReactFlowSerializer
    from app.graph.snapshot import graph_store

    user_id = current_user.user_id
    builder = SupplyChainGraphBuilder()
    G = builder.build_from_db(db, user_id=user_id)

    # Save to global store
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if not loop.is_running():
            graph_store._graph = G
    except Exception:
        graph_store._graph = G

    serializer = ReactFlowSerializer()
    filter_list = [t.strip() for t in filter_types.split(",")] if filter_types else None
    rf_data = serializer.serialize(G, filter_node_types=filter_list, max_nodes=max_nodes)

    is_empty = G.number_of_nodes() == 0

    return {
        "is_empty": is_empty,
        "empty_message": "No supply chain entities available. Complete your company setup and onboard suppliers to begin building your digital twin graph.",
        "store_stats": {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "graph_version": "2.0.0-db",
        },
        "react_flow": rf_data,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. GET /graph/stats — Graph statistics
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/stats", summary="Graph statistics summary")
def get_graph_stats(
    db: Session = Depends(get_db),
    current_user: UserPrincipal = Depends(get_current_user),
) -> Dict[str, Any]:
    from app.graph.builder import SupplyChainGraphBuilder
    from app.graph.algorithms import GraphAlgorithms
    G = SupplyChainGraphBuilder().build_from_db(db, user_id=current_user.user_id)
    return GraphAlgorithms().graph_stats(G)


# ─────────────────────────────────────────────────────────────────────────────
# 3. GET /graph/nodes — All nodes
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/nodes", summary="List all graph nodes")
def list_nodes(
    node_type:     Optional[str]  = Query(default=None, description="Filter by type"),
    min_risk:      Optional[float] = Query(default=None, ge=0, le=100),
    sort_by:       str             = Query(default="risk_score"),
    db:            Session        = Depends(get_db),
    current_user:  UserPrincipal  = Depends(get_current_user),
) -> Dict[str, Any]:
    from app.graph.builder import SupplyChainGraphBuilder
    from app.graph.search import GraphSearch
    G = SupplyChainGraphBuilder().build_from_db(db, user_id=current_user.user_id)

    searcher = GraphSearch()
    if node_type:
        nodes = searcher.get_nodes_by_type(G, node_type, sort_by=sort_by)
    elif min_risk is not None:
        nodes = searcher.get_high_risk_nodes(G, min_risk_score=min_risk)
    else:
        nodes = []
        for nid, attrs in G.nodes(data=True):
            nodes.append({
                "node_id":    nid,
                "label":      attrs.get("label", nid),
                "node_type":  attrs.get("node_type", "unknown"),
                "risk_score": attrs.get("risk_score", 0.0),
                "status":     attrs.get("status", "unknown"),
                "country_code": attrs.get("country_code"),
                "tier":       attrs.get("tier"),
            })
        nodes.sort(key=lambda x: x.get(sort_by, 0), reverse=True)

    return {"total": len(nodes), "nodes": nodes}


# ─────────────────────────────────────────────────────────────────────────────
# 4. GET /graph/nodes/{node_id} — Single node + full dependency analysis
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/nodes/{node_id}", summary="Get single node with full dependency analysis")
def get_node(
    node_id: str,
    db: Session = Depends(get_db),
    current_user: UserPrincipal = Depends(get_current_user),
) -> Dict[str, Any]:
    from app.graph.builder import SupplyChainGraphBuilder
    from app.graph.analyzer import DependencyAnalyzer
    G = SupplyChainGraphBuilder().build_from_db(db, user_id=current_user.user_id)
    return DependencyAnalyzer().analyze_node(G, node_id)


# ─────────────────────────────────────────────────────────────────────────────
# 5. GET /graph/edges — All edges
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/edges", summary="List all graph edges")
def list_edges(
    edge_type: Optional[str] = Query(default=None),
    min_risk_weight: Optional[float] = Query(default=None, ge=0, le=1),
    db: Session = Depends(get_db),
    current_user: UserPrincipal = Depends(get_current_user),
) -> Dict[str, Any]:
    from app.graph.builder import SupplyChainGraphBuilder
    G = SupplyChainGraphBuilder().build_from_db(db, user_id=current_user.user_id)
    edges = []
    for src, tgt, data in G.edges(data=True):
        et = data.get("edge_type", "unknown")
        rw = data.get("risk_weight", 0.5)
        if edge_type and et != edge_type:
            continue
        if min_risk_weight is not None and rw < min_risk_weight:
            continue
        edges.append({
            "source_id":   src,
            "source_label": G.nodes[src].get("label", src) if G.has_node(src) else src,
            "target_id":   tgt,
            "target_label": G.nodes[tgt].get("label", tgt) if G.has_node(tgt) else tgt,
            "edge_type":   et,
            "weight":      data.get("weight", 1.0),
            "risk_weight": round(rw, 3),
        })
    edges.sort(key=lambda x: x["risk_weight"], reverse=True)
    return {"total": len(edges), "edges": edges}


# ─────────────────────────────────────────────────────────────────────────────
# 6. POST /graph/bfs — BFS from source
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/bfs", summary="BFS traversal from source node")
def run_bfs(
    req: BFSRequest,
    db: Session = Depends(get_db),
    current_user: UserPrincipal = Depends(get_current_user),
) -> Dict[str, Any]:
    from app.graph.builder import SupplyChainGraphBuilder
    from app.graph.algorithms import GraphAlgorithms
    G = SupplyChainGraphBuilder().build_from_db(db, user_id=current_user.user_id)
    return GraphAlgorithms().bfs_tree(G, req.source, max_depth=req.max_depth)


# ─────────────────────────────────────────────────────────────────────────────
# 7. POST /graph/dfs — DFS from source
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/dfs", summary="DFS traversal from source node")
def run_dfs(
    req: DFSRequest,
    db: Session = Depends(get_db),
    current_user: UserPrincipal = Depends(get_current_user),
) -> Dict[str, Any]:
    from app.graph.builder import SupplyChainGraphBuilder
    from app.graph.algorithms import GraphAlgorithms
    G = SupplyChainGraphBuilder().build_from_db(db, user_id=current_user.user_id)
    return GraphAlgorithms().dfs_tree(G, req.source, max_depth=req.max_depth)


# ─────────────────────────────────────────────────────────────────────────────
# 8. POST /graph/dijkstra — Dijkstra shortest path
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/dijkstra", summary="Dijkstra shortest path between two nodes")
def run_dijkstra(
    req: DijkstraRequest,
    db: Session = Depends(get_db),
    current_user: UserPrincipal = Depends(get_current_user),
) -> Dict[str, Any]:
    from app.graph.builder import SupplyChainGraphBuilder
    from app.graph.algorithms import GraphAlgorithms
    G = SupplyChainGraphBuilder().build_from_db(db, user_id=current_user.user_id)
    return GraphAlgorithms().dijkstra_path(G, req.source, req.target, weight=req.weight)


# ─────────────────────────────────────────────────────────────────────────────
# 9. POST /graph/blast-radius — Blast radius analysis
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/blast-radius", summary="Blast radius analysis from a disrupted node")
def run_blast_radius(
    req: BlastRadiusRequest,
    db: Session = Depends(get_db),
    current_user: UserPrincipal = Depends(get_current_user),
) -> Dict[str, Any]:
    from app.graph.builder import SupplyChainGraphBuilder
    from app.graph.algorithms import GraphAlgorithms
    G = SupplyChainGraphBuilder().build_from_db(db, user_id=current_user.user_id)
    return GraphAlgorithms().blast_radius(G, req.disrupted_node, max_depth=req.max_depth)


# ─────────────────────────────────────────────────────────────────────────────
# 10. GET /graph/centrality — Degree centrality + SPOF list
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/centrality", summary="Degree centrality analysis + SPOF detection")
def get_centrality(
    top_n:           int   = Query(default=20, ge=1, le=100),
    spof_threshold:  float = Query(default=0.15, ge=0, le=1.0),
) -> Dict[str, Any]:
    G = _get_graph()
    from app.graph.algorithms import GraphAlgorithms
    return GraphAlgorithms().degree_centrality(G, top_n=top_n, spof_threshold=spof_threshold)


# ─────────────────────────────────────────────────────────────────────────────
# 11. GET /graph/betweenness — Betweenness centrality + bottlenecks
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/betweenness", summary="Betweenness centrality + bottleneck nodes")
def get_betweenness(
    top_n: int = Query(default=10, ge=1, le=50),
) -> Dict[str, Any]:
    G = _get_graph()
    from app.graph.algorithms import GraphAlgorithms
    return GraphAlgorithms().betweenness_centrality(G, top_n=top_n)


# ─────────────────────────────────────────────────────────────────────────────
# 12. POST /graph/search — Search nodes
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/search", summary="Search graph nodes by label or ID")
def search_nodes(req: SearchRequest) -> Dict[str, Any]:
    G = _get_graph()
    from app.graph.search import GraphSearch
    return GraphSearch().find_node(G, req.query, search_type=req.node_type)


# ─────────────────────────────────────────────────────────────────────────────
# 13. GET /graph/critical-paths — Pre-computed key Dijkstra paths
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/critical-paths", summary="Pre-computed critical supplier→product paths")
def get_critical_paths() -> Dict[str, Any]:
    G = _get_graph()
    from app.graph.algorithms import GraphAlgorithms

    algo = GraphAlgorithms()
    key_pairs = [
        ("supplier::TSMC",    "product::SMARTPHONE"),
        ("supplier::TSMC",    "product::SERVER"),
        ("supplier::CATL",    "product::EV_CAR"),
        ("supplier::BOSCH",   "product::EV_CAR"),
        ("supplier::SAMSUNG", "product::LAPTOP"),
        ("supplier::SAMSUNG", "product::SMARTPHONE"),
    ]
    paths = []
    for src, tgt in key_pairs:
        result = algo.dijkstra_path(G, src, tgt, weight="risk_weight")
        if result.get("reachable"):
            paths.append(result)

    return {"total": len(paths), "paths": paths}


# ─────────────────────────────────────────────────────────────────────────────
# 14. POST /graph/rebuild — Force rebuild graph from latest DB data
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/rebuild", summary="Force rebuild the graph from latest risk assessments")
async def rebuild_graph() -> Dict[str, Any]:
    try:
        from app.graph.builder import SupplyChainGraphBuilder
        from app.graph.algorithms import GraphAlgorithms
        from app.graph.analyzer import BlastRadiusAnalyzer
        from app.graph.serializer import ReactFlowSerializer
        from app.graph.snapshot import graph_store
        from app.db.supabase_client import get_supabase

        # Fetch latest risk assessments from Supabase REST
        sb = get_supabase()
        res = (
            sb.table("risk_assessments")
            .select("assessment_id,risk_score,risk_level,title,event_type,countries,industries")
            .order("assessed_at", desc=True)
            .limit(200)
            .execute()
        )
        rows = res.data or []
        risk_data = [
            {
                "assessment_id": r.get("assessment_id"),
                "risk_score":    r.get("risk_score"),
                "risk_level":    r.get("risk_level"),
                "title":         r.get("title"),
                "event_type":    r.get("event_type"),
                "countries":     r.get("countries") or [],
                "industries":    r.get("industries") or [],
            }
            for r in rows
        ]

        builder = SupplyChainGraphBuilder()
        G = builder.build(risk_assessments=risk_data)

        algo        = GraphAlgorithms()
        stats       = algo.graph_stats(G)
        centrality  = algo.degree_centrality(G)
        blast       = BlastRadiusAnalyzer().analyze_all(G)
        rf_data     = ReactFlowSerializer().serialize(G)

        snapshot = {
            "execution_id":        "manual_rebuild",
            "graph_stats":         stats,
            "react_flow":          rf_data,
            "centrality":          centrality,
            "blast_radius_report": blast,
        }
        await graph_store.update(G, "manual_rebuild", snapshot)

        return {
            "success":     True,
            "node_count":  G.number_of_nodes(),
            "edge_count":  G.number_of_edges(),
            "spof_count":  centrality.get("spof_count", 0),
            "risk_data_used": len(risk_data),
        }
    except Exception as e:
        logger.exception("rebuild_graph failed")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 15. POST /graph/rebuild-from-db — Full rebuild from all DB sources
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/rebuild-from-db", summary="Full graph rebuild from all database sources (risk + supplier portal)")
async def rebuild_graph_from_db(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Comprehensive graph rebuild using all available data:
      1. Risk assessments (same as /rebuild)
      2. Supplier portal data via supplier_seeder (profiles, capacity, inventory)

    Use this to immediately populate a Knowledge Graph on a fresh deployment
    without needing to wait for a full orchestrator workflow run.
    """
    try:
        from app.graph.snapshot import graph_store
        from app.graph.supplier_seeder import seed_from_supplier_data

        # Start with a fresh empty graph
        G = nx.DiGraph()

        # 1. Seed from supplier portal data first
        try:
            added = seed_from_supplier_data(G, db)
            logger.info(f"[rebuild-from-db] Seeder added {added} nodes from supplier portal")
        except Exception as exc:
            logger.warning(f"[rebuild-from-db] Seeder skipped: {exc}")

        # 2. Enrich with risk assessment data
        from app.db.supabase_client import get_supabase
        from app.graph.builder import SupplyChainGraphBuilder
        from app.graph.algorithms import GraphAlgorithms
        from app.graph.blast_radius import BlastRadiusAnalyzer
        from app.graph.serializer import ReactFlowSerializer

        try:
            sb = get_supabase()
            res = (
                sb.table("risk_assessments")
                .select("assessment_id,risk_score,risk_level,title,event_type,countries,industries")
                .order("assessed_at", desc=True)
                .limit(200)
                .execute()
            )
            risk_rows = res.data or []

            if risk_rows:
                risk_data = [
                    {
                        "assessment_id": r.get("assessment_id"),
                        "risk_score":    r.get("risk_score"),
                        "risk_level":    r.get("risk_level"),
                        "title":         r.get("title"),
                        "event_type":    r.get("event_type"),
                        "countries":     r.get("countries") or [],
                        "industries":    r.get("industries") or [],
                    }
                    for r in risk_rows
                ]
                # Merge risk nodes into existing supplier graph
                risk_G = SupplyChainGraphBuilder().build(risk_assessments=risk_data)
                for node_id, attrs in risk_G.nodes(data=True):
                    if node_id not in G:
                        G.add_node(node_id, **attrs)
                for u, v, attrs in risk_G.edges(data=True):
                    if not G.has_edge(u, v):
                        G.add_edge(u, v, **attrs)
        except Exception as exc:
            logger.warning(f"[rebuild-from-db] Risk enrichment skipped: {exc}")

        # 3. Compute stats & update store
        algo       = GraphAlgorithms()
        stats      = algo.graph_stats(G)
        centrality = algo.degree_centrality(G)
        rf_data    = ReactFlowSerializer().serialize(G)

        snapshot = {
            "execution_id": "rebuild_from_db",
            "graph_stats":  stats,
            "react_flow":   rf_data,
            "centrality":   centrality,
        }
        await graph_store.update(G, "rebuild_from_db", snapshot)

        return {
            "success":    True,
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "message":    f"Graph rebuilt from DB — {G.number_of_nodes()} nodes, {G.number_of_edges()} edges",
        }

    except Exception as e:
        logger.exception("rebuild_graph_from_db failed")
        raise HTTPException(status_code=500, detail=str(e))
