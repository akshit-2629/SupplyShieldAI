"""
AsyncEventBus — In-process async pub/sub event system.

Agents publish events after completing work instead of calling each other
directly. This keeps agents loosely coupled — adding a new subscriber
(agent, monitor, logger) requires zero changes to the publisher.

Design:
  - Handlers are async coroutines, called concurrently via asyncio.gather
  - Handler errors are isolated: one failing handler never blocks others
  - Event history (ringbuffer, max_history=1000) supports debugging/replay
  - Wildcard subscriptions receive ALL event types (useful for monitors)

In Phase 20 (Production), this class will be backed by Redis Pub/Sub
or Kafka without changing any agent code.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine, Dict, List, Optional

from app.orchestrator.events import Event, EventType

logger = logging.getLogger("orchestrator.event_bus")

# A handler is an async function that accepts an Event
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class AsyncEventBus:
    """
    Async pub/sub event bus with history, wildcards, and isolated handler errors.

    Usage:
        bus = AsyncEventBus()

        async def my_handler(event: Event):
            print(event.type, event.payload)

        bus.subscribe(EventType.NEWS_DISRUPTION_DETECTED, my_handler)
        await bus.publish(Event(type=EventType.NEWS_DISRUPTION_DETECTED, ...))
    """

    def __init__(self, max_history: int = 1000) -> None:
        # Typed subscribers: event_type → list of handlers
        self._subscribers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        # Wildcard subscribers receive every event regardless of type
        self._wildcard_subscribers: List[EventHandler] = []
        # Ringbuffer for event history / debugging
        self._history: List[Event] = []
        self._max_history = max_history
        self._lock = asyncio.Lock()
        # Counters
        self._publish_count = 0
        self._error_count = 0

    # ── Subscription API ──────────────────────────────────────────────────────

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe handler to a specific event type."""
        self._subscribers[event_type].append(handler)
        logger.debug(f"[event_bus] {handler.__name__!r} subscribed to {event_type.value!r}")

    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe handler to ALL event types (wildcard)."""
        self._wildcard_subscribers.append(handler)
        logger.debug(f"[event_bus] {handler.__name__!r} subscribed to all events (wildcard)")

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Remove a handler from a specific event type."""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    # ── Publishing API ────────────────────────────────────────────────────────

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all matching subscribers.

        Handlers are invoked concurrently. A failure in one handler
        is logged but never propagates to stop other handlers.
        """
        # Store in history (under lock to avoid corruption)
        async with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history.pop(0)
            self._publish_count += 1

        handlers = [
            *self._subscribers.get(event.type, []),
            *self._wildcard_subscribers,
        ]

        if not handlers:
            logger.debug(f"[event_bus] {event.type.value} published (no subscribers)")
            return

        logger.info(
            f"[event_bus] Publishing {event.type.value!r} "
            f"from [{event.source_agent}] → {len(handlers)} handler(s)"
        )

        # Run all handlers concurrently; collect exceptions without raising
        results = await asyncio.gather(
            *[self._safe_invoke(h, event) for h in handlers],
            return_exceptions=True,
        )

        for res in results:
            if isinstance(res, Exception):
                self._error_count += 1
                logger.error(
                    f"[event_bus] Handler error for {event.type.value}: {res}"
                )

    async def _safe_invoke(self, handler: EventHandler, event: Event) -> None:
        """Wrap handler call so exceptions propagate to gather's return_exceptions."""
        await handler(event)

    # ── Inspection API ────────────────────────────────────────────────────────

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        source_agent: Optional[str] = None,
        execution_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Event]:
        """Return filtered event history (most recent `limit` items)."""
        events = list(self._history)
        if event_type:
            events = [e for e in events if e.type == event_type]
        if source_agent:
            events = [e for e in events if e.source_agent == source_agent]
        if execution_id:
            events = [e for e in events if e.execution_id == execution_id]
        return events[-limit:]

    def stats(self) -> dict:
        return {
            "total_published":    self._publish_count,
            "total_handler_errors": self._error_count,
            "history_size":       len(self._history),
            "typed_subscribers":  sum(len(v) for v in self._subscribers.values()),
            "wildcard_subscribers": len(self._wildcard_subscribers),
        }

    def clear_history(self) -> None:
        self._history.clear()


# ── Module-level singleton ─────────────────────────────────────────────────────
# Imported and reused across the entire application.
# Components subscribe at import time; publish during request handling.
event_bus = AsyncEventBus()
