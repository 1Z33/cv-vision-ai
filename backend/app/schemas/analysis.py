"""
Schémas Pydantic pour les analyses de CV.
"""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class AnalysisCreate(BaseModel):
    cv_id: UUID
    overall_score: int
    structure_score: int
    content_score: int
    keywords_score: int
    detected_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    sections_detected: dict
    word_count: int
    contact_info_found: bool


class AnalysisResponse(BaseModel):
    id: UUID
    cv_id: UUID
    overall_score: int
    structure_score: int
    content_score: int
    keywords_score: int
    detected_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    sections_detected: dict
    word_count: int
    contact_info_found: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisSummary(BaseModel):
    overall_score: int
    detected_skills_count: int
    top_strength: Optional[str]
    top_weakness: Optional[str]