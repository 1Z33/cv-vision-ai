"""
Service de gestion des CVs : upload, stockage, extraction.
"""

import os
import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import UploadFile

# NOTE: imports kept for backward compatibility


from app.models.cv import CV
from app.core.config import settings
from app.utils.pdf_parser import PDFParser
from app.core.logging import logger


class CVService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.parser = PDFParser()
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def save_upload_file(self, file: UploadFile, user_id: uuid.UUID) -> CV:
        """
        Sauvegarde un fichier PDF uploadé et extrait son texte.
        
        Args:
            file: Fichier uploadé via FastAPI
            user_id: ID de l'utilisateur propriétaire
        
        Returns:
            Instance CV créée en base
        """
        # Générer un nom de fichier unique
        file_ext = Path(file.filename).suffix.lower()
        if file_ext != ".pdf":
            raise ValueError("Seuls les fichiers PDF sont acceptés")
        
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = self.upload_dir / unique_filename
        
        # Sauvegarder le fichier
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Extraire le texte et les métadonnées
        try:
            parsed = self.parser.parse(str(file_path))
            extracted_text = parsed["text"]
            page_count = parsed["page_count"]
            extraction_source = parsed.get("source", "native")
            ocr_triggered = parsed.get("ocr_triggered", False)
            native_text_length = len(parsed.get("native_text", ""))
            ocr_text_length = len(parsed.get("ocr_text", ""))
        except Exception as e:
            logger.error(f"Erreur extraction PDF: {e}")
            extracted_text = ""
            page_count = 0
            extraction_source = "error"
            ocr_triggered = False
            native_text_length = 0
            ocr_text_length = 0
        
        # Créer l'entrée en base
        file_size_kb = len(content) // 1024

        cv = CV(
            user_id=user_id,
            filename=file.filename,
            file_path=str(file_path),
            extracted_text=extracted_text,
            file_size_kb=file_size_kb,
            page_count=page_count,
        )

        self.db.add(cv)
        await self.db.commit()
        await self.db.refresh(cv)

        logger.info(
            "CV sauvegardé: %s pour user %s (source=%s ocr_triggered=%s native_len=%s ocr_len=%s)",
            cv.filename,
            user_id,
            extraction_source,
            ocr_triggered,
            native_text_length,
            ocr_text_length,
        )
        return cv
    
    async def get_user_cvs(self, user_id: uuid.UUID) -> list[CV]:
        """Récupère tous les CVs d'un utilisateur."""
        result = await self.db.execute(
            select(CV).where(CV.user_id == user_id).order_by(CV.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_cv(self, cv_id: uuid.UUID, user_id: uuid.UUID) -> CV | None:
        """Récupère un CV spécifique (avec vérification propriétaire)."""
        result = await self.db.execute(
            select(CV).where(CV.id == cv_id, CV.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def delete_cv(self, cv_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Supprime un CV et son fichier."""
        cv = await self.get_cv(cv_id, user_id)
        if not cv:
            return False
        
        # Supprimer le fichier physique
        try:
            Path(cv.file_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Impossible de supprimer le fichier {cv.file_path}: {e}")
        
        await self.db.delete(cv)
        await self.db.commit()
        
        logger.info(f"CV supprimé: {cv_id}")
        return True