"""
Routes API pour l'authentification (register, login, refresh).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token, TokenRefresh
from app.services.auth_service import AuthService
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Crée un nouveau compte utilisateur.
    """
    auth_service = AuthService(db)
    
    try:
        user = await auth_service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Authentifie un utilisateur et retourne les tokens JWT.
    """
    auth_service = AuthService(db)
    
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tokens = auth_service.create_tokens(user)
    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """
    Rafraîchit les tokens d'accès avec un refresh token valide.
    """
    from app.core.security import decode_token, create_access_token, create_refresh_token
    
    payload = decode_token(refresh_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token invalide")
    
    user_id = payload.get("sub")
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé ou inactif")
    
    token_data = {"sub": str(user.id), "email": user.email}
    
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    """
    Retourne les informations de l'utilisateur connecté.
    """
    return current_user