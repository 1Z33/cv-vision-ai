"""
Routes API pour la gestion des CVs et analyses.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.cv import CVUploadResponse, CVResponse, CVListResponse
from app.schemas.analysis import AnalysisResponse
from app.api.deps import get_current_user
from app.services.cv_service import CVService
from app.services.analyzer_engine import CVAnalyzerEngine
from app.models.analysis import Analysis

router = APIRouter()


@router.post("/upload", response_model=CVUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_cv(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload un CV PDF et lance l'analyse automatique.
    """
    # Validation du fichier
    from app.utils.validators import Validators
    is_valid, message = Validators.validate_pdf_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    # Sauvegarder le CV
    cv_service = CVService(db)
    cv = await cv_service.save_upload_file(file, current_user.id)
    
    # Lancer l'analyse IA
    analyzer = CVAnalyzerEngine()
    analysis_result = analyzer.analyze(cv.extracted_text or "")
    
    # Sauvegarder l'analyse
    analysis = Analysis(
        cv_id=cv.id,
        **analysis_result
    )
    db.add(analysis)
    await db.commit()
    
    return CVUploadResponse(
        id=cv.id,
        filename=cv.filename,
        file_size_kb=cv.file_size_kb,
        page_count=cv.page_count,
        message="CV uploadé et analysé avec succès"
    )


@router.get("", response_model=CVListResponse)
async def list_cvs(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Liste les CVs de l'utilisateur connecté."""
    cv_service = CVService(db)
    cvs = await cv_service.get_user_cvs(current_user.id)
    
    # Pagination manuelle
    paginated = cvs[skip:skip + limit]
    
    return CVListResponse(
        items=paginated,
        total=len(cvs)
    )


@router.get("/{cv_id}", response_model=CVResponse)
async def get_cv(
    cv_id: UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère un CV spécifique."""
    cv_service = CVService(db)
    cv = await cv_service.get_cv(cv_id, current_user.id)
    
    if not cv:
        raise HTTPException(status_code=404, detail="CV non trouvé")
    
    return cv


@router.get("/{cv_id}/analysis", response_model=AnalysisResponse)
async def get_cv_analysis(
    cv_id: UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère l'analyse d'un CV."""
    from sqlalchemy import select
    from app.models.cv import CV
    
    # Vérifier que le CV appartient à l'utilisateur
    cv_service = CVService(db)
    cv = await cv_service.get_cv(cv_id, current_user.id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV non trouvé")
    
    # Récupérer l'analyse
    result = await db.execute(select(Analysis).where(Analysis.cv_id == cv_id))
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    return analysis


@router.delete("/{cv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cv(
    cv_id: UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Supprime un CV."""
    cv_service = CVService(db)
    success = await cv_service.delete_cv(cv_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="CV non trouvé")
    
    return None


@router.post("/{cv_id}/reanalyze", response_model=AnalysisResponse)
async def reanalyze_cv(
    cv_id: UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Relance l'analyse d'un CV."""
    from sqlalchemy import select, delete
    
    cv_service = CVService(db)
    cv = await cv_service.get_cv(cv_id, current_user.id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV non trouvé")
    
    # Supprimer l'ancienne analyse
    await db.execute(delete(Analysis).where(Analysis.cv_id == cv_id))
    
    # Nouvelle analyse
    analyzer = CVAnalyzerEngine()
    analysis_result = analyzer.analyze(cv.extracted_text or "")
    
    analysis = Analysis(cv_id=cv.id, **analysis_result)
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    
    return analysis