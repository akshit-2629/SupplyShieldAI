from pydantic import BaseModel

class HealthResponse(BaseModel):
    """
    Schema for generic health responses.
    """
    status: str
    service: str

class DatabaseHealthResponse(BaseModel):
    """
    Schema for database check responses.
    """
    database: str
