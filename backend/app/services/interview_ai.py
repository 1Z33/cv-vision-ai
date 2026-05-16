"""
Moteur IA pour la génération de questions d'entretien et l'évaluation des réponses.
"""

import random
import re
from typing import Dict, List, Any
from rapidfuzz import fuzz

from app.core.logging import logger


class InterviewAI:
    """
    Génère des questions d'entretien personnalisées et évalue les réponses.
    Version MVP avec templates et règles heuristiques.
    """
    
    def __init__(self):
        self.question_templates = self._load_question_templates()
    
    def _load_question_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Charge les templates de questions par type et difficulté."""
        return {
            "technical": {
                "easy": [
                    {"text": "Pouvez-vous expliquer ce qu'est {skill} et dans quel contexte vous l'avez utilisé ?", "keywords": ["définition", "utilisation", "projet"]},
                    {"text": "Quelle est la différence entre {skill} et {alt_skill} ?", "keywords": ["différence", "comparaison", "avantages"]},
                    {"text": "Décrivez un projet où vous avez utilisé {skill}.", "keywords": ["projet", "réalisation", "résultat"]},
                ],
                "medium": [
                    {"text": "Quels sont les avantages et inconvénients de {skill} par rapport aux alternatives ?", "keywords": ["avantages", "inconvénients", "comparaison", "choix"]},
                    {"text": "Comment gérez-vous la sécurité lors de l'utilisation de {skill} ?", "keywords": ["sécurité", "bonnes pratiques", "précautions"]},
                    {"text": "Expliquez le concept de {concept} dans {skill}.", "keywords": ["concept", "explication", "compréhension"]},
                ],
                "hard": [
                    {"text": "Décrivez une situation complexe où {skill} a posé des défis. Comment les avez-vous surmontés ?", "keywords": ["problème", "solution", "défi", "résolution"]},
                    {"text": "Comment optimiseriez-vous les performances d'un système utilisant {skill} ?", "keywords": ["optimisation", "performance", "scalabilité", "architecture"]},
                    {"text": "Concevez une architecture utilisant {skill} pour gérer {scenario}.", "keywords": ["architecture", "conception", "scalabilité", "système"]},
                ]
            },
            "behavioral": {
                "easy": [
                    {"text": "Parlez-moi de vous et de votre parcours.", "keywords": ["parcours", "motivation", "expérience"]},
                    {"text": "Pourquoi souhaitez-vous rejoindre notre entreprise ?", "keywords": ["motivation", "entreprise", "intérêt"]},
                    {"text": "Où vous voyez-vous dans 3 ans ?", "keywords": ["objectifs", "évolution", "ambition"]},
                ],
                "medium": [
                    {"text": "Décrivez une situation où vous avez dû travailler sous pression.", "keywords": ["pression", "gestion", "résultat", "stress"]},
                    {"text": "Racontez un conflit avec un collègue et comment vous l'avez résolu.", "keywords": ["conflit", "communication", "résolution", "équipe"]},
                    {"text": "Comment gérez-vous les deadlines serrées ?", "keywords": ["organisation", "priorisation", "efficacité", "planning"]},
                ],
                "hard": [
                    {"text": "Décrivez un échec professionnel majeur et ce que vous en avez appris.", "keywords": ["échec", "apprentissage", "humilité", "amélioration"]},
                    {"text": "Comment avez-vous géré un changement majeur dans votre équipe ou projet ?", "keywords": ["adaptation", "leadership", "changement", "résilience"]},
                    {"text": "Donnez un exemple où vous avez dû convaincre une équipe de votre vision.", "keywords": ["leadership", "influence", "vision", "persuasion"]},
                ]
            },
            "situational": {
                "easy": [
                    {"text": "Que feriez-vous si vous découvriez un bug en production ?", "keywords": ["bug", "production", "réactivité", "processus"]},
                    {"text": "Comment réagiriez-vous si un client demandait une fonctionnalité impossible ?", "keywords": ["client", "gestion", "communication", "attentes"]},
                ],
                "medium": [
                    {"text": "Votre projet est en retard. Comment communiquez-vous cela aux parties prenantes ?", "keywords": ["communication", "transparence", "solution", "gestion"]},
                    {"text": "Un membre de l'équipe ne livre pas son travail. Que faites-vous ?", "keywords": ["équipe", "accompagnement", "responsabilité", "support"]},
                ],
                "hard": [
                    {"text": "Vous devez refactoriser un legacy code critique sans tests. Comment procédez-vous ?", "keywords": ["refactoring", "tests", "prudence", "stratégie"]},
                    {"text": "Votre système subit une panne majeure à 2h du matin. Décrivez votre procédure.", "keywords": ["incident", "urgence", "procédure", "calme"]},
                ]
            }
        }
    
    def generate_questions(self, cv_text: str, job_title: str | None, difficulty: str, num_questions: int = 5) -> List[Dict[str, Any]]:
        """
        Génère une série de questions personnalisées pour un entretien.
        
        Args:
            cv_text: Texte du CV pour personnalisation
            job_title: Poste visé
            difficulty: easy, medium, hard
            num_questions: Nombre de questions à générer
        
        Returns:
            Liste de questions avec métadonnées
        """
        # Extraire les compétences du CV pour personnaliser
        skills = self._extract_skills_from_cv(cv_text)
        
        questions = []
        types = ["technical", "behavioral", "situational"]
        
        # Répartition : 40% tech, 40% behavioral, 20% situational
        type_distribution = (
            ["technical"] * max(1, num_questions // 3) +
            ["behavioral"] * max(1, num_questions // 3) +
            ["situational"] * max(1, num_questions // 5)
        )
        
        # Compléter si nécessaire
        while len(type_distribution) < num_questions:
            type_distribution.append(random.choice(types))
        
        random.shuffle(type_distribution)
        
        for i, q_type in enumerate(type_distribution[:num_questions]):
            question = self._generate_single_question(q_type, difficulty, skills, job_title, i + 1)
            questions.append(question)
        
        return questions
    
    def _generate_single_question(self, q_type: str, difficulty: str, skills: List[str], job_title: str | None, q_num: int) -> Dict[str, Any]:
        """Génère une question individuelle."""
        templates = self.question_templates[q_type][difficulty]
        template = random.choice(templates)
        
        text = template["text"]
        
        # Personnaliser avec les skills si disponibles
        if "{skill}" in text and skills:
            skill = random.choice(skills)
            text = text.replace("{skill}", skill.title())
            
            # Remplacer les placeholders secondaires
            if "{alt_skill}" in text:
                alt = random.choice([s for s in skills if s != skill] or ["une alternative"])
                text = text.replace("{alt_skill}", alt.title())
            
            if "{concept}" in text:
                concepts = ["l'architecture", "les patterns", "l'optimisation", "la sécurité"]
                text = text.replace("{concept}", random.choice(concepts))
            
            if "{scenario}" in text:
                scenarios = ["un trafic élevé", "des données sensibles", "une équipe distribuée"]
                text = text.replace("{scenario}", random.choice(scenarios))
        
        # Ajouter le contexte du poste
        if job_title and random.random() > 0.5:
            text = f"[Contexte: {job_title}] {text}"
        
        return {
            "question_number": q_num,
            "question_text": text,
            "question_type": q_type,
            "expected_keywords": template["keywords"],
            "difficulty": difficulty
        }
    
    def evaluate_answer(self, question: Dict[str, Any], answer: str) -> Dict[str, Any]:
        """
        Évalue une réponse à une question d'entretien.
        
        Args:
            question: Dict avec question_text, expected_keywords, etc.
            answer: Réponse textuelle de l'utilisateur
        
        Returns Je vais te donner le code complet pour tous les fichiers restants. Continuons là où on s'est arrêté.

---

## 📁 BACKEND / SERVICES (Suite)

#### `backend/app/services/interview_ai.py` (Suite)
```python
        Returns:
            Dict avec score, feedback, keywords détectés/manquants
        """
        if not answer or len(answer.strip()) < 10:
            return {
                "answer_score": 0,
                "feedback_text": "Votre réponse est trop courte. Essayez de développer avec des exemples concrets.",
                "detected_keywords": [],
                "missing_keywords": question["expected_keywords"],
                "is_complete": False
            }
        
        answer_lower = answer.lower()
        expected_keywords = question.get("expected_keywords", [])
        
        # Détecter les keywords présents
        detected = []
        missing = []
        
        for keyword in expected_keywords:
            # Fuzzy matching pour tolérer les variations
            if fuzz.partial_ratio(keyword.lower(), answer_lower) > 75:
                detected.append(keyword)
            else:
                missing.append(keyword)
        
        # Calculer le score
        if expected_keywords:
            score = int((len(detected) / len(expected_keywords)) * 100)
        else:
            score = 70  # Score par défaut si pas de keywords attendus
        
        # Bonus pour la longueur de la réponse
        word_count = len(answer.split())
        if word_count >= 50:
            score = min(score + 10, 100)
        elif word_count < 20:
            score = max(score - 15, 0)
        
        # Générer le feedback
        feedback = self._generate_feedback(score, detected, missing, word_count, question["question_type"])
        
        return {
            "answer_score": score,
            "feedback_text": feedback,
            "detected_keywords": detected,
            "missing_keywords": missing,
            "is_complete": True
        }
    
    def _generate_feedback(self, score: int, detected: List[str], missing: List[str], word_count: int, q_type: str) -> str:
        """Génère un feedback personnalisé basé sur le score."""
        feedback_parts = []
        
        # Feedback général selon le score
        if score >= 90:
            feedback_parts.append("Excellent ! Votre réponse est très complète et bien structurée.")
        elif score >= 75:
            feedback_parts.append("Bonne réponse. Vous avez bien couvert les points essentiels.")
        elif score >= 50:
            feedback_parts.append("Réponse acceptable, mais quelques éléments importants manquent.")
        else:
            feedback_parts.append("Votre réponse nécessite plus de développement et d'exemples concrets.")
        
        # Points positifs
        if detected:
            feedback_parts.append(f"Points forts : vous avez abordé {', '.join(detected)}.")
        
        # Points à améliorer
        if missing:
            feedback_parts.append(f"À améliorer : pensez à mentionner {', '.join(missing)} dans votre réponse.")
        
        # Conseils spécifiques au type
        if q_type == "technical" and word_count < 30:
            feedback_parts.append("Pour les questions techniques, essayez d'illustrer avec du code ou des exemples concrets.")
        elif q_type == "behavioral" and word_count < 40:
            feedback_parts.append("Pour les questions comportementales, utilisez la méthode STAR (Situation, Tâche, Action, Résultat).")
        
        return " ".join(feedback_parts)
    
    def _extract_skills_from_cv(self, cv_text: str) -> List[str]:
        """Extrait rapidement les compétences du CV."""
        common_skills = [
            "python", "javascript", "java", "react", "node.js", "sql",
            "docker", "aws", "git", "agile", "machine learning", "data analysis"
        ]
        cv_lower = cv_text.lower()
        return [skill for skill in common_skills if skill in cv_lower]
    
    def generate_final_feedback(self, qa_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Génère un feedback global à la fin de la session d'entretien.
        
        Args:
            qa_list: Liste des Q&A avec scores
        
        Returns:
            Feedback global structuré
        """
        if not qa_list:
            return {
                "total_score": 0,
                "general_feedback": "Aucune réponse enregistrée.",
                "strengths": [],
                "areas_to_improve": []
            }
        
        scores = [qa["answer_score"] for qa in qa_list]
        total_score = int(sum(scores) / len(scores))
        
        # Analyser les types de questions
        tech_scores = [qa["answer_score"] for qa in qa_list if qa.get("question_type") == "technical"]
        behav_scores = [qa["answer_score"] for qa in qa_list if qa.get("question_type") == "behavioral"]
        
        strengths = []
        areas = []
        
        if tech_scores and sum(tech_scores) / len(tech_scores) >= 75:
            strengths.append("Solides compétences techniques démontrées")
        elif tech_scores:
            areas.append("Renforcez vos connaissances techniques avec des exemples concrets")
        
        if behav_scores and sum(behav_scores) / len(behav_scores) >= 75:
            strengths.append("Excellente communication et posture professionnelle")
        elif behav_scores:
            areas.append("Pratiquez davantage les questions comportementales avec la méthode STAR")
        
        if total_score >= 80:
            general = "Félicitations ! Vous démontrez un excellent niveau de préparation."
        elif total_score >= 60:
            general = "Bon niveau global. Quelques ajustements vous permettront d'atteindre l'excellence."
        else:
            general = "Continuez à pratiquer ! La préparation régulière est la clé du succès."
        
        return {
            "total_score": total_score,
            "general_feedback": general,
            "strengths": strengths,
            "areas_to_improve": areas
        }