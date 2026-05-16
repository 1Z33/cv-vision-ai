"""
Service de gestion des offres d'emploi.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.job import Job
from app.schemas.job import JobCreate, JobUpdate
from app.core.logging import logger


class JobService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_job(self, job_data: JobCreate) -> Job:
        """Crée une nouvelle offre d'emploi."""
        job = Job(
            title=job_data.title,
            company=job_data.company,
            description=job_data.description,
            required_skills=job_data.required_skills,
            preferred_skills=job_data.preferred_skills,
            experience_level=job_data.experience_level,
            location=job_data.location
        )
        
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        
        logger.info(f"Offre créée: {job.title}")
        return job
    
    async def get_jobs(self, skip: int = 0, limit: int = 100) -> list[Job]:
        """Récupère toutes les offres (paginées)."""
        result = await self.db.execute(
            select(Job).order_by(Job.created_at.desc())
            .offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def get_job(self, job_id: UUID) -> Optional[Job]:
        """Récupère une offre par son ID."""
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()
    
    async def update_job(self, job_id: UUID, job_data: JobUpdate) -> Optional[Job]:
        """Met à jour une offre d'emploi."""
        job = await self.get_job(job_id)
        if not job:
            return None
        
        update_data = job_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)
        
        await self.db.commit()
        await self.db.refresh(job)
        
        logger.info(f"Offre mise à jour: {job.title}")
        return job
    
    async def delete_job(self, job_id: UUID) -> bool:
        """Supprime une offre d'emploi."""
        job = await self.get_job(job_id)
        if not job:
            return False
        
        await self.db.delete(job)
        await self.db.commit()
        
        logger.info(f"Offre supprimée: {job_id}")
        return True