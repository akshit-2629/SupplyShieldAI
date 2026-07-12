from fastapi import status

def test_root_welcome_endpoint(client):
    """
    Asserts welcome entrypoint details correct service fields.
    """
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["service"] == "SupplyShield AI"

def test_health_v1_endpoint(client):
    """
    Asserts GET /api/v1/health maps correct healthy payload.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status": "healthy",
        "service": "SupplyShield AI"
    }

def test_application_health_details(client):
    """
    Asserts detailed application parameters exist.
    """
    response = client.get("/api/v1/health/application")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert "debug_mode" in data

def test_database_health_checks(client):
    """
    Asserts connection validation query connects and passes correctly.
    """
    response = client.get("/api/v1/health/database")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "database": "connected"
    }
