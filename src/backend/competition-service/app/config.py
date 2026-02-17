"""
Configuration module for Competition Service

All sensitive configuration is loaded from environment variables.
Never commit secrets to version control.
"""

import os
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    """Application settings - loaded from environment variables"""

    # Service Configuration
    SERVICE_NAME: str = "competition-service"
    SERVICE_PORT: int = 8080
    SERVICE_HOST: str = "0.0.0.0"
    DEBUG: bool = False  # Default to False for safety
    ENVIRONMENT: str = "production"  # Default to production for safety

    # Database - MUST be set via environment variable
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://avar_user:avar_password@localhost:5432/avar_db"
    )
    DATABASE_ECHO: bool = False  # Disable SQL logging in production

    # JWT Configuration - MUST be set via environment variable
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Service URLs
    AI_DETECTION_SERVICE_URL: str = os.getenv(
        "AI_DETECTION_SERVICE_URL", "http://ai-detection-service:8001"
    )
    API_GATEWAY_URL: str = os.getenv(
        "API_GATEWAY_URL", "http://api-gateway:8000"
    )

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024  # 50MB in bytes
    UPLOAD_DIR: str = "./uploads"
    ALLOWED_IMAGE_EXTENSIONS: str = "jpg,jpeg,png,tiff,raw,cr2,nef,arw,dng"

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # CORS - Properly configured, no wildcards
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://localhost:8080"
    )

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Ensure JWT secret is set and strong enough"""
        if not v or len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be set and at least 32 characters. "
                "Generate one with: openssl rand -hex 32"
            )
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list - no wildcards allowed"""
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        # Remove any wildcards for security
        return [o for o in origins if o != "*"]

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get allowed file extensions as list"""
        return [ext.strip().lower() for ext in self.ALLOWED_IMAGE_EXTENSIONS.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT.lower() == "production" and not self.DEBUG

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra env vars


# Global settings instance
settings = Settings()
