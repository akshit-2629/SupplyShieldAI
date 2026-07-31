"""
Orchestrator REST API Endpoints.

PostgreSQL single source of truth with strict tenant isolation.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, UserPrincipal
from app.db.models.workflow_run import WorkflowRun
from app.orchestrator.orchestrator import MasterOrchestrator

logger = logging.getLogger("api.orchestrator")

router = APIRouter(prefix="/orchestrator", tags=["Master Orchestrator"])


def get_orchestrator() -> MasterOrchestrator:
    return MasterOrchestrator.get_instance()


class TriggerRequest(BaseModel):
    trigger_type: str  = "manual"
    payload:      dict = {}


@router.post(
    "/trigger",
    summary="Trigger a workflow run",
)
async def trigger_workflow(
    body:         TriggerRequest           = TriggerRequest(),
    current_user: UserPrincipal            = Depends(get_current_user),
    orchestrator: MasterOrchestrator       = Depends(get_orchestrator),
) -> Dict[str, Any]:
    try:
        payload = body.payload or {}
        payload["user_id"] = current_user.user_id
        result = await orchestrator.trigger(
            trigger_type=body.trigger_type,
            payload=payload,
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
    current_user: UserPrincipal      = Depends(get_current_user),
    orchestrator: MasterOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    return {"active_runs": orchestrator.get_active_runs()}


@router.get(
    "/runs",
    summary="List workflow run history from the database",
)
def get_workflow_runs(
    limit:        int           = Query(default=20, ge=1, le=100),
    current_user: UserPrincipal = Depends(get_current_user),
    db:           Session       = Depends(get_db),
) -> Dict[str, Any]:
    try:
        runs = (
            db.query(WorkflowRun)
            .order_by(WorkflowRun.started_at.desc())
            .limit(limit)
            .all()
        )
        return {
            "total": len(runs),
            "runs": [
                {
                    "execution_id": r.execution_id,
                    "trigger_type": r.trigger_type,
                    "status":       r.status,
                    "started_at":   r.started_at.isoformat() if r.started_at else None,
                    "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                    "agent_count":  len(r.agent_results or []),
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
    current_user: UserPrincipal      = Depends(get_current_user),
    db:           Session            = Depends(get_db),
    orchestrator: MasterOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    for run in orchestrator.get_active_runs():
        if run["execution_id"] == execution_id:
            return {"source": "active", "run": run}

    run = (
        db.query(WorkflowRun)
        .filter((WorkflowRun.execution_id == execution_id) | (WorkflowRun.id == execution_id))
        .first()
    )

    if run:
        return {
            "source": "database",
            "id": run.id,
            "execution_id": run.execution_id,
            "trigger_type": run.trigger_type,
            "status": run.status,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "agent_results": run.agent_results or [],
            "trigger_payload": run.trigger_payload or {},
        }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Workflow run '{execution_id}' not found",
    )


@router.get(
    "/agents/health",
    summary="Get health status of all registered agents",
)
def get_agent_health(
    current_user: UserPrincipal      = Depends(get_current_user),
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
    current_user: UserPrincipal     = Depends(get_current_user),
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


@router.get(
    "/events",
    summary="Get recent events from the event bus",
)
def get_event_history(
    limit:        int              = Query(default=50, ge=1, le=500),
    current_user: UserPrincipal    = Depends(get_current_user),
    orchestrator: MasterOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    return {
        "events":    orchestrator.get_event_history(limit=limit),
        "bus_stats": orchestrator.get_event_bus_stats(),
    }


@router.get(
    "/plan",
    summary="Get the workflow execution plan (topological order)",
)
def get_workflow_plan(
    current_user: UserPrincipal    = Depends(get_current_user),
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
    current_user: UserPrincipal    = Depends(get_current_user),
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
