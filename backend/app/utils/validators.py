"""
Validateurs réutilisables pour l'application.
"""

import re
from pathlib import Path
from fastapi import UploadFile


class Validators:
    """
    Validateurs pour les entrées utilisateur et fichiers.
    """
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valide le format d'un email."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """
        Valide la force d'un mot de passe.
        
        Returns:
            (is_valid, message)
        """
        if len(password) < 8:
            return False, "Le mot de passe doit contenir au moins 8 caractères"
        
        if not re.search(r'[A-Z]', password):
            return False, "Le mot de passe doit contenir au moins une majuscule"
        
        if not re.search(r'[a-z]', password):
            return False, "Le mot de passe doit contenir au moins une minuscule"
        
        if not re.search(r'\d', password):
            return False, "Le mot de passe doit contenir au moins un chiffre"
        
        return True, "Mot de passe valide"
    
    @staticmethod
    def validate_pdf_file(file: UploadFile, max_size_mb: int = 5) -> tuple[bool, str]:
        """
        Valide un fichier PDF uploadé.
        
        Returns:
            (is_valid, message)
        """
        # Vérifier l'extension
        filename = file.filename or ""
        if not filename.lower().endswith('.pdf'):
            return False, "Seuls les fichiers PDF sont acceptés"
        
        # Vérifier le type MIME
        if file.content_type not in ["application/pdf", "application/octet-stream"]:
            return False, "Type de fichier non valide"
        
        # Vérifier la taille (approximative)
        # Note: La vérification exacte se fait lors de la lecture du contenu
        
        return True, "Fichier valide"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Nettoie un nom de fichier pour éviter les injections."""
        # Supprimer les caractères dangereux
        sanitized = re.sub(r'[<>:\"/\\|?*]', '', filename)
        # Limiter la longueur
        return sanitized[:255]