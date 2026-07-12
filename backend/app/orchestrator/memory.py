"""
AgentMemory — Shared key-value memory store for the orchestrator workflow.

Provides two namespaces:
  1. Global workspace  — any agent can read/write (e.g. shared disruption context)
  2. Agent-private     — per-agent_id store (e.g. agent's own running totals)

Thread-safe via asyncio.Lock.
In Phase 20 (Production), this will be backed by Redis for cross-process sharing.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("orchestrator.memory")


class AgentMemory:
    """
    In-process shared memory with global and per-agent namespaces.

    Global memory:
        await memory.set("key", value)
        value = await memory.get("key")

    Agent-private memory:
        await memory.set("key", value, agent_id="news_agent")
        value = await memory.get("key", agent_id="news_agent")
    """

    def __init__(self) -> None:
        self._global: Dict[str, Any]              = {}
        self._per_agent: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._write_log: List[dict]               = []
        self._lock = asyncio.Lock()

    # ── Write / Read ──────────────────────────────────────────────────────────

    async def set(
        self,
        key: str,
        value: Any,
        agent_id: Optional[str] = None,
    ) -> None:
        async with self._lock:
            if agent_id:
                self._per_agent[agent_id][key] = value
            else:
                self._global[key] = value
            self._write_log.append({
                "key":       key,
                "agent_id":  agent_id,
                "timestamp": datetime.utcnow().isoformat(),
            })

    async def get(
        self,
        key: str,
        agent_id: Optional[str] = None,
        default: Any = None,
    ) -> Any:
        async with self._lock:
            if agent_id:
                return self._per_agent[agent_id].get(key, default)
            return self._global.get(key, default)

    async def delete(self, key: str, agent_id: Optional[str] = None) -> None:
        async with self._lock:
            if agent_id:
                self._per_agent[agent_id].pop(key, None)
            else:
                self._global.pop(key, None)

    # ── Snapshots ─────────────────────────────────────────────────────────────

    async def get_agent_snapshot(self, agent_id: str) -> Dict[str, Any]:
        """Return a copy of an agent's private memory."""
        async with self._lock:
            return dict(self._per_agent.get(agent_id, {}))

    async def get_global_snapshot(self) -> Dict[str, Any]:
        """Return a copy of the global shared memory."""
        async with self._lock:
            return dict(self._global)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def clear_agent(self, agent_id: str) -> None:
        async with self._lock:
            self._per_agent[agent_id].clear()

    async def clear_all(self) -> None:
        async with self._lock:
            self._global.clear()
            self._per_agent.clear()
            self._write_log.clear()

    def stats(self) -> dict:
        return {
            "global_keys":  len(self._global),
            "agent_count":  len(self._per_agent),
            "total_writes": len(self._write_log),
        }

    def write_log(self, limit: int = 50) -> List[dict]:
        return self._write_log[-limit:]
