"""
OrchestratorBridge — wraps MasterOrchestrator.trigger() for supplier portal events.

All supplier data updates call this bridge. It:
  1. Builds a structured event payload
  2. Calls orchestrator.trigger() as a background asyncio task (non-blocking)
  3. Never raises — logs warnings if orchestrator is unavailable

Architecture rule: Never call AI agents directly. Everything goes through here.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("supplier_portal.orchestrator_bridge")


class OrchestratorBridge:
    """
    Thin wrapper that routes supplier portal events into the MasterOrchestrator.
    Designed to be fire-and-forget: HTTP response is never delayed waiting for agents.
    """

    async def notify(
        self,
        event_type_str: str,
        supplier_id: str,
        payload: Optional[Dict[str, Any]] = None,
        db: Any = None,
    ) -> None:
        """
        Trigger the MasterOrchestrator for a supplier portal event.
        Runs as a background task — caller does NOT await the AI pipeline.

        Args:
            event_type_str: The EventType enum value string
            supplier_id: Supabase UID of the supplier who triggered the event
            payload: Event-specific data dict
            db: Optional SQLAlchemy session for orchestrator DB persistence
        """
        try:
            from app.orchestrator.orchestrator import MasterOrchestrator
            orchestrator = MasterOrchestrator.get_instance()

            trigger_payload = {
                "source": "supplier_portal",
                "event_type": event_type_str,
                "supplier_id": supplier_id,
                **(payload or {}),
            }

            # Fire and forget — do not block the HTTP response
            asyncio.create_task(
                orchestrator.trigger(
                    trigger_type="event",
                    payload=trigger_payload,
                    db=db,
                )
            )
            logger.info(
                f"[orchestrator_bridge] ▶ Dispatched {event_type_str!r} "
                f"for supplier={supplier_id[:8]}"
            )
        except RuntimeError as exc:
            # Orchestrator not initialized yet (e.g., during testing / cold start)
            logger.warning(
                f"[orchestrator_bridge] Orchestrator not ready — "
                f"event {event_type_str!r} not dispatched: {exc}"
            )
        except Exception as exc:
            # Never fail the supplier's request due to orchestrator issues
            logger.error(
                f"[orchestrator_bridge] Unexpected error dispatching {event_type_str!r}: {exc}",
                exc_info=True,
            )

    def notify_sync(
        self,
        event_type_str: str,
        supplier_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Synchronous fire-and-forget wrapper for use in non-async contexts.
        Safely dispatches event without blocking request execution.
        """
        try:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.notify(event_type_str, supplier_id, payload))
            except RuntimeError:
                pass
        except Exception as exc:
            logger.warning(f"[orchestrator_bridge] sync notify failed: {exc}")


# Module-level singleton
orchestrator_bridge = OrchestratorBridge()
