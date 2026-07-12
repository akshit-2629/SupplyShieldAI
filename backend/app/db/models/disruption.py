from sqlalchemy import String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.base import Base, AuditMixin

class DisruptionEvent(Base, AuditMixin):
    """
    Database model representing active supply chain disruptions.
    """
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(50), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    impact_score: Mapped[float] = mapped_column(Float, default=0.0)
