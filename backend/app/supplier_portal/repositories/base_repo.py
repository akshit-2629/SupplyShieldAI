"""
BaseRepository — common DB patterns for all supplier portal repos.
"""
from __future__ import annotations
import math
from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar
from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Generic CRUD repository. All supplier portal repositories extend this.

    Subclasses set:
        model_class = SomeORMModel
    """
    model_class: Type[T]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, record_id: Any) -> Optional[T]:
        return self.db.query(self.model_class).filter(
            self.model_class.id == record_id
        ).first()

    def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[T], int]:
        """Returns (rows, total_count) for pagination."""
        q = self.db.query(self.model_class)
        if filters:
            for col, val in filters.items():
                if val is not None and hasattr(self.model_class, col):
                    q = q.filter(getattr(self.model_class, col) == val)
        total = q.count()
        if order_by and hasattr(self.model_class, order_by):
            col = getattr(self.model_class, order_by)
            q = q.order_by(col.desc() if order_desc else col.asc())
        rows = q.offset(offset).limit(limit).all()
        return rows, total

    def create(self, obj: T) -> T:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: T, data: Dict[str, Any]) -> T:
        for key, val in data.items():
            if val is not None and hasattr(obj, key):
                setattr(obj, key, val)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: T) -> None:
        self.db.delete(obj)
        self.db.commit()

    def soft_delete(self, obj: T, field: str = "deleted_at") -> T:
        from datetime import datetime, timezone
        setattr(obj, field, datetime.now(timezone.utc))
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def total_pages(self, total: int, page_size: int) -> int:
        return math.ceil(total / page_size) if page_size > 0 else 1
