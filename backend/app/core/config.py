import os
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


def _build_sync_database_url(url: str) -> str:
    """Retourne une URL de base de données SQLAlchemy sync compatible (pour Alembic)."""
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if url.startswith("sqlite+aiosqlite:///"):
        return url.replace("sqlite+aiosqlite:///", "sqlite:///", 1)
    return url


class Settings(BaseSettings):
    # ============================================
    # BASE DE DONNÉES
    # ============================================
    DATABASE_URL: str = _build_async_database_url(
        os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./cv_vision_ai.db")
    )
    SYNC_DATABASE_URL: str = _build_sync_database_url(
        os.getenv("SYNC_DATABASE_URL", 
                  os.getenv("DATABASE_URL", "sqlite:///./cv_vision_ai.db"))
    )
    
    # ============================================
    # SÉCURITÉ JWT
    # ============================================
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", 
        "votre-cle-secrete-changez-moi-immediatement-123456789"
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # ============================================
    # ENVIRONNEMENT
    # ============================================
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    
    # ============================================
    # UPLOADS
    # ============================================
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra='ignore'
    )


# Instance singleton des settings
settings = Settings()