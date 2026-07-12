"""
RiskAgent — Phase 4: Risk Assessment Agent (REAL implementation)

Replaces RiskAgentStub. Runs the full RiskPipeline:
  score → rule_engine → timeline → store

Reads news_events from the LangGraph WorkflowState (produced by Phase 3
NewsAgent) and returns risk_assessments to the state for downstream agents
(Graph Agent Phase 5, Supplier Agent Phase 6, Inventory Agent Phase 7).

Data contract (matches WorkflowState.risk_assessments):
  [
    {
      "assessment_id":   str (UUID),
      "news_event_id":   str (UUID),
      "title":           str,
      "url":             str,
      "event_type":      str,
      "countries":       List[str],
      "industries":      List[str],
      "risk_score":      float (0–100),
      "risk_level":      str (LOW/MEDIUM/HIGH/CRITICAL),
      "severity_score":  float (0–10, from Phase 3),
      "severity_label":  str,
      "formula_components": dict,    # full audit trail
      "geo_risk":        dict,
      "industry_risk":   dict,
      "supplier_dependency": dict,
      "confidence":      dict,
      "rule_engine_results": dict,
      "trajectory":      dict,
      "assessed_at":     str (ISO),
    }
  ]
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict

from app.agents.base import BaseAgent
from app.orchestrator.state import WorkflowState

logger = logging.getLogger("agent.risk")


class RiskAgent(BaseAgent):
    """
    Real Phase 4 Risk Assessment Agent.

    Runs the full RiskPipeline over all news_events from Phase 3
    and returns structured risk_assessments to the orchestrator.
    """

    agent_id    = "risk_agent"
    description = (
        "Converts raw supply chain news events into quantified business risk scores. "
        "Uses weighted scoring (severity × likelihood × exposure), "
        "geographic and industry risk multipliers, "
        "a 12-rule business logic engine, and trajectory tracking. "
        "Produces risk_score (0–100), risk_level (LOW/MEDIUM/HIGH/CRITICAL), "
        "confidence score, and risk trend (ESCALATING/STABLE/DECLINING/RECOVERING)."
    )
    version = "1.0.0"  # Phase 4 real implementation

    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Run the full risk pipeline over news_events from WorkflowState.

        Args:
            state: Full WorkflowState. Reads state["news_events"].

        Returns:
            Partial WorkflowState dict with:
              - risk_assessments: List of full assessment dicts
              - completed_agents, failed_agents, errors, agent_results
        """
        from app.risk.pipeline import RiskPipeline
        from app.db.session import SessionLocal

        news_events = state.get("news_events", [])

        logger.info(
            f"[risk_agent] Starting — {len(news_events)} news events to assess"
        )

        if not news_events:
            logger.warning("[risk_agent] No news events to assess (empty news_events)")
            return {
                "risk_assessments": [],
                "completed_agents": ["risk_agent"],
                "failed_agents":    [],
                "errors":           [],
                "agent_results": [{
                    "agent_id":    "risk_agent",
                    "status":      "success",
                    "data":        {"scored": 0, "note": "no news events in state"},
                    "error":       None,
                    "duration_ms": 0,
                    "retry_count": 0,
                    "timestamp":   datetime.utcnow().isoformat(),
                }],
            }

        db = SessionLocal()
        try:
            pipeline = RiskPipeline()
            result   = await pipeline.run(news_events)

            # Persist assessments to DB
            persisted_count = self._persist_assessments(db, result.assessments)
            logger.info(
                f"[risk_agent] Persisted {persisted_count}/{len(result.assessments)} "
                f"assessments to DB"
            )

            logger.info(
                f"[risk_agent] Pipeline complete — "
                f"scored={result.scored}, "
                f"CRITICAL={result.critical_count}, "
                f"HIGH={result.high_count}, "
                f"MEDIUM={result.medium_count}, "
                f"LOW={result.low_count}, "
                f"avg_score={result.avg_risk_score:.1f}, "
                f"avg_confidence={result.avg_confidence:.3f}, "
                f"rules_triggered={result.rules_triggered}"
            )

            return {
                "risk_assessments": result.assessments,
                "completed_agents": ["risk_agent"],
                "failed_agents":    [],
                "errors":           result.errors,
                "agent_results": [{
                    "agent_id": "risk_agent",
                    "status":   "success",
                    "data": {
                        "total_events":    result.total_events,
                        "scored":          result.scored,
                        "critical_count":  result.critical_count,
                        "high_count":      result.high_count,
                        "medium_count":    result.medium_count,
                        "low_count":       result.low_count,
                        "avg_risk_score":  round(result.avg_risk_score, 2),
                        "avg_confidence":  round(result.avg_confidence, 4),
                        "rules_triggered": result.rules_triggered,
                        "persisted_to_db": persisted_count,
                        "pipeline_started_at":   result.started_at,
                        "pipeline_completed_at": result.completed_at,
                    },
                    "error":       result.errors[0] if result.errors else None,
                    "duration_ms": 0,      # Set by BaseAgent.run() wrapper
                    "retry_count": 0,
                    "timestamp":   datetime.utcnow().isoformat(),
                }],
            }

        except Exception as exc:
            logger.exception(f"[risk_agent] Unhandled error: {exc}")
            raise   # BaseAgent.run() handles retry + failed_result
        finally:
            db.close()

    def _persist_assessments(self, db: Any, assessments: list) -> int:
        """
        Persist risk assessments to PostgreSQL.
        Returns count of successfully persisted rows.
        Gracefully handles DB unavailability.
        """
        try:
            from app.db.models.risk_assessment import RiskAssessment
            from datetime import datetime, timezone

            count = 0
            for a in assessments:
                try:
                    # Upsert: skip if assessment_id already exists
                    existing = db.query(RiskAssessment).filter(
                        RiskAssessment.assessment_id == a.get("assessment_id")
                    ).first()
                    if existing:
                        continue

                    # Parse published_at
                    published_at = None
                    if a.get("published_at"):
                        try:
                            published_at = datetime.fromisoformat(
                                a["published_at"].replace("Z", "+00:00")
                            )
                        except Exception:
                            pass

                    row = RiskAssessment(
                        assessment_id= a.get("assessment_id"),
                        news_event_id= str(a.get("news_event_id") or ""),
                        title=        a.get("title", ""),
                        url=          a.get("url", ""),
                        source=       a.get("source", ""),
                        event_type=   a.get("event_type"),
                        published_at= published_at,
                        countries=    a.get("countries", []),
                        industries=   a.get("industries", []),
                        risk_score=   a.get("risk_score", 0.0),
                        risk_level=   a.get("risk_level", "LOW"),
                        severity_score= a.get("severity_score"),
                        severity_label= a.get("severity_label"),
                        formula_components= a.get("formula_components"),
                        geo_risk=     a.get("geo_risk"),
                        industry_risk= a.get("industry_risk"),
                        supplier_tier= a.get("supplier_dependency", {}).get("tier"),
                        exposure_weight= a.get("supplier_dependency", {}).get("exposure_weight"),
                        confidence_score= a.get("confidence", {}).get("score"),
                        confidence_label= a.get("confidence", {}).get("label"),
                        confidence_breakdown= a.get("confidence", {}).get("breakdown"),
                        rule_engine_results= a.get("rule_engine_results"),
                        trajectory=   a.get("trajectory", {}).get("trajectory"),
                        trend_slope=  a.get("trajectory", {}).get("trend_slope"),
                    )
                    db.add(row)
                    count += 1
                except Exception as row_exc:
                    logger.debug(f"[risk_agent] Row persist error: {row_exc}")

            db.commit()
            return count
        except Exception as e:
            logger.warning(f"[risk_agent] DB persist failed (non-fatal): {e}")
            try:
                db.rollback()
            except Exception:
                pass
            return 0
