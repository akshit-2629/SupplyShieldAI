"""
supabase_client.py — Central Supabase REST API client singleton.

All API endpoints use this instead of direct SQLAlchemy connections when
the direct DB connection is unavailable (e.g. Supabase free tier firewall).

The client uses the service_role key so it bypasses RLS and can read all rows.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("db.supabase_client")

_client = None


def get_supabase():
    """Return the singleton Supabase admin client (lazy init)."""
    global _client
    if _client is not None:
        return _client

    try:
        from supabase import create_client
        from app.core.config import settings

        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            logger.warning("[supabase_client] Missing SUPABASE_URL or SERVICE_ROLE_KEY")
            return None

        _client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
        logger.info("[supabase_client] Supabase client initialized")
    except Exception as e:
        logger.error(f"[supabase_client] Init failed: {e}")
        return None

    return _client
