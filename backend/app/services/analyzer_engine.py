"""
Moteur d'analyse IA de CV : extraction, scoring, recommandations.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any
from rapidfuzz import fuzz, process

from app.core.logging import logger


class CVAnalyzerEngine:
    """
    Moteur d'analyse de CV basé sur des règles heuristiques et du NLP.
    Version MVP - peut être enrichie avec des modèles ML entraînés.
    """
    
    def __init__(self):
        self.skills_corpus = self._load_skills_corpus()
        self.section_patterns = self._get_section_patterns()
    
    def _load_skills_corpus(self) -> List[str]:
        """Charge le corpus de compétences techniques."""
        corpus_path = Path(__file__).parent.parent / "ml" / "data" / "skills_corpus.json"
        
        if corpus_path.exists():
            with open(corpus_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("skills", [])
        
        # Corpus par défaut si fichier non trouvé
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
            "project management", "time management", "critical thinking"
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
    
    def analyze(self, cv_text: str) -> Dict[str, Any]:
        """
        Analyse complète d'un CV et retourne les résultats structurés.
        
        Args:
            cv_text: Texte brut extrait du PDF
        
        Returns:
            Dict avec scores, skills, forces, faiblesses, recommandations
        """
        if not cv_text or len(cv_text.strip()) < 50:
            return self._empty_analysis()
        
        # Nettoyer le texte
        clean_text = self._clean_text(cv_text)
        words = clean_text.split()
        word_count = len(words)
        
        # Détecter les sections
        sections_detected = self._detect_sections(cv_text.lower())
        
        # Extraire les compétences
        detected_skills = self._extract_skills(clean_text)
        
        # Calculer les scores
        structure_score = self._calculate_structure_score(sections_detected, word_count)
        content_score = self._calculate_content_score(word_count, detected_skills)
        keywords_score = self._calculate_keywords_score(detected_skills)
        
        overall_score = int((structure_score * 0.35 + content_score * 0.40 + keywords_score * 0.25))
        
        # Générer forces/faiblesses/recommandations
        strengths = self._generate_strengths(sections_detected, detected_skills, word_count)
        weaknesses = self._generate_weaknesses(sections_detected, detected_skills, word_count)
        recommendations = self._generate_recommendations(weaknesses, sections_detected)
        
        # Détecter si les infos de contact sont présentes
        contact_info_found = self._has_contact_info(cv_text)
        
        return {
            "overall_score": overall_score,
            "structure_score": structure_score,
            "content_score": content_score,
            "keywords_score": keywords_score,
            "detected_skills": detected_skills,
            "missing_skills": self._suggest_missing_skills(detected_skills),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "sections_detected": sections_detected,
            "word_count": word_count,
            "contact_info_found": contact_info_found
        }
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte pour l'analyse."""
        # Supprimer les caractères spéciaux excessifs
        text = re.sub(r'[^\w\s\-./@]', ' ', text)
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip().lower()
    
    def _detect_sections(self, text: str) -> Dict[str, bool]:
        """Détecte quelles sections sont présentes dans le CV."""
        sections = {}
        for section_name, patterns in self.section_patterns.items():
            found = any(re.search(pattern, text) for pattern in patterns)
            sections[section_name] = found
        return sections
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extrait les compétences du texte via fuzzy matching."""
        detected = []
        text_lower = text.lower()
        
        for skill in self.skills_corpus:
            # Fuzzy matching pour gérer les variations
            matches = process.extract(skill, text_lower.split(), scorer=fuzz.partial_ratio, limit=1)
            if matches and matches[0][1] > 85:  # Score de similarité > 85%
                detected.append(skill)
        
        # Supprimer les doublons en gardant l'ordre
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
    
    def _calculate_content_score(self, word_count: int, skills: List[str]) -> int:
        """Calcule le score de contenu (0-100)."""
        score = 0
        
        # Score basé sur la longueur
        if word_count >= 300: score += 30
        elif word_count >= 150: score += 20
        else: score += 10
        
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
        score = min(len(skills) * 8, 80)
        
        # Bonus pour compétences recherchées
        high_value_skills = ["python", "react", "docker", "aws", "sql", "git", "agile"]
        high_value_count = sum(1 for s in skills if s.lower() in high_value_skills)
        score += min(high_value_count * 5, 20)
        
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
    
    def _suggest_missing_skills(self, detected: List[str]) -> List[str]:
        """Suggère des compétences manquantes basées sur les tendances du marché."""
        trending_skills = [
            "docker", "kubernetes", "aws", "react", "typescript",
            "python", "sql", "git", "ci/cd", "agile", "rest api"
        ]
        
        detected_lower = [s.lower() for s in detected]
        missing = [s for s in trending_skills if s.lower() not in detected_lower]
        
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