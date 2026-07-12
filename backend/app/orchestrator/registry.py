"""
AgentRegistry — Central directory for all SupplyShield AI agents.

Maintains live agent instances and their operational health.
The orchestrator uses the registry to discover, dispatch, and control agents.

Pattern: Registry / Service Locator
Thread-safe: yes (asyncio.Lock on write operations)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional

from app.agents.base import BaseAgent, AgentStatus

logger = logging.getLogger("orchestrator.registry")


class AgentRegistry:
    """
    Registry storing live BaseAgent instances keyed by agent_id.

    register()   — add or replace an agent
    get()        — retrieve agent by ID
    all()        — all registered agents
    all_enabled() — only agents that are currently enabled
    enable() / disable() — toggle agent execution
    health_report() — full health snapshot of all agents
    """

    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}
        self._lock = asyncio.Lock()

    # ── Registration ──────────────────────────────────────────────────────────

    async def register(self, agent: BaseAgent) -> None:
        """Register an agent. Re-registering an existing ID replaces the instance."""
        async with self._lock:
            self._agents[agent.agent_id] = agent
        logger.info(
            f"[registry] Registered [{agent.agent_id}] v{agent.version} — "
            f"{agent.description[:60]}..."
        )

    async def unregister(self, agent_id: str) -> None:
        async with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                logger.info(f"[registry] Unregistered [{agent_id}]")

    # ── Lookup ────────────────────────────────────────────────────────────────

    def get(self, agent_id: str) -> Optional[BaseAgent]:
        return self._agents.get(agent_id)

    def all(self) -> List[BaseAgent]:
        return list(self._agents.values())

    def all_enabled(self) -> List[BaseAgent]:
        return [a for a in self._agents.values() if a.is_enabled]

    def is_registered(self, agent_id: str) -> bool:
        return agent_id in self._agents

    def count(self) -> int:
        return len(self._agents)

    # ── Control ───────────────────────────────────────────────────────────────

    async def enable(self, agent_id: str) -> bool:
        """Enable an agent. Returns False if agent_id not found."""
        agent = self._agents.get(agent_id)
        if agent:
            agent.enable()
            logger.info(f"[registry] Enabled [{agent_id}]")
            return True
        return False

    async def disable(self, agent_id: str) -> bool:
        """Disable an agent (skips it in future workflow runs)."""
        agent = self._agents.get(agent_id)
        if agent:
            agent.disable()
            logger.info(f"[registry] Disabled [{agent_id}]")
            return True
        return False

    # ── Health ────────────────────────────────────────────────────────────────

    def health_report(self) -> List[dict]:
        """Return health snapshot for all registered agents."""
        return [agent.health_snapshot() for agent in self._agents.values()]
