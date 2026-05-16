"""
Routes API pour la gestion des offres d'emploi.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.job import JobCreate, JobResponse, JobListResponse, JobUpdate
from app.api.deps import get_current_user
from app.services.job_service import JobService

router = APIRouter()


@router.get("", response_model=JobListResponse)
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Liste toutes les offres d'emploi."""
    service = JobService(db)
    jobs = await service.get_jobs(skip=skip, limit=limit)
    
    return JobListResponse(items=jobs, total=len(jobs))


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Crée une nouvelle offre d'emploi."""
    service = JobService(db)
    job = await service.create_job(job_data)
    return job


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Récupère une offre spécifique."""
    service = JobService(db)
    job = await service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    
    return job


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: UUID,
    job_data: JobUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Met à jour une offre d'emploi."""
    service = JobService(db)
    job = await service.update_job(job_id, job_data)
    
    if not job:
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Supprime une offre d'emploi."""
    service = JobService(db)
    success = await service.delete_job(job_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    
    return None