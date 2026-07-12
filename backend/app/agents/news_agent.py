"""
NewsAgent — Phase 3: News Intelligence Agent (REAL implementation)

Replaces NewsAgentStub. Runs the full NewsPipeline:
  collect → clean → extract → embed → deduplicate → store

Feeds real disruption events into the LangGraph WorkflowState so that the
downstream agents (Risk, Graph, Supplier, Inventory, Recommendation) can
process genuinely collected supply chain news.

Data contract (matches WorkflowState.news_events):
  [
    {
      "id":             str (UUID),
      "title":          str,
      "url":            str,
      "source":         str,
      "countries":      List[str],  # ISO codes
      "industries":     List[str],
      "severity":       str,        # CRITICAL/HIGH/MEDIUM/LOW/NONE
      "severity_score": float,
      "event_type":     str,        # GEOPOLITICAL/NATURAL_DISASTER/etc.
      "entities":       dict,
      "published_at":   str,
      "collected_at":   str,
    }
  ]
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict

from app.agents.base import BaseAgent
from app.orchestrator.state import WorkflowState

logger = logging.getLogger("agent.news")


class NewsAgent(BaseAgent):
    """
    Real Phase 3 News Intelligence Agent.

    Runs the full NewsPipeline and returns disruption events to the orchestrator.
    The pipeline fetches live news from RSS feeds and Tavily, extracts metadata
    with NLP, deduplicates via cosine similarity, and persists to PostgreSQL.
    """

    agent_id    = "news_agent"
    description = (
        "Collects real-time supply chain news from RSS feeds and Tavily API; "
        "extracts entities, countries, industries, and severity via NLP; "
        "deduplicates using cosine similarity embeddings; "
        "persists disruption events to PostgreSQL."
    )
    version = "1.0.0"  # Phase 3 real implementation

    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Run the full news pipeline and return:
          - news_events: List of disruption event dicts
          - completed_agents / failed_agents / errors: standard fields
          - agent_results: pipeline statistics
        """
        from app.news.pipeline import NewsPipeline
        from app.db.session import SessionLocal

        db = SessionLocal()
        try:
            logger.info("[news_agent] Starting pipeline (real data collection)...")

            pipeline = NewsPipeline()
            result   = await pipeline.run(db=db)

            if result.errors:
                logger.warning(f"[news_agent] Pipeline had {len(result.errors)} error(s)")

            # Fetch recent disruption events from DB for downstream agents
            news_events = pipeline.get_recent_disruptions(db, limit=100)

            logger.info(
                f"[news_agent] Pipeline complete — "
                f"collected={result.collected}, stored={result.stored}, "
                f"disruptions={result.disruptions}, "
                f"returning {len(news_events)} events to orchestrator"
            )

            return {
                "news_events":      news_events,
                "completed_agents": ["news_agent"],
                "failed_agents":    [],
                "errors":           result.errors,
                "agent_results": [{
                    "agent_id":    "news_agent",
                    "status":      "success",
                    "data": {
                        "pipeline_collected":  result.collected,
                        "pipeline_cleaned":    result.cleaned,
                        "pipeline_embedded":   result.embedded,
                        "pipeline_duplicates": result.duplicates,
                        "pipeline_stored":     result.stored,
                        "pipeline_disruptions": result.disruptions,
                        "events_returned":     len(news_events),
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
            logger.exception(f"[news_agent] Unhandled error: {exc}")
            raise   # BaseAgent.run() handles retry + failed_result formatting
        finally:
            db.close()
