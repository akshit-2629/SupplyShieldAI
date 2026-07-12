"""
Phase 5: Knowledge Graph — In-Memory Graph Store

Singleton that holds the latest compiled supply chain DiGraph in memory.
Updated on every workflow run by GraphAgent.execute().

Design:
  - One DiGraph per process lifecycle (rebuilt on each workflow trigger)
  - Stores the last N graph snapshots for comparison (ring buffer, N=5)
  - Thread-safe updates via asyncio.Lock (one write at a time)
  - Provides instant read access to the current graph for API endpoints
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Optional

import networkx as nx

logger = logging.getLogger("graph.snapshot")

MAX_SNAPSHOT_HISTORY = 5


class GraphSnapshotStore:
    """
    Process-wide singleton that stores the live supply chain DiGraph.

    Updated by GraphAgent after every workflow run.
    Read by REST API endpoints at any time.
    """

    def __init__(self) -> None:
        self._graph:      Optional[nx.DiGraph]         = None
        self._history:    Deque[Dict[str, Any]]        = deque(maxlen=MAX_SNAPSHOT_HISTORY)
        self._lock:       asyncio.Lock                  = asyncio.Lock()
        self._updated_at: Optional[str]                = None
        self._run_count:  int                          = 0

    async def update(
        self,
        graph:         nx.DiGraph,
        execution_id:  str,
        snapshot_data: Dict[str, Any],
    ) -> None:
        """
        Replace the current graph with a newly built one.
        Archives the previous snapshot to history.
        Thread-safe via asyncio.Lock.
        """
        async with self._lock:
            if self._graph is not None:
                # Archive previous snapshot summary (not the full graph object)
                self._history.append({
                    "execution_id": execution_id,
                    "updated_at":   self._updated_at,
                    "node_count":   self._graph.number_of_nodes(),
                    "edge_count":   self._graph.number_of_edges(),
                })

            self._graph      = graph
            self._updated_at = datetime.now(timezone.utc).isoformat()
            self._run_count += 1

            logger.info(
                f"[graph_store] Updated — "
                f"nodes={graph.number_of_nodes()}, "
                f"edges={graph.number_of_edges()}, "
                f"run_count={self._run_count}"
            )

    def get_graph(self) -> Optional[nx.DiGraph]:
        """Return the current DiGraph (read-only reference). Thread-safe for reads."""
        return self._graph

    def is_ready(self) -> bool:
        """True if the graph has been built at least once."""
        return self._graph is not None

    def stats(self) -> Dict[str, Any]:
        """Return summary stats without serializing the full graph."""
        if self._graph is None:
            return {"ready": False, "message": "Graph not yet built"}
        return {
            "ready":        True,
            "node_count":   self._graph.number_of_nodes(),
            "edge_count":   self._graph.number_of_edges(),
            "updated_at":   self._updated_at,
            "run_count":    self._run_count,
            "history":      list(self._history),
        }


# Module-level singleton
graph_store = GraphSnapshotStore()
