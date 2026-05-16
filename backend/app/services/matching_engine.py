"""
Moteur de matching CV / Offre d'emploi.
"""

from uuid import UUID
from typing import Dict, List, Any
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.core.logging import logger


class MatchingEngine:
    """
    Moteur de compatibilité entre CV et offres d'emploi.
    Combine matching sémantique (embeddings) et matching de compétences (fuzzy).
    """
    
    def __init__(self):
        # Charger le modèle d'embeddings (téléchargement automatique la première fois)
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.use_embeddings = True
            logger.info("Modèle d'embeddings chargé avec succès")
        except Exception as e:
            logger.warning(f"Impossible de charger le modèle d'embeddings: {e}")
            self.use_embeddings = False
    
    def calculate_match(self, cv_text: str, job_description: str, 
                       required_skills: List[str], cv_skills: List[str]) -> Dict[str, Any]:
        """
        Calcule le score de compatibilité entre un CV et une offre.
        
        Args:
            cv_text: Texte complet du CV
            job_description: Description du poste
            required_skills: Compétences requises par l'offre
            cv_skills: Compétences détectées dans le CV
        
        Returns:
            Dict avec score, skills matchés/manquants, analyse
        """
        # 1. Score sémantique (embeddings)
        semantic_score = self._semantic_similarity(cv_text, job_description)
        
        # 2. Score de compétences
        skill_result = self._skill_matching(required_skills, cv_skills)
        
        # 3. Score final pondéré
        final_score = int(0.4 * semantic_score + 0.6 * skill_result["score"])
        
        # 4. Analyse des écarts
        gap_analysis = self._analyze_skill_gaps(skill_result["matched"], skill_result["missing"])
        
        return {
            "compatibility_score": final_score,
            "matching_skills": skill_result["matched"],
            "missing_skills": skill_result["missing"],
            "skill_gap_analysis": gap_analysis,
            "semantic_score": int(semantic_score),
            "skill_score": int(skill_result["score"])
        }
    
    def _semantic_similarity(self, cv_text: str, job_text: str) -> float:
        """Calcule la similarité sémantique via embeddings."""
        if not self.use_embeddings or not cv_text or not job_text:
            # Fallback: similarité basique sur mots communs
            return self._fallback_similarity(cv_text, job_text)
        
        try:
            embeddings = self.model.encode([cv_text, job_text])
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(similarity) * 100  # Convertir en pourcentage
        except Exception as e:
            logger.error(f"Erreur similarité sémantique: {e}")
            return self._fallback_similarity(cv_text, job_text)
    
    def _fallback_similarity(self, text1: str, text2: str) -> float:
        """Similarité basique si les embeddings ne sont pas disponibles."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return (len(intersection) / len(union)) * 100 if union else 0.0
    
    def _skill_matching(self, required: List[str], cv_skills: List[str]) -> Dict[str, Any]:
        """Match les compétences requises avec celles du CV."""
        if not required:
            return {"score": 100, "matched": [], "missing": []}
        
        required_lower = [s.lower().strip() for s in required]
        cv_lower = [s.lower().strip() for s in cv_skills]
        
        matched = []
        missing = []
        
        for req in required_lower:
            # Fuzzy matching pour chaque compétence requise
            best_match = None
            best_score = 0
            
            for cv_skill in cv_lower:
                score = fuzz.ratio(req, cv_skill)
                if score > best_score:
                    best_score = score
                    best_match = cv_skill
            
            if best_score >= 80:  # Seuil de similarité
                matched.append(req)
            else:
                missing.append(req)
        
        score = (len(matched) / len(required)) * 100 if required else 100
        
        return {
            "score": score,
            "matched": matched,
            "missing": missing
        }
    
    def _analyze_skill_gaps(self, matched: List[str], missing: List[str]) -> Dict[str, Any]:
        """Analyse détaillée des écarts de compétences."""
        # Catégorisation simple des compétences
        categories = {
            "programming": ["python", "javascript", "java", "c++", "typescript", "go", "rust"],
            "web": ["react", "vue", "angular", "html", "css", "node.js", "django", "fastapi"],
            "data": ["sql", "postgresql", "mongodb", "pandas", "numpy", "machine learning"],
            "devops": ["docker", "kubernetes", "aws", "azure", "ci/cd", "git"],
            "soft_skills": ["communication", "leadership", "teamwork", "agile", "scrum"]
        }
        
        gap_by_category = {}
        
        for category, skills in categories.items():
            cat_missing = [s for s in missing if any(fuzz.ratio(s, cs) > 70 for cs in skills)]
            cat_matched = [s for s in matched if any(fuzz.ratio(s, cs) > 70 for cs in skills)]
            
            if cat_missing or cat_matched:
                gap_by_category[category] = {
                    "matched_count": len(cat_matched),
                    "missing_count": len(cat_missing),
                    "missing_skills": cat_missing
                }
        
        return {
            "total_required": len(matched) + len(missing),
            "total_matched": len(matched),
            "total_missing": len(missing),
            "match_rate": round((len(matched) / (len(matched) + len(missing))) * 100, 1) if (matched or missing) else 100,
            "gap_by_category": gap_by_category
        }