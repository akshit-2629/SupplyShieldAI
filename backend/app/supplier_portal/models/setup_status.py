"""
SupplierSetupStatus — tracks wizard completion for a supplier.
One row per supplier.  Updated atomically on each wizard step save.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Boolean, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.models.base import Base


class SupplierSetupStatus(Base):
    __tablename__ = "supplier_setup_status"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id     = Column(Text, nullable=False, unique=True, index=True)

    # Step completion flags
    step_company_profile = Column(Boolean, nullable=False, default=False)
    step_contacts        = Column(Boolean, nullable=False, default=False)
    step_locations       = Column(Boolean, nullable=False, default=False)
    step_products        = Column(Boolean, nullable=False, default=False)
    step_production      = Column(Boolean, nullable=False, default=False)
    step_lead_times      = Column(Boolean, nullable=False, default=False)
    step_certifications  = Column(Boolean, nullable=False, default=False)
    step_media           = Column(Boolean, nullable=False, default=False)

    is_complete      = Column(Boolean, nullable=False, default=False)
    completion_pct   = Column(Integer, nullable=False, default=0)

    wizard_started_at   = Column(DateTime(timezone=True), nullable=True)
    wizard_completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # ── Helper ──────────────────────────────────────────────────────────────
    STEPS = [
        "step_company_profile", "step_contacts", "step_locations",
        "step_products", "step_production", "step_lead_times",
        "step_certifications", "step_media",
    ]

    def recalculate(self) -> None:
        """Recompute is_complete and completion_pct from step flags."""
        done = sum(bool(getattr(self, s)) for s in self.STEPS)
        self.completion_pct = int(done / len(self.STEPS) * 100)
        self.is_complete    = done == len(self.STEPS)
        if self.is_complete and not self.wizard_completed_at:
            self.wizard_completed_at = datetime.now(timezone.utc)
