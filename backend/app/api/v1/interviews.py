"""
Routes API pour la préparation aux entretiens.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.logging import logger
from app.schemas.interview import (

    InterviewStartRequest, InterviewStartResponse,
    AnswerSubmitRequest, AnswerSubmitResponse,
    InterviewFeedbackResponse, InterviewSessionResponse,
    ShareResponse, UnshareResponse,
    PublicInterviewResponse, PublicQuestionResponse,
    VocalStartResponse, VocalAnswerResponse,
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
    return {
        "session_id": result["session_id"],
        "question_number": result["question_number"],
        "question_text": result["question_text"],
        "question_type": result["question_type"],
        "source": result.get("source", "gemini"),
        "fallback_reason": result.get("fallback_reason"),
    }



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


@router.post("/{session_id}/share", response_model=ShareResponse)
async def share_interview(
    session_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rend une session d'entretien publique et génère un lien de partage."""
    service = InterviewService(db)
    try:
        session = await service.share_session(session_id, current_user.id, db)
    except ValueError as e:
        error_msg = str(e).lower()
        if "non trouvée" in error_msg:
            raise HTTPException(status_code=404, detail=str(e))
        if "non autorisé" in error_msg:
            raise HTTPException(status_code=403, detail=str(e))
        if "terminée" in error_msg or "terminee" in error_msg:
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    share_url = f"/api/v1/interviews/public/{session.share_token}"
    return ShareResponse(
        message="Session partagée avec succès",
        share_token=session.share_token,
        share_url=share_url,
        shared_at=session.shared_at,
    )


@router.post("/{session_id}/unshare", response_model=UnshareResponse)
async def unshare_interview(
    session_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Révoque le partage d'une session d'entretien."""
    service = InterviewService(db)
    try:
        await service.unshare_session(session_id, current_user.id, db)
    except ValueError as e:
        error_msg = str(e).lower()
        if "non trouvée" in error_msg:
            raise HTTPException(status_code=404, detail=str(e))
        if "non autorisé" in error_msg:
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    return UnshareResponse(message="Partage révoqué")


@router.get("/public/{share_token}", response_model=PublicInterviewResponse)
async def get_public_interview(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):

    """Récupère une session d'entretien publique via son token de partage."""
    service = InterviewService(db)
    try:
        session = await service.get_public_session(share_token, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    from sqlalchemy import select
    from app.models.interview import InterviewQA

    qa_result = await db.execute(
        select(InterviewQA).where(InterviewQA.session_id == session.id).order_by(InterviewQA.question_number)
    )
    questions = qa_result.scalars().all()

    return PublicInterviewResponse(
        session_id=str(session.id),
        job_title=session.job_title,
        difficulty=session.difficulty,
        total_score=session.total_score,
        status=session.status,
        completed_at=session.completed_at,
        shared_at=session.shared_at,
        questions=[
            PublicQuestionResponse(
                question_number=q.question_number,
                question_text=q.question_text,
                question_type=q.question_type,
                expected_keywords=q.expected_keywords or [],
                user_answer=q.user_answer,
                answer_score=q.answer_score,
                feedback_text=q.feedback_text,
                detected_keywords=q.detected_keywords or [],
                missing_keywords=q.missing_keywords or [],
            )
            for q in questions
        ],
    )


@router.post("/{session_id}/vocal-start", response_model=VocalStartResponse)
async def start_vocal_interview(
    session_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    """Démarre un entretien vocal.

    Idempotent: si des questions existent déjà, on renvoie/génère la prochaine question à jouer.
    """
    from uuid import UUID

    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    InterviewSessionModel = __import__("app.models.interview", fromlist=["InterviewSession"]).InterviewSession
    session = await db.get(InterviewSessionModel, session_uuid)

    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")

    if str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    from app.models.interview import InterviewQA

    # Prochaine question à générer = (nombre de QA répondues) + 1
    answered_count_result = await db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(__import__("sqlalchemy", fromlist=["func"]).func.count(InterviewQA.id)).where(
            InterviewQA.session_id == session_uuid,
            InterviewQA.user_answer.isnot(None),
        )
    )
    answered_count = answered_count_result.scalar() or 0
    next_number = answered_count + 1

    cv_text = ""
    if session.cv_id:
        from app.models.cv import CV

        cv = await db.get(CV, session.cv_id)
        if cv:
            cv_text = cv.extracted_text or ""

    service = InterviewService(db)

    # Si la QA pour next_number existe déjà, on la réutilise (évite doublons)
    existing_qa_result = await db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(InterviewQA).where(
            InterviewQA.session_id == session_uuid,
            InterviewQA.question_number == next_number,
        )
    )
    existing_qa_obj = existing_qa_result.scalars().first()

    question_data: dict
    if existing_qa_obj and existing_qa_obj.question_text:
        question_data = {
            "question_text": existing_qa_obj.question_text,
            "question_type": existing_qa_obj.question_type,
            "expected_keywords": existing_qa_obj.expected_keywords or [],
        }
    else:
        try:
            question_data = await service.generate_vocal_question(
                session_id=session_id,
                cv_text=cv_text,
                job_title=session.job_title,
                difficulty=session.difficulty,
                question_number=next_number,
                db=db,
            )
        except Exception as e:
            logger.error(f"Erreur génération question vocale: {e}")
            question_data = {
                "question_text": f"Parlez-moi de vous et de votre expérience pour le poste de {session.job_title}.",
                "question_type": "behavioral",
                "expected_keywords": ["expérience", "motivation"],
            }

        # Persist QA next_number
        import uuid
        if existing_qa_obj:
            existing_qa_obj.question_text = question_data["question_text"]
            existing_qa_obj.question_type = question_data.get("question_type", existing_qa_obj.question_type)
            if not existing_qa_obj.expected_keywords:
                existing_qa_obj.expected_keywords = question_data.get("expected_keywords", [])
            await db.commit()
        else:
            qa = InterviewQA(
                id=uuid.uuid4(),
                session_id=session_uuid,
                question_number=next_number,
                question_text=question_data["question_text"],
                question_type=question_data.get("question_type", "behavioral"),
                expected_keywords=question_data.get("expected_keywords", []),
            )
            db.add(qa)
            await db.commit()

    # Générer l'audio de la question (TTS)
    from app.services.vocal_service import VocalService

    vocal_service = VocalService()
    question_audio_url = await vocal_service.text_to_speech(question_data["question_text"])

    return {
        "session_id": session_id,
        "question_text": question_data["question_text"],
        "question_audio_url": question_audio_url,
        "question_number": next_number,
        "total_questions": 5,
        "is_complete": False,
    }





@router.get("/{session_id}/my-answer/{question_number}")
async def get_my_answer(
    session_id: str,
    question_number: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Récupère la réponse (texte + feedback + score) d'une question déjà répondue."""

    from sqlalchemy import select
    from uuid import UUID
    from app.models.interview import InterviewSession as InterviewSessionModel, InterviewQA

    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    session = await db.get(InterviewSessionModel, session_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")

    if str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    qa_result = await db.execute(
        select(InterviewQA).where(
            InterviewQA.session_id == session_uuid,
            InterviewQA.question_number == question_number,
        )
    )
    qa = qa_result.scalars().first()

    if not qa or not qa.user_answer:
        raise HTTPException(status_code=404, detail="Réponse non trouvée")


    return {
        "question_text": qa.question_text,
        "user_answer_text": qa.user_answer,
        "feedback_text": qa.feedback_text,
        "answer_score": qa.answer_score,
        "question_number": qa.question_number,
    }


@router.post("/{session_id}/replay-question")
async def replay_question(
    session_id: str,
    question_number: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Régénère l'audio TTS d'une question déjà posée."""

    from sqlalchemy import select
    from uuid import UUID

    from app.models.interview import InterviewSession as InterviewSessionModel, InterviewQA
    from app.services.vocal_service import VocalService

    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    session = await db.get(InterviewSessionModel, session_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")

    if str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    qa_result = await db.execute(
        select(InterviewQA).where(
            InterviewQA.session_id == session_uuid,
            InterviewQA.question_number == question_number,
        )
    )
    qa = qa_result.scalars().first()

    if not qa:
        raise HTTPException(status_code=404, detail="Question non trouvée")

    vocal_service = VocalService()
    audio_url = await vocal_service.text_to_speech(qa.question_text)

    return {
        "question_text": qa.question_text,
        "question_audio_url": audio_url,
        "question_number": question_number,
    }


@router.post("/{session_id}/vocal-answer", response_model=VocalAnswerResponse)
async def process_vocal_answer(
    session_id: str,
    audio: UploadFile = File(None, description="Fichier audio de la réponse (optionnel si answer_text JSON fourni)"),
    question_number: int = Form(1),
    answer_text: str | None = Form(None),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):




    """Reçoit une réponse vocale, l'évalue et génère la suite."""
    from app.models.interview import InterviewSession as InterviewSessionModel, InterviewQA
    from sqlalchemy import func
    from datetime import datetime
    import uuid

    from uuid import UUID
    try:
        session_uuid = UUID(str(session_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    session = await db.get(InterviewSessionModel, session_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")

    if str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    service = InterviewService(db)

    # Récupère la question correspondant exactement au question_number reçu,
    # uniquement si elle n'a pas encore été répondue.
    # Cherche la première question non encore répondue pour ce numéro.
    result = await db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(InterviewQA)
        .where(InterviewQA.session_id == session_uuid)
        .where(InterviewQA.question_number == question_number)
        .where(InterviewQA.user_answer.is_(None))
        .order_by(InterviewQA.answered_at.asc().nullsfirst(), InterviewQA.id.asc())
    )
    current_qa = result.scalars().first()


    if not current_qa:
        # Soit aucune QA pour ce numéro, soit déjà répondu.
        raise HTTPException(
            status_code=400,
            detail=f"Question {question_number} non trouvée ou déjà répondue",
        )


    from app.services.vocal_service import VocalService

    vocal_service = VocalService()

    # 1) STT : audio -> texte (ou fallback sur answer_text fourni)
    if answer_text is None:
        answer_text = ""

    if answer_text.strip() == "" and audio is not None:
        try:
            answer_text = await vocal_service.speech_to_text(audio)
        except Exception as e:
            logger.error(f"Erreur STT: {e}")
            answer_text = ""



    try:
        evaluation = await service.evaluate_vocal_answer(
            answer=answer_text,
            question=current_qa.question_text,
            expected_keywords=current_qa.expected_keywords or [],
            db=db,
        )

    except Exception as e:
        logger.error(f"Erreur évaluation: {e}")
        evaluation = {"score": 50, "feedback": "Réponse enregistrée."}


    # Sécurise les valeurs avant commit (évite certains types inattendus)
    current_qa.user_answer = answer_text if isinstance(answer_text, str) else str(answer_text)

    current_qa.answer_score = evaluation.get("score", 50)
    current_qa.answer_score = int(current_qa.answer_score) if current_qa.answer_score is not None else None

    current_qa.feedback_text = evaluation.get("feedback", "")
    current_qa.feedback_text = current_qa.feedback_text if isinstance(current_qa.feedback_text, str) else str(current_qa.feedback_text)

    # answered_at: datetime attendu (nullable)
    current_qa.answered_at = datetime.utcnow()
    await db.commit()


    answered_result = await db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(func.count(InterviewQA.id))
        .where(InterviewQA.session_id == session_uuid)
        .where(InterviewQA.user_answer.isnot(None))
    )
    answered_count = answered_result.scalar()

    if answered_count >= 5:
        scores_result = await db.execute(
            __import__("sqlalchemy", fromlist=["select"]).select(InterviewQA.answer_score)
            .where(InterviewQA.session_id == session_uuid)
            .where(InterviewQA.answer_score.isnot(None))
        )
        scores = [s for s in scores_result.scalars().all() if s is not None]
        # Corrige le cas où answer_score en base peut être une chaîne (ex: '50')
        numeric_scores: list[int] = []
        for s in scores:
            try:
                numeric_scores.append(int(s))
            except Exception:
                logger.warning(f"answer_score non numérique ignoré: {s!r}")
        total_score = int(sum(numeric_scores) / len(numeric_scores)) if numeric_scores else 0


        session.total_score = total_score
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        await db.commit()

        feedback = await service.generate_final_feedback(session_id, db)

        feedback_audio_url = await vocal_service.text_to_speech(feedback) if feedback else None

        return {
            "is_complete": True,
            "total_score": total_score,
            "feedback_text": feedback,
            "feedback_audio_url": feedback_audio_url,
            "answer_transcription": answer_text,
            "evaluation": evaluation,
        }


    next_number = answered_count + 1
    cv_text = ""
    if session.cv_id:
        from app.models.cv import CV

        cv = await db.get(CV, session.cv_id)
        if cv:
            cv_text = cv.extracted_text or ""

    try:
        next_q = await service.generate_vocal_question(
            session_id=session_id,
            cv_text=cv_text,
            job_title=session.job_title,
            difficulty=session.difficulty,
            question_number=next_number,
            previous_answer=answer_text,
            db=db,
        )

    except Exception as e:
        logger.error(f"Erreur question suivante: {e}")
        next_q = {
            "question_text": "Pouvez-vous me donner un exemple concret ?",
            "question_type": "behavioral",
            "expected_keywords": ["exemple", "expérience"],
        }

    # TTS feedback + prochaine question
    feedback_audio_url = await vocal_service.text_to_speech(evaluation.get("feedback", "")) if evaluation.get("feedback") else None
    next_question_audio_url = await vocal_service.text_to_speech(next_q["question_text"]) if next_q.get("question_text") else None

    # Idempotence: si une QA existe déjà pour (session_uuid, next_number), on la met à jour.
    existing_next_result = await db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(InterviewQA).where(
            InterviewQA.session_id == session_uuid,
            InterviewQA.question_number == next_number,
        )
    )
    existing_next_qa = existing_next_result.scalars().first()

    if existing_next_qa:
        existing_next_qa.question_text = next_q["question_text"]
        existing_next_qa.question_type = next_q.get("question_type", existing_next_qa.question_type)
        if not existing_next_qa.expected_keywords:
            existing_next_qa.expected_keywords = next_q.get("expected_keywords", [])
        db.add(existing_next_qa)
    else:
        new_qa = InterviewQA(
            id=uuid.uuid4(),
            session_id=session_uuid,
            question_number=next_number,
            question_text=next_q["question_text"],
            question_type=next_q.get("question_type", "behavioral"),
            expected_keywords=next_q.get("expected_keywords", []),
        )
        db.add(new_qa)

    await db.commit()



    return {
        "is_complete": False,
        "answer_transcription": answer_text,
        "score": evaluation.get("score", 0) if evaluation else 0,
        "feedback_text": evaluation.get("feedback", ""),
        "feedback_audio_url": feedback_audio_url,
        "next_question_number": next_number,
        "next_question_text": next_q["question_text"],
        "next_question_audio_url": next_question_audio_url,
        "evaluation": evaluation,
        "total_score": None,
    }



