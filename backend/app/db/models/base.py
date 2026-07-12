from datetime import datetime, timezone
from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Custom constraints and naming convention configurations for Alembic migration stability
POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

class Base(DeclarativeBase):
    """
    Standard declarative class for database models.
    """
    metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)
    
    @classmethod
    @property
    def __tablename__(cls) -> str:
        """
        Dynamically infers table name from model class name in snake_case format.
        """
        name = cls.__name__
        out = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                out.append('_')
            out.append(char.lower())
        return "".join(out)

class AuditMixin:
    """
    Mixin tracking modification history for models.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
