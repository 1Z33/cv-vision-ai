"""CV Model Compliance Service

Compare un CV (texte extrait) avec un modèle universel JSON.

Note: la mise en forme (couleurs/polices) n'est pas vérifiable via texte extrait uniquement.
On score donc la compliance visuelle à un niveau "non vérifiable".
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional



class CVModelComplianceService:
    def __init__(self, model_path: Optional[str | Path] = None):
        if model_path is None:
            model_path = Path(__file__).parent.parent / "data" / "cv_model_universal_reference.json"
        self.model_path = Path(model_path)
        with open(self.model_path, "r", encoding="utf-8") as f:
            self.model = json.load(f)

        self.structure_model = self.model.get("structure", {})
        self.ats_model = self.model.get("ats_compatibility", {})
        self.weights = (self.model.get("scoring", {}) or {}).get("weights", {})

        # heuristiques
        self.section_patterns = {
            "contact": [r"contact", r"coordonnées", r"coordonnees", r"informations personnelles"],
            "summary": [r"résumé", r"resume", r"profil", r"objective", r"summary", r"objectif"],
            "experience": [r"expérience", r"experience", r"expériences", r"parcours"],
            "skills": [r"compétences", r"competences", r"skills", r"technologies", r"stack"],
            "education": [r"formation", r"éducation", r"education", r"diplôme", r"diplome", r"études"],
        }

        # Regex invariantes (évite de reconstruire à chaque evaluate)
        self._email_pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        self._phone_pattern = re.compile(r"\+?\d[\d\s().-]{7,}")
        self._token_pattern = re.compile(r"[a-zA-Z][a-zA-Z0-9+#/.]{1,30}")
        self._word_boundary_template = r"(?<![\w]){kw}(?![\w])"


        self.action_verbs = [
            "développé",
            "développée",
            "développés",
            "conçu",
            "géré",
            "optimisé",
            "réduit",
            "augmenté",
            "créé",
            "implémenté",
            "piloté",
            "automatisé",
            "analysé",
            "coordonné",
            "formé",
            "résolu",
            "supervisé",
            "conduit",
            "amélioré",
            "lancé",
        ]
        self.weak_verbs = [
            "fait",
            "aide",
            "participé",
            "assisté",
            "travaillé",
            "occupé",
            "tenu",
            "assuré",
            "effectué",
            "réalisé",
        ]

        self.metrics_number = re.compile(r"\b\d+(?:[.,]\d+)?\b")
        self.metrics_percentage = re.compile(r"\b\d+(?:[.,]\d+)?\s*%\b")

    # ---------------- Public API ----------------

    def evaluate(self, cv_text: str, job_title: str | None = None, job_description: str | None = None) -> Dict[str, Any]:
        cv_text = cv_text or ""
        text_lower = cv_text.lower()

        structure_breakdown = self._check_structure(cv_text)
        metrics_breakdown = self._check_metrics(cv_text)
        keywords_breakdown = self._check_keywords(text_lower, job_title or "", job_description or "")
        length_breakdown = self._check_length(cv_text)
        ats_breakdown = self._check_ats(text_lower)
        visual_breakdown = self._check_visual_unverifiable()

        total = self._aggregate_score(
            ats_breakdown["score"],
            structure_breakdown["score"],
            metrics_breakdown["score"],
            keywords_breakdown["score"],
            length_breakdown["score"],
            visual_breakdown["score"],
        )

        return {
            "model_name": self.model.get("model_name"),
            "model_version": self.model.get("version"),
            "total_score": total,
            "breakdown": {
                "ats_compatibility": ats_breakdown,
                "structure_sections": structure_breakdown,
                "metrics_presence": metrics_breakdown,
                "keywords_relevance": keywords_breakdown,
                "length_optimization": length_breakdown,
                "visual_consistency": visual_breakdown,
            },
        }

    # ---------------- Scoring helpers ----------------

    def _aggregate_score(
        self,
        ats_score: int,
        structure_score: int,
        metrics_score: int,
        keywords_score: int,
        length_score: int,
        visual_score: int,
    ) -> int:
        w = self.weights
        # fallback weights
        ats_w = float(w.get("ats_compatibility", 20))
        structure_w = float(w.get("structure_sections", 30))
        metrics_w = float(w.get("metrics_presence", 20))
        keywords_w = float(w.get("keywords_relevance", 15))
        length_w = float(w.get("length_optimization", 10))
        visual_w = float(w.get("visual_consistency", 5))
        w_sum = ats_w + structure_w + metrics_w + keywords_w + length_w + visual_w
        if w_sum <= 0:
            return 0

        # Visual peut être None => exclure du calcul pour éviter un score fantôme.
        visual_score_eff = 0 if visual_score is None else visual_score

        # On réduit le dénominateur si visual_score est None (exclu).
        if visual_score is None:
            w_sum_eff = w_sum - visual_w
            if w_sum_eff <= 0:
                return 0
            total = (
                ats_score * ats_w
                + structure_score * structure_w
                + metrics_score * metrics_w
                + keywords_score * keywords_w
                + length_score * length_w
            ) / w_sum_eff
        else:
            total = (
                ats_score * ats_w
                + structure_score * structure_w
                + metrics_score * metrics_w
                + keywords_score * keywords_w
                + length_score * length_w
                + visual_score_eff * visual_w
            ) / w_sum

        return int(round(max(0, min(100, total))))

    def _check_structure(self, cv_text: str) -> Dict[str, Any]:
        t = (cv_text or "").lower()

        # presence of required sections
        required = ["header", "professional_summary", "experience", "skills", "education"]
        found_flags = {
            "contact": any(re.search(p, t) for p in self.section_patterns["contact"]),
            "summary": any(re.search(p, t) for p in self.section_patterns["summary"]),
            "experience": any(re.search(p, t) for p in self.section_patterns["experience"]),
            "skills": any(re.search(p, t) for p in self.section_patterns["skills"]),
            "education": any(re.search(p, t) for p in self.section_patterns["education"]),
        }

        # ATS model wants header fields; we can only proxy via regex
        email_found = bool(self._email_pattern.search(cv_text or ""))
        phone_found = bool(self._phone_pattern.search(cv_text or ""))


        score = 0
        max_score = 100

        # Contact/header
        if found_flags["contact"] or email_found or phone_found:
            score += 25
        # Summary
        if found_flags["summary"]:
            score += 20
        # Experience
        if found_flags["experience"]:
            score += 25
        # Skills
        if found_flags["skills"]:
            score += 15
        # Education
        if found_flags["education"]:
            score += 15

        score = min(score, max_score)

        return {
            "score": int(score),
            "max_score": max_score,
            "found": found_flags,
            "header_proxies": {
                "email_found": email_found,
                "phone_found": phone_found,
            },
        }

    def _check_metrics(self, cv_text: str) -> Dict[str, Any]:
        t = cv_text or ""
        numbers = self.metrics_number.findall(t)
        percentages = self.metrics_percentage.findall(t)

        # action verbs proxy (presence)
        lower = t.lower()
        action_hits = 0
        weak_hits = 0
        for v in self.action_verbs:
            if v in lower:
                action_hits += 1
        for v in self.weak_verbs:
            if v in lower:
                weak_hits += 1

        score = 0
        # heuristics: numbers/percentages
        score += min(len(numbers) * 3, 45)
        score += min(len(percentages) * 7, 30)

        # verbs
        score += min(action_hits * 5, 20)
        score -= min(weak_hits * 4, 15)

        score = int(max(0, min(100, score)))
        return {
            "score": score,
            "metrics_numbers_count": len(numbers),
            "metrics_percentages_count": len(percentages),
            "action_verbs_hits": action_hits,
            "weak_verbs_hits": weak_hits,
        }

    def _check_keywords(self, text_lower: str, job_title: str, job_description: str) -> Dict[str, Any]:
        # Try to extract keywords from job_description; fallback to job_title tokens
        tokens: List[str] = []
        jd = (job_description or "").lower()
        src = jd if jd.strip() else (job_title or "").lower()
        tokens = self._token_pattern.findall(src)


        # normalize tokens
        stop = {"avec", "pour", "et", "ou", "de", "la", "le", "les", "du", "des", "en", "un", "une", "the", "and", "or", "to"}
        tokens = [t for t in tokens if t not in stop and len(t) >= 3]

        # choose top N unique
        uniq = []
        seen = set()
        for t in tokens:
            if t not in seen:
                uniq.append(t)
                seen.add(t)
            if len(uniq) >= 25:
                break

        if not uniq:
            return {
                "score": 40,
                "matched_keywords": [],
                "missing_keywords": [],
                "keywords_budget": 0,
            }

        matched = [k for k in uniq if re.search(rf"(?<![\w]){re.escape(k)}(?![\w])", text_lower)]

        missing = [k for k in uniq if k not in matched]

        ratio = len(matched) / max(len(uniq), 1)
        score = int(round(max(0, min(100, ratio * 100))))

        return {
            "score": score,
            "matched_keywords": matched[:10],
            "missing_keywords": missing[:10],
            "keywords_budget": len(uniq),
        }

    def _check_length(self, cv_text: str) -> Dict[str, Any]:
        # use word count heuristic
        words = (cv_text or "").split()
        word_count = len(words)

        # estimate pages ~ 1 page per 550 words (rough)
        pages_est = word_count / 550 if word_count else 0

        # score: prefer 1-2 pages. model guidelines are in chars; we do proxy via words.
        if pages_est <= 0.9:
            score = 45
            rec = "CV potentiellement trop court"
        elif pages_est <= 1.1:
            score = 95
            rec = "Longueur idéale (≈ 1 page)"
        elif pages_est <= 2.1:
            score = 85
            rec = "Longueur acceptable (≈ 1-2 pages)"
        else:
            score = 55
            rec = "CV potentiellement trop long"

        return {
            "score": int(score),
            "word_count": word_count,
            "estimated_pages": round(pages_est, 2),
            "recommendation": rec,
        }

    def _check_ats(self, text_lower: str) -> Dict[str, Any]:
        # text-only proxy: detect common table-like patterns
        issues: List[str] = []

        score = 0
        # PDF requirement cannot be verified from text; but we can penalize if text mentions non-PDF
        score += 10

        # forbidden elements via heuristics
        if "photo" in text_lower:
            issues.append("photo détectée (texte)")
        if "tableau" in text_lower or "|" in text_lower or "\t" in text_lower:
            issues.append("tableau/colonnes détectés (texte)")
        if any(kw in text_lower for kw in ["graphique", "diagramme", "chart", "image", "icône", "icon", "emoji"]):
            issues.append("élément graphique détecté (texte)")

        # base for structure compliance
        score += 60
        if issues:
            # penalize for each issue
            score -= 20 * min(len(issues), 3)

        score = int(max(0, min(100, score)))
        return {
            "score": score,
            "issues": issues,
        }

    def _check_visual_unverifiable(self) -> Dict[str, Any]:
        # Texte-only : on ne peut pas estimer la mise en forme visuelle.
        # Retourne score None pour permettre une exclusion dans l'agrégat.
        return {
            "score": None,
            "issues": ["Mise en forme visuelle non vérifiable depuis le texte extrait uniquement"],
            "status": "unverifiable_text_only",
        }


# Singleton
_compliance_service: Optional[CVModelComplianceService] = None


def get_cv_model_compliance_service() -> CVModelComplianceService:
    global _compliance_service
    if _compliance_service is None:
        _compliance_service = CVModelComplianceService()
    return _compliance_service

