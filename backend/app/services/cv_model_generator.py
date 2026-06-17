"""
CV Model Generator Service

Génère des CV optimisés basés sur le modèle universel.
Modes:
- improve: Corrige un CV existant selon les recommandations
- generate: Crée un CV from scratch à partir des données utilisateur
"""

import json
import re
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from app.services.cv_model_compliance import get_cv_model_compliance_service


class CVModelGeneratorService:
    """
    Générateur de CV basé sur le modèle universel professionnel.
    """

    def __init__(self):
        self.compliance = get_cv_model_compliance_service()

        # Charger le template HTML
        template_path = Path(__file__).parent.parent / "templates" / "cv_profesionnal.html"
        with open(template_path, "r", encoding="utf-8") as f:
            self.html_template = f.read()

        # Charger le modèle
        model_path = Path(__file__).parent.parent / "data" / "cv_model_universal.json"
        with open(model_path, "r", encoding="utf-8") as f:
            self.model = json.load(f)

    def improve_cv(
        self,
        cv_text: str,
        job_title: str,
        user_data: Optional[Dict] = None
    ) -> Dict:
        """
        Améliore un CV existant selon le modèle universel.

        Args:
            cv_text: Texte du CV original
            job_title: Poste visé
            user_data: Données utilisateur complémentaires (optionnel)

        Returns:
            Dict avec CV amélioré, scores et recommandations
        """
        # 1. Analyser le CV existant
        compliance = self.compliance.evaluate(cv_text, job_title)

        # 2. Extraire les données structurées du CV
        extracted = self._extract_structure(cv_text)

        # 3. Appliquer les corrections selon les recommandations
        improved = self._apply_improvements(extracted, compliance, job_title)

        # 4. Générer les différents formats
        text_cv = self._render_text(improved)
        html_cv = self._render_html(improved)
        markdown_cv = self._render_markdown(improved)

        # 5. Ré-analyser le CV amélioré
        new_compliance = self.compliance.evaluate(text_cv, job_title)

        return {
            "mode": "improve",
            "original_score": compliance.total_score,
            "improved_score": new_compliance.total_score,
            "score_improvement": round(new_compliance.total_score - compliance.total_score, 1),
            "model_version": self.model["version"],
            "generated_at": datetime.now().isoformat(),
            "formats": {
                "text": text_cv,
                "html": html_cv,
                "markdown": markdown_cv
            },
            "improvements_applied": compliance.recommendations,
            "remaining_issues": new_compliance.recommendations,
            "compliance_details": {
                "original": {
                    "structure": compliance.structure_compliance["score"],
                    "metrics": compliance.metrics_compliance["score"],
                    "ats": compliance.ats_compliance["score"],
                    "keywords": compliance.keywords_compliance["score"],
                    "length": compliance.length_compliance["score"]
                },
                "improved": {
                    "structure": new_compliance.structure_compliance["score"],
                    "metrics": new_compliance.metrics_compliance["score"],
                    "ats": new_compliance.ats_compliance["score"],
                    "keywords": new_compliance.keywords_compliance["score"],
                    "length": new_compliance.length_compliance["score"]
                }
            }
        }

    def generate_cv(
        self,
        user_data: Dict,
        job_title: str,
        output_format: str = "all"
    ) -> Dict:
        """
        Génère un CV from scratch optimisé.

        Args:
            user_data: Données structurées de l'utilisateur
            job_title: Poste visé
            output_format: all | text | html | markdown

        Returns:
            Dict avec CV généré et métriques
        """
        # 1. Construire la structure optimisée
        cv_structure = self._build_optimal_structure(user_data, job_title)

        # 2. Générer les formats
        result = {
            "mode": "generate",
            "model_version": self.model["version"],
            "job_title": job_title,
            "generated_at": datetime.now().isoformat()
        }

        if output_format in ["text", "all"]:
            result["text"] = self._render_text(cv_structure)

        if output_format in ["html", "all"]:
            result["html"] = self._render_html(cv_structure)

        if output_format in ["markdown", "all"]:
            result["markdown"] = self._render_markdown(cv_structure)

        # 3. Évaluer la qualité
        text_for_eval = result.get("text", "")
        if text_for_eval:
            compliance = self.compliance.evaluate(text_for_eval, job_title)
            result["estimated_score"] = compliance.total_score
            result["estimated_ats_score"] = compliance.ats_compliance["score"]
            result["compliance_breakdown"] = {
                "structure": compliance.structure_compliance["score"],
                "metrics": compliance.metrics_compliance["score"],
                "ats": compliance.ats_compliance["score"],
                "keywords": compliance.keywords_compliance["score"],
                "length": compliance.length_compliance["score"]
            }

        return result

    def _extract_structure(self, cv_text: str) -> Dict:
        """Extrait la structure d'un CV existant."""
        lines = cv_text.strip().split("\n")
        text_lower = cv_text.lower()

        # Détection simple des sections
        structure = {
            "name": "",
            "contact": {},
            "summary": "",
            "experience": [],
            "skills": [],
            "education": [],
            "certifications": [],
            "languages": []
        }

        # Extraire le nom (première ligne non vide)
        for line in lines:
            stripped = line.strip()
            if stripped and not any(kw in stripped.lower() for kw in ["email", "téléphone", "phone", "@"]):
                structure["name"] = stripped
                break

        # Extraire le contact (lignes avec email/téléphone)
        contact_line = ""
        for line in lines:
            if "@" in line or "+243" in line or "téléphone" in line.lower():
                contact_line = line.strip()
                break

        # Extraire le résumé
        in_summary = False
        summary_lines = []
        for line in lines:
            if any(kw in line.lower() for kw in ["résumé", "profil", "summary", "objectif"]):
                in_summary = True
                continue
            if in_summary:
                if line.strip() and not any(kw in line.lower() for kw in ["expérience", "compétences", "formation"]):
                    summary_lines.append(line.strip())
                elif any(kw in line.lower() for kw in ["expérience", "compétences", "formation"]):
                    break
        structure["summary"] = " ".join(summary_lines)

        # Extraire l'expérience (simplifié)
        in_exp = False
        current_exp = None
        for line in lines:
            if any(kw in line.lower() for kw in ["expérience", "experience", "parcours"]):
                in_exp = True
                continue
            if in_exp:
                if any(kw in line.lower() for kw in ["compétences", "formation", "éducation", "certifications"]):
                    if current_exp:
                        structure["experience"].append(current_exp)
                    break

                stripped = line.strip()
                if stripped:
                    if "|" in stripped or "-" in stripped and any(c.isdigit() for c in stripped):
                        # Nouvelle expérience
                        if current_exp:
                            structure["experience"].append(current_exp)
                        parts = stripped.split("|")
                        current_exp = {
                            "title": parts[0].strip() if parts else "",
                            "company": parts[1].strip() if len(parts) > 1 else "",
                            "dates": "",
                            "location": "",
                            "bullets": []
                        }
                    elif stripped.startswith("•") or stripped.startswith("-"):
                        if current_exp:
                            current_exp["bullets"].append(stripped[1:].strip())

        if current_exp and current_exp not in structure["experience"]:
            structure["experience"].append(current_exp)

        return structure

    def _apply_improvements(self, extracted: Dict, compliance, job_title: str) -> Dict:
        """Applique les améliorations selon les recommandations."""
        improved = extracted.copy()

        # Améliorer le résumé
        if not improved.get("summary") or compliance.structure_compliance["score"] < 70:
            years = self._estimate_years(improved.get("experience", []))
            improved["summary"] = self._generate_summary(job_title, years, improved.get("experience", []))

        # Améliorer les bullets avec métriques
        for exp in improved.get("experience", []):
            bullets = exp.get("bullets", [])
            improved_bullets = []
            for bullet in bullets:
                # S'assurer que chaque bullet commence par un verbe d'action
                if not any(bullet.startswith(v) for v in self.model["structure"]["experience"]["action_verbs"]):
                    bullet = f"Développé {bullet[0].lower()}{bullet[1:]}"
                improved_bullets.append(bullet)
            exp["bullets"] = improved_bullets

        # Ajouter les mots-clés manquants
        missing_kw = compliance.keywords_compliance.get("missing_keywords", [])
        if missing_kw and "skills" in improved:
            improved["skills"] = list(set(improved.get("skills", []) + missing_kw[:3]))

        return improved

    def _build_optimal_structure(self, user_data: Dict, job_title: str) -> Dict:
        """Construit une structure CV optimale from scratch."""

        # Générer le résumé
        years = self._estimate_years(user_data.get("experience", []))
        summary = self._generate_summary(job_title, years, user_data.get("experience", []))

        # Formater l'expérience
        experience = []
        for exp in user_data.get("experience", []):
            bullets = exp.get("bullets", [])
            # Optimiser les bullets
            optimized = []
            for bullet in bullets:
                if not any(bullet.startswith(v) for v in self.model["structure"]["experience"]["action_verbs"]):
                    bullet = f"Développé {bullet[0].lower()}{bullet[1:]}"
                optimized.append(bullet)

            experience.append({
                "title": exp.get("title", ""),
                "company": exp.get("company", ""),
                "dates": exp.get("dates", ""),
                "location": exp.get("location", ""),
                "bullets": optimized[:5]  # Max 5 bullets
            })

        # Organiser les compétences
        skills = self._categorize_skills(user_data.get("skills", []))

        return {
            "name": user_data.get("name", "").upper(),
            "job_title": job_title,
            "contact": {
                "email": user_data.get("email", ""),
                "phone": user_data.get("phone", ""),
                "location": user_data.get("location", ""),
                "linkedin": user_data.get("linkedin", "")
            },
            "summary": summary,
            "experience": experience,
            "skills": skills,
            "education": user_data.get("education", []),
            "certifications": user_data.get("certifications", []),
            "languages": user_data.get("languages", [])
        }

    def _generate_summary(self, job_title: str, years: int, experience: List[Dict]) -> str:
        """Génère un résumé professionnel optimisé."""
        # Extraire les métriques des expériences
        metrics = []
        for exp in experience:
            for bullet in exp.get("bullets", []):
                if any(c.isdigit() for c in bullet):
                    metrics.append(bullet)

        top_metrics = metrics[:2] if metrics else []

        summary = f"{job_title} avec {years} an{'s' if years > 1 else ''} d'expérience. "

        if top_metrics:
            summary += f"{top_metrics[0]}. "
            if len(top_metrics) > 1:
                summary += f"{top_metrics[1]}. "

        summary += f"À la recherche d'un poste de {job_title} pour contribuer à des projets ambitieux et continuer à développer mon expertise."

        return summary

    def _categorize_skills(self, skills: List[str]) -> Dict:
        """Catégorise les compétences."""
        tech_keywords = ["python", "javascript", "react", "node", "sql", "docker", "aws", "git", "java", "php", "typescript", "angular", "vue", "html", "css"]
        soft_keywords = ["communication", "leadership", "gestion", "analyse", "résolution", "équipe", "autonomie", "créativité"]
        tool_keywords = ["excel", "sap", "sage", "word", "powerpoint", "jira", "trello", "slack"]

        hard_skills = [s for s in skills if any(t in s.lower() for t in tech_keywords)]
        soft_skills = [s for s in skills if any(t in s.lower() for t in soft_keywords)]
        tools = [s for s in skills if any(t in s.lower() for t in tool_keywords)]
        other = [s for s in skills if s not in hard_skills and s not in soft_skills and s not in tools]

        return {
            "hard_skills": hard_skills,
            "soft_skills": soft_skills,
            "tools": tools,
            "other": other
        }

    def _render_text(self, cv_data: Dict) -> str:
        """Rendu en texte brut."""
        lines = []

        # Header
        lines.append(cv_data.get("name", ""))
        contact = cv_data.get("contact", {})
        contact_items = [v for v in [
            contact.get("email"),
            contact.get("phone"),
            contact.get("location"),
            contact.get("linkedin")
        ] if v]
        if contact_items:
            lines.append(" | ".join(contact_items))
        lines.append("")

        # Summary
        if cv_data.get("summary"):
            lines.append("RÉSUMÉ PROFESSIONNEL")
            lines.append("-" * 40)
            lines.append(cv_data["summary"])
            lines.append("")

        # Experience
        if cv_data.get("experience"):
            lines.append("EXPÉRIENCE PROFESSIONNELLE")
            lines.append("-" * 40)
            for exp in cv_data["experience"]:
                lines.append(f"{exp.get('title', '')} | {exp.get('company', '')}")
                meta = " | ".join(filter(None, [exp.get("dates"), exp.get("location")]))
                if meta:
                    lines.append(meta)
                for bullet in exp.get("bullets", []):
                    lines.append(f"• {bullet}")
                lines.append("")

        # Skills
        skills = cv_data.get("skills", {})
        if skills:
            lines.append("COMPÉTENCES")
            lines.append("-" * 40)
            if skills.get("hard_skills"):
                lines.append(f"Techniques: {', '.join(skills['hard_skills'])}")
            if skills.get("soft_skills"):
                lines.append(f"Comportementales: {', '.join(skills['soft_skills'])}")
            if skills.get("tools"):
                lines.append(f"Outils: {', '.join(skills['tools'])}")
            lines.append("")

        # Education
        if cv_data.get("education"):
            lines.append("FORMATION")
            lines.append("-" * 40)
            for edu in cv_data["education"]:
                mention = f" ({edu['mention']})" if edu.get("mention") else ""
                lines.append(f"{edu.get('degree', '')}{mention} — {edu.get('school', '')} | {edu.get('year', '')}")

        return "\n".join(lines)

    def _render_html(self, cv_data: Dict) -> str:
        """Rendu en HTML avec le template professionnel."""
        c = self.model["visual_design"]["colors"]

        contact = cv_data.get("contact", {})
        contact_items = [v for v in [
            contact.get("email"),
            contact.get("phone"),
            contact.get("location"),
            contact.get("linkedin")
        ] if v]

        parts = []
        parts.append('<!DOCTYPE html>')
        parts.append('<html lang="fr">')
        parts.append('<head>')
        parts.append('    <meta charset="UTF-8">')
        parts.append(f'    <title>CV - {cv_data.get("name", "")}</title>')
        parts.append('    <style>')
        parts.append(f'        body {{ font-family: Helvetica, Arial, sans-serif; color: {c["text"]}; background: {c["background"]}; margin: 15mm 20mm; line-height: 1.15; font-size: 10.5pt; }}')
        parts.append(f'        .name {{ font-size: 18pt; color: {c["primary"]}; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; text-align: center; margin-bottom: 4pt; }}')
        parts.append(f'        .title {{ font-size: 12pt; color: {c["secondary"]}; text-align: center; margin-bottom: 6pt; }}')
        parts.append(f'        .contact {{ text-align: center; font-size: 9pt; color: #4a5568; margin-bottom: 12pt; padding-bottom: 8pt; border-bottom: 1.5px solid {c["primary"]}; }}')
        parts.append(f'        .section {{ margin-bottom: 10pt; }}')
        parts.append(f'        .section-title {{ font-size: 12pt; color: {c["primary"]}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 5pt; padding-bottom: 2pt; border-bottom: 1.5px solid {c["primary"]}; }}')
        parts.append(f'        .summary {{ font-style: italic; color: {c["secondary"]}; margin-bottom: 6pt; }}')
        parts.append(f'        .job {{ margin-bottom: 7pt; }}')
        parts.append(f'        .job-title {{ font-weight: 700; }}')
        parts.append(f'        .job-company {{ color: {c["secondary"]}; font-style: italic; }}')
        parts.append(f'        .job-meta {{ font-size: 9pt; color: #4a5568; margin-bottom: 2pt; }}')
        parts.append(f'        .bullets {{ margin-left: 12pt; list-style: none; }}')
        parts.append(f'        .bullets li {{ position: relative; margin-bottom: 1pt; padding-left: 10pt; }}')
        parts.append(f'        .bullets li::before {{ content: "▸"; position: absolute; left: 0; color: {c["accent"]}; font-weight: bold; font-size: 8pt; }}')
        parts.append(f'        .skills-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4pt 12pt; }}')
        parts.append(f'        .skill-label {{ font-weight: 700; color: {c["primary"]}; font-size: 9pt; text-transform: uppercase; }}')
        parts.append(f'        .edu-item {{ margin-bottom: 3pt; }}')
        parts.append(f'        @media print {{ body {{ margin: 0; }} }}')
        parts.append('    </style>')
        parts.append('</head>')
        parts.append('<body>')

        # Header
        parts.append(f'    <div class="name">{cv_data.get("name", "")}</div>')
        parts.append(f'    <div class="title">{cv_data.get("job_title", "")}</div>')
        parts.append(f'    <div class="contact">{" | ".join(contact_items)}</div>')

        # Summary
        if cv_data.get("summary"):
            parts.append('    <div class="section">')
            parts.append('        <div class="section-title">Résumé Professionnel</div>')
            parts.append(f'        <div class="summary">{cv_data["summary"]}</div>')
            parts.append('    </div>')

        # Experience
        if cv_data.get("experience"):
            parts.append('    <div class="section">')
            parts.append('        <div class="section-title">Expérience Professionnelle</div>')
            for exp in cv_data["experience"]:
                meta = " | ".join(filter(None, [exp.get("dates"), exp.get("location")]))
                bullets_html = "".join([f'<li>{b}</li>' for b in exp.get("bullets", [])])
                parts.append('        <div class="job">')
                parts.append(f'            <div><span class="job-title">{exp.get("title", "")}</span> | <span class="job-company">{exp.get("company", "")}</span></div>')
                parts.append(f'            <div class="job-meta">{meta}</div>')
                parts.append(f'            <ul class="bullets">{bullets_html}</ul>')
                parts.append('        </div>')
            parts.append('    </div>')

        # Skills
        skills = cv_data.get("skills", {})
        if skills and any(skills.get(k) for k in ["hard_skills", "soft_skills", "tools"]):
            parts.append('    <div class="section">')
            parts.append('        <div class="section-title">Compétences</div>')
            parts.append('        <div class="skills-grid">')
            for cat, items in skills.items():
                if items and cat != "other":
                    cat_name = {"hard_skills": "Techniques", "soft_skills": "Comportementales", "tools": "Outils"}.get(cat, cat)
                    parts.append('            <div>')
                    parts.append(f'                <div class="skill-label">{cat_name}</div>')
                    parts.append(f'                <div>{", ".join(items)}</div>')
                    parts.append('            </div>')
            parts.append('        </div>')
            parts.append('    </div>')

        # Education
        if cv_data.get("education"):
            parts.append('    <div class="section">')
            parts.append('        <div class="section-title">Formation</div>')
            for edu in cv_data["education"]:
                mention = f" ({edu['mention']})" if edu.get("mention") else ""
                parts.append(f'        <div class="edu-item"><strong>{edu.get("degree", "")}</strong>{mention} — <em>{edu.get("school", "")}</em> | {edu.get("year", "")}</div>')
            parts.append('    </div>')

        # Certifications
        if cv_data.get("certifications"):
            parts.append('    <div class="section">')
            parts.append('        <div class="section-title">Certifications</div>')
            for cert in cv_data["certifications"]:
                parts.append(f'        <div class="edu-item"><strong>{cert.get("name", "")}</strong> — <em>{cert.get("organization", "")}</em> | {cert.get("year", "")}</div>')
            parts.append('    </div>')

        # Languages
        if cv_data.get("languages"):
            parts.append('    <div class="section">')
            parts.append('        <div class="section-title">Langues</div>')
            lang_items = []
            for lang in cv_data["languages"]:
                lang_items.append(f'<strong>{lang.get("name", "")}:</strong> <em>{lang.get("level", "")}</em>')
            parts.append(f'        <div>{" | ".join(lang_items)}</div>')
            parts.append('    </div>')

        parts.append('</body>')
        parts.append('</html>')

        return "\n".join(parts)

    def _render_markdown(self, cv_data: Dict) -> str:
        """Rendu en Markdown."""
        lines = [
            f"# {cv_data.get('name', '')}",
            f"**{cv_data.get('job_title', '')}**",
            ""
        ]

        contact = cv_data.get("contact", {})
        contact_items = [v for v in [
            contact.get("email"),
            contact.get("phone"),
            contact.get("location")
        ] if v]
        if contact_items:
            lines.append(" | ".join(contact_items))
            lines.append("")

        if cv_data.get("summary"):
            lines.extend(["## Résumé Professionnel", cv_data["summary"], ""])

        if cv_data.get("experience"):
            lines.append("## Expérience Professionnelle")
            for exp in cv_data["experience"]:
                lines.append(f"### {exp.get('title', '')} | {exp.get('company', '')}")
                meta = " | ".join(filter(None, [exp.get("dates"), exp.get("location")]))
                if meta:
                    lines.append(f"*{meta}*")
                for bullet in exp.get("bullets", []):
                    lines.append(f"- {bullet}")
                lines.append("")

        skills = cv_data.get("skills", {})
        if skills:
            lines.append("## Compétences")
            for cat, items in skills.items():
                if items and cat != "other":
                    cat_name = {"hard_skills": "Techniques", "soft_skills": "Comportementales", "tools": "Outils"}.get(cat, cat)
                    lines.append(f"**{cat_name}:** {', '.join(items)}")
            lines.append("")

        if cv_data.get("education"):
            lines.append("## Formation")
            for edu in cv_data["education"]:
                mention = f" ({edu['mention']})" if edu.get("mention") else ""
                lines.append(f"- **{edu.get('degree', '')}**{mention} — {edu.get('school', '')} | {edu.get('year', '')}")

        return "\n".join(lines)

    def _estimate_years(self, experience: List[Dict]) -> int:
        """Estime les années d'expérience."""
        if not experience:
            return 0

        total = 0
        for exp in experience:
            dates = exp.get("dates", "")
            if "Présent" in dates or "present" in dates.lower():
                total += 2
            elif "-" in dates:
                parts = dates.split("-")
                if len(parts) == 2:
                    try:
                        start = int(parts[0].strip().split("/")[-1])
                        end_str = parts[1].strip().split("/")[-1]
                        end = 2025 if "Présent" in end_str else int(end_str)
                        total += max(0, end - start)
                    except:
                        total += 1
            else:
                total += 1

        return max(1, total)


# Instance singleton
_generator_service: Optional[CVModelGeneratorService] = None

def get_generator_service() -> CVModelGeneratorService:
    global _generator_service
    if _generator_service is None:
        _generator_service = CVModelGeneratorService()
    return _generator_service