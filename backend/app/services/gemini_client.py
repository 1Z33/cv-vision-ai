"""Client Gemini mutualisé.

Ce module est volontairement simple :
- Ne remplace pas l'analyse CV existante (gemini_cv_analyzer.py)
- Sert à réutiliser la logique Gemini côté future interview/évaluation
- Utilise le singleton existant gemini_analyzer (optionnel) pour éviter les doublons

Note : ce projet gère déjà l'analyse CV dans app/services/gemini_cv_analyzer.py.
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any, Dict, Optional, List

from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Wrapper minimal Gemini.

    - Si le singleton gemini_analyzer est disponible, on le réutilise.
    - Sinon, on tente une configuration directe via google-genai.

    But: fournir une base réutilisable pour l'interview (questions + évaluation).
    """

    def __init__(self):
        self.enabled: bool = False
        self.client = None
        self._configure()

        # Réutilisation du singleton existant (si présent)
        self.cv_analyzer = None
        try:
            from app.services.gemini_cv_analyzer import gemini_analyzer

            self.cv_analyzer = gemini_analyzer
        except Exception:
            self.cv_analyzer = None

    def _configure(self) -> None:
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

    def _strip_json_fence(self, text: str) -> str:
        text = text.strip()
        # Supprime éventuellement les fences markdown
        text = text.replace("```json", "").replace("```", "").strip()
        return text

    def analyze_questions_and_evaluate(
        self,
        job_description: str,
        candidate_profile: str,
        questions_count: int = 8,
        temperature: float = 0.2,
    ) -> Optional[Dict[str, Any]]:
        """Génère des questions d'entretien + une grille d'évaluation.

        Retourne UNIQUEMENT un dict JSON si succès, sinon None.

        Schéma JSON attendu (exemple) :
        {
          "questions": [{"question": "...", "focus": "..."}],
          "evaluation_rubric": {
              "criteria": [{"name": "...", "weight": 0.2}],
              "scoring_notes": "..."
          },
          "meta": {"questions_count": 8, "generated_at": "..."}
        }
        """

        if not self.enabled:
            return None
        if not job_description or not candidate_profile:
            return None

        prompt = f"""
Tu es un expert RH senior spécialisé en recrutement tech.

Objectif :
1) Générer des questions d'entretien pertinentes (fondées sur l'offre)
2) Fournir une grille d'évaluation claire (critères + pondérations)
3) Éviter les hallucinations : rester plausible et opérationnel

=== OFFRE D'EMPLOI ===
{job_description[:4000]}

=== PROFIL CANDIDAT ===
{candidate_profile[:4000]}

=== CONTRAINTES ===
- Nombre de questions: {questions_count}
- Retourne UNIQUEMENT un JSON valide, sans balises markdown.

=== JSON SORTIE EXACTEMENT ===
{{
  "questions": [
    {{
      "question": "string",
      "focus": "string"
    }}
  ],
  "evaluation_rubric": {{
    "criteria": [
      {{
        "name": "string",
        "weight": 0.0
      }}
    ],
    "scoring_notes": "string"
  }},
  "meta": {{
    "questions_count": {questions_count},
    "generated_at": "ISO_TIMESTAMP"
  }}
}}
"""

        # Rate limit global Gemini (partagé avec gemini_cv_analyzer)
        try:
            from app.services.gemini_cv_analyzer import gemini_limiter

            if not gemini_limiter.can_request():
                wait = gemini_limiter.wait_time()
                logger.warning(f"Rate limit Gemini atteint. Attente: {wait:.1f}s")
                return None
        except Exception:
            # Ne jamais casser l'app si le limiter n'est pas importable
            pass

        try:
            from google.genai import types



            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=2048,
                ),
            )

            raw_text = self._strip_json_fence(response.text)
            result = json.loads(raw_text)

            # Validation minimale
            if not isinstance(result, dict):
                return None
            if "questions" not in result or not isinstance(result["questions"], list):
                result["questions"] = []
            if "evaluation_rubric" not in result or not isinstance(result["evaluation_rubric"], dict):
                result["evaluation_rubric"] = {"criteria": [], "scoring_notes": ""}

            result["meta"] = result.get("meta") or {}
            result["meta"]["generated_at"] = datetime.utcnow().isoformat()
            result["meta"]["questions_count"] = questions_count
            result["used_gemini"] = True
            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON invalide de Gemini: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur génération questions/evaluation: {e}")
            return None

    def status(self) -> Dict[str, Any]:
        return {
            "enabled": bool(self.enabled),
            "model": "gemini-2.0-flash" if self.enabled else None,
            "has_cv_analyzer_singleton": self.cv_analyzer is not None,
        }


# Singleton (optionnel)
gemini_client = GeminiClient()
