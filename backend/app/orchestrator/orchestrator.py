"""
MasterOrchestrator — The central brain of SupplyShield AI.

Responsibilities:
  1. Bootstraps all agents and registers them in the AgentRegistry
  2. Owns the compiled LangGraph DAG (one per process lifetime)
  3. Accepts workflow trigger requests and returns structured summaries
  4. Persists WorkflowRun rows to the database (with graceful fallback if DB is unavailable)
  5. Maintains the AsyncEventBus, AgentMemory, and PriorityTaskQueue singletons
  6. Exposes health, status, and history data to the REST API layer

Singleton pattern: one instance created at app startup via FastAPI lifespan.
Retrieve it anywhere with: MasterOrchestrator.get_instance()
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("orchestrator.master")


class MasterOrchestrator:
    """
    Singleton master controller for all SupplyShield AI agent workflows.

    Startup:
        orchestrator = MasterOrchestrator.get_instance()
        await orchestrator.initialize()

    Trigger a workflow:
        result = await orchestrator.trigger(trigger_type="manual", payload={})
    """

    _instance: Optional["MasterOrchestrator"] = None

    def __init__(self) -> None:
        from app.orchestrator.event_bus import event_bus as _global_bus
        from app.orchestrator.memory import AgentMemory
        from app.orchestrator.registry import AgentRegistry
        from app.orchestrator.task_queue import PriorityTaskQueue
        from app.orchestrator.workflow_planner import WorkflowPlanner

        self.event_bus       = _global_bus
        self.registry        = AgentRegistry()
        self.memory          = AgentMemory()
        self.task_queue      = PriorityTaskQueue()
        self.workflow_planner = WorkflowPlanner()

        self._compiled_graph  = None
        self._active_runs:    Dict[str, dict] = {}
        self._initialized:    bool = False

    @classmethod
    def get_instance(cls) -> "MasterOrchestrator":
        """Return (or create) the process-wide singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def initialize(self) -> None:
        """
        Bootstrap the orchestrator at application startup.

        Steps:
        1. Register stub agents (real agents swap in at Phase 3-8)
        2. Build and compile the LangGraph DAG
        3. Validate the DAG is cycle-free (Kahn's algorithm)
        4. Subscribe to workflow lifecycle events
        """
        if self._initialized:
            logger.warning("[orchestrator] Already initialized — skipping")
            return

        logger.info("[orchestrator] Initializing MasterOrchestrator...")

        # 1. Register agents — Phase 3: real NewsAgent; Phase 4: real RiskAgent;
        #                        Phase 5: real GraphAgent; Phase 6: real SupplierAgent; others remain stubs
        from app.agents.news_agent import NewsAgent
        from app.agents.risk_agent import RiskAgent
        from app.agents.graph_agent import GraphAgent
        from app.agents.supplier_agent import SupplierAgent
        from app.agents.inventory_agent import InventoryAgent
        from app.agents.recommendation_agent import RecommendationAgent
        for agent in [
            NewsAgent(),
            RiskAgent(),
            GraphAgent(),
            SupplierAgent(),
            InventoryAgent(),
            RecommendationAgent(),
        ]:
            await self.registry.register(agent)

        # 2. Compile the LangGraph DAG
        from app.orchestrator.graph import OrchestratorGraph
        builder = OrchestratorGraph(
            registry=self.registry,
            event_bus=self.event_bus,
            memory=self.memory,
        )
        self._compiled_graph = builder.build()

        # 3. Validate DAG (no cycles)
        if not self.workflow_planner.validate():
            raise RuntimeError(
                "[orchestrator] Agent dependency graph contains cycles — cannot start"
            )
        plan = self.workflow_planner.plan()
        logger.info(f"[orchestrator] DAG validated. Execution order: {' → '.join(plan)}")

        # 4. Subscribe to lifecycle events for internal monitoring
        from app.orchestrator.events import EventType
        self.event_bus.subscribe(EventType.WORKFLOW_COMPLETED, self._on_workflow_complete)
        self.event_bus.subscribe(EventType.AGENT_FAILED,       self._on_agent_failed)

        self._initialized = True
        logger.info(
            f"[orchestrator] Ready — {self.registry.count()} agents registered"
        )

    async def shutdown(self) -> None:
        """Clean up resources on application shutdown."""
        logger.info("[orchestrator] Shutting down...")
        await self.memory.clear_all()
        logger.info("[orchestrator] Shutdown complete")

    # ── Workflow Triggering ───────────────────────────────────────────────────

    async def trigger(
        self,
        trigger_type: str = "manual",
        payload: Optional[Dict[str, Any]] = None,
        db: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Trigger a full orchestration workflow run.

        Flow:
        1. Build initial WorkflowState
        2. Persist WorkflowRun to DB (if db session provided)
        3. Invoke the compiled LangGraph DAG (ainvoke)
        4. Update DB with final status and agent results
        5. Return summary dict

        Args:
            trigger_type: "manual" | "scheduled" | "event"
            payload:      Optional trigger-specific context
            db:           Optional SQLAlchemy Session for DB persistence

        Returns:
            Summary dict with execution_id, status, agent counts, timing
        """
        if not self._initialized:
            raise RuntimeError(
                "[orchestrator] Not initialized. Call initialize() first."
            )

        from app.orchestrator.state import WorkflowState, WorkflowStatus
        from app.orchestrator.events import Event, EventType

        execution_id = str(uuid.uuid4())
        started_at   = datetime.now(timezone.utc).isoformat()

        logger.info(
            f"[orchestrator] ▶ Triggering workflow "
            f"execution_id={execution_id[:8]} type={trigger_type}"
        )

        # Publish STARTED event
        await self.event_bus.publish(Event(
            type=EventType.WORKFLOW_STARTED,
            source_agent="orchestrator",
            payload={"trigger_type": trigger_type, "execution_id": execution_id},
            execution_id=execution_id,
        ))

        # Build the initial state for the LangGraph DAG
        initial_state: WorkflowState = {
            "execution_id":          execution_id,
            "trigger_type":          trigger_type,
            "trigger_payload":       payload or {},
            "current_phase":         "news_agent",
            "workflow_status":       WorkflowStatus.RUNNING.value,
            "agent_results":         [],
            "completed_agents":      [],
            "failed_agents":         [],
            "errors":                [],
            "news_events":           [],
            "risk_assessments":      [],
            "graph_snapshot":        {},
            "supplier_scores":       [],
            "inventory_projections": [],
            "recommendations":       [],
            "started_at":            started_at,
            "updated_at":            started_at,
        }

        self._active_runs[execution_id] = initial_state

        # Persist to DB
        if db:
            self._safe_persist_run(db, execution_id, trigger_type, started_at, payload)

        try:
            # Invoke the LangGraph DAG
            # thread_id enables per-run checkpointing via MemorySaver
            config = {"configurable": {"thread_id": execution_id}}
            final_state = await self._compiled_graph.ainvoke(initial_state, config=config)

            self._active_runs[execution_id] = final_state

            if db:
                self._safe_update_run(
                    db, execution_id,
                    status=final_state.get("workflow_status", WorkflowStatus.COMPLETED.value),
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    agent_results=final_state.get("agent_results", []),
                )

            summary = self._build_summary(execution_id, final_state)
            logger.info(
                f"[orchestrator] ■ Workflow {execution_id[:8]} done "
                f"status={final_state.get('workflow_status')}"
            )
            return summary

        except Exception as exc:
            logger.exception(f"[orchestrator] Workflow {execution_id[:8]} crashed: {exc}")

            if db:
                self._safe_update_run(
                    db, execution_id,
                    status=WorkflowStatus.FAILED.value,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    agent_results=[],
                )

            self._active_runs.pop(execution_id, None)
            raise

    # ── Status & Monitoring ───────────────────────────────────────────────────

    def get_active_runs(self) -> List[Dict[str, Any]]:
        return [
            {
                "execution_id":     eid,
                "status":           s.get("workflow_status"),
                "current_phase":    s.get("current_phase"),
                "trigger_type":     s.get("trigger_type"),
                "started_at":       s.get("started_at"),
                "completed_agents": s.get("completed_agents", []),
                "failed_agents":    s.get("failed_agents", []),
            }
            for eid, s in self._active_runs.items()
        ]

    def get_agent_health(self) -> List[dict]:
        return self.registry.health_report()

    def get_event_history(self, limit: int = 50) -> List[dict]:
        events = self.event_bus.get_history(limit=limit)
        return [
            {
                "event_id":     e.event_id,
                "type":         e.type.value,
                "source_agent": e.source_agent,
                "execution_id": e.execution_id,
                "timestamp":    e.timestamp.isoformat(),
                "payload_keys": list(e.payload.keys()),
            }
            for e in events
        ]

    def get_queue_stats(self) -> dict:
        return self.task_queue.stats()

    def get_event_bus_stats(self) -> dict:
        return self.event_bus.stats()

    def get_memory_stats(self) -> dict:
        return self.memory.stats()

    def get_workflow_plan(self) -> List[str]:
        return self.workflow_planner.plan()

    def get_dependency_map(self) -> dict:
        return self.workflow_planner.dependency_map()

    # ── Database helpers (graceful fallback) ──────────────────────────────────

    def _safe_persist_run(
        self,
        db: Any,
        execution_id: str,
        trigger_type: str,
        started_at: str,
        payload: Optional[dict],
    ) -> None:
        try:
            from app.db.models.workflow_run import WorkflowRun
            run = WorkflowRun(
                execution_id=execution_id,
                trigger_type=trigger_type,
                status="running",
                started_at=datetime.fromisoformat(started_at.replace("Z", "+00:00")),
                trigger_payload=payload or {},
            )
            db.add(run)
            db.commit()
        except Exception as e:
            logger.warning(f"[orchestrator] DB persist failed (non-fatal): {e}")
            try:
                db.rollback()
            except Exception:
                pass

    def _safe_update_run(
        self,
        db: Any,
        execution_id: str,
        status: str,
        completed_at: str,
        agent_results: list,
    ) -> None:
        try:
            from app.db.models.workflow_run import WorkflowRun
            run = db.query(WorkflowRun).filter(
                WorkflowRun.execution_id == execution_id
            ).first()
            if run:
                run.status       = status
                run.completed_at = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                run.agent_results = agent_results
                run.agent_count  = str(len(agent_results))
                db.commit()
        except Exception as e:
            logger.warning(f"[orchestrator] DB update failed (non-fatal): {e}")
            try:
                db.rollback()
            except Exception:
                pass

    def _build_summary(self, execution_id: str, state: dict) -> Dict[str, Any]:
        return {
            "execution_id":     execution_id,
            "status":           state.get("workflow_status"),
            "trigger_type":     state.get("trigger_type"),
            "completed_agents": state.get("completed_agents", []),
            "failed_agents":    state.get("failed_agents",    []),
            "errors":           state.get("errors",           []),
            "agent_count":      len(state.get("agent_results", [])),
            "news_events":      len(state.get("news_events", [])),
            "risk_assessments": len(state.get("risk_assessments", [])),
            "recommendations":  len(state.get("recommendations", [])),
            "started_at":       state.get("started_at"),
            "updated_at":       state.get("updated_at"),
        }

    # ── Event subscribers ─────────────────────────────────────────────────────

    async def _on_workflow_complete(self, event: Any) -> None:
        exec_id = event.payload.get("execution_id", "")
        logger.info(f"[orchestrator] ✓ Workflow complete: {exec_id[:8]}")
        self._active_runs.pop(exec_id, None)

    async def _on_agent_failed(self, event: Any) -> None:
        logger.warning(
            f"[orchestrator] ⚠ Agent failed: [{event.source_agent}] "
            f"exec={event.execution_id[:8]}"
        )
