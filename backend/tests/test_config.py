import os
from app.core.config import settings

def test_settings_load_defaults():
    """
    Validates that default configurations parse correctly when no custom env is set.
    """
    assert settings.APP_NAME == "SupplyShield AI"
    assert settings.APP_VERSION == "1.0.0"
    assert settings.ENVIRONMENT in ["development", "testing", "production"]
    assert "postgresql://" in settings.SQLALCHEMY_DATABASE_URI
