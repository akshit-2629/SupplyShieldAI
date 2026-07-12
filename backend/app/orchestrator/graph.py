"""
OrchestratorGraph — Builds and compiles the LangGraph StateGraph.

This is the core State Machine implementation. Each AI agent is a node.
Edges encode dependencies. Conditional edges implement routing logic.
LangGraph handles topological DAG execution, state merging, and checkpointing.

State Machine topology:
  START
    ↓
  news_agent ──────────────── route_after_news ────────────────────┐
                                                                    │ error
                       ↓ has_events                                 ↓
                   risk_agent ─── route_after_risk ─────────→ finalize
                             ↓ high_risk | normal
                         graph_agent ─── route_after_graph ──→ finalize
                               ↓ continue
                          supplier_agent ── route_after_supplier → finalize
                                 ↓ continue
                           inventory_agent ── route_after_inventory → finalize
                                   ↓ continue
                            recommendation_agent
                                     ↓ (always)
                                  finalize
                                     ↓
                                    END

Each node:
  1. Gets the agent from the registry
  2. Calls agent.run(state) which wraps execute() with retry logic
  3. Publishes an event to the event bus
  4. Returns a partial WorkflowState dict (LangGraph merges automatically)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict

from app.orchestrator.state import WorkflowState, WorkflowStatus
from app.orchestrator.events import Event, EventType
from app.orchestrator.router import (
    route_after_news,
    route_after_risk,
    route_after_graph,
    route_after_supplier,
    route_after_inventory,
)

if TYPE_CHECKING:
    from app.orchestrator.registry import AgentRegistry
    from app.orchestrator.event_bus import AsyncEventBus
    from app.orchestrator.memory import AgentMemory

logger = logging.getLogger("orchestrator.graph")

# ── LangGraph import with version compatibility ────────────────────────────────
try:
    from langgraph.graph import StateGraph, END, START
    _HAS_START_CONST = True
except ImportError:
    from langgraph.graph import StateGraph, END  # type: ignore
    START = "__start__"
    _HAS_START_CONST = False

try:
    from langgraph.checkpoint.memory import MemorySaver
    _HAS_CHECKPOINTER = True
except ImportError:
    _HAS_CHECKPOINTER = False
    logger.warning("[graph] MemorySaver not available — workflow state will not be checkpointed")


MAX_AGENT_RETRIES = 3


class OrchestratorGraph:
    """
    Builds the LangGraph DAG for the SupplyShield AI agent pipeline.

    Call build() once at startup to compile a reusable graph.
    The compiled graph is stored by MasterOrchestrator and called via ainvoke().
    """

    def __init__(
        self,
        registry: "AgentRegistry",
        event_bus: "AsyncEventBus",
        memory: "AgentMemory",
    ) -> None:
        self.registry  = registry
        self.event_bus = event_bus
        self.memory    = memory

    # ── Graph Construction ────────────────────────────────────────────────────

    def build(self):
        """
        Build and compile the LangGraph StateGraph.
        Returns a compiled graph ready for ainvoke().
        """
        workflow = StateGraph(WorkflowState)

        # ── Add agent nodes ────────────────────────────────────────────────────
        workflow.add_node("news_agent",           self._node_news)
        workflow.add_node("risk_agent",           self._node_risk)
        workflow.add_node("graph_agent",          self._node_graph)
        workflow.add_node("supplier_agent",       self._node_supplier)
        workflow.add_node("inventory_agent",      self._node_inventory)
        workflow.add_node("recommendation_agent", self._node_recommendation)
        workflow.add_node("finalize",             self._node_finalize)

        # ── Define DAG edges ───────────────────────────────────────────────────
        # Entry point
        if _HAS_START_CONST:
            workflow.add_edge(START, "news_agent")
        else:
            workflow.set_entry_point("news_agent")  # type: ignore

        # news_agent → conditional routing
        workflow.add_conditional_edges(
            "news_agent",
            route_after_news,
            {
                "has_events": "risk_agent",
                "no_events":  "finalize",
                "error":      "finalize",
            },
        )

        # risk_agent → conditional routing (high_risk / normal / error)
        workflow.add_conditional_edges(
            "risk_agent",
            route_after_risk,
            {
                "high_risk": "graph_agent",
                "normal":    "graph_agent",
                "error":     "finalize",
            },
        )

        # Sequential from graph → supplier → inventory → recommendation → finalize
        workflow.add_conditional_edges(
            "graph_agent",
            route_after_graph,
            {"continue": "supplier_agent", "error": "finalize"},
        )
        workflow.add_conditional_edges(
            "supplier_agent",
            route_after_supplier,
            {"continue": "inventory_agent", "error": "finalize"},
        )
        workflow.add_conditional_edges(
            "inventory_agent",
            route_after_inventory,
            {"continue": "recommendation_agent", "error": "finalize"},
        )
        workflow.add_edge("recommendation_agent", "finalize")
        workflow.add_edge("finalize", END)

        # ── Compile ────────────────────────────────────────────────────────────
        if _HAS_CHECKPOINTER:
            compiled = workflow.compile(checkpointer=MemorySaver())
        else:
            compiled = workflow.compile()

        logger.info("[graph] LangGraph StateGraph compiled successfully")
        return compiled

    # ── Node implementations ──────────────────────────────────────────────────
    # Pattern: get agent → publish STARTED event → agent.run(state) →
    #          publish output event → return partial state

    async def _run_agent_node(
        self,
        agent_id: str,
        state: WorkflowState,
        output_event_type: EventType,
    ) -> Dict[str, Any]:
        """
        Central dispatcher called by every agent node.
        Handles missing agents, event publishing, and graceful failure.
        """
        execution_id = state.get("execution_id", "")

        agent = self.registry.get(agent_id)
        if not agent:
            err = f"Agent [{agent_id}] is not registered in AgentRegistry"
            logger.error(f"[graph] {err}")
            return {
                "agent_results": [{
                    "agent_id":    agent_id,
                    "status":      "failed",
                    "data":        {},
                    "error":       err,
                    "duration_ms": 0,
                    "retry_count": 0,
                    "timestamp":   datetime.now(timezone.utc).isoformat(),
                }],
                "completed_agents": [],
                "failed_agents":    [agent_id],
                "errors":           [err],
            }

        # Publish STARTED
        await self.event_bus.publish(Event(
            type=EventType.AGENT_STARTED,
            source_agent=agent_id,
            payload={"execution_id": execution_id, "agent_id": agent_id},
            execution_id=execution_id,
        ))

        # Execute with retry logic (inside BaseAgent.run)
        result = await agent.run(state, max_retries=MAX_AGENT_RETRIES)

        # Publish agent output event
        await self.event_bus.publish(Event(
            type=output_event_type,
            source_agent=agent_id,
            payload=result,
            execution_id=execution_id,
        ))

        # Publish COMPLETED or FAILED lifecycle event
        is_failed = agent_id in result.get("failed_agents", [])
        await self.event_bus.publish(Event(
            type=EventType.AGENT_FAILED if is_failed else EventType.AGENT_COMPLETED,
            source_agent=agent_id,
            payload={"execution_id": execution_id, "status": "failed" if is_failed else "completed"},
            execution_id=execution_id,
        ))

        logger.info(
            f"[graph] Node [{agent_id}] → "
            f"{'FAILED' if is_failed else 'OK'}"
        )
        return result

    async def _node_news(self, state: WorkflowState) -> Dict[str, Any]:
        logger.info(f"[graph] ── Entering: news_agent (exec={state.get('execution_id', '')[:8]})")
        return await self._run_agent_node(
            "news_agent", state, EventType.NEWS_DISRUPTION_DETECTED
        )

    async def _node_risk(self, state: WorkflowState) -> Dict[str, Any]:
        logger.info("[graph] ── Entering: risk_agent")
        return await self._run_agent_node(
            "risk_agent", state, EventType.RISK_SCORE_CALCULATED
        )

    async def _node_graph(self, state: WorkflowState) -> Dict[str, Any]:
        logger.info("[graph] ── Entering: graph_agent")
        return await self._run_agent_node(
            "graph_agent", state, EventType.BLAST_RADIUS_TRACED
        )

    async def _node_supplier(self, state: WorkflowState) -> Dict[str, Any]:
        logger.info("[graph] ── Entering: supplier_agent")
        return await self._run_agent_node(
            "supplier_agent", state, EventType.SUPPLIER_SCORED
        )

    async def _node_inventory(self, state: WorkflowState) -> Dict[str, Any]:
        logger.info("[graph] ── Entering: inventory_agent")
        return await self._run_agent_node(
            "inventory_agent", state, EventType.STOCK_IMPACT_PROJECTED
        )

    async def _node_recommendation(self, state: WorkflowState) -> Dict[str, Any]:
        logger.info("[graph] ── Entering: recommendation_agent")
        return await self._run_agent_node(
            "recommendation_agent", state, EventType.RECOMMENDATIONS_GENERATED
        )

    async def _node_finalize(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Terminal node — determines overall workflow status and publishes
        the WORKFLOW_COMPLETED event consumed by the monitoring layer.
        """
        failed    = state.get("failed_agents",    [])
        completed = state.get("completed_agents", [])
        errors    = state.get("errors",           [])

        if failed and completed:
            status = WorkflowStatus.PARTIALLY_COMPLETED.value
        elif failed:
            status = WorkflowStatus.FAILED.value
        else:
            status = WorkflowStatus.COMPLETED.value

        now = datetime.now(timezone.utc).isoformat()

        await self.event_bus.publish(Event(
            type=EventType.WORKFLOW_COMPLETED,
            source_agent="orchestrator",
            payload={
                "execution_id":     state.get("execution_id"),
                "status":           status,
                "completed_agents": completed,
                "failed_agents":    failed,
                "error_count":      len(errors),
            },
            execution_id=state.get("execution_id", ""),
        ))

        logger.info(
            f"[graph] ── finalize: status={status} | "
            f"completed={completed} | failed={failed}"
        )

        return {
            "workflow_status": status,
            "current_phase":   "completed",
            "updated_at":      now,
        }
