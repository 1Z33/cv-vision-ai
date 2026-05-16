"""
Service centralisé de calcul des scores.
"""

from typing import Dict, List


class ScoringService:
    """
    Service utilitaire pour normaliser et agréger les scores.
    """
    
    @staticmethod
    def normalize_score(raw_score: float, min_val: float = 0, max_val: float = 100) -> int:
        """
        Normalise un score entre 0 et 100.
        
        Args:
            raw_score: Score brut
            min_val: Valeur minimale possible
            max_val: Valeur maximale possible
        
        Returns:
            Score normalisé (int, 0-100)
        """
        if max_val == min_val:
            return 50
        
        normalized = ((raw_score - min_val) / (max_val - min_val)) * 100
        return int(max(0, min(100, normalized)))
    
    @staticmethod
    def weighted_average(scores: Dict[str, float], weights: Dict[str, float]) -> int:
        """
        Calcule une moyenne pondérée.
        
        Args:
            scores: Dict {nom: score}
            weights: Dict {nom: poids} (doivent sommer à 1.0)
        
        Returns:
            Score pondéré (int, 0-100)
        """
        total = sum(scores.get(k, 0) * weights.get(k, 0) for k in set(scores) & set(weights))
        return int(max(0, min(100, total)))
    
    @staticmethod
    def calculate_progression(history: List[int]) -> Dict[str, any]:
        """
        Calcule les statistiques de progression.
        
        Args:
            history: Liste chronologique des scores
        
        Returns:
            Dict avec tendance, moyenne, meilleur score
        """
        if not history:
            return {"trend": "stable", "average": 0, "best": 0, "improvement": 0}
        
        average = sum(history) / len(history)
        best = max(history)
        
        # Calculer la tendance
        if len(history) >= 2:
            first_half = sum(history[:len(history)//2]) / max(len(history)//2, 1)
            second_half = sum(history[len(history)//2:]) / max(len(history) - len(history)//2, 1)
            improvement = second_half - first_half
            
            if improvement > 5:
                trend = "improving"
            elif improvement < -5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"
            improvement = 0
        
        return {
            "trend": trend,
            "average": round(average, 1),
            "best": best,
            "improvement": round(improvement, 1),
            "total_sessions": len(history)
        }