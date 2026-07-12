"""
RiskPipeline — Phase 4: Orchestrates full risk assessment.

Pipeline steps:
  1. Score each news event with RiskScorer
  2. Apply 12-rule business logic via RuleEngine
  3. Compute trajectory via RiskTimeline
  4. Persist to Supabase via REST API
  5. Return structured PipelineResult
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("risk.pipeline")


@dataclass
class RiskPipelineResult:
    total_events:   int = 0
    scored:         int = 0
    critical_count: int = 0
    high_count:     int = 0
    medium_count:   int = 0
    low_count:      int = 0
    avg_risk_score: float = 0.0
    avg_confidence: float = 0.0
    rules_triggered: int = 0
    assessments:    List[Dict[str, Any]] = field(default_factory=list)
    errors:         List[str] = field(default_factory=list)
    started_at:     str = ""
    completed_at:   str = ""


class RiskPipeline:
    """
    Processes news_events from the WorkflowState into structured risk assessments.

    Usage:
        pipeline = RiskPipeline()
        result = await pipeline.run(news_events)
    """

    def __init__(self) -> None:
        from app.risk.scorer      import RiskScorer
        from app.risk.rule_engine import RuleEngine
        from app.risk.timeline    import RiskTimeline

        self.scorer    = RiskScorer()
        self.rules     = RuleEngine()
        self.timeline  = RiskTimeline()

    async def run(self, news_events: List[Dict[str, Any]]) -> RiskPipelineResult:
        result = RiskPipelineResult(
            total_events=len(news_events),
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        if not news_events:
            result.completed_at = datetime.now(timezone.utc).isoformat()
            return result

        assessments: List[Dict[str, Any]] = []

        for event in news_events:
            try:
                assessment = await asyncio.to_thread(self._assess_event, event)
                assessments.append(assessment)
            except Exception as exc:
                logger.warning(f"[risk_pipeline] Event assessment failed: {exc}")
                result.errors.append(str(exc))

        # ── Aggregate stats ────────────────────────────────────────────────────
        result.assessments   = assessments
        result.scored        = len(assessments)
        result.critical_count= sum(1 for a in assessments if a["risk_level"] == "CRITICAL")
        result.high_count    = sum(1 for a in assessments if a["risk_level"] == "HIGH")
        result.medium_count  = sum(1 for a in assessments if a["risk_level"] == "MEDIUM")
        result.low_count     = sum(1 for a in assessments if a["risk_level"] == "LOW")
        result.avg_risk_score= (
            sum(a["risk_score"] for a in assessments) / len(assessments)
            if assessments else 0.0
        )
        result.avg_confidence= (
            sum(a.get("confidence", {}).get("score", 0.5) for a in assessments) / len(assessments)
            if assessments else 0.0
        )
        result.rules_triggered = sum(
            a.get("rule_engine_results", {}).get("rules_fired", 0)
            for a in assessments
        )

        # ── Persist to Supabase REST API ───────────────────────────────────────
        if assessments:
            await asyncio.to_thread(self._persist_supabase, assessments)

        result.completed_at = datetime.now(timezone.utc).isoformat()
        logger.info(
            f"[risk_pipeline] Done: scored={result.scored}, "
            f"CRITICAL={result.critical_count}, HIGH={result.high_count}, "
            f"avg={result.avg_risk_score:.1f}"
        )
        return result

    def _assess_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Score + rule-apply a single event synchronously."""
        # 1. Score
        scored = self.scorer.score(event)

        # 2. Merge event metadata
        assessment = {
            "assessment_id": str(uuid.uuid4()),
            "news_event_id": event.get("id", ""),
            "title":         event.get("title", ""),
            "url":           event.get("url", ""),
            "source":        event.get("source", ""),
            "event_type":    event.get("event_type"),
            "published_at":  event.get("published_at"),
            "countries":     event.get("countries") or [],
            "industries":    event.get("industry_tags") or event.get("industries") or [],
            "severity_score": event.get("severity_score", 0.0),
            "severity_label": event.get("severity", "NONE"),
            **scored,
        }

        # 3. Apply rules
        assessment = self.rules.apply(assessment, event)

        # 4. Trajectory (no history for first run → NEW)
        traj = self.timeline.compute(assessment["risk_score"])
        assessment["trajectory"]  = traj.get("trajectory")
        assessment["trend_slope"] = traj.get("trend_slope", 0.0)

        assessment["assessed_at"] = datetime.now(timezone.utc).isoformat()
        return assessment

    def _persist_supabase(self, assessments: List[Dict[str, Any]]) -> None:
        """Store assessments to Supabase via REST API."""
        try:
            from app.db.supabase_client import get_supabase
            sb = get_supabase()

            rows = []
            for a in assessments:
                rows.append({
                    "assessment_id":       a.get("assessment_id"),
                    "news_event_id":       str(a.get("news_event_id") or ""),
                    "title":               (a.get("title") or "")[:2000],
                    "url":                 (a.get("url") or "")[:2048],
                    "source":              (a.get("source") or "")[:200],
                    "event_type":          a.get("event_type"),
                    "published_at":        a.get("published_at"),
                    "assessed_at":         a.get("assessed_at"),
                    "countries":           a.get("countries") or [],
                    "industries":          a.get("industries") or [],
                    "risk_score":          a.get("risk_score", 0.0),
                    "risk_level":          a.get("risk_level", "LOW"),
                    "severity_score":      a.get("severity_score"),
                    "severity_label":      a.get("severity_label"),
                    "formula_components":  a.get("formula_components"),
                    "geo_risk":            a.get("geo_risk"),
                    "industry_risk":       a.get("industry_risk"),
                    "supplier_tier":       a.get("supplier_dependency", {}).get("tier"),
                    "exposure_weight":     a.get("supplier_dependency", {}).get("exposure_weight"),
                    "confidence_score":    a.get("confidence", {}).get("score"),
                    "confidence_label":    a.get("confidence", {}).get("label"),
                    "confidence_breakdown": a.get("confidence", {}).get("breakdown"),
                    "rule_engine_results": a.get("rule_engine_results"),
                    "trajectory":          a.get("trajectory"),
                    "trend_slope":         a.get("trend_slope"),
                })

            # Upsert in batches of 50
            for i in range(0, len(rows), 50):
                batch = rows[i:i+50]
                sb.table("risk_assessments").upsert(batch, on_conflict="assessment_id").execute()

            logger.info(f"[risk_pipeline] Persisted {len(rows)} assessments to Supabase")
        except Exception as exc:
            logger.warning(f"[risk_pipeline] Supabase persist failed (non-fatal): {exc}")
