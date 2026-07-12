from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings

# Setup database engine with robust connection pooling
# pool_pre_ping checks connections on fetch, preventing stale connection errors
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

# Session Local factory definition
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency generator yielding database sessions and ensuring closure.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
