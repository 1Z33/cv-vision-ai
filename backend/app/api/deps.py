"""
Dépendances injectables pour FastAPI (DB, auth, etc.).
"""

from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import decode_token
from app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """
    Dépendance pour récupérer l'utilisateur authentifié.
    À utiliser sur les endpoints protégés.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id = payload.get("sub")
    token_type = payload.get("type")
    
    if user_id is None or token_type != "access":
        raise credentials_exception
    
    # Convertir user_id string en UUID
    try:
        user_id = UUID(user_id)
    except (ValueError, TypeError):
        raise credentials_exception
    
    # Vérifier que l'utilisateur existe toujours
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    
    if user is None or not user.is_active:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user = Depends(get_current_user)):
    """
    Vérifie que l'utilisateur est actif.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Utilisateur inactif")
    return current_user
