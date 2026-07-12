"""
NewsScheduler — Background APScheduler for automatic news collection.

Runs the full NewsPipeline every NEWS_COLLECTION_INTERVAL_MINUTES minutes
(default: 15 min) using APScheduler's AsyncIOScheduler.

Design:
  - AsyncIOScheduler runs in the same event loop as FastAPI
  - Start/stop controlled by the FastAPI lifespan
  - Manual trigger via REST API: POST /news/scheduler/toggle
  - Thread-safe: only one pipeline run at a time (job coalescing disabled)

State:
  "stopped"  → scheduler not started yet or was explicitly stopped
  "running"  → scheduler is active and jobs are firing
  "paused"   → scheduler started but temporarily paused (no new jobs fire)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval  import IntervalTrigger

logger = logging.getLogger("news.scheduler")

JOB_ID = "news_collection"


class NewsScheduler:
    """Wraps APScheduler to periodically run the news pipeline."""

    def __init__(self, interval_minutes: int = 15) -> None:
        self.interval_minutes  = interval_minutes
        self._scheduler        = AsyncIOScheduler(timezone="UTC")
        self._last_run:   Optional[datetime] = None
        self._run_count:  int  = 0
        self._is_started: bool = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the scheduler (called from FastAPI lifespan startup)."""
        if self._is_started:
            logger.warning("[scheduler] Already running — skipping start()")
            return

        self._scheduler.add_job(
            func            = self._run_pipeline_job,
            trigger         = IntervalTrigger(minutes=self.interval_minutes),
            id              = JOB_ID,
            replace_existing = True,
            coalesce        = True,     # Skip missed fires instead of batching them
            max_instances   = 1,        # Never run 2 pipeline jobs simultaneously
        )
        self._scheduler.start()
        self._is_started = True
        logger.info(
            f"[scheduler] Started — pipeline runs every {self.interval_minutes} min"
        )

    def stop(self) -> None:
        """Gracefully stop the scheduler."""
        if not self._is_started:
            return
        try:
            self._scheduler.shutdown(wait=False)
        except Exception as e:
            logger.warning(f"[scheduler] Shutdown error (non-fatal): {e}")
        self._is_started = False
        logger.info("[scheduler] Stopped")

    def pause(self) -> None:
        """Pause job execution without shutting down the scheduler."""
        if self._is_started:
            self._scheduler.pause()
            logger.info("[scheduler] Paused")

    def resume(self) -> None:
        """Resume after a pause."""
        if self._is_started:
            self._scheduler.resume()
            logger.info("[scheduler] Resumed")

    # ── Manual trigger ────────────────────────────────────────────────────────

    async def trigger_now(self) -> dict:
        """
        Immediately run a pipeline cycle (bypasses scheduler timing).
        Used by POST /news/collect REST endpoint.
        """
        logger.info("[scheduler] Manual trigger — running pipeline now")
        return await self._run_pipeline_job()

    # ── Status ────────────────────────────────────────────────────────────────

    def status(self) -> dict:
        state = "stopped"
        if self._is_started:
            state = "paused" if self._scheduler.state == 2 else "running"

        next_run: Optional[str] = None
        try:
            job = self._scheduler.get_job(JOB_ID)
            if job and job.next_run_time:
                next_run = job.next_run_time.isoformat()
        except Exception:
            pass

        return {
            "state":            state,
            "interval_minutes": self.interval_minutes,
            "run_count":        self._run_count,
            "last_run":         self._last_run.isoformat() if self._last_run else None,
            "next_run":         next_run,
        }

    # ── Background job ────────────────────────────────────────────────────────

    async def _run_pipeline_job(self) -> dict:
        """The async function APScheduler calls on each interval tick."""
        self._last_run = datetime.now(timezone.utc)
        self._run_count += 1

        logger.info(
            f"[scheduler] Pipeline job #{self._run_count} starting "
            f"at {self._last_run.isoformat()}"
        )

        from app.news.pipeline  import NewsPipeline
        from app.db.session     import SessionLocal

        pipeline = NewsPipeline()
        db = SessionLocal()
        try:
            result = await pipeline.run(db=db)
            summary = {
                "run":         self._run_count,
                "collected":   result.collected,
                "stored":      result.stored,
                "duplicates":  result.duplicates,
                "disruptions": result.disruptions,
                "errors":      result.errors,
                "started_at":  result.started_at,
                "completed_at": result.completed_at,
            }
            logger.info(
                f"[scheduler] Job #{self._run_count} done — "
                f"stored={result.stored}, disruptions={result.disruptions}"
            )
            return summary
        except Exception as e:
            logger.exception(f"[scheduler] Pipeline job #{self._run_count} failed: {e}")
            return {"run": self._run_count, "error": str(e)}
        finally:
            db.close()


# ── Module-level singleton ─────────────────────────────────────────────────────
# Created at import time; started/stopped via FastAPI lifespan in main.py

def _make_scheduler() -> NewsScheduler:
    try:
        from app.core.config import settings
        interval = getattr(settings, "NEWS_COLLECTION_INTERVAL_MINUTES", 15)
    except Exception:
        interval = 15
    return NewsScheduler(interval_minutes=interval)


news_scheduler = _make_scheduler()
