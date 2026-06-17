"""Routes pour la simulation d'entretien vocal (architecture cible).

Note de compatibilité:
- Ne supprime aucune route existante.
- Ces routes sont ajoutées en plus des routes vocales actuelles.
"""

from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user

from app.core.logging import logger

# Les services/logiciels "cibles" seront implémentés ensuite.
# Pour l'instant, on délègue au service vocal existant afin de garantir la compatibilité.
from app.services.interview_service import InterviewService
from app.services.vocal_service import VocalService

from app.schemas.interview import VocalStartResponse, VocalAnswerResponse


router = APIRouter(prefix="/interview", tags=["Interview Vocal"])


@router.post("/start", response_model=VocalStartResponse, status_code=status.HTTP_201_CREATED)
async def interview_start(
    cv_id: UUID | None = None,
    job_title: str | None = None,
    difficulty: str = "medium",
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Démarre une session d'entretien vocal.

    Implémentation compat: utilise InterviewService + génération vocale existante.
    """
    service = InterviewService(db)

    # Démarre la session avec le schéma existant
    from app.schemas.interview import InterviewStartRequest

    start_req = InterviewStartRequest(cv_id=cv_id, job_title=job_title, difficulty=difficulty)
    result = await service.start_session(current_user.id, start_req)

    # Puis génère la première question vocale
    try:
        cv_text = ""
        if result.get("session_id") and job_title:
            # le service vocal gère déjà la récupération CV dans l'endpoint existant
            pass

        vocal_q = await service.generate_vocal_question(
            session_id=str(result["session_id"]),
            cv_text="",
            job_title=job_title or result.get("question_type") or "poste",
            difficulty=difficulty,
            question_number=1,
            db=db,
        )
    except Exception as e:
        logger.error(f"Erreur generate_vocal_question /interview/start: {e}")
        vocal_q = {
            "question_text": "Parlez-moi de votre expérience en lien avec le poste.",
            "question_type": "behavioral",
            "expected_keywords": ["expérience", "poste"],
            "source": "fallback",
            "fallback_reason": "error",
        }

    from app.models.interview import InterviewQA
    import uuid

    qa = InterviewQA(
        id=uuid.uuid4(),
        session_id=result["session_id"],
        question_number=1,
        question_text=vocal_q["question_text"],
        question_type=vocal_q.get("question_type", "behavioral"),
        expected_keywords=vocal_q.get("expected_keywords", []),
    )
    db.add(qa)
    await db.commit()

    vocal_service = VocalService()
    question_audio_url = await vocal_service.text_to_speech(vocal_q["question_text"])

    return {
        "session_id": str(result["session_id"]),
        "question_text": vocal_q["question_text"],
        "question_audio_url": question_audio_url,
        "question_number": 1,
        "total_questions": 5,
        "is_complete": False,
    }


@router.post("/transcribe")
async def interview_transcribe(
    audio: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint utilitaire STT (audio -> texte).

    Pour l'instant, délégation à VocalService existant.
    """
    vocal_service = VocalService()
    try:
        text = await vocal_service.speech_to_text(audio)
    except Exception as e:
        logger.error(f"STT /interview/transcribe failed: {e}")
        raise HTTPException(status_code=400, detail="Impossible de transcrire l'audio")

    return {"transcript": text or ""}


@router.get("/question-audio/{id}")
async def question_audio(id: str):
    """Récupère/retourne l'URL audio TTS d'une question.

    Mode compat: pour le moment on régénère via VocalService si nécessaire.
    L'étape suivante (cache) sera implémentée ensuite.
    """
    # i) si id correspond à question_number => on ne sait pas lier ici sans DB.
    # ii) donc cette route sera complétée après création du modèle cible.
    raise HTTPException(status_code=501, detail="Cache audio non implémenté encore")


@router.post("/answer", response_model=VocalAnswerResponse)
async def interview_answer(
    session_id: str = Form(...),
    audio: UploadFile | None = File(None),
    question_number: int = Form(1),
    answer_text: str | None = Form(None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soumet une réponse vocale et obtient l'évaluation + prochaine question.

    Compat: délégation à l'endpoint existant /{session_id}/vocal-answer.
    """
    # Délégation "à la main" à l'implémentation existante (évite de dépendre d'un http client).
    service = InterviewService(db)
    vocal_service = VocalService()

    from app.models.interview import InterviewSession as InterviewSessionModel, InterviewQA
    from sqlalchemy import select, func
    from datetime import datetime
    import uuid

    session = await db.get(InterviewSessionModel, UUID(session_id))
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    if str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    # récupérer QA correspondante
    result = await db.execute(
        select(InterviewQA)
        .where(InterviewQA.session_id == session_id)
        .where(InterviewQA.question_number == question_number)
        .where(InterviewQA.user_answer.is_(None))
    )
    current_qa = result.scalars().first()

    if not current_qa:
        raise HTTPException(status_code=400, detail=f"Question {question_number} non trouvée ou déjà répondue")

    # STT
    if answer_text is None:
        answer_text = ""
    if answer_text.strip() == "" and audio is not None:
        answer_text = await vocal_service.speech_to_text(audio)

    evaluation = await service.evaluate_vocal_answer(
        answer=answer_text,
        question=current_qa.question_text,
        expected_keywords=current_qa.expected_keywords or [],
        db=db,
    )

    current_qa.user_answer = answer_text
    current_qa.answer_score = evaluation.get("score", 50)
    current_qa.feedback_text = evaluation.get("feedback", "")
    current_qa.answered_at = datetime.utcnow()
    await db.commit()

    answered_result = await db.execute(
        select(func.count(InterviewQA.id))
        .where(InterviewQA.session_id == session_id)
        .where(InterviewQA.user_answer.isnot(None))
    )
    answered_count = answered_result.scalar()

    if answered_count >= 5:
        # calcul score moyen
        scores_result = await db.execute(
            select(InterviewQA.answer_score)
            .where(InterviewQA.session_id == session_id)
            .where(InterviewQA.answer_score.isnot(None))
        )
        scores = [s for s in scores_result.scalars().all() if s is not None]
        total_score = int(sum(scores) / len(scores)) if scores else 0

        session.total_score = total_score
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        await db.commit()

        feedback_obj = await service.generate_final_feedback(session_id=UUID(session_id), db=db)
        feedback_text = str(feedback_obj)
        feedback_audio_url = await vocal_service.text_to_speech(feedback_text) if feedback_text else None

        return {
            "answer_transcription": answer_text,
            "score": evaluation.get("score", 50),
            "feedback_text": feedback_text,
            "feedback_audio_url": feedback_audio_url,
            "next_question_text": None,
            "next_question_audio_url": None,
            "is_complete": True,
            "total_score": session.total_score,
            "evaluation": evaluation,
        }

    next_number = answered_count + 1


    # récupération cv_text
    cv_text = ""
    if session.cv_id:
        from app.models.cv import CV
        cv = await db.get(CV, session.cv_id)
        if cv:
            cv_text = cv.extracted_text or ""

    next_q = await service.generate_vocal_question(
        session_id=session_id,
        cv_text=cv_text,
        job_title=session.job_title,
        difficulty=session.difficulty,
        question_number=next_number,
        previous_answer=answer_text,
        db=db,
    )

    feedback_audio_url = await vocal_service.text_to_speech(evaluation.get("feedback", "")) if evaluation.get("feedback") else None
    next_question_audio_url = await vocal_service.text_to_speech(next_q["question_text"]) if next_q.get("question_text") else None

    new_qa = InterviewQA(
        id=uuid.uuid4().hex,
        session_id=session_id,
        question_number=next_number,
        question_text=next_q["question_text"],
        question_type=next_q.get("question_type", "behavioral"),
        expected_keywords=next_q.get("expected_keywords", []),
    )
    db.add(new_qa)
    await db.commit()

    return {
        "answer_transcription": answer_text,
        "score": evaluation.get("score", 0),
        "feedback_text": evaluation.get("feedback", ""),
        "feedback_audio_url": feedback_audio_url,
        "next_question_text": next_q["question_text"],
        "next_question_audio_url": next_question_audio_url,
        "is_complete": False,
        "total_score": None,
        "evaluation": evaluation,
    }

