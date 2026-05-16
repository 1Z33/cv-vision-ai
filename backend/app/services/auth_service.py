"""
Service d'authentification : logique métier pour register/login.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.core.logging import logger


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_email(self, email: str) -> User | None:
        """Récupère un utilisateur par son email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Récupère un utilisateur par son ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        Crée un nouvel utilisateur avec mot de passe hashé.
        
        Raises:
            ValueError: Si l'email existe déjà
        """
        # Vérifier si l'email existe déjà
        existing = await self.get_user_by_email(user_data.email)
        if existing:
            raise ValueError("Un utilisateur avec cet email existe déjà")
        
        # Créer l'utilisateur
        db_user = User(
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name
        )
        
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        logger.info(f"Nouvel utilisateur créé: {db_user.email}")
        return db_user
    
    async def authenticate_user(self, email: str, password: str) -> User | None:
        """
        Authentifie un utilisateur avec email + mot de passe.
        
        Returns:
            User si authentification réussie, None sinon
        """
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        logger.info(f"Utilisateur authentifié: {user.email}")
        return user
    
    def create_tokens(self, user: User) -> dict:
        """
        Génère les tokens JWT pour un utilisateur.
        
        Returns:
            Dict avec access_token et refresh_token
        """
        token_data = {"sub": str(user.id), "email": user.email}
        
        return {
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
            "token_type": "bearer"
        }