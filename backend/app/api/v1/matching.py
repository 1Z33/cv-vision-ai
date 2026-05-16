"""
Routes API pour le matching CV / Offre d'emploi.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.schemas.match import MatchRequest, MatchResponse, BestMatchResponse, MatchSummary
from app.api.deps import get_current_user
from app.services.matching_engine import MatchingEngine
from app.services.cv_service import CVService
from app.models.job import Job
from app.models.match import Match
from app.models.analysis import Analysis

router = APIRouter()


@router.post("", response_model=MatchResponse, status_code=201)
async def create_match(
    request: MatchRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Crée un matching entre un CV et une offre d'emploi."""
    # Vérifier que le CV appartient à l'utilisateur
    cv_service = CVService(db)
    cv = await cv_service.get_cv(request.cv_id, current_user.id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV non trouvé")
    
    # Vérifier que l'offre existe
    result = await db.execute(select(Job).where(Job.id == request.job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    
    # Récupérer les skills du CV depuis l'analyse
    result = await db.execute(select(Analysis).where(Analysis.cv_id == request.cv_id))
    analysis = result.scalar_one_or_none()
    cv_skills = analysis.detected_skills if analysis else []
    
    # Calculer le matching
    engine = MatchingEngine()
    match_result = engine.calculate_match(
        cv_text=cv.extracted_text or "",
        job_description=job.description,
        required_skills=job.required_skills or [],
        cv_skills=cv_skills
    )
    
    # Sauvegarder le résultat
    match = Match(
        cv_id=request.cv_id,
        job_id=request.job_id,
        **match_result
    )
    db.add(match)
    await db.commit()
    await db.refresh(match)
    
    return match


@router.get("/{cv_id}", response_model=list[MatchSummary])
async def get_cv_matches(
    cv_id: UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère tous les matchs d'un CV."""
    # Vérifier propriétaire
    cv_service = CVService(db)
    cv = await cv_service.get_cv(cv_id, current_user.id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV non trouvé")
    
    result = await db.execute(select(Match).where(Match.cv_id == cv_id))
    matches = result.scalars().all()
    
    # Enrichir avec les titres des jobs
    summaries = []
    for match in matches:
        job_result = await db.execute(select(Job).where(Job.id == match.job_id))
        job = job_result.scalar_one_or_none()
        
        summaries.append(MatchSummary(
            job_title=job.title if job else "Inconnu",
            compatibility_score=match.compatibility_score,
            matching_skills_count=len(match.matching_skills),
            missing_skills_count=len(match.missing_skills)
        ))
    
    return summaries


@router.get("/{cv_id}/best", response_model=BestMatchResponse)
async def get_best_match(
    cv_id: UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère le meilleur match pour un CV."""
    cv_service = CVService(db)
    cv = await cv_service.get_cv(cv_id, current_user.id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV non trouvé")
    
    result = await db.execute(
        select(Match).where(Match.cv_id == cv_id)
        .order_by(Match.compatibility_score.desc())
    )
    matches = result.scalars().all()
    
    if not matches:
        raise HTTPException(status_code=404, detail="Aucun match trouvé")
    
    best = matches[0]
    
    # Récupérer tous les summaries
    summaries = []
    for match in matches:
        job_result = await db.execute(select(Job).where(Job.id == match.job_id))
        job = job_result.scalar_one_or_none()
        summaries.append(MatchSummary(
            job_title=job.title if job else "Inconnu",
            compatibility_score=match.compatibility_score,
            matching_skills_count=len(match.matching_skills),
            missing_skills_count=len(match.missing_skills)
        ))
    
    return BestMatchResponse(
        cv_id=cv_id,
        best_match=best,
        all_matches=summaries
    )