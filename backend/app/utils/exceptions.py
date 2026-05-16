"""
Exceptions personnalisées pour l'application.
"""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Exception de base pour l'application."""
    pass


class AuthenticationError(AppException):
    """Erreur d'authentification."""
    
    def __init__(self, detail: str = "Authentification échouée"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(AppException):
    """Erreur d'autorisation."""
    
    def __init__(self, detail: str = "Accès non autorisé"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class NotFoundError(AppException):
    """Ressource non trouvée."""
    
    def __init__(self, detail: str = "Ressource non trouvée"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class ValidationError(AppException):
    """Erreur de validation des données."""
    
    def __init__(self, detail: str = "Données invalides"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class FileError(AppException):
    """Erreur liée aux fichiers."""
    
    def __init__(self, detail: str = "Erreur de traitement du fichier"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )