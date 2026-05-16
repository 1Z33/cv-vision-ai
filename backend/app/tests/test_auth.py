"""
Tests du module d'authentification.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import AuthService
from app.schemas.user import UserCreate
from app.core.security import verify_password


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession, sample_user_data):
    """Test la création d'un utilisateur."""
    service = AuthService(db_session)
    
    user_data = UserCreate(**sample_user_data)
    user = await service.create_user(user_data)
    
    assert user.email == sample_user_data["email"]
    assert user.full_name == sample_user_data["full_name"]
    assert verify_password(sample_user_data["password"], user.hashed_password)


@pytest.mark.asyncio
async def test_authenticate_user(db_session: AsyncSession, sample_user_data):
    """Test l'authentification d'un utilisateur."""
    service = AuthService(db_session)
    
    # Créer l'utilisateur
    user_data = UserCreate(**sample_user_data)
    await service.create_user(user_data)
    
    # Authentifier
    user = await service.authenticate_user(
        sample_user_data["email"],
        sample_user_data["password"]
    )
    
    assert user is not None
    assert user.email == sample_user_data["email"]


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(db_session: AsyncSession, sample_user_data):
    """Test l'authentification avec mauvais mot de passe."""
    service = AuthService(db_session)
    
    user_data = UserCreate(**sample_user_data)
    await service.create_user(user_data)
    
    user = await service.authenticate_user(
        sample_user_data["email"],
        "wrong_password"
    )
    
    assert user is None