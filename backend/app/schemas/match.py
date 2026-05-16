"""
Schémas Pydantic pour le matching CV/Job.
"""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class MatchRequest(BaseModel):
    cv_id: UUID
    job_id: UUID


class MatchResponse(BaseModel):
    id: UUID
    cv_id: UUID
    job_id: UUID
    compatibility_score: int
    matching_skills: list[str]
    missing_skills: list[str]
    skill_gap_analysis: dict
    created_at: datetime
    
    class Config:
        from_attributes = True


class MatchSummary(BaseModel):
    job_title: str
    compatibility_score: int
    matching_skills_count: int
    missing_skills_count: int


class BestMatchResponse(BaseModel):
    cv_id: UUID
    best_match: MatchResponse
    all_matches: list[MatchSummary]