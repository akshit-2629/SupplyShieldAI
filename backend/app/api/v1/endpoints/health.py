from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.schemas.health import HealthResponse, DatabaseHealthResponse
from app.core.config import settings

router = APIRouter()

@router.get("/", response_model=HealthResponse)
def get_root():
    """
    Base API v1 health check endpoint.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME
    }

@router.get("/health", response_model=HealthResponse)
def get_health():
    """
    Standard health check endpoint.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME
    }

@router.get("/health/application")
def get_application_health():
    """
    Detailed server environment and application status configurations.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG
    }

@router.get("/health/database", response_model=DatabaseHealthResponse)
def get_database_health(db: Session = Depends(get_db)):
    """
    Performs validation query against the database engine session.
    """
    try:
        # Run standard ping statement to ensure connectivity
        db.execute(text("SELECT 1"))
        return {
            "database": "connected"
        }
    except Exception as e:
        from app.core.exceptions import DatabaseException
        # Raise DatabaseException to be mapped by global handlers
        raise DatabaseException(
            message=f"Database connection failed: {str(e)}",
            error_code="DB_CONNECTION_ERROR"
        )

@router.get("/health/validation-test")
def validation_test(value: int):
    """
    Test endpoint to trigger validation exceptions.
    """
    return {"value": value}

