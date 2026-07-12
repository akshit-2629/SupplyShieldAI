from fastapi import status
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

def test_validation_error_formatting(client):
    """
    Asserts bad formatting triggers custom validation payload formats.
    """
    # Trigger validation by requesting an integer parameter with a string
    response = client.get("/api/v1/health/validation-test?value=invalid-format")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "query -> value" in data["message"]

def test_http_unauthorized_error_formatting(client):
    """
    Asserts security exceptions map HTTP codes to standard formats.
    """
    # Request JWT protected endpoint without credentials
    response = client.get("/api/v1/security-demo/jwt-protected")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "UNAUTHORIZED"
    assert "Bearer token missing" in data["message"]

def test_database_operational_error_formatting(client, monkeypatch):
    """
    Asserts database failures are captured and return clean connection errors.
    """
    def mock_db_ping(*args, **kwargs):
        raise OperationalError("Connection refused by test mock", params=None, orig=None)
        
    monkeypatch.setattr(Session, "execute", mock_db_ping)
    
    response = client.get("/api/v1/health/database")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "DB_CONNECTION_ERROR"
    assert "Database connection failed" in data["message"]
