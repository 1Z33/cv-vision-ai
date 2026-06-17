"""app.services.gemini_service

Service Gemini-first pour l'entretien vocal.

- Une seule classe: GeminiService
- Fournit:
  - generate_next_question()
  - evaluate_answer()
  - generate_final_feedback()

Gemini d'abord, fallback sur InterviewEngine.ai (heuristiques déjà existantes).
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    from app.services.gemini_client import gemini_client
    from app.services.interview_engine import InterviewEngine
except ModuleNotFoundError:  # pragma: no cover
    # Permet d'importer le module en dehors du contexte backend/app
    from services.gemini_client import gemini_client
    from services.interview_engine import InterviewEngine


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InterviewHistoryTurn:
    question_text: str
    answer_text: str
    score: Optional[int] = None
    detected_keywords: Optional[List[str]] = None
    missing_keywords: Optional[List[str]] = None


class GeminiService:
    """Gemini interview orchestration."""

    def __init__(
        self,
        *,
        engine: Optional[InterviewEngine] = None,
        client=gemini_client,
    ) -> None:
        self.engine = engine or InterviewEngine()
        self.client = client

        self._recruiter_context = (
            "Tu es un recruteur professionnel menant un entretien ORAL. "
            "Tu dois être naturel à l'oral, concis et adaptatif. "
            "Tu évalues les réponses et tu déduis des faiblesses."
        )

    def is_available(self) -> bool:
        return bool(
            self.client
            and getattr(self.client, "enabled", False)
            and getattr(self.client, "client", None)
        )

    @staticmethod
    def _strip_json_fence(text: str) -> str:
        text = (text or "").strip()
        return text.replace("```json", "").replace("```", "").strip()

    def _fallback_next_question(
        self,
        *,
        job_title: str,
        difficulty: str,
        cv_text: str = "",
        question_number: int = 1,
        previous_answer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Désactivé pour Live Interview WS (Gemini-only)."""
        raise RuntimeError("_fallback_next_question is disabled in Gemini-only mode")


    def _build_prompt_next_question(
        self,
        *,
        job_title: str,
        difficulty: str,
        question_number: int,
        history: List[InterviewHistoryTurn],
    ) -> str:
        history_block: List[Dict[str, Any]] = []
        for i, t in enumerate(history):
            history_block.append(
                {
                    "turn": i + 1,
                    "question": t.question_text,
                    "answer": t.answer_text,
                    "score": t.score,
                    "detected_keywords": t.detected_keywords or [],
                    "missing_keywords": t.missing_keywords or [],
                }
            )

        return (
            f"{self._recruiter_context}\n\n"
            f"Contexte entretien:\n"
            f"- Poste visé: {job_title}\n"
            f"- Difficulté: {difficulty}\n"
            f"- Prochaine question: {question_number}\n\n"
            f"Historique complet (tours précédents):\n"
            f"{json.dumps(history_block, ensure_ascii=False, indent=2)}\n\n"
            "Règles (très important):\n"
            "1) Génère UNE seule question ORALE (max 2 phrases).\n"
            "2) Adapte la question aux faiblesses déduites de l'historique.\n"
            "3) Ne génère PAS de listes.\n"
            "4) Doit être naturellement interrogative.\n"
            "5) Réponds UNIQUEMENT avec un JSON valide.\n\n"
            "Schéma JSON:\n"
            f"{{\n"
            f"  \"question_number\": {question_number},\n"
            f"  \"question_text\": \"string\",\n"
            "  \"question_type\": \"technical|behavioral|situational\",\n"
            "  \"expected_keywords\": [\"string\"],\n"
            "  \"weaknesses_to_address\": [\"string\"],\n"
            "  \"source\": \"gemini\",\n"
            "  \"fallback_reason\": null\n"
            "}}"
        )

    async def generate_next_question(
        self,
        *,
        job_title: str,
        difficulty: str,
        question_number: int,
        history: List[InterviewHistoryTurn],
        cv_text: str = "",
    ) -> Dict[str, Any]:
        """Génère la question suivante avec historique et fallback."""
        if not self.is_available():
            raise RuntimeError("Gemini client indisponible")


        prompt = self._build_prompt_next_question(
            job_title=job_title,
            difficulty=difficulty,
            question_number=question_number,
            history=history,
        )

        try:
            from google.genai import types as genai_types

            def _call():
                return self.client.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        temperature=0.55,
                        max_output_tokens=350,
                    ),
                )

            response = await asyncio.to_thread(_call)
            raw = self._strip_json_fence(getattr(response, "text", "") or "")
            result = json.loads(raw)

            if not isinstance(result, dict) or "question_text" not in result:
                raise ValueError("Gemini JSON invalide")

            result.setdefault("fallback_reason", None)
            result.setdefault("expected_keywords", [])
            result.setdefault("question_type", "behavioral")
            result.setdefault("weaknesses_to_address", [])
            result.setdefault("source", "gemini")
            return result

        except Exception as e:
            logger.warning("GeminiService.generate_next_question fallback: %s", e)
            return self._fallback_next_question(
                job_title=job_title,
                difficulty=difficulty,
                cv_text=cv_text,
                question_number=question_number,
                previous_answer=(history[-1].answer_text if history else None),
            )

    async def evaluate_answer(
        self,
        *,
        question: Dict[str, Any],
        answer: str,
        job_title: str = "",
        history: Optional[List[InterviewHistoryTurn]] = None,
    ) -> Dict[str, Any]:
        """Évalue une réponse (Gemini d'abord, sinon fallback InterviewEngine.ai)."""
        if not self.is_available():
            return self.engine.ai.evaluate_answer(question, answer)

        # Schéma attendu par l'application: au minimum answer_score, feedback_text.
        eval_input = {
            "question": question,
            "answer": answer,
            "job_title": job_title,
        }

        try:
            from google.genai import types as genai_types

            instruction = (
                "Tu évalues la réponse et renvoies UNIQUEMENT un JSON valide avec:\n"
                "- answer_score: int (0-100)\n"
                "- feedback_text: string\n"
                "- detected_keywords: list[string]\n"
                "- missing_keywords: list[string]\n"
                "- is_complete: bool\n"
            )

            def _call():
                return self.client.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=instruction + "\n" + json.dumps(eval_input, ensure_ascii=False),
                    config=genai_types.GenerateContentConfig(
                        temperature=0.3,
                        max_output_tokens=450,
                    ),
                )

            response = await asyncio.to_thread(_call)
            raw = self._strip_json_fence(getattr(response, "text", "") or "")
            result = json.loads(raw)

            if not isinstance(result, dict) or "answer_score" not in result:
                raise ValueError("Gemini JSON invalide pour evaluate_answer")

            result.setdefault("detected_keywords", [])
            result.setdefault("missing_keywords", question.get("expected_keywords", []))
            result.setdefault("is_complete", True)
            result.setdefault("feedback_text", "")
            return result

        except Exception as e:
            logger.warning("GeminiService.evaluate_answer fallback: %s", e)
            return self.engine.ai.evaluate_answer(question, answer)

    async def generate_final_feedback(
        self,
        *,
        qa_list: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Génère un feedback global de fin (Gemini d'abord, sinon fallback InterviewEngine.ai)."""
        if not self.is_available():
            return self.engine.ai.generate_final_feedback(qa_list)

        try:
            from google.genai import types as genai_types

            instruction = (
                "Tu fournis un feedback final structuré. Renvoie UNIQUEMENT un JSON valide avec:\n"
                "- total_score: int\n"
                "- general_feedback: string\n"
                "- strengths: list[string]\n"
                "- areas_to_improve: list[string]\n"
            )

            payload = {"qa_list": qa_list}

            def _call():
                return self.client.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=instruction + "\n" + json.dumps(payload, ensure_ascii=False),
                    config=genai_types.GenerateContentConfig(
                        temperature=0.4,
                        max_output_tokens=600,
                    ),
                )

            response = await asyncio.to_thread(_call)
            raw = self._strip_json_fence(getattr(response, "text", "") or "")
            result = json.loads(raw)

            if not isinstance(result, dict) or "total_score" not in result:
                raise ValueError("Gemini JSON invalide pour generate_final_feedback")

            result.setdefault("general_feedback", "")
            result.setdefault("strengths", [])
            result.setdefault("areas_to_improve", [])
            return result

        except Exception as e:
            logger.warning("GeminiService.generate_final_feedback fallback: %s", e)
            return self.engine.ai.generate_final_feedback(qa_list)

