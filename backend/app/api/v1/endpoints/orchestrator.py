"""
Orchestrator REST API Endpoints.

Provides HTTP access to the MasterOrchestrator for:
  • Triggering workflow runs
  • Listing and inspecting workflow runs (active + DB history)
  • Viewing agent health status
  • Toggling individual agents on/off
  • Inspecting event bus history
  • Getting full system status

All endpoints are prefix /orchestrator and tagged "Master Orchestrator"
for the auto-generated Swagger/OpenAPI docs.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.db.supabase_client import get_supabase
from app.orchestrator.orchestrator import MasterOrchestrator

logger = logging.getLogger("api.orchestrator")

router = APIRouter(prefix="/orchestrator", tags=["Master Orchestrator"])


# ── Dependency injection ───────────────────────────────────────────────────────

def get_orchestrator() -> MasterOrchestrator:
    return MasterOrchestrator.get_instance()


# ── Request/Response schemas ───────────────────────────────────────────────────

class TriggerRequest(BaseModel):
    trigger_type: str  = "manual"
    payload:      dict = {}


# ── Workflow Endpoints ────────────────────────────────────────────────────────

@router.post(
    "/trigger",
    summary="Trigger a workflow run",
    description=(
        "Manually trigger a full 6-agent SupplyShield AI workflow. "
        "Returns immediately with the execution summary once all agents complete."
    ),
)
async def trigger_workflow(
    body:         TriggerRequest           = TriggerRequest(),
    orchestrator: MasterOrchestrator       = Depends(get_orchestrator),
) -> Dict[str, Any]:
    try:
        result = await orchestrator.trigger(
            trigger_type=body.trigger_type,
            payload=body.payload,
        )
        return {"success": True, "result": result}
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.exception("Workflow trigger failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/runs/active",
    summary="List active (in-progress) workflow runs",
)
def get_active_runs(
    orchestrator: MasterOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    return {"active_runs": orchestrator.get_active_runs()}


@router.get(
    "/runs",
    summary="List workflow run history from the database",
)
def get_workflow_runs(
    limit: int = Query(default=20, ge=1, le=100),
) -> Dict[str, Any]:
    sb = get_supabase()
    try:
        res = (
            sb.table("workflow_runs")
            .select("execution_id,trigger_type,status,started_at,completed_at,agent_results")
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )
        runs = res.data or []
        return {
            "total": len(runs),
            "runs": [
                {
                    "execution_id": r.get("execution_id"),
                    "trigger_type": r.get("trigger_type"),
                    "status":       r.get("status"),
                    "started_at":   r.get("started_at"),
                    "completed_at": r.get("completed_at"),
                    "agent_count":  len(r.get("agent_results") or []),
                }
                for r in runs
            ],
        }
    except Exception as e:
        logger.warning(f"DB query failed for workflow runs: {e}")
        return {"total": 0, "runs": [], "error": str(e)}


@router.get(
    "/runs/{execution_id}",
    summary="Get full detail of a specific workflow run",
)
def get_workflow_run_detail(
    execution_id: str,
    orchestrator: MasterOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    # Check in-memory active runs first
    for run in orchestrator.get_active_runs():
        if run["execution_id"] == execution_id:
            return {"source": "active", "run": run}

    # Fall back to Supabase REST
    sb = get_supabase()
    try:
        res = (
            sb.table("workflow_runs")
            .select("*")
            .eq("execution_id", execution_id)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if rows:
            return {"source": "database", **rows[0]}
    except Exception as e:
        logger.warning(f"DB lookup failed for execution_id={execution_id}: {e}")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Workflow run '{execution_id}' not found",
    )


# ── Agent Health Endpoints ────────────────────────────────────────────────────

@router.get(
    "/agents/health",
    summary="Get health status of all registered agents",
)
def get_agent_health(
    orchestrator: MasterOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    agents = orchestrator.get_agent_health()
    return {
        "total":   len(agents),
        "enabled": sum(1 for a in agents if a.get("enabled")),
        "agents":  agents,
    }


@router.post(
    "/agents/{agent_id}/toggle",
    summary="Enable or disable a specific agent",
)
async def toggle_agent(
    agent_id:     str,
    enable:       bool              = Query(..., description="true=enable, false=disable"),
    orchestrator: MasterOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    if enable:
        success = await orchestrator.registry.enable(agent_id)
    else:
        success = await orchestrator.registry.disable(agent_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found in registry",
        )
    return {"agent_id": agent_id, "enabled": enable}


# ── Event Bus & System Status ─────────────────────────────────────────────────

@router.get(
    "/events",
    summary="Get recent events from the event bus",
)
def get_event_history(
    limit:        int              = Query(default=50, ge=1, le=500),
    orchestrator: MasterOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    return {
        "events":   orchestrator.get_event_history(limit=limit),
        "bus_stats": orchestrator.get_event_bus_stats(),
    }


@router.get(
    "/plan",
    summary="Get the workflow execution plan (topological order)",
)
def get_workflow_plan(
    orchestrator: MasterOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    return {
        "execution_order": orchestrator.get_workflow_plan(),
        "dependency_map":  orchestrator.get_dependency_map(),
    }


@router.get(
    "/status",
    summary="Get full orchestrator system status",
)
def get_orchestrator_status(
    orchestrator: MasterOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    agents = orchestrator.get_agent_health()
    return {
        "orchestrator_status": "running",
        "agent_count":         len(agents),
        "active_runs":         len(orchestrator.get_active_runs()),
        "workflow_plan":       orchestrator.get_workflow_plan(),
        "queue":               orchestrator.get_queue_stats(),
        "event_bus":           orchestrator.get_event_bus_stats(),
        "memory":              orchestrator.get_memory_stats(),
        "agents":              agents,
    }
