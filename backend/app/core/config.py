from pathlib import Path
from typing import List, Union
from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve paths to locate .env whether run from repo root, backend, or scripts directory
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ENV_FILE_CANDIDATES = (
    _BACKEND_DIR / ".env",
    _BACKEND_DIR.parent / ".env",
    Path(".env"),
)

for _candidate in _ENV_FILE_CANDIDATES:
    if _candidate.is_file():
        load_dotenv(_candidate, override=False)
        break


class Settings(BaseSettings):
    PROJECT_NAME: str = "DealFlow360"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000

    # PostgreSQL Database (Direct / Self-Managed)
    DATABASE_URL: str = "postgresql://dealflow_user:dealflow_password@localhost:5432/dealflow360"

    # Manual Authentication Configuration
    JWT_SECRET_KEY: str = "dealflow360-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_COOKIE_NAME: str = "refresh_token"
    REFRESH_COOKIE_SECURE: bool = False
    REFRESH_COOKIE_SAMESITE: str = "lax"
    REFRESH_COOKIE_HTTPONLY: bool = True

    # Security & CORS
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        return []

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE_CANDIDATES,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
