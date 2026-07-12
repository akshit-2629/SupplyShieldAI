"""
WorkflowPlanner — DAG execution planning via Kahn's topological sort algorithm.

Given a set of agent dependencies (A must run after B), produces an ordered
execution list that satisfies all precedence constraints. This is the explicit
'DAG Execution' algorithm implementation for Phase 2.

The LangGraph StateGraph already enforces topological order through its compiled
edge definitions. This module provides:
  • An explicit, queryable dependency model
  • Pre-flight DAG cycle detection (validates no cycles before run starts)
  • Dynamic plan generation for subsets of enabled agents
  • Clear dependency introspection for the API / UI

Kahn's algorithm:
  1. Compute in-degree for each node
  2. Seed queue with nodes whose in-degree = 0 (no dependencies)
  3. Greedily dequeue, reduce neighbors' in-degrees, re-enqueue zeros
  4. If result length < node count → cycle detected → raise error
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger("orchestrator.workflow_planner")


class CyclicDependencyError(Exception):
    """Raised when the agent dependency graph contains a cycle (invalid DAG)."""
    pass


class WorkflowPlanner:
    """
    Plans agent execution order using Kahn's topological sort.

    Default workflow (SupplyShield AI Phase 2 sequential pipeline):
        news_agent
            ↓
        risk_agent
            ↓
        graph_agent
            ↓
        supplier_agent
            ↓
        inventory_agent
            ↓
        recommendation_agent
    """

    # Full ordered list of agents in the default pipeline
    ALL_AGENTS: List[str] = [
        "news_agent",
        "risk_agent",
        "graph_agent",
        "supplier_agent",
        "inventory_agent",
        "recommendation_agent",
    ]

    # Default dependency edges: (agent, must_run_after)
    DEFAULT_DEPENDENCIES: List[Tuple[str, str]] = [
        ("risk_agent",           "news_agent"),
        ("graph_agent",          "risk_agent"),
        ("supplier_agent",       "graph_agent"),
        ("inventory_agent",      "supplier_agent"),
        ("recommendation_agent", "inventory_agent"),
    ]

    def __init__(self) -> None:
        # adj[a] = list of agents that must run AFTER a  (forward edges)
        self._adj: Dict[str, List[str]]  = defaultdict(list)
        self._in_degree: Dict[str, int]  = defaultdict(int)
        self._nodes: Set[str]            = set()

        # Seed all known agents
        for node in self.ALL_AGENTS:
            self._nodes.add(node)
            _ = self._adj[node]
            _ = self._in_degree[node]

        # Load default dependency graph
        for agent, after in self.DEFAULT_DEPENDENCIES:
            self.add_dependency(agent, after=after)

    # ── Dependency management ─────────────────────────────────────────────────

    def add_dependency(self, agent: str, after: str) -> None:
        """
        Declare: `agent` must run AFTER `after`.
        Edge direction: after → agent
        """
        self._nodes.update({agent, after})
        self._adj[after].append(agent)
        self._in_degree[agent] += 1
        # Ensure all nodes appear in both maps
        self._adj.setdefault(agent, [])
        self._in_degree.setdefault(after, 0)

    # ── Kahn's Topological Sort ───────────────────────────────────────────────

    def plan(self, enabled_agents: Optional[List[str]] = None) -> List[str]:
        """
        Produce an ordered execution list via Kahn's algorithm.

        Args:
            enabled_agents: If provided, only include these agents in the plan.
                            Dependency edges to disabled agents are ignored.

        Returns:
            Ordered list of agent IDs (index 0 runs first).

        Raises:
            CyclicDependencyError: If a cycle is detected.
        """
        nodes: Set[str] = set(enabled_agents) if enabled_agents else set(self._nodes)

        # Build sub-graph for this specific set of nodes
        adj: Dict[str, List[str]]  = defaultdict(list)
        in_deg: Dict[str, int]     = {n: 0 for n in nodes}

        for node in nodes:
            for neighbor in self._adj.get(node, []):
                if neighbor in nodes:
                    adj[node].append(neighbor)
                    in_deg[neighbor] += 1

        # Kahn's BFS
        queue: deque = deque(n for n in nodes if in_deg[n] == 0)
        result: List[str] = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for neighbor in adj[node]:
                in_deg[neighbor] -= 1
                if in_deg[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(nodes):
            unresolved = nodes - set(result)
            raise CyclicDependencyError(
                f"Cycle detected in agent dependency graph. "
                f"Unresolved: {unresolved}"
            )

        logger.info(f"[workflow_planner] Execution order: {' → '.join(result)}")
        return result

    # ── Validation ────────────────────────────────────────────────────────────

    def validate(self) -> bool:
        """Returns True if the dependency graph is cycle-free (valid DAG)."""
        try:
            self.plan()
            return True
        except CyclicDependencyError as e:
            logger.error(f"[workflow_planner] DAG validation failed: {e}")
            return False

    # ── Introspection ─────────────────────────────────────────────────────────

    def get_predecessors(self, agent_id: str) -> List[str]:
        """Agents that must run BEFORE agent_id."""
        return [n for n, neighbors in self._adj.items() if agent_id in neighbors]

    def get_successors(self, agent_id: str) -> List[str]:
        """Agents that run AFTER agent_id."""
        return list(self._adj.get(agent_id, []))

    def dependency_map(self) -> Dict[str, List[str]]:
        """Return the full dependency graph as a dict."""
        return {n: list(neighbors) for n, neighbors in self._adj.items()}
