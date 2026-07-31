"""
Reports API Endpoints — SupplyShield AI.

Provides enterprise report management backed by PostgreSQL:
  GET  /reports/           — List all reports (workflow-run derived + manual)
  POST /reports/generate   — Trigger AI workflow and create a report record
  GET  /reports/{id}       — Get single report detail
  GET  /reports/{id}/data  — Full JSON payload for preview/download
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, UserPrincipal
from app.db.models.workflow_run import WorkflowRun
from app.db.models.risk_assessment import RiskAssessment
from app.db.models.recommendation import RecommendationRow

logger = logging.getLogger("api.reports")

router = APIRouter(prefix="/reports", tags=["Reports"])

# ── Helpers ───────────────────────────────────────────────────────────────────

REPORT_TYPES = {
    "executive":  {"label": "Executive Summary",      "color": "#7C3AED"},
    "risk":       {"label": "Risk Assessment Report",  "color": "#DC2626"},
    "supplier":   {"label": "Supplier Intelligence",   "color": "#2563EB"},
    "inventory":  {"label": "Inventory Impact",        "color": "#059669"},
    "incident":   {"label": "Incident Analysis",       "color": "#D97706"},
}

def _infer_type(payload: dict) -> str:
    evt = (payload or {}).get("event_type", "")
    if "incident" in evt.lower():   return "incident"
    if "inventory" in evt.lower():  return "inventory"
    if "supplier" in evt.lower():   return "supplier"
    if "risk" in evt.lower():       return "risk"
    return "executive"

def _format_run_obj(run: WorkflowRun) -> dict:
    payload = run.trigger_payload or {}
    rtype = _infer_type(payload)
    meta  = REPORT_TYPES.get(rtype, REPORT_TYPES["executive"])
    n_news  = run.news_event_count or 0
    n_risks = run.risk_assessment_count or 0
    n_recs  = run.recommendation_count or 0
    n_agents = run.agent_count or 6

    status = run.status or "unknown"
    ui_status = (
        "ready"      if status == "completed" else
        "generating" if status == "running"   else
        "failed"     if status == "failed"    else
        status
    )

    return {
        "id":           run.id or run.execution_id,
        "execution_id": run.execution_id,
        "title":        f"{meta['label']} — {(run.execution_id or '')[:8]}…",
        "type":         rtype,
        "type_label":   meta["label"],
        "status":       ui_status,
        "trigger_type": run.trigger_type or "manual",
        "generated_at": run.completed_at.isoformat() if run.completed_at else (run.started_at.isoformat() if run.started_at else None),
        "started_at":   run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "pages":        max(n_agents, 1),
        "news_count":   n_news,
        "risk_count":   n_risks,
        "rec_count":    n_recs,
        "agent_count":  n_agents,
        "summary": (
            f"Processed {n_news} news events, identified {n_risks} risk assessments, "
            f"generated {n_recs} supplier recommendations across {n_agents} AI agents."
        ) if status == "completed" else (
            "Workflow is currently running…" if status == "running"
            else "Workflow failed — check orchestrator logs."
        ),
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", summary="List all AI-generated reports")
def list_reports(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    type_filter: Optional[str] = Query(default=None, description="Filter by report type"),
    current_user: UserPrincipal = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Lists reports derived from workflow_runs in PostgreSQL, newest first.
    """
    query = db.query(WorkflowRun).order_by(WorkflowRun.started_at.desc())
    total = query.count()
    runs  = query.offset(offset).limit(limit).all()

    reports = [_format_run_obj(r) for r in runs]

    if type_filter:
        reports = [r for r in reports if r["type"] == type_filter]

    return {
        "reports": reports,
        "total":   total,
        "limit":   limit,
        "offset":  offset,
    }


@router.post("/generate", summary="Trigger AI workflow and generate a new report")
async def generate_report(
    trigger_type: str = "manual",
    current_user: UserPrincipal = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Triggers the Master Orchestrator to run the full 6-agent AI pipeline.
    """
    try:
        from app.orchestrator.orchestrator import MasterOrchestrator
        orchestrator = MasterOrchestrator.get_instance()
        result = await orchestrator.trigger(
            trigger_type=trigger_type,
            payload={"source": "reports_ui", "action": "generate_report", "user_id": current_user.user_id},
        )
        return {
            "message": "Report generation started",
            "execution_id": result.get("execution_id"),
            "status": result.get("status"),
        }
    except Exception as exc:
        logger.error(f"[reports] generate failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{report_id}", summary="Get report detail by execution_id")
def get_report(
    report_id: str,
    current_user: UserPrincipal = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns detailed report data for the given execution_id from PostgreSQL."""
    run = (
        db.query(WorkflowRun)
        .filter((WorkflowRun.execution_id == report_id) | (WorkflowRun.id == report_id))
        .first()
    )

    if not run:
        raise HTTPException(status_code=404, detail="Report not found")

    return _format_run_obj(run)


@router.get("/{report_id}/data", summary="Get full JSON report payload for download")
def get_report_data(
    report_id: str,
    current_user: UserPrincipal = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns the full agent_results payload from a workflow run.
    """
    run = (
        db.query(WorkflowRun)
        .filter((WorkflowRun.execution_id == report_id) | (WorkflowRun.id == report_id))
        .first()
    )

    if not run:
        raise HTTPException(status_code=404, detail="Report not found")

    formatted = _format_run_obj(run)

    enrichment: Dict[str, Any] = {}
    try:
        started_at = run.started_at
        completed_at = run.completed_at or datetime.now(timezone.utc)
        if started_at:
            risk_rows = (
                db.query(RiskAssessment)
                .filter(RiskAssessment.assessed_at >= started_at, RiskAssessment.assessed_at <= completed_at)
                .order_by(RiskAssessment.risk_score.desc())
                .limit(20)
                .all()
            )
            enrichment["risk_assessments"] = [
                {
                    "title": r.title,
                    "risk_level": r.risk_level,
                    "risk_score": r.risk_score,
                    "countries": r.countries or [],
                    "assessed_at": r.assessed_at.isoformat() if r.assessed_at else None,
                }
                for r in risk_rows
            ]

        rec_rows = db.query(RecommendationRow).limit(10).all()
        enrichment["recommendations"] = [
            {
                "summary": r.explanation,
                "recommendation_type": r.action,
                "priority_score": r.revenue_protected_usd,
            }
            for r in rec_rows
        ]
    except Exception as exc:
        logger.warning(f"[reports] enrichment failed: {exc}")

    return {
        **formatted,
        "agent_results":   run.agent_results or [],
        "trigger_payload": run.trigger_payload or {},
        **enrichment,
    }
