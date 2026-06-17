"""
CV Model Analyzer - Analyse complète des CV selon le modèle universel

Combine analyse heuristique (rapide) + analyse Gemini (profonde) + analyse visuelle (PDF).
"""

import json
import re
import os
from typing import Dict, List, Optional, Any
from pathlib import Path


class CVModelAnalyzer:
    """
    Analyseur de CV basé sur le modèle universel professionnel.

    Modes:
    - analyze_only: Analyse + score + recommandations
    - improve: Analyse + suggestions détaillées d'amélioration
    - generate: Analyse + génération d'un CV optimisé
    """

    def __init__(self, model_file: Optional[str] = None):
        if model_file is None:
            base_dir = Path(__file__).parent.parent
            model_file = base_dir / "data" / "cv_model_universal.json"

        with open(model_file, "r", encoding="utf-8") as f:
            self.model = json.load(f)

        self.structure = self.model["structure"]
        self.visual = self.model["visual_design"]
        self.ats = self.model["ats_compatibility"]
        self.scoring = self.model["scoring_global"]

    def analyze(self, cv_text: str, job_title: str, mode: str = "analyze_only") -> Dict:
        """
        Analyse complète d'un CV.

        Args:
            cv_text: Texte extrait du CV
            job_title: Poste visé
            mode: analyze_only | improve | generate

        Returns:
            Dict avec scores, recommandations et (optionnel) CV généré
        """
        # 1. Analyse heuristique (rapide)
        structure_score = self._analyze_structure(cv_text)
        metrics_score = self._analyze_metrics(cv_text)
        ats_score = self._analyze_ats(cv_text)
        keywords_score = self._analyze_keywords(cv_text, job_title)
        length_score = self._analyze_length(cv_text)

        # 2. Scores pondérés
        total = (
            structure_score["score"] * 0.25 +
            metrics_score["score"] * 0.25 +
            ats_score["score"] * 0.20 +
            keywords_score["score"] * 0.15 +
            length_score["score"] * 0.15
        )

        # 3. Recommandations
        recommendations = self._generate_recommendations(
            structure_score, metrics_score, ats_score, keywords_score, length_score
        )

        # 4. Éléments manquants
        missing = self._find_missing(cv_text)

        result = {
            "total_score": round(total, 1),
            "model_version": self.model["version"],
            "mode": mode,
            "structure_score": structure_score,
            "metrics_score": metrics_score,
            "ats_score": ats_score,
            "keywords_score": keywords_score,
            "length_score": length_score,
            "recommendations": recommendations,
            "priority_actions": self._priority_actions(recommendations, missing),
            "model_compliance_percent": round(total, 1),
            "missing_elements": missing
        }

        # 5. Génération si demandée
        if mode == "generate":
            result["generated_cv"] = self._generate_improved_cv(cv_text, job_title, recommendations)
            result["generated_cv_html"] = self._generate_html_cv(result["generated_cv"])

        return result

    def _analyze_structure(self, cv_text: str) -> Dict:
        """Analyse la structure du CV."""
        text_lower = cv_text.lower()
        score = 0
        max_score = 100
        feedback = []
        suggestions = []

        # Détection des sections
        sections_found = []
        section_keywords = {
            "header": ["nom", "email", "téléphone", "phone", "adresse", "linkedin"],
            "summary": ["résumé", "profil", "summary", "objectif", "objective"],
            "experience": ["expérience", "experience", "expériences", "parcours"],
            "skills": ["compétences", "competences", "skills", "aptitudes"],
            "education": ["formation", "éducation", "education", "diplôme", "diplome", "études"]
        }

        for section, keywords in section_keywords.items():
            if any(kw in text_lower for kw in keywords):
                sections_found.append(section)
                score += 15

        # Bonus sections optionnelles
        optional = ["certifications", "projets", "langues", "publications"]
        for opt in optional:
            if opt in text_lower:
                score += 5

        # Pénalités
        if len(sections_found) < 4:
            suggestions.append(f"Ajoutez les sections manquantes: {set(section_keywords.keys()) - set(sections_found)}")

        # Ordre anti-chronologique (heuristique simple)
        dates = re.findall(r"(19|20)\d{2}", cv_text)
        if len(dates) >= 2:
            try:
                if int(dates[0]) < int(dates[-1]):
                    score += 10
                    feedback.append("Ordre anti-chronologique détecté ✓")
                else:
                    suggestions.append("Vérifiez l'ordre anti-chronologique (plus récent en haut)")
            except:
                pass

        score = min(score, max_score)

        return {
            "section": "structure",
            "score": score,
            "max_score": max_score,
            "feedback": "; ".join(feedback) if feedback else "Structure de base présente",
            "suggestions": suggestions if suggestions else ["Structure correcte"],
            "sections_found": sections_found
        }

    def _analyze_metrics(self, cv_text: str) -> Dict:
        """Analyse la présence de métriques chiffrées."""
        text = cv_text

        # Compte les chiffres/signes de pourcentage
        numbers = re.findall(r"\b\d+(?:[.,]\d+)?\b", text)
        percentages = re.findall(r"\d+(?:[.,]\d+)?\s*%", text)

        # Verbes d'action
        action_verbs = self.structure["experience"]["action_verbs"]
        verbs_found = [v for v in action_verbs if v.lower() in text.lower()]

        # Verbes faibles
        weak_verbs = self.structure["experience"]["weak_verbs"]
        weak_found = [v for v in weak_verbs if v.lower() in text.lower()]

        # Calcul du score
        score = 0
        score += min(len(numbers) * 3, 30)  # Max 30 pts
        score += min(len(percentages) * 5, 25)  # Max 25 pts
        score += min(len(verbs_found) * 4, 30)  # Max 30 pts
        score -= min(len(weak_found) * 3, 15)  # Pénalité max 15 pts

        score = max(0, min(score, 100))

        # Exemples de métriques trouvées
        metric_examples = []
        sentences = text.split(".")
        for sent in sentences:
            if re.search(r"\d+(?:[.,]\d+)?\s*%", sent) or re.search(r"\b(?:augmenté|réduit|augmente|reduit|gagné|gagne|créé|cree|développé|developpe)\b.*\d+", sent.lower()):
                metric_examples.append(sent.strip()[:100])

        return {
            "score": score,
            "metrics_count": len(numbers),
            "metrics_ratio": round(len(numbers) / max(len(sentences), 1), 2),
            "action_verbs_count": len(verbs_found),
            "weak_verbs_count": len(weak_found),
            "examples": metric_examples[:5]
        }

    def _analyze_ats(self, cv_text: str) -> Dict:
        """Analyse la compatibilité ATS."""
        text_lower = cv_text.lower()
        score = 0
        issues = []

        # Format (15 pts) - on suppose PDF
        score += 15

        # Structure (20 pts)
        if any(s in text_lower for s in ["expérience", "compétences", "formation"]):
            score += 20
        else:
            issues.append("Sections standard manquantes")

        # Mots-clés (25 pts) - simplifié
        score += 15  # Base

        # Pas de tableaux (15 pts)
        if "|" in cv_text or "\t" in cv_text:
            issues.append("Tableaux détectés - risque pour l'ATS")
        else:
            score += 15

        # Police standard (10 pts) - impossible à vérifier sur texte brut
        score += 10

        # Pas de graphiques (15 pts)
        graphic_keywords = ["image", "graphique", "chart", "diagramme", "photo"]
        if any(kw in text_lower for kw in graphic_keywords):
            issues.append("Éléments graphiques détectés")
        else:
            score += 15

        score = min(score, 100)

        return {
            "score": score,
            "file_format": "PDF (supposé)",
            "has_tables": "|" in cv_text,
            "has_images": any(kw in text_lower for kw in graphic_keywords),
            "has_graphics": any(kw in text_lower for kw in graphic_keywords),
            "standard_fonts": True,
            "keyword_density": 0.0,  # Sera calculé par Gemini
            "issues": issues if issues else ["Aucun problème ATS majeur détecté"]
        }

    def _analyze_keywords(self, cv_text: str, job_title: str) -> Dict:
        """Analyse la pertinence des mots-clés pour le poste."""
        text_lower = cv_text.lower()

        # Mots-clés génériques par métier (simplifié)
        job_keywords = {
            "developpeur": ["python", "javascript", "react", "node", "sql", "git", "api", "docker"],
            "medecin": ["diagnostic", "patient", "traitement", "clinique", "soins", "chirurgie"],
            "comptable": ["comptabilité", "bilan", "audit", "fiscal", "excel", "sap"],
            "marketing": ["stratégie", "digital", "seo", "réseaux sociaux", "analytics", "campagne"],
            "ingenieur": ["projet", "conception", "supervision", "normes", "autocad", "gestion"]
        }

        # Trouver les mots-clés pertinents
        matched = []
        missing = []

        job_lower = job_title.lower()
        keywords = job_keywords.get(job_lower, [])

        if not keywords:
            # Génération générique
            keywords = job_title.lower().split()

        for kw in keywords:
            if kw in text_lower:
                matched.append(kw)
            else:
                missing.append(kw)

        ratio = len(matched) / max(len(keywords), 1)
        score = min(ratio * 100, 100)

        return {
            "score": round(score, 1),
            "matched_keywords": matched,
            "missing_keywords": missing,
            "keyword_density": round(ratio, 2)
        }

    def _analyze_length(self, cv_text: str) -> Dict:
        """Analyse la longueur du CV."""
        chars = len(cv_text)

        # Estimation pages (environ 2000-2500 caractères par page)
        pages_estimate = chars / 2200

        # Recommandation
        if chars < 1500:
            recommendation = "CV trop court - développez vos expériences"
            score = 40
        elif chars < 3500:
            recommendation = "Longueur idéale pour un junior (1 page)"
            score = 90
        elif chars < 5000:
            recommendation = "Longueur acceptable (1-2 pages)"
            score = 85
        elif chars < 6000:
            recommendation = "Longueur correcte pour un senior (2 pages)"
            score = 80
        else:
            recommendation = "CV trop long - synthétisez (max 2 pages)"
            score = 50

        return {
            "score": score,
            "current_length_chars": chars,
            "recommended_max": 5500,
            "current_pages_estimate": round(pages_estimate, 1),
            "recommendation": recommendation
        }

    def _generate_recommendations(self, structure, metrics, ats, keywords, length) -> List[str]:
        """Génère les recommandations globales."""
        recs = []

        if structure["score"] < 70:
            recs.append("📋 **Structure**: Ajoutez les sections manquantes (résumé, expérience, compétences, formation)")

        if metrics["score"] < 60:
            recs.append("📊 **Métriques**: Ajoutez des chiffres et résultats quantifiés (ex: 'augmenté les ventes de 20%')")

        if ats["score"] < 70:
            recs.append("🤖 **ATS**: Évitez les tableaux, images et polices non standard")

        if keywords["score"] < 60:
            recs.append(f"🔑 **Mots-clés**: Intégrez les termes manquants: {', '.join(keywords['missing_keywords'][:5])}")

        if length["score"] < 70:
            recs.append(f"📄 **Longueur**: {length['recommendation']}")

        if not recs:
            recs.append("✅ Votre CV est bien structuré ! Quelques optimisations possibles pour viser l'excellence.")

        return recs

    def _priority_actions(self, recommendations: List[str], missing: List[str]) -> List[str]:
        """Actions prioritaires."""
        actions = []

        if missing:
            actions.append(f"Ajouter: {', '.join(missing[:3])}")

        for rec in recommendations:
            if "métriques" in rec.lower() or "chiffres" in rec.lower():
                actions.append("Ajouter 3-5 résultats chiffrés dans vos expériences")
            if "mots-clés" in rec.lower():
                actions.append("Adapter les mots-clés à l'offre d'emploi visée")
            if "structure" in rec.lower():
                actions.append("Réorganiser selon le format anti-chronologique")

        return actions[:5]

    def _find_missing(self, cv_text: str) -> List[str]:
        """Trouve les éléments manquants."""
        text_lower = cv_text.lower()
        missing = []

        required = {
            "Résumé professionnel": ["résumé", "profil", "summary"],
            "Expérience": ["expérience", "experience"],
            "Compétences": ["compétences", "competences", "skills"],
            "Formation": ["formation", "éducation", "education", "diplôme"],
            "Contact": ["email", "téléphone", "phone"]
        }

        for element, keywords in required.items():
            if not any(kw in text_lower for kw in keywords):
                missing.append(element)

        return missing

    def _generate_improved_cv(self, cv_text: str, job_title: str, recommendations: List[str]) -> str:
        """
        Génère un CV amélioré basé sur les recommandations.
        (Version simplifiée - la version complète utilisera Gemini)
        """
        # Template de base
        template = f"""=== CV OPTIMISÉ ===
Poste visé: {job_title}

RECOMMANDATIONS APPLIQUÉES:
{chr(10).join(f"- {r}" for r in recommendations[:5])}

--- CONTENU ORIGINAL AMÉLIORÉ ---

{cv_text[:500]}...

[Le CV complet optimisé serait généré ici par Gemini]
"""
        return template

    def _generate_html_cv(self, cv_text: str) -> str:
        """Génère une version HTML du CV."""
        colors = self.visual["colors"]
        fonts = self.visual["fonts"]

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>CV Optimisé</title>
    <style>
        body {{ font-family: {fonts['body']}; color: {colors['text']}; background: {colors['background']}; margin: 20mm; }}
        h1 {{ color: {colors['primary']}; font-size: {fonts['size_title']}; }}
        h2 {{ color: {colors['secondary']}; font-size: {fonts['size_heading']}; border-bottom: 1px solid {colors['light_gray']}; }}
        .section {{ margin-bottom: 14pt; }}
        .metric {{ font-weight: bold; color: {colors['accent']}; }}
    </style>
</head>
<body>
    <div class="cv-content">
        {cv_text.replace(chr(10), '<br>')}
    </div>
</body>
</html>"""
        return html


# Instance singleton
_analyzer: Optional[CVModelAnalyzer] = None

def get_analyzer() -> CVModelAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = CVModelAnalyzer()
    return _analyzer