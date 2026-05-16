"""
Schémas Pydantic pour les offres d'emploi.
"""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class JobCreate(BaseModel):
    title: str
    company: Optional[str] = None
    description: str
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    experience_level: Optional[str] = None
    location: Optional[str] = None


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[list[str]] = None
    preferred_skills: Optional[list[str]] = None
    experience_level: Optional[str] = None
    location: Optional[str] = None


class JobResponse(BaseModel):
    id: UUID
    title: str
    company: Optional[str]
    description: str
    required_skills: list[str]
    preferred_skills: list[str]
    experience_level: Optional[str]
    location: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int