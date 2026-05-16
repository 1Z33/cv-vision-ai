"""
Gestion de la sécurité : hash des mots de passe, création et vérification des tokens JWT.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal

# Contexte pour le hash bcrypt — éviter l'erreur de troncature du backend bcrypt
# et autoriser passlib à gérer les mots de passe plus longs sans lever d'exception.
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False,
)


def _truncate_password_to_72_bytes(password: str) -> str:
    """
    Tronque une chaîne UTF-8 à 72 octets (limite de bcrypt).
    Retourne une chaîne décodée en ignorant l'octet final tronqué si nécessaire.
    """
    if password is None:
        return password
    # encoder puis tronquer en octets, décoder en ignorant les caractères incomplets
    b = password.encode("utf-8")[:72]
    return b.decode("utf-8", errors="ignore")

# Schéma OAuth2 pour récupérer le token depuis le header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si un mot de passe correspond au hash (avec troncature sécurisée)."""
    return pwd_context.verify(_truncate_password_to_72_bytes(plain_password), hashed_password)


def get_password_hash(password: str) -> str:
    """Génère un hash bcrypt d'un mot de passe en tronquant à 72 octets si nécessaire."""
    return pwd_context.hash(_truncate_password_to_72_bytes(password))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un token JWT d'accès.
    
    Args:
        data: Payload à encoder (généralement {"sub": user_id})
        expires_delta: Durée de validité personnalisée
    
    Returns:
        Token JWT encodé
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Crée un token JWT de rafraîchissement (durée plus longue)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Décode et vérifie un token JWT.
    
    Returns:
        Payload décodé ou None si invalide
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dépendance FastAPI : récupère l'utilisateur courant depuis le token JWT.
    À utiliser comme dépendance sur les endpoints protégés.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    token_type: str = payload.get("type")
    
    if user_id is None or token_type != "access":
        raise credentials_exception
    
    return {"user_id": user_id, "email": payload.get("email")}