import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    APP_NAME: str = Field(default="SupplyShield AI")
    APP_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="production")
    LOG_LEVEL: str = Field(default="INFO")

    # Database Configuration
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="supplyshield")

    # Optional: full connection URL override (takes priority over individual POSTGRES_* vars)
    # Paste full Supabase connection string here from: Dashboard → Settings → Database → URI
    DATABASE_URL: Optional[str] = Field(default=None)

    # Supabase Configuration
    SUPABASE_URL: str = Field(default="")
    SUPABASE_ANON_KEY: str = Field(default="")
    SUPABASE_JWT_SECRET: str = Field(default="")

    # Supabase Admin (service role key — NEVER expose to clients)
    # Required for backend admin operations: creating users, bypassing RLS
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="")

    # Google OAuth 2.0
    # Obtain from: Google Cloud Console → APIs & Services → Credentials
    GOOGLE_CLIENT_ID: str = Field(default="")
    GOOGLE_CLIENT_SECRET: str = Field(default="")
    GOOGLE_REDIRECT_URI: str = Field(default="http://localhost:8000/api/v1/auth/google/callback")

    # Frontend URL — used for post-auth redirects from backend OAuth flow
    FRONTEND_URL: str = Field(default="http://localhost:5173")

    # AI / External API Keys
    GEMINI_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None   # Phase 3: News Intelligence
    QDRANT_URL:     Optional[str] = None

    # Phase 3: News Intelligence Scheduler
    # How often the background news pipeline runs (in minutes)
    NEWS_COLLECTION_INTERVAL_MINUTES: int = Field(default=15)
    # Set to False to disable auto-start (useful during tests)
    NEWS_SCHEDULER_AUTO_START: bool = Field(default=True)

    # SMTP Configuration (Gmail, SendGrid, Mailgun, AWS SES, Custom SMTP)
    SMTP_HOST: Optional[str] = Field(default=None)
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    SMTP_FROM_EMAIL: Optional[str] = Field(default=None)
    SMTP_FROM_NAME: str = Field(default="SupplyShield AI")
    SMTP_TLS: bool = Field(default=True)


    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Returns DATABASE_URL if set, otherwise builds from individual POSTGRES_* vars."""
        if self.DATABASE_URL:
            # Supabase returns postgresql+asyncpg:// or postgres:// — normalise to postgresql://
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()

