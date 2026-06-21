""" 
Moteur d'entretien : Gemini-first + fallback InterviewAI

Ce module sert d'orchestrateur :
- Tente d'utiliser Gemini si disponible
- Sinon, retombe sur l'implémentation heuristique/templates existante (InterviewAI)

Note: Les méthodes Gemini ici sont volontairement minimalistes pour rester compatibles avec
les contraintes de l'application actuelle.
"""

import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


from app.services.interview_ai import InterviewAI
from app.services.gemini_client import gemini_client
from app.services.gemini_cv_analyzer import gemini_limiter

logger = logging.getLogger(__name__)



class InterviewEngine:
    """Orchestration : Gemini si dispo, sinon InterviewAI."""

    def __init__(self):
        self.ai = InterviewAI()
        self.gemini = gemini_client

    def generate_questions(
        self,
        cv_text: str,

        job_title: Optional[str],
        difficulty: str,
        num_questions: int = 5,
    ) -> List[Dict[str, Any]]:
        """Génère des questions : Gemini si dispo, sinon InterviewAI."""

        # Essayer Gemini
        if self.gemini.enabled and cv_text:
            try:
                gemini_questions = self._generate_with_gemini(
                    cv_text=cv_text,
                    job_title=job_title,
                    difficulty=difficulty,
                    num_questions=num_questions,
                )
                if gemini_questions:
                    logger.info("Questions Gemini générées: %s", len(gemini_questions))
                    return gemini_questions
            except Exception as e:
                logger.error("Erreur Gemini questions: %s", e)



        # Fallback InterviewAI
        logger.info("Fallback InterviewAI pour questions")
        return self.ai.generate_questions(cv_text, job_title, difficulty, num_questions)

    async def generate_questions_parallel(
        self,
        cv_text: str,
        job_title: Optional[str],
        difficulty: str,
        count: int = 5,
    ) -> List[Dict[str, Any]]:
        """Génère N questions en parallèle via Gemini (SDK synchrone wrap en threads).

        - Semaphore(3) pour limiter la concurrence
        - Rate-limit global via gemini_limiter
        - Fallback individuel par question via InterviewAI
        """
        # Gemini indisponible => fallback complet
        if not (self.gemini and getattr(self.gemini, "enabled", False) and cv_text):
            return self.ai.generate_questions(cv_text, job_title, difficulty, count)

        # Prépare les infos pour générer les prompts
        level_map = {"easy": "junior", "medium": "confirmé", "hard": "senior"}
        level = level_map.get(difficulty, "confirmé")
        skills = self.ai._extract_skills_from_cv(cv_text)
        skill = skills[0] if skills else "général"
        types = ["technical", "behavioral", "situational"]

        semaphore = asyncio.Semaphore(3)

        def build_prompt(q_type: str) -> str:
            return f"""
Tu es un recruteur technique.
Génère une question d'entretien {q_type}.
Niveau: {level}.
Compétence ciblée: {skill}.

Optionnel contexte poste: {job_title or 'N/A'}.

Contexte CV (extrait):
{cv_text[:800]}

Contraintes:
- Retourne UNIQUEMENT la question (texte brut) sans guillemets.
- La question doit être interrogative et contenir au moins 20 caractères.
""".strip()

        async def fetch_one(idx: int) -> Dict[str, Any]:
            q_num = idx + 1
            q_type = types[idx % len(types)]
            prompt = build_prompt(q_type)

            async with semaphore:
                # Rate limit global Gemini (plan gratuit)
                try:
                    can_req = gemini_limiter.can_request()
                    if not can_req:
                        wait_time = gemini_limiter.wait_time()
                        logger.warning(f"Gemini rate limit: wait {wait_time}s")
                        raise RuntimeError(
                            f"Rate limit Gemini atteint. Attente: {wait_time:.1f}s"
                        )
                except Exception as e:
                    raise

                try:
                    from google.genai import types as genai_types

                    def call_gemini() -> Optional[Dict[str, Any]]:
                        response = self.gemini.client.models.generate_content(
model="gemini-1.5-flash-8b",
                    contents=prompt,
                            config=genai_types.GenerateContentConfig(
                                temperature=0.7,
                                max_output_tokens=220,
                            ),
                        )
                        question_text = (response.text or "").strip().strip('"').strip("'")
                        if len(question_text) < 20 or "?" not in question_text:
                            return None
                        return {
                            "question_number": q_num,
                            "question_text": question_text,
                            "question_type": q_type,
                            "expected_keywords": ["réponse personnalisée"],
                            "difficulty": difficulty,
                            "source": "gemini",
                            "used_gemini": True,
                        }

                    result = await asyncio.to_thread(call_gemini)
                    if result:
                        return result
                    raise ValueError("Structure Gemini invalide")

                except Exception as e:
                    logger.warning(f"Gemini question {q_num} failed: {e}")
                    # fallback individuel (heuristique) - méthode privée
                    fallback = self.ai._generate_single_question(
                        q_type, difficulty, skills, job_title, q_num
                    )
                    return {
                        **fallback,
                        "question_number": q_num,
                        "source": "fallback",
                        "fallback_reason": "rate_limit" if "limit" in str(e).lower() else "error"
                    }

        tasks = [fetch_one(i) for i in range(count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        questions: List[Dict[str, Any]] = []
        for i, res in enumerate(results):
            q_num = i + 1
            if isinstance(res, Exception) or not isinstance(res, dict):
                q_type = types[i % len(types)]
                fallback = self.ai._generate_single_question(
                    q_type, difficulty, skills, job_title, q_num
                )
                questions.append({**fallback, "question_number": q_num, "source": "fallback", "fallback_reason": "timeout_or_error"})
            else:
                questions.append(res)

        return questions

    def _generate_with_gemini(

        self,
        cv_text: str,
        job_title: Optional[str],
        difficulty: str,
        num_questions: int,
    ) -> Optional[List[Dict[str, Any]]]:
        """Génère questions via Gemini.

        Retourne une liste du même schéma que `InterviewAI.generate_questions`.
        """

        # Mapping difficulté
        level_map = {"easy": "junior", "medium": "confirmé", "hard": "senior"}
        level = level_map.get(difficulty, "confirmé")

        # Extraire skills du CV (si possible)
        skills = self.ai._extract_skills_from_cv(cv_text)
        skill = skills[0] if skills else "général"

        # Répartition des types
        types = ["technical", "behavioral", "situational"]

        questions: List[Dict[str, Any]] = []

        for i in range(num_questions):
            q_type = types[i % len(types)]

            prompt = f"""
Tu es un recruteur technique.
Génère une question d'entretien {q_type}.
Niveau: {level}.
Compétence ciblée: {skill}.

Optionnel contexte poste: {job_title or 'N/A'}.

Contexte CV (extrait):
{cv_text[:800]}

Contraintes:
- Retourne UNIQUEMENT la question (texte brut) sans guillemets.
- La question doit être interrogative et contenir au moins 20 caractères.
""".strip()

            # Rate limit global Gemini (plan gratuit)
            if not gemini_limiter.can_request():
                wait = gemini_limiter.wait_time()
                logger.warning(f"Rate limit Gemini atteint (interview questions). Attente: {wait:.1f}s")
                return None

            try:
                from google.genai import types as genai_types

                response = self.gemini.client.models.generate_content(
                    model="gemini-1.5-flash-8b",
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=220,
                    ),
                )


                question_text = (response.text or "").strip().strip('"').strip("'")

                if len(question_text) < 20 or "?" not in question_text:
                    return None

                questions.append(
                    {
                        "question_number": i + 1,
                        "question_text": question_text,
                        "question_type": q_type,
                        "expected_keywords": ["réponse personnalisée"],
                        "difficulty": difficulty,
                        "used_gemini": True,
                    }
                )
            except Exception:
                return None

        return questions

    def evaluate_answer(
        self,
        question: Dict[str, Any],
        answer: str,
    ) -> Dict[str, Any]:
        """Évalue une réponse : Gemini si dispo, sinon InterviewAI."""

        # Essayer Gemini
        if self.gemini.enabled and answer and len(answer) > 10:
            try:
                gemini_eval = self._evaluate_with_gemini(question=question, answer=answer)
                if gemini_eval:
                    logger.info(
                        "Évaluation Gemini - Score: %s",
                        gemini_eval.get("answer_score", 0),
                    )
                    return gemini_eval
            except Exception as e:
                logger.error("Erreur Gemini évaluation: %s", e)

        # Fallback InterviewAI
        return self.ai.evaluate_answer(question, answer)

    def _evaluate_with_gemini(
        self,
        question: Dict[str, Any],
        answer: str,
    ) -> Optional[Dict[str, Any]]:
        """Évalue via Gemini.

        Retourne un dict au même format que `InterviewAI.evaluate_answer`.
        """

        prompt = f"""
Tu es un expert en évaluation d'entretiens.
Évalue cette réponse.

=== QUESTION ===
{question.get('question_text', '')}

=== RÉPONSE ===
{answer}

Retourne UNIQUEMENT ce JSON valide (pas de texte autour) :
{{
  "answer_score": 75,
  "feedback_text": "Feedback constructif en 2-3 phrases",
  "detected_keywords": ["point abordé 1"],
  "missing_keywords": ["point manquant 1"],
  "is_complete": true
}}
""".strip()

        # Rate limit global Gemini (plan gratuit)
        if not gemini_limiter.can_request():
            wait = gemini_limiter.wait_time()
            logger.warning(f"Rate limit Gemini atteint (interview evaluation). Attente: {wait:.1f}s")
            return None

        try:
            from google.genai import types as genai_types

            response = self.gemini.client.models.generate_content(
model="gemini-1.5-flash-8b",
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=380,
                ),
            )


            raw = (response.text or "").strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(raw)

            if not isinstance(result, dict):
                return None

            return {
                "answer_score": result.get("answer_score", 0),
                "feedback_text": result.get("feedback_text", "Évaluation non disponible"),
                "detected_keywords": result.get("detected_keywords", []),
                "missing_keywords": result.get("missing_keywords", []),
                "is_complete": result.get("is_complete", True),
                "used_gemini": True,
            }
        except Exception:
            return None

    def generate_final_feedback(self, qa_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Feedback global : Gemini si dispo, sinon InterviewAI."""

        if self.gemini.enabled and qa_list:
            try:
                gemini_feedback = self._feedback_with_gemini(qa_list)
                if gemini_feedback:
                    return gemini_feedback
            except Exception as e:
                logger.error("Erreur Gemini feedback: %s", e)

        return self.ai.generate_final_feedback(qa_list)

    def _feedback_with_gemini(self, qa_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Feedback global via Gemini."""

        history = "\n".join(
            [
                f"Q{i+1}: {qa.get('question_text', '')[:70]}... Score: {qa.get('answer_score', 0)}"
                for i, qa in enumerate(qa_list)
            ]
        )

        avg = sum(qa.get("answer_score", 0) for qa in qa_list) / max(1, len(qa_list))

        prompt = f"""
Tu es un coach carrière.
Fais un bilan de cet entretien.

=== HISTORIQUE ===
{history}

Score moyen: {avg:.0f}/100

Retourne UNIQUEMENT ce JSON (pas de texte autour) :
{{
  "total_score": 75,
  "general_feedback": "Bilan en 2-3 phrases",
  "strengths": ["force 1", "force 2"],
  "areas_to_improve": ["axe 1", "axe 2"]
}}
""".strip()

        # Rate limit global Gemini (plan gratuit)
        if not gemini_limiter.can_request():
            wait = gemini_limiter.wait_time()
            logger.warning(f"Rate limit Gemini atteint (interview feedback). Attente: {wait:.1f}s")
            return None

        try:
            from google.genai import types as genai_types

            response = self.gemini.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=genai_types.GenerateContentConfig(temperature=0.4, max_output_tokens=500),
            )


            raw = (response.text or "").strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(raw)
            if not isinstance(result, dict):
                return None

            result["used_gemini"] = True
            return result
        except Exception:
            return None
