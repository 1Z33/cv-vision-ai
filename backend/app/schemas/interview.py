"""
Schémas Pydantic pour les entretiens.
"""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class InterviewStartRequest(BaseModel):
    cv_id: Optional[UUID] = None
    job_title: Optional[str] = None
    difficulty: str = "medium"


class InterviewStartResponse(BaseModel):
    session_id: UUID
    question_number: int
    question_text: str
    question_type: str


class AnswerSubmitRequest(BaseModel):
    answer: str


class AnswerSubmitResponse(BaseModel):
    question_number: int
    answer_score: int
    feedback_text: str
    detected_keywords: list[str]
    missing_keywords: list[str]
    next_question: Optional[str] = None
    is_complete: bool = False


class InterviewFeedbackResponse(BaseModel):
    session_id: UUID
    total_score: int
    total_questions: int
    answers_summary: list[dict]
    general_feedback: str
    strengths: list[str]
    areas_to_improve: list[str]


class InterviewSessionResponse(BaseModel):
    id: UUID
    job_title: Optional[str]
    difficulty: str
    total_score: Optional[int]
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True