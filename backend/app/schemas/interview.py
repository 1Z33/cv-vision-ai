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

    # Source de génération + raison du fallback (si indisponible)
    source: Optional[str] = None
    fallback_reason: Optional[str] = None




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


class ShareResponse(BaseModel):
    message: str
    share_token: str
    share_url: str
    shared_at: Optional[datetime] = None


class UnshareResponse(BaseModel):
    message: str


class PublicQuestionResponse(BaseModel):
    question_number: int
    question_text: str
    question_type: str
    expected_keywords: list[str]
    user_answer: Optional[str]
    answer_score: Optional[int]
    feedback_text: Optional[str]
    detected_keywords: list[str]
    missing_keywords: list[str]



class PublicInterviewResponse(BaseModel):
    session_id: str
    job_title: str
    difficulty: str
    total_score: Optional[int]
    status: str
    completed_at: Optional[datetime]
    shared_at: Optional[datetime]
    questions: list[PublicQuestionResponse]


class VocalStartResponse(BaseModel):
    session_id: str
    question_text: str
    question_audio_url: Optional[str] = None
    question_number: int
    total_questions: int
    is_complete: bool




class VocalAnswerResponse(BaseModel):
    answer_transcription: str
    score: int = 0

    feedback_text: Optional[str] = None
    feedback_audio_url: Optional[str] = None

    next_question_text: Optional[str] = None
    next_question_audio_url: Optional[str] = None

    is_complete: bool
    total_score: Optional[int] = None

    # Debug / compat
    evaluation: Optional[dict] = None












