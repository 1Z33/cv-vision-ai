import os

"""
Configuration centralisée de l'application via Pydantic Settings.
Charge automatiquement les variables depuis .env
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


def _build_async_database_url(url: str) -> str:
    """Retourne une URL de base de données SQLAlchemy async compatible."""
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite:///") and "+aiosqlite" not in url:
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    return url


class Settings(BaseSettings):
    # ============================================
    # BASE DE DONNÉES
    # ============================================
    DATABASE_URL: str = _build_async_database_url(
        os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./cv_vision_ai.db")
    )
    SYNC_DATABASE_URL: str = os.getenv(
        "SYNC_DATABASE_URL",
        os.getenv("DATABASE_URL", "sqlite:///./cv_vision_ai.db"),
    )
    
    # ============================================
    # SÉCURITÉ JWT
    # ============================================
    SECRET_KEY: str = "votre-cle-secrete-changez-moi-immediatement-123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ============================================
    # ENVIRONNEMENT
    # ============================================
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # ============================================
    # UPLOADS
    # ============================================
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 5
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra='ignore'
    )


# Instance singleton des settings
settings = Settings()