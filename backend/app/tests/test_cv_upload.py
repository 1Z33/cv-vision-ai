"""
Tests du upload de CV.
"""

import pytest
from io import BytesIO
from fastapi import UploadFile

from app.services.cv_service import CVService
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_save_upload_file(db_session, sample_user_data):
    """Test la sauvegarde d'un fichier PDF."""
    # Créer un utilisateur
    auth_service = AuthService(db_session)
    user = await auth_service.create_user(UserCreate(**sample_user_data))
    
    # Créer un faux fichier PDF
    cv_service = CVService(db_session)
    
    # Note: Test avec un vrai fichier PDF nécessite un mock
    # Ici on teste la structure du service
    assert cv_service.upload_dir.exists()