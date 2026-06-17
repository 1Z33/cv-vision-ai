"""
Moteur d'analyse IA de CV : extraction, scoring, recommandations.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


from app.core.logging import logger


class CVAnalyzerEngine:
    """Moteur d'analyse de CV : heuristique + (optionnel) Gemini."""

    def __init__(self):
        # Gemini (optionnel)
        try:
            from app.services.gemini_cv_analyzer import gemini_analyzer
            self.gemini = gemini_analyzer
        except Exception:
            self.gemini = None

        # Fallback heuristique
        self.skills_corpus = self._load_skills_corpus()
        self.section_patterns = self._get_section_patterns()

    
    def _load_skills_corpus(self) -> List[str]:
        """Charge le corpus de compétences.

        Supporte plusieurs formats pour éviter de casser l'app lors d'un changement de génération de corpus:
        - Format historique attendu: {"skills": [...]} (clé "skills")
        - Format flat: [...]
        - Format structuré: {"_metadata":..., "domain": {"category": ["skill", ...], ...}, ...}
        """

        data_dir = Path(__file__).parent.parent / "ml" / "data"

        # 1) Priorité: skills_corpus.json (actuel)
        candidates = [
            data_dir / "skills_corpus.json",
            data_dir / "skills_corpus_flat.json",
            data_dir / "skills_corpus_structured.json",
        ]

        for corpus_path in candidates:
            if not corpus_path.exists():
                continue

            try:
                with open(corpus_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                logger.warning(f"Impossible de charger le corpus depuis {corpus_path}: {e}")
                continue

            # Format {"skills": [...]} (ancien)
            if isinstance(data, dict) and "skills" in data:
                skills = data.get("skills", [])
                return sorted({s.lower().strip() for s in skills if isinstance(s, str) and s.strip()})

            # Format flat: [...]
            if isinstance(data, list):
                return sorted({s.lower().strip() for s in data if isinstance(s, str) and s.strip()})

            # Format structuré: flatten dynamique
            if isinstance(data, dict):
                skills_set = set()

                def _extract(obj: Any):
                    if isinstance(obj, list):
                        for item in obj:
                            if isinstance(item, str) and item.strip():
                                skills_set.add(item.lower().strip())
                            else:
                                _extract(item)
                    elif isinstance(obj, dict):
                        for k, v in obj.items():
                            if isinstance(k, str) and k.startswith("_"):
                                continue
                            _extract(v)

                _extract(data)
                if skills_set:
                    return sorted(skills_set)

        # Corpus par défaut si fichier non trouvé / non valide
        return [
            "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
            "react", "vue", "angular", "node.js", "django", "fastapi", "flask",
            "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "docker", "kubernetes", "aws", "azure", "gcp", "terraform",
            "git", "github", "gitlab", "ci/cd", "jenkins", "github actions",
            "machine learning", "deep learning", "nlp", "computer vision",
            "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
            "agile", "scrum", "kanban", "jira", "confluence",
            "html", "css", "sass", "tailwind", "bootstrap",
            "rest api", "graphql", "websocket", "microservices",
            "linux", "bash", "powershell", "nginx", "apache",
            "excel", "powerpoint", "word", "google sheets",
            "photoshop", "figma", "sketch", "adobe xd",
            "communication", "leadership", "teamwork", "problem solving",
            "project management", "time management", "critical thinking",
        ]
    
    def _get_section_patterns(self) -> Dict[str, List[str]]:
        """Patterns regex pour détecter les sections d'un CV."""
        return {
            "contact": [r"contact", r"coordonnées", r"informations personnelles"],
            "experience": [r"expérience", r"expériences professionnelles", r"parcours"],
            "education": [r"formation", r"éducation", r"diplôme", r"diplômes", r"études"],
            "skills": [r"compétences", r"skills", r"technologies", r"stack"],
            "projects": [r"projet", r"projets", r"portfolio"],
            "languages": [r"langue", r"langues", r"languages"],
            "certifications": [r"certification", r"certifications", r"diplôme"]
        }
    
    async def analyze(self, cv_text: str, job_description: Optional[str] = None) -> Dict[str, Any]:

        """Analyse complète d'un CV.

        - Gemini d'abord (si activé) puis fallback heuristique si échec/indisponibilité.

        - Sinon : analyse heuristique.
        """

        if not cv_text or len(cv_text.strip()) < 50:
            return self._empty_analysis()

        # 1) Gemini (optionnel)
        if self.gemini is not None and getattr(self.gemini, "enabled", False):
            try:
                gemini_result = self.gemini.analyze(cv_text)
                if gemini_result:
                    # Matching job si demandé
                    if job_description:
                        try:
                            job_match = self.gemini.compare_with_job(cv_text, job_description)
                            if job_match:
                                gemini_result["job_match"] = job_match
                        except Exception as e:
                            logger.warning(f"Échec du matching job Gemini: {e}")

                    mapped = self._map_gemini_result_to_analysis(gemini_result, fallback_text=cv_text)
                    return mapped
            except Exception as e:
                # Toujours fallback propre
                logger.error(f"Échec de l'analyse Gemini, passage au fallback heuristique: {e}")


        # 2) Fallback heuristique
        result = self._heuristic_analyze(cv_text, job_description)
        return result


    def _heuristic_analyze(self, cv_text: str, job_description: Optional[str] = None) -> Dict[str, Any]:
        """Ton code existant (regex + corpus + scoring heuristique)."""
        # Nettoyer le texte
        clean_text = self._clean_text(cv_text)
        words = clean_text.split()
        word_count = len(words)

        # Détecter les sections
        sections_detected = self._detect_sections(cv_text.lower())

        # Identifier le métier (Job Title)
        job_title = self._extract_job_title(cv_text)

        # Extraire les compétences
        detected_skills = self._extract_skills(clean_text)

        # Calculer les scores
        structure_score = self._calculate_structure_score(sections_detected, word_count)
        content_score = self._calculate_content_score(word_count, detected_skills, job_title)
        keywords_score = self._calculate_keywords_score(detected_skills)

        overall_score = int((structure_score * 0.35 + content_score * 0.40 + keywords_score * 0.25))

        # Générer forces/faiblesses/recommandations
        strengths = self._generate_strengths(sections_detected, detected_skills, word_count)
        weaknesses = self._generate_weaknesses(sections_detected, detected_skills, word_count)
        recommendations = self._generate_recommendations(weaknesses, sections_detected)

        # Détecter si les infos de contact sont présentes
        contact_info_found = self._has_contact_info(cv_text)

        # --- Compliance Model (ATS/universel JSON) ---
        # Le score visuel peut être non vérifiable depuis texte-only.
        try:
            from app.services.cv_model_compliance import get_cv_model_compliance_service

            compliance = get_cv_model_compliance_service().evaluate(
                cv_text=cv_text,
                job_title=job_title,
                job_description=job_description or "",
            )

            model_compliance_score = int(compliance.get("total_score", 0))
            breakdown = compliance.get("breakdown", {}) or {}

            # Recalage (Option A): rendre cohérents les sous-scores affichés.
            # Mapping conservateur:
            # - structure_sections => structure_score
            # - metrics_presence + length_optimization => content_score (proxy)
            # - ats_compatibility + keywords_relevance => keywords_score (proxy)
            structure_c = int((breakdown.get("structure_sections") or {}).get("score", 0) or 0)
            metrics_c = int((breakdown.get("metrics_presence") or {}).get("score", 0) or 0)
            length_c = int((breakdown.get("length_optimization") or {}).get("score", 0) or 0)
            ats_c = int((breakdown.get("ats_compatibility") or {}).get("score", 0) or 0)
            keywords_c = int((breakdown.get("keywords_relevance") or {}).get("score", 0) or 0)

            # Exclure visual_consistency de l'agrégat si non vérifiable (C6)
            visual_breakdown = breakdown.get("visual_consistency") or {}
            visual_status = visual_breakdown.get("status")
            visual_unverifiable = visual_status == "unverifiable_text_only"

            # Fusion pondérée cohérente sur les sous-scores
            structure_score = int(round(structure_score * 0.65 + structure_c * 0.35))
            content_proxy_c = int(round((metrics_c + length_c) / 2))
            content_score = int(round(content_score * 0.65 + content_proxy_c * 0.35))
            keywords_proxy_c = int(round((ats_c + keywords_c) / 2))
            keywords_score = int(round(keywords_score * 0.65 + keywords_proxy_c * 0.35))

            # overall_score hybridé (garde le total compliance, mais cohérence UI via sous-scores recalés)
            overall_score = int(round(overall_score * 0.65 + model_compliance_score * 0.35))

        except Exception as e:
            logger.warning(f"Compliance CV model non calculée: {e}")
            compliance = None
            model_compliance_score = None

        result = {
            "overall_score": overall_score,
            "structure_score": structure_score,
            "content_score": content_score,
            "keywords_score": keywords_score,
            "detected_skills": detected_skills,
            "missing_skills": self._suggest_missing_skills(detected_skills, job_title),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "sections_detected": sections_detected,
            "word_count": word_count,
            "contact_info_found": contact_info_found
        }

        if compliance is not None:
            result["model_compliance_score"] = model_compliance_score
            result["model_compliance_breakdown"] = compliance.get("breakdown", {})

        return result

    def _map_gemini_result_to_analysis(self, gemini_result: Dict[str, Any], fallback_text: str) -> Dict[str, Any]:
        """Mappe le JSON Gemini vers le format attendu par Analysis/AnalysisResponse."""
        detected_skills = gemini_result.get("detected_skills") or gemini_result.get("skills", []) or []
        missing_skills = gemini_result.get("missing_skills") or []

        # Si Gemini ne fournit pas detected_skills sous la forme attendue
        if isinstance(detected_skills, dict):
            # cas improbable : on aplatit
            tmp = []
            for v in detected_skills.values():
                if isinstance(v, list):
                    tmp.extend([x for x in v if isinstance(x, str)])
            detected_skills = tmp

        structure_score = int(gemini_result.get("structure_score", 0) or 0)
        content_score = int(gemini_result.get("content_score", 0) or 0)
        keywords_score = int(gemini_result.get("keywords_score", 0) or 0)
        overall_score = int(gemini_result.get("overall_score", 0) or 0)

        # sections_detected / word_count : fallback basique pour remplir le schéma
        clean_text = self._clean_text(fallback_text)
        word_count = len(clean_text.split())
        sections_detected = self._detect_sections(fallback_text.lower())

        job_match = gemini_result.get("job_match")

        return {
            "overall_score": overall_score,
            "structure_score": structure_score,
            "content_score": content_score,
            "keywords_score": keywords_score,
            "detected_skills": detected_skills if isinstance(detected_skills, list) else [],
            "missing_skills": missing_skills if isinstance(missing_skills, list) else [],
            "strengths": gemini_result.get("strengths", []) or [],
            "weaknesses": gemini_result.get("weaknesses", []) or [],
            "recommendations": gemini_result.get("recommendations", []) or [],
            "sections_detected": sections_detected,
            "word_count": word_count,
            "contact_info_found": self._has_contact_info(fallback_text),
            # Champs non présents dans le mapping initial (C3/C7)
            "job_match": job_match,
            "estimated_seniority": gemini_result.get("estimated_seniority"),
            "experience_years": gemini_result.get("experience_years"),
        }

    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte pour l'analyse."""
        # Supprimer les caractères spéciaux excessifs
        text = re.sub(r'[^\w\s\-./@]', ' ', text)
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip().lower()
    
    def _extract_job_title(self, text: str) -> str:
        """Tente d'extraire l'intitulé du poste en haut du CV."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        # On cherche dans les 10 premières lignes, en ignorant ce qui ressemble à des contacts
        for line in lines[:10]:
            if len(line) > 3 and not re.search(r'@|0\d|\.com|\.fr|http', line.lower()):
                # Si la ligne ne contient pas trop de chiffres, c'est probablement le titre
                if sum(c.isdigit() for c in line) < 3:
                    return line
        return "Profil Professionnel"

    def _detect_sections(self, text: str) -> Dict[str, bool]:
        """Détecte quelles sections sont présentes dans le CV."""
        sections = {}
        for section_name, patterns in self.section_patterns.items():
            found = any(re.search(pattern, text) for pattern in patterns)
            sections[section_name] = found
        return sections
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extrait les compétences du texte via matching exact par mot complet."""
        detected = []
        text_lower = text.lower()
        
        # On trie par longueur décroissante pour éviter que "C" ne matche dans "C++"
        sorted_corpus = sorted(self.skills_corpus, key=len, reverse=True)
        
        for skill in sorted_corpus:
            # Regex avec lookbehind/lookahead pour matcher le mot exact (gère C++, .NET, etc.)
            # Cela évite de matcher "git" dans "digital"
            pattern = rf"(?<![\w]){re.escape(skill.lower())}(?![\w])"
            if re.search(pattern, text_lower):
                detected.append(skill)
        
        return list(dict.fromkeys(detected))
    
    def _calculate_structure_score(self, sections: Dict[str, bool], word_count: int) -> int:
        """Calcule le score de structure (0-100)."""
        score = 0
        
        # Points pour chaque section importante
        if sections.get("contact"): score += 15
        if sections.get("experience"): score += 25
        if sections.get("education"): score += 20
        if sections.get("skills"): score += 20
        if sections.get("projects"): score += 10
        if sections.get("languages"): score += 5
        if sections.get("certifications"): score += 5
        
        # Bonus pour la longueur appropriée
        if 200 <= word_count <= 800:
            score += 10
        elif word_count > 800:
            score += 5
        
        return min(score, 100)
    
    def _calculate_content_score(self, word_count: int, skills: List[str], job_title: str) -> int:
        """Calcule le score de contenu (0-100)."""
        score = 0
        
        # Score basé sur la longueur
        if word_count >= 300: score += 30
        elif word_count >= 150: score += 20
        else: score += 10

        # Bonus si un titre de métier clair est identifié
        if job_title and job_title != "Profil Professionnel":
            score += 10
        
        # Score basé sur le nombre de compétences
        if len(skills) >= 10: score += 40
        elif len(skills) >= 5: score += 30
        elif len(skills) >= 3: score += 20
        else: score += 10
        
        # Bonus diversité
        if len(skills) >= 15: score += 20
        elif len(skills) >= 8: score += 15
        else: score += 10
        
        # Pénalité si trop court
        if word_count < 100:
            score -= 20
        
        return max(0, min(score, 100))
    
    def _calculate_keywords_score(self, skills: List[str]) -> int:
        """Calcule le score de mots-clés (0-100)."""
        if not skills:
            return 20
        
        # Score basé sur la quantité et la diversité
        score = min(len(skills) * 5, 75)
        
        # Bonus pour la présence de compétences variées (soft + hard)
        if len(skills) > 5:
            score += 25
        else:
            score += len(skills) * 5
        
        return min(score, 100)
    
    def _generate_strengths(self, sections: Dict[str, bool], skills: List[str], word_count: int) -> List[str]:
        """Génère les points forts du CV."""
        strengths = []
        
        if sections.get("experience"):
            strengths.append("Votre section expérience est bien présente et structurée")
        
        if len(skills) >= 8:
            strengths.append(f"Excellent panel de compétences techniques ({len(skills)} détectées)")
        
        if sections.get("projects"):
            strengths.append("La présence de projets personnels renforce votre profil")
        
        if word_count >= 400:
            strengths.append("CV détaillé avec un contenu riche et informatif")
        
        if sections.get("certifications"):
            strengths.append("Vos certifications ajoutent de la crédibilité à votre profil")
        
        if not strengths:
            strengths.append("Structure de base du CV respectée")
        
        return strengths[:4]  # Max 4 forces
    
    def _generate_weaknesses(self, sections: Dict[str, bool], skills: List[str], word_count: int) -> List[str]:
        """Génère les points faibles du CV."""
        weaknesses = []
        
        if not sections.get("contact"):
            weaknesses.append("Informations de contact manquantes ou difficiles à trouver")
        
        if not sections.get("experience"):
            weaknesses.append("Section expérience professionnelle absente ou peu visible")
        
        if not sections.get("skills"):
            weaknesses.append("Section compétences non identifiée clairement")
        
        if len(skills) < 5:
            weaknesses.append("Nombre de compétences techniques limité")
        
        if word_count < 200:
            weaknesses.append("CV trop concis - manque de détails sur vos réalisations")
        
        if word_count > 1000:
            weaknesses.append("CV potentiellement trop long - privilégiez la concision")
        
        if not sections.get("projects") and not sections.get("certifications"):
            weaknesses.append("Absence de projets ou certifications pour démontrer vos compétences")
        
        return weaknesses[:4]  # Max 4 faiblesses
    
    def _generate_recommendations(self, weaknesses: List[str], sections: Dict[str, bool]) -> List[str]:
        """Génère des recommandations personnalisées."""
        recommendations = []
        
        if not sections.get("contact"):
            recommendations.append("Ajoutez clairement vos coordonnées en haut de page (email, téléphone, LinkedIn)")
        
        if not sections.get("experience"):
            recommendations.append("Structurez votre expérience avec des verbes d'action et des résultats quantifiés")
        
        if not sections.get("skills"):
            recommendations.append("Créez une section 'Compétences' dédiée avec vos technologies maîtrisées")
        
        if any("trop concis" in w for w in weaknesses):
            recommendations.append("Détaillez vos réalisations avec la méthode STAR (Situation, Tâche, Action, Résultat)")
        
        if any("trop long" in w for w in weaknesses):
            recommendations.append("Ciblez 1-2 pages maximum et supprimez les informations non pertinentes")
        
        recommendations.append("Utilisez des mots-clés issus des offres d'emploi pour passer les ATS")
        recommendations.append("Quantifiez vos résultats (%, €, temps gagné) pour plus d'impact")
        
        return recommendations[:5]
    
    def _suggest_missing_skills(self, detected: List[str], job_title: str) -> List[str]:
        """Suggère des compétences adaptées au profil détecté."""
        # Détecter si le profil est orienté Tech
        tech_keywords = ["python", "java", "javascript", "code", "dev", "système", "réseau", "cloud", "data"]
        is_tech = any(k in job_title.lower() for k in tech_keywords) or \
                  any(s.lower() in ["python", "javascript", "sql", "git"] for s in detected)

        if is_tech:
            trending = [
                "Docker", "AWS", "CI/CD", "TypeScript", "Agile", "Unit Testing"
            ]
        else:
            # Suggestions pour profils généraux/non-tech
            trending = [
                "Gestion de projet", "Communication", "Résolution de problèmes", 
                "Adaptabilité", "Pack Office", "Relation client", "Autonomie"
            ]

        detected_lower = [s.lower() for s in detected]
        missing = [s for s in trending if s.lower() not in detected_lower]
        
        return missing[:5]
    
    def _has_contact_info(self, text: str) -> bool:
        """Vérifie si des informations de contact sont présentes."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}'
        
        has_email = bool(re.search(email_pattern, text))
        has_phone = bool(re.search(phone_pattern, text))
        
        return has_email or has_phone
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Retourne une analyse vide pour les CV illisibles."""
        return {
            "overall_score": 0,
            "structure_score": 0,
            "content_score": 0,
            "keywords_score": 0,
            "detected_skills": [],
            "missing_skills": [],
            "strengths": ["Impossible d'analyser le contenu"],
            "weaknesses": ["Le texte du CV est vide ou illisible"],
            "recommendations": ["Vérifiez que votre PDF n'est pas scanné ou protégé"],
            "sections_detected": {},
            "word_count": 0,
            "contact_info_found": False
        }