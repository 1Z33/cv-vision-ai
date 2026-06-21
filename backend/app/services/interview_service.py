"""
Service de gestion des sessions d'entretien.
"""

import asyncio
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.interview import InterviewSession, InterviewQA
from app.schemas.interview import InterviewStartRequest, AnswerSubmitRequest
from app.services.interview_engine import InterviewEngine  # NOUVEAU
from app.core.logging import logger
from app.services.gemini_cv_analyzer import gemini_limiter


import secrets



class InterviewService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.engine = InterviewEngine()




    
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
        questions = await self.engine.generate_questions_parallel(
            cv_text=cv_text,
            job_title=request.job_title,
            difficulty=request.difficulty,
            count=5,
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
        
        source = first_question.get("source", "gemini")
        fallback_reason = first_question.get("fallback_reason")

        return {
            "session_id": session.id,
            "question_number": first_question["question_number"],
            "question_text": first_question["question_text"],
            "question_type": first_question["question_type"],
            "source": source,
            "fallback_reason": fallback_reason,
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
            select(InterviewQA)
            .where(
                and_(
                    InterviewQA.session_id == session_id,
                    InterviewQA.user_answer.is_(None),
                )
            )
            .order_by(InterviewQA.question_number)
            .limit(1)
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
        
        evaluation = self.engine.evaluate_answer(question_data, request.answer)

        
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
            select(InterviewQA)
            .where(
                and_(
                    InterviewQA.session_id == session_id,
                    InterviewQA.user_answer.is_(None),
                    InterviewQA.question_number > current_qa.question_number,
                )
            )
            .order_by(InterviewQA.question_number)
            .limit(1)
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
        
        final_feedback = self.engine.generate_final_feedback(qa_list)

        
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

    async def share_session(self, session_id: str, user_id: str, db: AsyncSession) -> InterviewSession:
        """Rend une session d'entretien publique et génère un token de partage."""
        session = await db.get(InterviewSession, session_id)
        if not session:
            raise ValueError("Session non trouvée")

        if str(session.user_id) != str(user_id):
            raise ValueError("Accès non autorisé")

        if session.status != "completed":
            raise ValueError("La session doit être terminée avant d'être partagée")

        if not session.share_token:
            session.share_token = secrets.token_urlsafe(32)
            session.is_public = True
            session.shared_at = datetime.utcnow()
            await db.commit()
            await db.refresh(session)

        return session

    async def unshare_session(self, session_id: str, user_id: str, db: AsyncSession) -> None:
        """Révoque le partage d'une session d'entretien."""
        session = await db.get(InterviewSession, session_id)
        if not session:
            raise ValueError("Session non trouvée")

        if str(session.user_id) != str(user_id):
            raise ValueError("Accès non autorisé")

        session.is_public = False
        session.share_token = None
        session.shared_at = None
        await db.commit()

    async def get_public_session(self, share_token: str, db: AsyncSession) -> InterviewSession:
        """Récupère une session publique via son token de partage."""
        result = await db.execute(
            select(InterviewSession).where(
                InterviewSession.share_token == share_token,
                InterviewSession.is_public == True,
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError("Session non trouvée ou non publique")

        return session

    async def generate_vocal_question(
        self,
        session_id: str,
        cv_text: str,
        job_title: str,
        difficulty: str,
        question_number: int,
        db: AsyncSession,
        previous_answer: Optional[str] = None,
    ) -> dict:
        """Génère une question vocale via Gemini ou fallback."""
        prompt = f"""
Tu es un recruteur professionnel menant un entretien ORAL.

Poste: {job_title}
Difficulté: {difficulty}
Question {question_number}/5

Contexte CV: {cv_text[:800]}
{"" if not previous_answer else f"Réponse précédente: {previous_answer[:200]}"}

RÈGLES:
- Pose UNE question courte (MAXIMUM 2 phrases)
- Naturelle à l'oral, pas de listes
- Adapte au niveau de difficulté

Réponds en JSON:
{{
  "question_text": "Ta question ici ?",
  "question_type": "technical|behavioral|situational",
  "expected_keywords": ["mot-clé1", "mot-clé2"]
}}
""".strip()
        
        # Vérification du Rate Limit avant l'appel
        if not gemini_limiter.can_request():
            logger.warning("Gemini rate limit atteint pour vocal_question")
            skills = []
            try:
                from app.services.interview_fallback import extract_skills, detect_job_family
                skills = extract_skills(cv_text or "")
            except Exception:
                skills = []

            primary_skill = skills[0] if skills else "votre domaine"
            question_text = f"Décrivez comment vous utilisez {primary_skill} dans votre pratique de {job_title}."
            return {
                "question_text": question_text,
                "question_type": "technical",
                "expected_keywords": [primary_skill, "pratique", job],
                "expected_keywords": [primary_skill, "pratique", job_title],
                "source": "fallback",
                "fallback_reason": "rate_limit"
            }

        try:
            if self.engine.gemini and self.engine.gemini.enabled:
                response = await asyncio.to_thread(
                    self.engine.gemini.client.models.generate_content,
                    model="gemini-1.5-flash-8b",
                    contents=prompt,
                )
                text = getattr(response, "text", "{}") or "{}"
                import json
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    data = json.loads(text[start:end])
                    if "question_text" in data and len(data["question_text"]) > 10:
                        data["source"] = "gemini"
                        return data
        except Exception as e:
            logger.warning(f"Gemini vocal question failed: {e}")

        # Fallback (heuristique)
        try:
            from app.services.interview_fallback import extract_skills
            skills = extract_skills(cv_text or "")
            q_text = f"Parlez-moi de votre expérience avec {skills[0] if skills else 'vos projets'}."
            return {
                "question_text": q_text,
                "question_type": "behavioral",
                "expected_keywords": ["expérience", "compétences"],
                "source": "fallback",
                "fallback_reason": "generation_failed"
            }
        except Exception as e:
            logger.error(f"Fallback fatal dans generate_vocal_question: {e}")
            return {
                "question_text": f"Pouvez-vous me décrire votre parcours professionnel en lien avec le poste de {job_title} ?",
                "question_type": "behavioral",
                "expected_keywords": ["parcours", "expérience", job_title.lower()],
                "source": "fallback",
                "fallback_reason": "critical_error"
            }


    async def evaluate_vocal_answer(
        self,
        answer: str,
        question: str,
        expected_keywords: list,
        db: AsyncSession,
    ) -> dict:
        """Évalue une réponse vocale."""
        prompt = f"""
Évalue cette réponse d'entretien ORAL:

Question: {question}
Réponse: {answer}

Critères: pertinence, clarté, contenu

Réponds en JSON:
{{
  "score": 75,
  "feedback": "Feedback en 2-3 phrases",
  "strengths": ["point fort"],
  "weaknesses": ["point à améliorer"]
}}
""".strip()

        # Rate limit Gemini (plan gratuit)
        if not gemini_limiter.can_request():
            wait = gemini_limiter.wait_time()
            if wait > 0:
                logger.info(
                    f"Rate limit Gemini atteint, attente de {wait:.1f}s pour vocal evaluation"
                )
                await asyncio.sleep(min(wait, 10))

            if not gemini_limiter.can_request():
                eval_fallback = self.engine.ai.evaluate_answer(
                    {"question_text": question, "expected_keywords": expected_keywords},
                    answer,
                )
                return {
                    "score": eval_fallback.get("answer_score", 50),
                    "answer_score": eval_fallback.get("answer_score", 50),
                    "feedback": eval_fallback.get(
                        "feedback_text", "Réponse enregistrée."
                    ),
                    "feedback_text": eval_fallback.get("feedback_text", "Réponse enregistrée."),
                    "strengths": eval_fallback.get("detected_keywords", []),
                    "weaknesses": eval_fallback.get("missing_keywords", []),
                    "source": "fallback_rate_limited",
                    "fallback_reason": "rate_limit"
                }

        try:
            if hasattr(self.engine, "gemini") and getattr(self.engine.gemini, "enabled", False):
                gemini_client = getattr(self.engine, "gemini", None)
            else:
                gemini_client = None

            if gemini_client and getattr(gemini_client, "client", None):

                response = await asyncio.to_thread(
                    gemini_client.client.models.generate_content,
model="gemini-1.5-flash-8b",
                    contents=prompt,
                )

                text = getattr(response, "text", "{}") or "{}"

                import json

                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    data = json.loads(text[start:end])
                    # alignement avec la spec
                    return {
                        "score": data.get("score", 50),
                        "answer_score": data.get("score", 50),
                        "feedback": data.get("feedback", ""),
                        "feedback_text": data.get("feedback", ""),
                        "strengths": data.get("strengths", []),
                        "weaknesses": data.get("weaknesses", []),
                        "source": "gemini"
                    }

        except Exception as e:
            logger.warning(f"Gemini vocal eval failed: {e}")

        # Fallback
        try:
            eval_fallback = self.engine.ai.evaluate_answer(
                {"question_text": question, "expected_keywords": expected_keywords},
                answer,
            )
            return {
                "score": eval_fallback.get("answer_score", 50),
                "answer_score": eval_fallback.get("answer_score", 50),
                "feedback": eval_fallback.get("feedback_text", "Réponse enregistrée."),
                "feedback_text": eval_fallback.get("feedback_text", "Réponse enregistrée."),
                "strengths": eval_fallback.get("detected_keywords", []),
                "weaknesses": eval_fallback.get("missing_keywords", []),
                "source": "fallback"
            }
        except Exception:
            return {"score": 50, "feedback": "Réponse enregistrée."}
