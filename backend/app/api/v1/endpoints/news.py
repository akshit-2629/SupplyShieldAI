"""
News Intelligence REST API Endpoints — Phase 3.

Provides HTTP access to the news pipeline for:
  • Manual pipeline trigger
  • Listing collected articles (paginated + filterable)
  • Disruption events feed
  • Pipeline statistics
  • Configured RSS source listing
  • Scheduler status and start/stop toggle

All routes prefixed /news and tagged "News Intelligence".
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db.supabase_client import get_supabase

logger = logging.getLogger("api.news")

router = APIRouter(prefix="/news", tags=["News Intelligence"])


# ── Scheduler dependency ───────────────────────────────────────────────────────

def get_news_scheduler():
    from app.news.scheduler import news_scheduler
    return news_scheduler


# ── 1. Manual pipeline trigger ────────────────────────────────────────────────

@router.post(
    "/collect",
    summary="Manually trigger one news collection pipeline run",
    description=(
        "Immediately executes collect → clean → extract → embed → dedup → store. "
        "Returns summary statistics when the run completes."
    ),
)
async def collect_news(
    scheduler = Depends(get_news_scheduler),
) -> Dict[str, Any]:
    try:
        result = await scheduler.trigger_now()
        return {"success": True, "result": result}
    except Exception as e:
        logger.exception("Manual collect failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ── 2. List all collected articles (paginated) ────────────────────────────────

@router.get(
    "/articles",
    summary="List collected news articles",
)
def list_articles(
    page:          int            = Query(default=1,     ge=1),
    page_size:     int            = Query(default=20,    ge=1, le=100),
    disruption_only: bool         = Query(default=False),
    severity:      Optional[str]  = Query(default=None,  description="CRITICAL/HIGH/MEDIUM/LOW/NONE"),
    country:       Optional[str]  = Query(default=None,  description="ISO country code e.g. CN"),
    industry:      Optional[str]  = Query(default=None,  description="Industry tag e.g. semiconductor"),
) -> Dict[str, Any]:
    sb = get_supabase()
    try:
        q = sb.table("news_articles").select(
            "id,title,url,source_name,severity,severity_score,event_type,"
            "country_codes,industry_tags,entities,is_disruption,is_duplicate,"
            "published_at,collected_at",
            count="exact"
        )
        if disruption_only:
            q = q.eq("is_disruption", True)
        if severity:
            q = q.eq("severity", severity.upper())

        offset = (page - 1) * page_size
        res = q.order("collected_at", desc=True).range(offset, offset + page_size - 1).execute()
        rows = res.data or []
        total = res.count or 0

        # Client-side filter for JSONB country/industry
        if country:
            rows = [r for r in rows if country.upper() in (r.get("country_codes") or [])]
        if industry:
            rows = [r for r in rows if industry.lower() in (r.get("industry_tags") or [])]

        return {
            "total":     total,
            "page":      page,
            "page_size": page_size,
            "pages":     max(1, (total + page_size - 1) // page_size),
            "articles": [
                {
                    "id":             a.get("id"),
                    "title":          a.get("title"),
                    "url":            a.get("url"),
                    "source":         a.get("source_name"),
                    "severity":       a.get("severity"),
                    "severity_score": float(a.get("severity_score") or 0),
                    "event_type":     a.get("event_type"),
                    "countries":      a.get("country_codes") or [],
                    "industries":     a.get("industry_tags") or [],
                    "entities":       a.get("entities") or {},
                    "is_disruption":  a.get("is_disruption"),
                    "is_duplicate":   a.get("is_duplicate"),
                    "published_at":   a.get("published_at"),
                    "collected_at":   a.get("collected_at"),
                }
                for a in rows
            ],
        }
    except Exception as e:
        logger.exception("list_articles failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ── 3. Disruption events feed ─────────────────────────────────────────────────

@router.get(
    "/events",
    summary="Get supply chain disruption events (is_disruption=True)",
)
def list_disruption_events(
    limit:    int           = Query(default=50, ge=1, le=200),
    severity: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    sb = get_supabase()
    try:
        q = sb.table("news_articles").select(
            "id,title,url,source_name,severity,severity_score,event_type,"
            "country_codes,industry_tags,entities,published_at,collected_at"
        ).eq("is_disruption", True)
        if severity:
            q = q.eq("severity", severity.upper())
        res = q.order("severity_score", desc=True).order("collected_at", desc=True).limit(limit).execute()
        rows = res.data or []
        return {
            "total":  len(rows),
            "events": [
                {
                    "id":             a.get("id"),
                    "title":          a.get("title"),
                    "url":            a.get("url"),
                    "source":         a.get("source_name"),
                    "severity":       a.get("severity"),
                    "severity_score": float(a.get("severity_score") or 0),
                    "event_type":     a.get("event_type"),
                    "countries":      a.get("country_codes") or [],
                    "industries":     a.get("industry_tags") or [],
                    "entities":       a.get("entities") or {},
                    "published_at":   a.get("published_at"),
                    "collected_at":   a.get("collected_at"),
                }
                for a in rows
            ],
        }
    except Exception as e:
        logger.exception("list_disruption_events failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ── 4. Pipeline statistics ────────────────────────────────────────────────────

@router.get(
    "/stats",
    summary="News pipeline statistics",
)
def get_news_stats() -> Dict[str, Any]:
    sb = get_supabase()
    try:
        total_res = sb.table("news_articles").select("id", count="exact").execute()
        disruption_res = sb.table("news_articles").select("id", count="exact").eq("is_disruption", True).execute()
        duplicate_res = sb.table("news_articles").select("id", count="exact").eq("is_duplicate", True).execute()
        # Severity breakdown from all rows
        all_res = sb.table("news_articles").select("severity,event_type").execute()
        rows = all_res.data or []
        severity_counts: Dict[str, int] = {}
        event_type_counts: Dict[str, int] = {}
        for r in rows:
            s = r.get("severity") or "NONE"
            severity_counts[s] = severity_counts.get(s, 0) + 1
            et = r.get("event_type")
            if et:
                event_type_counts[et] = event_type_counts.get(et, 0) + 1
        return {
            "total_articles":      total_res.count or 0,
            "disruption_events":   disruption_res.count or 0,
            "duplicates_removed":  duplicate_res.count or 0,
            "severity_breakdown":  severity_counts,
            "event_type_breakdown": event_type_counts,
        }
    except Exception as e:
        logger.warning(f"get_news_stats error: {e}")
        return {"total_articles": 0, "error": str(e)}



# ── 5. Configured sources ─────────────────────────────────────────────────────

@router.get(
    "/sources",
    summary="List configured RSS news sources",
)
def list_sources() -> Dict[str, Any]:
    from app.news.sources import SUPPLY_CHAIN_RSS_SOURCES, TAVILY_SEARCH_QUERIES
    return {
        "rss_sources": [
            {
                "name":              s.name,
                "rss_url":           s.rss_url,
                "category":          s.category,
                "credibility_score": s.credibility_score,
            }
            for s in SUPPLY_CHAIN_RSS_SOURCES
        ],
        "tavily_queries": TAVILY_SEARCH_QUERIES,
    }


# ── 6. Scheduler status ───────────────────────────────────────────────────────

@router.get(
    "/scheduler/status",
    summary="Get background scheduler status",
)
def get_scheduler_status(
    scheduler = Depends(get_news_scheduler),
) -> Dict[str, Any]:
    return scheduler.status()


# ── 7. Scheduler toggle ───────────────────────────────────────────────────────

@router.post(
    "/scheduler/toggle",
    summary="Start or stop the background news collection scheduler",
)
def toggle_scheduler(
    action:    str       = Query(..., description="start | stop | pause | resume"),
    scheduler            = Depends(get_news_scheduler),
) -> Dict[str, Any]:
    action = action.lower().strip()
    if action == "start":
        scheduler.start()
    elif action == "stop":
        scheduler.stop()
    elif action == "pause":
        scheduler.pause()
    elif action == "resume":
        scheduler.resume()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown action '{action}'. Use: start | stop | pause | resume",
        )
    return {"action": action, "status": scheduler.status()}
