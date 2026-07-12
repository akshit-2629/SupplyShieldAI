"""
BaseAgent — Abstract base class for all SupplyShield AI agents.

Every agent (News, Risk, Graph, Supplier, Inventory, Recommendation) must:
  1. Inherit from BaseAgent
  2. Set class attributes: agent_id, description
  3. Implement: async execute(state) → Dict[str, Any]
  4. Optionally override: async health_check() → bool

The run() method wraps execute() with:
  - Exponential backoff retry (1 s → 2 s → 4 s → ...)
  - Duration tracking
  - Status transitions (IDLE → RUNNING → COMPLETED/FAILED)
  - Standardised AgentResult dict structure

The execute() method must return a PARTIAL WorkflowState dict containing
only the keys this agent updates. LangGraph merges partials automatically.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from app.orchestrator.state import WorkflowState

logger = logging.getLogger("agent.base")


class AgentStatus(str, Enum):
    IDLE      = "idle"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    DISABLED  = "disabled"


class BaseAgent(ABC):
    """
    Abstract base for all SupplyShield AI agents.

    Class attributes to define in subclasses:
        agent_id:    str   — unique identifier, e.g. "news_agent"
        description: str   — human-readable purpose
        version:     str   — semantic version, default "0.1.0"
    """

    agent_id:    str
    description: str
    version:     str = "0.1.0"

    def __init__(self) -> None:
        self._status:          AgentStatus     = AgentStatus.IDLE
        self._enabled:         bool            = True
        self._success_count:   int             = 0
        self._failure_count:   int             = 0
        self._last_error:      Optional[str]   = None
        self._last_run_at:     Optional[datetime] = None
        self._avg_duration_ms: float           = 0.0

    # ── Abstract interface ────────────────────────────────────────────────────

    @abstractmethod
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Execute the agent's primary logic.

        Args:
            state: Full WorkflowState from the orchestrator.

        Returns:
            A PARTIAL WorkflowState dict — only the fields this agent updates.
            LangGraph merges this with the existing state automatically.

        Must always include at minimum:
            {
                "agent_results":    [AgentResult],
                "completed_agents": [] | [self.agent_id],
                "failed_agents":    [] | [self.agent_id],
                "errors":           [],
            }
        """
        ...

    async def health_check(self) -> bool:
        """
        Override to add connectivity checks (e.g. can we reach the news API?).
        Default implementation returns True if the agent is enabled.
        """
        return self._enabled

    # ── Retry-aware execution ─────────────────────────────────────────────────

    async def run(self, state: WorkflowState, max_retries: int = 3) -> Dict[str, Any]:
        """
        Execute with exponential backoff retry.

        On each attempt:
          attempt 0 → immediate
          attempt 1 → sleep 1 s
          attempt 2 → sleep 2 s
          attempt 3 → sleep 4 s  (max_retries=3 means 4 total attempts)

        If all attempts fail, returns a structured failed result.
        """
        if not self._enabled:
            logger.warning(f"[{self.agent_id}] disabled — skipping execution")
            return self._skipped_result("Agent is disabled")

        last_exc: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            start = time.monotonic()
            self._status   = AgentStatus.RUNNING
            self._last_run_at = datetime.utcnow()

            try:
                result = await self.execute(state)
                duration_ms = int((time.monotonic() - start) * 1000)

                self._status = AgentStatus.COMPLETED
                self._success_count += 1
                self._update_avg_duration(duration_ms)

                logger.info(
                    f"[{self.agent_id}] ✓ completed in {duration_ms} ms "
                    f"(attempt {attempt + 1}/{max_retries + 1})"
                )
                return result

            except Exception as exc:
                last_exc = exc
                self._failure_count += 1
                self._last_error = str(exc)
                self._status    = AgentStatus.FAILED

                if attempt < max_retries:
                    delay = float(2 ** attempt)
                    logger.warning(
                        f"[{self.agent_id}] attempt {attempt + 1} failed: {exc}. "
                        f"Retrying in {delay:.0f} s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"[{self.agent_id}] ✗ all {max_retries + 1} attempts failed: {exc}"
                    )

        return self._failed_result(str(last_exc), retry_count=max_retries)

    # ── Standard result builders ──────────────────────────────────────────────

    def _skipped_result(self, reason: str) -> Dict[str, Any]:
        return {
            "agent_results": [{
                "agent_id":    self.agent_id,
                "status":      "skipped",
                "data":        {},
                "error":       reason,
                "duration_ms": 0,
                "retry_count": 0,
                "timestamp":   datetime.utcnow().isoformat(),
            }],
            "completed_agents": [],
            "failed_agents":    [],
            "errors":           [],
        }

    def _failed_result(self, error: str, retry_count: int = 0) -> Dict[str, Any]:
        return {
            "agent_results": [{
                "agent_id":    self.agent_id,
                "status":      "failed",
                "data":        {},
                "error":       error,
                "duration_ms": 0,
                "retry_count": retry_count,
                "timestamp":   datetime.utcnow().isoformat(),
            }],
            "completed_agents": [],
            "failed_agents":    [self.agent_id],
            "errors":           [f"[{self.agent_id}] {error}"],
        }

    def _update_avg_duration(self, duration_ms: int) -> None:
        n = self._success_count  # already incremented before this call
        if n == 0:
            n = 1
        self._avg_duration_ms = (
            (self._avg_duration_ms * (n - 1) + duration_ms) / n
        )

    # ── Control interface ─────────────────────────────────────────────────────

    def enable(self) -> None:
        self._enabled = True
        self._status  = AgentStatus.IDLE

    def disable(self) -> None:
        self._enabled = False
        self._status  = AgentStatus.DISABLED

    @property
    def status(self) -> AgentStatus:
        return self._status

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def health_snapshot(self) -> dict:
        """Return a serialisable health report for the registry and API."""
        return {
            "agent_id":       self.agent_id,
            "description":    self.description,
            "version":        self.version,
            "status":         self._status.value,
            "enabled":        self._enabled,
            "success_count":  self._success_count,
            "failure_count":  self._failure_count,
            "last_error":     self._last_error,
            "last_run_at":    self._last_run_at.isoformat() if self._last_run_at else None,
            "avg_duration_ms": round(self._avg_duration_ms, 2),
        }
