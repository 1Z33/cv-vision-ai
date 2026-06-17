import os
import json
import logging
import time
from collections import deque
from typing import Dict, Optional
from datetime import datetime
from app.core.config import settings


logger = logging.getLogger(__name__)


class GeminiRateLimiter:
    """Limite les appels Gemini à 60 req/minute (plan gratuit)."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = deque()

    def _purge_old(self, now: float) -> None:
        while self.requests and self.requests[0] < now - self.window:
            self.requests.popleft()

    def can_request(self) -> bool:
        now = time.time()
        self._purge_old(now)

        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False

    def wait_time(self) -> float:
        now = time.time()
        self._purge_old(now)

        if len(self.requests) < self.max_requests:
            return 0.0
        return (self.requests[0] + self.window) - time.time()

    def get_status(self) -> dict:
        """Statut actuel du limiter."""
        now = time.time()
        self._purge_old(now)
        remaining = max(0, self.max_requests - len(self.requests))
        return {
            "used_requests": len(self.requests),
            "max_requests": self.max_requests,
            "remaining": remaining,
            "reset_in_seconds": self.wait_time(),
        }



# Singleton global - partagé par tous les appels Gemini de ce module
gemini_limiter = GeminiRateLimiter()


class GeminiCVAnalyzer:
    """Analyseur CV via Gemini API - SDK google-genai (officiel)"""

    def __init__(self):
        self.enabled = False
        self.client = None
        self._configure()

    def _configure(self):
        """Configuration avec nouveau SDK - import différé"""
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("GEMINI_API_KEY non définie - mode fallback activé")
            return

        try:
            from google import genai

            self.client = genai.Client(api_key=api_key)
            self.enabled = True
            logger.info("Gemini configuré avec succès (SDK google-genai)")

        except ImportError:
            logger.error("Package google-genai non installé. Run: pip install google-genai")
        except Exception as e:
            logger.error(f"Erreur configuration Gemini: {e}")

    def analyze(self, cv_text: str) -> Optional[Dict]:
        """Analyse un CV avec Gemini. Retourne None si indisponible."""
        if not self.enabled or not cv_text or len(cv_text) < 50:
            return None

        text_truncated = cv_text[:7000]

        prompt = f"""
Tu es un expert RH senior spécialisé en tech. Analyse ce CV de manière factuelle.

=== CV ===
{text_truncated}

=== INSTRUCTIONS STRICTES ===
Retourne UNIQUEMENT un JSON valide, sans balises markdown, sans texte avant/après.
Structure exacte :

{{
    "overall_score": 75,
    "structure_score": 80,
    "content_score": 70,
    "keywords_score": 75,
    "detected_skills": ["Python", "FastAPI", "PostgreSQL"],
    "missing_skills": [],
    "strengths": ["Bonne progression technique", "Expérience variée"],
    "weaknesses": ["Manque de détails sur les projets"],
    "recommendations": ["Ajouter des métriques aux projets", "Détailler l'architecture"],
    "estimated_seniority": "confirmé",
    "experience_years": 4,
    "raw_analysis": {{}}
}}

Règles :
- Scores sur 100, entiers
- detected_skills : compétences techniques UNIQUEMENT
- missing_skills : laisser vide si non pertinent
- estimated_seniority : "junior", "confirmé", "senior", ou "lead"
- experience_years : nombre entier d'années estimées
- raw_analysis : dict vide pour extensions futures
"""

        # Rate limit (plan gratuit)
        if not gemini_limiter.can_request():
            wait = gemini_limiter.wait_time()
            logger.warning(f"Rate limit Gemini atteint. Attente: {wait:.1f}s")
            return None

        try:
            from google.genai import types

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=2048,
                ),
            )

            raw_text = response.text.strip()
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

            result = json.loads(raw_text)

            # Validation minimale
            required_fields = {
                "overall_score": 0,
                "detected_skills": [],
                "strengths": [],
                "weaknesses": [],
            }
            for field, default in required_fields.items():
                if field not in result:
                    logger.warning(f"Champ manquant dans réponse Gemini: {field}")
                    result[field] = default

            result["used_gemini"] = True
            result["analyzed_at"] = datetime.utcnow().isoformat()

            logger.info(f"Analyse Gemini réussie - Score: {result['overall_score']}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON invalide de Gemini: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur analyse Gemini: {e}")
            return None

    def compare_with_job(self, cv_text: str, job_description: str) -> Optional[Dict]:
        """Matching CV vs offre d'emploi."""
        if not self.enabled:
            return None

        try:
            from google.genai import types

            prompt = f"""
Compare ce profil avec l'offre d'emploi. Retourne UNIQUEMENT JSON valide.

=== CV ===
{cv_text[:4000]}

=== OFFRE ===
{job_description[:4000]}

{{
    "match_score": 72,
    "matching_skills": ["Python", "Docker"],
    "missing_skills": ["Kubernetes", "AWS"],
    "gap_analysis": "Le candidat a les bases DevOps mais pas l'orchestration avancée",
    "learning_path": ["Cours Kubernetes de base", "Certification CKA"],
    "interview_focus": ["Vérifier l'expérience réelle avec Docker", "Tester l'apprentissage rapide"]
}}
"""

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2),
            )

            text = response.text.strip().replace("```json", "").replace("```", "").strip()
            result = json.loads(text)
            result["used_gemini"] = True
            return result

        except Exception as e:
            logger.error(f"Erreur matching job: {e}")
            return None


# Singleton
gemini_analyzer = GeminiCVAnalyzer()
