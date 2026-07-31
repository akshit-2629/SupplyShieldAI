"""
Common Pydantic schemas shared across all supplier portal modules.
"""
from __future__ import annotations
from typing import Any, Dict, Generic, List, Optional, TypeVar
from datetime import datetime
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard envelope for all API responses."""
    success: bool = True
    message: str = "OK"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response with cursor metadata."""
    success: bool = True
    message: str = "OK"
    data: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PaginationParams(BaseModel):
    """Common query params for paginated endpoints."""
    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = None
    sort_order: str = "desc"   # "asc" | "desc"
    search: Optional[str] = None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class AuditEntry(BaseModel):
    """Read-only audit log entry exposed via API."""
    id: str
    action: str
    entity: str
    entity_id: Optional[str]
    old_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


def paginate(total: int, page: int, page_size: int) -> dict:
    """Compute pagination metadata."""
    import math
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if page_size > 0 else 1,
    }
