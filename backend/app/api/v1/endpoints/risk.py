"""
Risk Assessment REST API Endpoints — Phase 4.

All READ endpoints use Supabase REST API (supabase-py) because direct
PostgreSQL connections are blocked by Supabase free-tier firewall.

Routes:
  GET  /risk/assessments        — List all risk assessments (paginated + filterable)
  GET  /risk/assessments/{id}   — Get single assessment by ID
  POST /risk/score              — Score a single event on demand
  GET  /risk/stats              — Risk statistics + level breakdown
  GET  /risk/timeline           — All tracked risk trajectories
  GET  /risk/timeline/{id}      — Trajectory for specific event
  GET  /risk/high               — High + Critical assessments only
  GET  /risk/rules              — List all active rule engine rules
  GET  /risk/geo                — Geographic risk multiplier lookup
  GET  /risk/industry           — Industry risk multiplier lookup
  POST /risk/pipeline/run       — Manually trigger full risk pipeline
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.db.supabase_client import get_supabase

logger = logging.getLogger("api.risk")

router = APIRouter(prefix="/risk", tags=["Risk Assessment"])


# ─────────────────────────────────────────────────────────────────────────────
# 1. List all risk assessments (paginated + filterable)
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/assessments",
    summary="List risk assessments",
)
def list_risk_assessments(
    page:        int            = Query(default=1,   ge=1),
    page_size:   int            = Query(default=20,  ge=1, le=100),
    risk_level:  Optional[str]  = Query(default=None, description="LOW/MEDIUM/HIGH/CRITICAL"),
    country:     Optional[str]  = Query(default=None, description="ISO code e.g. CN"),
    industry:    Optional[str]  = Query(default=None, description="e.g. semiconductor"),
    event_type:  Optional[str]  = Query(default=None, description="e.g. GEOPOLITICAL"),
    min_score:   Optional[float] = Query(default=None, ge=0, le=100),
) -> Dict[str, Any]:
    sb = get_supabase()
    try:
        # Build query with filters
        q = sb.table("risk_assessments").select(
            "assessment_id,news_event_id,title,url,source,event_type,"
            "published_at,assessed_at,countries,industries,risk_score,risk_level,"
            "severity_score,severity_label,formula_components,geo_risk,industry_risk,"
            "supplier_tier,exposure_weight,confidence_score,confidence_label,"
            "confidence_breakdown,rule_engine_results,trajectory,trend_slope",
            count="exact"
        )

        if risk_level:
            q = q.eq("risk_level", risk_level.upper())
        if event_type:
            q = q.eq("event_type", event_type.upper())
        if min_score is not None:
            q = q.gte("risk_score", min_score)

        # Supabase REST doesn't support JSONB contains for free tier via simple filters,
        # so country/industry filters are applied client-side below

        offset = (page - 1) * page_size
        q = q.order("risk_score", desc=True).order("assessed_at", desc=True)
        q = q.range(offset, offset + page_size - 1)

        res = q.execute()
        rows = res.data or []
        total = res.count or 0

        # Client-side filter for country/industry (JSONB arrays)
        if country:
            country_upper = country.upper()
            rows = [r for r in rows if country_upper in (r.get("countries") or [])]
        if industry:
            industry_lower = industry.lower()
            rows = [r for r in rows if industry_lower in (r.get("industries") or [])]

        return {
            "total":     total,
            "page":      page,
            "page_size": page_size,
            "pages":     max(1, (total + page_size - 1) // page_size),
            "assessments": rows,
        }
    except Exception as e:
        logger.exception("list_risk_assessments failed")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 2. Get single assessment by assessment_id
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/assessments/{assessment_id}",
    summary="Get a single risk assessment",
)
def get_risk_assessment(assessment_id: str) -> Dict[str, Any]:
    sb = get_supabase()
    try:
        res = (
            sb.table("risk_assessments")
            .select("*")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assessment '{assessment_id}' not found"
            )
        return rows[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_risk_assessment failed")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 3. Score a single event on demand (no DB persistence)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/score",
    summary="Score a single news event on demand",
)
async def score_event(
    event:         Dict[str, Any],
    supplier_tier: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    try:
        from app.risk.scorer import risk_scorer
        from app.risk.rule_engine import rule_engine

        assessment = risk_scorer.score(event, supplier_tier=supplier_tier)
        assessment = rule_engine.apply(assessment)
        return {"success": True, "assessment": assessment}
    except Exception as e:
        logger.exception("score_event failed")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 4. Risk statistics
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/stats", summary="Risk assessment statistics")
def get_risk_stats() -> Dict[str, Any]:
    sb = get_supabase()
    try:
        # Total count
        total_res = sb.table("risk_assessments").select("id", count="exact").execute()
        total = total_res.count or 0

        # All rows for breakdowns (only fields needed)
        all_res = sb.table("risk_assessments").select(
            "risk_level,risk_score,confidence_score,trajectory,event_type"
        ).execute()
        rows = all_res.data or []

        # Level breakdown
        level_counts: Dict[str, int] = {}
        scores = []
        confidences = []
        trajectory_counts: Dict[str, int] = {}
        event_type_counts: Dict[str, int] = {}

        for r in rows:
            level = r.get("risk_level") or "UNKNOWN"
            level_counts[level] = level_counts.get(level, 0) + 1

            if r.get("risk_score") is not None:
                scores.append(r["risk_score"])
            if r.get("confidence_score") is not None:
                confidences.append(r["confidence_score"])

            traj = r.get("trajectory")
            if traj:
                trajectory_counts[traj] = trajectory_counts.get(traj, 0) + 1

            et = r.get("event_type")
            if et:
                event_type_counts[et] = event_type_counts.get(et, 0) + 1

        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.0

        try:
            from app.risk.timeline import risk_timeline_store
            timeline_stats = risk_timeline_store.stats()
        except Exception:
            timeline_stats = {}

        return {
            "total_assessments":    total,
            "risk_level_breakdown": level_counts,
            "avg_risk_score":       avg_score,
            "avg_confidence_score": avg_confidence,
            "trajectory_breakdown": trajectory_counts,
            "event_type_breakdown": event_type_counts,
            "timeline":             timeline_stats,
        }
    except Exception as e:
        logger.warning(f"get_risk_stats error: {e}")
        return {"total_assessments": 0, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# 5. Timeline — all trajectories
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/timeline", summary="Get all risk trajectories")
def get_all_timelines() -> Dict[str, Any]:
    try:
        from app.risk.timeline import risk_timeline_store
        trajectories = risk_timeline_store.get_all_trajectories()
        return {
            "total":        len(trajectories),
            "trajectories": trajectories,
            "stats":        risk_timeline_store.stats(),
        }
    except Exception as e:
        logger.exception("get_all_timelines failed")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 6. Timeline — single event
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/timeline/{event_id}", summary="Get risk trajectory for a specific event")
def get_event_timeline(event_id: str) -> Dict[str, Any]:
    try:
        from app.risk.timeline import risk_timeline_store
        return risk_timeline_store.get_trajectory(event_id)
    except Exception as e:
        logger.exception("get_event_timeline failed")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 7. High + Critical assessments (fast path for dashboard)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/high", summary="Get HIGH and CRITICAL risk assessments")
def get_high_risk_assessments(
    limit: int = Query(default=50, ge=1, le=200),
) -> Dict[str, Any]:
    sb = get_supabase()
    try:
        res = (
            sb.table("risk_assessments")
            .select(
                "assessment_id,title,url,event_type,risk_score,risk_level,"
                "confidence_score,trajectory,countries,industries,assessed_at"
            )
            .in_("risk_level", ["HIGH", "CRITICAL"])
            .order("risk_score", desc=True)
            .limit(limit)
            .execute()
        )
        rows = res.data or []
        return {"total": len(rows), "assessments": rows}
    except Exception as e:
        logger.exception("get_high_risk_assessments failed")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 8. Rule engine — list all rules
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/rules", summary="List all active risk rule engine rules")
def list_risk_rules() -> Dict[str, Any]:
    try:
        from app.risk.rule_engine import rule_engine
        return {
            "total": len(rule_engine.list_rules()),
            "rules": rule_engine.list_rules(),
        }
    except Exception as e:
        logger.exception("list_risk_rules failed")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 9. Geographic risk info
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/geo", summary="Geographic risk multiplier lookup")
def get_geo_risk(
    country_codes: str = Query(..., description="Comma-separated ISO codes e.g. CN,US,TW"),
) -> Dict[str, Any]:
    try:
        from app.risk.geo_risk import geo_risk_calculator
        codes = [c.strip().upper() for c in country_codes.split(",") if c.strip()]
        return geo_risk_calculator.calculate(codes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 10. Industry risk info
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/industry", summary="Industry risk multiplier lookup")
def get_industry_risk(
    industry_tags: str = Query(..., description="Comma-separated tags e.g. semiconductor,automotive"),
) -> Dict[str, Any]:
    try:
        from app.risk.industry_risk import industry_risk_calculator
        tags = [t.strip().lower() for t in industry_tags.split(",") if t.strip()]
        return industry_risk_calculator.calculate(tags)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 11. Manually run the full risk pipeline against recent news
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/pipeline/run",
    summary="Manually trigger the risk pipeline against recent news",
)
async def run_risk_pipeline(
    limit:         int           = Query(default=100, ge=1, le=500),
    supplier_tier: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    sb = get_supabase()
    try:
        # Fetch recent disruption news events via Supabase REST
        res = (
            sb.table("news_articles")
            .select(
                "id,title,url,source_name,severity,severity_score,"
                "event_type,country_codes,industry_tags,entities,published_at"
            )
            .eq("is_disruption", True)
            .order("severity_score", desc=True)
            .limit(limit)
            .execute()
        )
        news_events = res.data or []

        if not news_events:
            return {
                "success": True,
                "message": "No disruption events found in DB. Run /news/collect first.",
                "scored":  0,
            }

        # Normalize field names for the risk pipeline
        normalized = []
        for a in news_events:
            normalized.append({
                "id":             a.get("id"),
                "title":          a.get("title"),
                "url":            a.get("url"),
                "source":         a.get("source_name"),
                "severity":       a.get("severity"),
                "severity_score": a.get("severity_score"),
                "event_type":     a.get("event_type"),
                "countries":      a.get("country_codes") or [],
                "industries":     a.get("industry_tags") or [],
                "entities":       a.get("entities") or {},
                "published_at":   a.get("published_at"),
            })

        from app.risk.pipeline import RiskPipeline
        risk_pipeline = RiskPipeline()
        result = await risk_pipeline.run(normalized, supplier_tier=supplier_tier)

        return {
            "success":   True,
            "summary":   result.summary,
            "top_risks": [
                {
                    "title":      a.get("title", "")[:100],
                    "risk_score": a.get("risk_score"),
                    "risk_level": a.get("risk_level"),
                    "event_type": a.get("event_type"),
                    "countries":  a.get("countries", []),
                    "industries": a.get("industries", []),
                    "trajectory": a.get("trajectory", {}).get("trajectory"),
                }
                for a in result.assessments[:10]
            ],
        }
    except Exception as e:
        logger.exception("run_risk_pipeline failed")
        raise HTTPException(status_code=500, detail=str(e))
