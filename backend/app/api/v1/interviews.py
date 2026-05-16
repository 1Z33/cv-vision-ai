"""
Routes API pour la préparation aux entretiens.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.interview import (
    InterviewStartRequest, InterviewStartResponse,
    AnswerSubmitRequest, AnswerSubmitResponse,
    InterviewFeedbackResponse, InterviewSessionResponse
)
from app.api.deps import get_current_user
from app.services.interview_service import InterviewService

router = APIRouter()


@router.post("/start", response_model=InterviewStartResponse, status_code=status.HTTP_201_CREATED)
async def start_interview(
    request: InterviewStartRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Démarre une nouvelle session d'entretien."""
    service = InterviewService(db)
    result = await service.start_session(current_user.id, request)
    return result


@router.post("/{session_id}/answer", response_model=AnswerSubmitResponse)
async def submit_answer(
    session_id: UUID,
    request: AnswerSubmitRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soumet une réponse à la question actuelle."""
    service = InterviewService(db)
    
    try:
        result = await service.submit_answer(session_id, current_user.id, request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{session_id}/feedback", response_model=InterviewFeedbackResponse)
async def get_interview_feedback(
    session_id: UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère le feedback global d'une session terminée."""
    service = InterviewService(db)
    
    try:
        result = await service.get_feedback(session_id, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/history", response_model=list[InterviewSessionResponse])
async def get_interview_history(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère l'historique des entretiens."""
    service = InterviewService(db)
    sessions = await service.get_user_sessions(current_user.id)
    return sessions