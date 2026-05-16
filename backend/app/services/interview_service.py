"""
Service de gestion des sessions d'entretien.
"""

from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.interview import InterviewSession, InterviewQA
from app.schemas.interview import InterviewStartRequest, AnswerSubmitRequest
from app.services.interview_ai import InterviewAI
from app.core.logging import logger


class InterviewService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai = InterviewAI()
    
    async def start_session(self, user_id: UUID, request: InterviewStartRequest) -> dict:
        """
        Démarre une nouvelle session d'entretien et génère la première question.
        """
        # Créer la session
        session = InterviewSession(
            user_id=user_id,
            cv_id=request.cv_id,
            job_title=request.job_title,
            difficulty=request.difficulty
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        # Récupérer le texte du CV si disponible
        cv_text = ""
        if request.cv_id:
            from app.models.cv import CV
            result = await self.db.execute(select(CV).where(CV.id == request.cv_id))
            cv = result.scalar_one_or_none()
            if cv:
                cv_text = cv.extracted_text or ""
        
        # Générer les questions
        questions = self.ai.generate_questions(
            cv_text=cv_text,
            job_title=request.job_title,
            difficulty=request.difficulty,
            num_questions=5
        )
        
        # Sauvegarder les questions en base
        for q in questions:
            qa = InterviewQA(
                session_id=session.id,
                question_number=q["question_number"],
                question_text=q["question_text"],
                question_type=q["question_type"],
                expected_keywords=q["expected_keywords"]
            )
            self.db.add(qa)
        
        await self.db.commit()
        
        first_question = questions[0]
        logger.info(f"Session entretien démarrée: {session.id} pour user {user_id}")
        
        return {
            "session_id": session.id,
            "question_number": first_question["question_number"],
            "question_text": first_question["question_text"],
            "question_type": first_question["question_type"]
        }
    
    async def submit_answer(self, session_id: UUID, user_id: UUID, request: AnswerSubmitRequest) -> dict:
        """
        Soumet une réponse et retourne l'évaluation + question suivante.
        """
        # Vérifier la session
        result = await self.db.execute(
            select(InterviewSession).where(
                and_(InterviewSession.id == session_id, InterviewSession.user_id == user_id)
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError("Session non trouvée")
        
        if session.status == "completed":
            raise ValueError("Cette session est déjà terminée")
        
        # Trouver la question actuelle (la première non répondue)
        result = await self.db.execute(
            select(InterviewQA).where(
                and_(InterviewQA.session_id == session_id, InterviewQA.user_answer == None)
            ).order_by(InterviewQA.question_number)
        )
        current_qa = result.scalar_one_or_none()
        
        if not current_qa:
            raise ValueError("Plus de questions disponibles")
        
        # Évaluer la réponse
        question_data = {
            "question_text": current_qa.question_text,
            "expected_keywords": current_qa.expected_keywords,
            "question_type": current_qa.question_type
        }
        
        evaluation = self.ai.evaluate_answer(question_data, request.answer)
        
        # Mettre à jour la Q&A
        current_qa.user_answer = request.answer
        current_qa.answer_score = evaluation["answer_score"]
        current_qa.feedback_text = evaluation["feedback_text"]
        current_qa.detected_keywords = evaluation["detected_keywords"]
        current_qa.missing_keywords = evaluation["missing_keywords"]
        current_qa.answered_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        
        # Vérifier s'il reste des questions
        result = await self.db.execute(
            select(InterviewQA).where(
                and_(InterviewQA.session_id == session_id, InterviewQA.user_answer == None)
            ).order_by(InterviewQA.question_number)
        )
        next_qa = result.scalar_one_or_none()
        
        response = {
            "question_number": current_qa.question_number,
            "answer_score": evaluation["answer_score"],
            "feedback_text": evaluation["feedback_text"],
            "detected_keywords": evaluation["detected_keywords"],
            "missing_keywords": evaluation["missing_keywords"],
            "is_complete": next_qa is None
        }
        
        if next_qa:
            response["next_question"] = next_qa.question_text
        else:
            # Terminer la session
            await self._complete_session(session)
        
        return response
    
    async def _complete_session(self, session: InterviewSession):
        """Finalise une session d'entretien."""
        result = await self.db.execute(
            select(InterviewQA).where(InterviewQA.session_id == session.id)
        )
        qas = result.scalars().all()
        
        scores = [qa.answer_score for qa in qas if qa.answer_score is not None]
        if scores:
            session.total_score = int(sum(scores) / len(scores))
        
        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
        await self.db.commit()
        
        logger.info(f"Session entretien terminée: {session.id}, score: {session.total_score}")
    
    async def get_feedback(self, session_id: UUID, user_id: UUID) -> dict:
        """Récupère le feedback global d'une session terminée."""
        result = await self.db.execute(
            select(InterviewSession).where(
                and_(InterviewSession.id == session_id, InterviewSession.user_id == user_id)
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError("Session non trouvée")
        
        result = await self.db.execute(
            select(InterviewQA).where(InterviewQA.session_id == session_id)
            .order_by(InterviewQA.question_number)
        )
        qas = result.scalars().all()
        
        qa_list = [{
            "question_number": qa.question_number,
            "question_text": qa.question_text,
            "question_type": qa.question_type,
            "answer_score": qa.answer_score,
            "feedback_text": qa.feedback_text,
            "detected_keywords": qa.detected_keywords,
            "missing_keywords": qa.missing_keywords
        } for qa in qas]
        
        final_feedback = self.ai.generate_final_feedback(qa_list)
        
        return {
            "session_id": session.id,
            "total_score": session.total_score,
            "total_questions": len(qas),
            "answers_summary": qa_list,
            **final_feedback
        }
    
    async def get_user_sessions(self, user_id: UUID) -> list:
        """Récupère l'historique des sessions d'un utilisateur."""
        result = await self.db.execute(
            select(InterviewSession).where(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.started_at.desc())
        )
        return result.scalars().all()