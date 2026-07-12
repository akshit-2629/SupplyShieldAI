"""
PriorityTaskQueue — Async min-heap priority queue for agent task scheduling.

Uses Python's heapq (min-heap) so:
  - Lower priority integer = higher urgency
  - Tasks with equal priority are processed FIFO (via sequence counter)
  - get() blocks until a task is available (no busy-waiting)

TaskPriority constants:
  CRITICAL  = 1  (e.g. active factory shutdown)
  HIGH      = 2  (e.g. major port closure)
  NORMAL    = 3  (e.g. routine news scan)
  LOW       = 4  (e.g. scheduled re-scoring)
  BACKGROUND = 5 (e.g. graph maintenance)
"""

from __future__ import annotations

import asyncio
import heapq
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("orchestrator.task_queue")


class TaskPriority:
    """Priority constants — lower value = executed first."""
    CRITICAL   = 1
    HIGH       = 2
    NORMAL     = 3
    LOW        = 4
    BACKGROUND = 5


@dataclass(order=True)
class Task:
    """
    A unit of work dispatched to an agent.

    Ordering: first by priority (int), then by sequence (insertion order)
    so equal-priority tasks are FIFO.
    """
    priority:     int
    sequence:     int    = field(compare=True,  default=0)
    # Non-comparable fields (compare=False)
    task_id:      str    = field(compare=False, default_factory=lambda: str(uuid.uuid4()))
    agent_id:     str    = field(compare=False, default="")
    payload:      Dict[str, Any] = field(compare=False, default_factory=dict)
    retry_count:  int    = field(compare=False, default=0)
    max_retries:  int    = field(compare=False, default=3)
    created_at:   datetime = field(compare=False, default_factory=datetime.utcnow)
    execution_id: str    = field(compare=False, default="")

    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

    def next_retry_delay_seconds(self) -> float:
        """Exponential backoff: 1 s, 2 s, 4 s, 8 s ..."""
        return float(2 ** self.retry_count)


class PriorityTaskQueue:
    """
    Thread-safe async priority queue backed by Python's heapq.

    put()  — add a task (O log n)
    get()  — remove and return the highest-priority task; blocks if empty
    peek() — inspect without removing
    """

    def __init__(self) -> None:
        self._heap:    List[Task] = []
        self._lock:    asyncio.Lock   = asyncio.Lock()
        self._not_empty: asyncio.Event = asyncio.Event()
        self._sequence = 0
        self._total_enqueued = 0
        self._total_dequeued = 0

    async def put(self, task: Task) -> None:
        """Enqueue a task. Assigns an insertion-order sequence for FIFO tie-breaking."""
        async with self._lock:
            task.sequence = self._sequence
            self._sequence += 1
            heapq.heappush(self._heap, task)
            self._total_enqueued += 1
            self._not_empty.set()
        logger.debug(
            f"[task_queue] Enqueued task {task.task_id[:8]} "
            f"for [{task.agent_id}] priority={task.priority}"
        )

    async def get(self) -> Task:
        """
        Dequeue the highest-priority task.
        Blocks (yields to event loop) if the queue is currently empty.
        """
        while True:
            # Fast path: queue already has items
            async with self._lock:
                if self._heap:
                    task = heapq.heappop(self._heap)
                    self._total_dequeued += 1
                    if not self._heap:
                        self._not_empty.clear()
                    logger.debug(
                        f"[task_queue] Dequeued task {task.task_id[:8]} "
                        f"for [{task.agent_id}]"
                    )
                    return task
            # Slow path: wait until something is enqueued
            await self._not_empty.wait()

    async def peek(self) -> Optional[Task]:
        """Return the top task without removing it."""
        async with self._lock:
            return self._heap[0] if self._heap else None

    def size(self) -> int:
        return len(self._heap)

    def is_empty(self) -> bool:
        return not self._heap

    def stats(self) -> dict:
        return {
            "current_size":   len(self._heap),
            "total_enqueued": self._total_enqueued,
            "total_dequeued": self._total_dequeued,
        }
