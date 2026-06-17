"""
Routes API pour la gestion des CVs et analyses.
"""

import time
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cv_analysis_cache, invalidate_cv_cache


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
    analysis_result = await analyzer.analyze(cv.extracted_text or "")

    
    # Sauvegarder l'analyse
    analysis = Analysis(
        cv_id=cv.id,
        **analysis_result
    )
    db.add(analysis)
    await db.commit()

    # Invalidation cache (edge-cases / cohérence)
    invalidate_cv_cache(cv.id)
    
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
    """Récupère l'analyse d'un CV (cache mémoire TTL)."""
    from sqlalchemy import select

    cache_key = f"cv:{cv_id}:analysis:user:{current_user.id}"

    # 1) Tentative cache
    cached = cv_analysis_cache.get(cache_key)
    if cached is not None:
        return {
            **cached,
            "_cached": True,
            "_cached_at": time.strftime(
                '%Y-%m-%d %H:%M:%S',
                time.localtime(cached.get("_timestamp", 0))
            )
        }

    # 2) Vérification propriétaire + 3) Récupération DB
    cv_service = CVService(db)
    cv = await cv_service.get_cv(cv_id, current_user.id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV non trouvé")

    result = await db.execute(select(Analysis).where(Analysis.cv_id == cv_id))
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")

    # 4) Sérialisation + mise en cache
    response = {
        "id": analysis.id,
        "cv_id": str(cv_id),
        "overall_score": analysis.overall_score,
        "structure_score": analysis.structure_score,
        "content_score": analysis.content_score,
        "keywords_score": analysis.keywords_score,
        "detected_skills": analysis.detected_skills or [],
        "missing_skills": analysis.missing_skills or [],
        "strengths": analysis.strengths or [],
        "weaknesses": analysis.weaknesses or [],
        "recommendations": analysis.recommendations or [],
        "sections_detected": analysis.sections_detected or {},
        "word_count": analysis.word_count,
        "contact_info_found": analysis.contact_info_found or 0,
        # used_gemini (optionnel)
        "used_gemini": getattr(analysis, "used_gemini", None),

        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        "_timestamp": time.time(),
    }

    cv_analysis_cache.set(cache_key, response, ttl=1800)

    return {
        **response,
        "_cached": False
    }



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
    analysis_result = await analyzer.analyze(cv.extracted_text or "")

    analysis = Analysis(cv_id=cv.id, **analysis_result)
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    # Invalidation cache après reanalyse (C2)
    invalidate_cv_cache(cv.id)

    return analysis


@router.post("/{cv_id}/analyze-gemini", response_model=AnalysisResponse)
async def analyze_cv_gemini(
    cv_id: UUID,
    job_id: int | None = None,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyse avancée avec Gemini (fallback heuristique via CVAnalyzerEngine).

    Note: si job_id est fourni, le moteur tentera d'incorporer l'offre d'emploi via Gemini.
    """
    cv_service = CVService(db)
    cv = await cv_service.get_cv(cv_id, current_user.id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV non trouvé")

    job_description = None
    if job_id is not None:
        from app.models.job import Job
        from sqlalchemy import select

        job_result = await db.execute(select(Job).where(Job.id == job_id))
        job = job_result.scalar_one_or_none()
        if job is not None:
            job_description = job.description

    analyzer = CVAnalyzerEngine()
    # CVAnalyzerEngine accepte job_description optionnel
    result = await analyzer.analyze(cv.extracted_text or "", job_description)

    # FIX critique: Analysis.cv_id est unique => on UPDATE s'il existe déjà
    from sqlalchemy import select

    query = await db.execute(select(Analysis).where(Analysis.cv_id == cv.id))
    existing_analysis = query.scalar_one_or_none()

    if existing_analysis is not None:
        for field, value in result.items():
            if hasattr(existing_analysis, field):
                setattr(existing_analysis, field, value)
        db.add(existing_analysis)
        await db.commit()
        await db.refresh(existing_analysis)

        # Invalidation cache après analyse Gemini (C2)
        invalidate_cv_cache(cv.id)

        return existing_analysis

    analysis = Analysis(cv_id=cv.id, **result)
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    # Invalidation cache après analyse Gemini (C2)
    invalidate_cv_cache(cv.id)

    return analysis


@router.post("/{cv_id}/match-job/{job_id}", response_model=AnalysisResponse)
async def match_cv_job(
    cv_id: UUID,
    job_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Shortcut pour analyse + matching avec une offre spécifique."""
    return await analyze_cv_gemini(cv_id=cv_id, job_id=job_id, current_user=current_user, db=db)





