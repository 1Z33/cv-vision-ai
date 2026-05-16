"""
Configuration des fixtures pour pytest.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import delete

from app.db.base import Base
from app.models.user import User
from app.models.cv import CV
from app.models.analysis import Analysis
from app.models.interview import InterviewSession, InterviewQA
from app.models.job import Job
from app.models.match import Match

# Base de données de test (SQLite en mémoire pour les tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    """Fixture pour une session DB propre par test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Créer les tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        yield session
        # Nettoyer après le test
        await session.rollback()
    
    # Supprimer les tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def sample_user_data():
    """Données d'utilisateur de test."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123",
        "full_name": "Test User"
    }