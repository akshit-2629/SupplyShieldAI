"""
app/core/json_utils.py — Helper for recursively sanitizing non-JSON serializable objects (datetime, date, UUID, Decimal).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any


def sanitize_json_payload(obj: Any) -> Any:
    """
    Recursively converts datetime, date, time, UUID, Decimal, and set objects
    into standard JSON-serializable primitives (ISO8601 strings, str, float, list).
    
    Ensures Python objects are never persisted directly into Postgres JSON/JSONB fields.
    """
    if obj is None:
        return None
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {str(k): sanitize_json_payload(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_json_payload(x) for x in obj]
    return obj
