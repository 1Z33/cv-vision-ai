"""
Nettoyage et prétraitement du texte pour l'analyse NLP.
"""

import re
import string
from typing import List


class TextCleaner:
    """
    Nettoie et normalise le texte extrait des CVs.
    """
    
    @staticmethod
    def clean(text: str) -> str:
        """
        Nettoie le texte en supprimant le bruit et normalisant.
        
        Args:
            text: Texte brut
        
        Returns:
            Texte nettoyé
        """
        if not text:
            return ""
        
        # Convertir en minuscules
        text = text.lower()
        
        # Supprimer les URLs
        text = re.sub(r'http\S+|www\S+|@\S+', '', text)
        
        # Supprimer les emails
        text = re.sub(r'\S+@\S+', '', text)
        
        # Supprimer les numéros de téléphone
        text = re.sub(r'\+?\d[\d\s\-\(\)]{7,}\d', '', text)
        
        # Supprimer les caractères spéciaux excessifs
        text = re.sub(r'[^\w\s\-./]', ' ', text)
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les lignes vides multiples
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()
    
    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Tokenise le texte en mots.
        
        Args:
            text: Texte nettoyé
        
        Returns:
            Liste de tokens
        """
        # Supprimer la ponctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        return text.split()
    
    @staticmethod
    def remove_stopwords(tokens: List[str], language: str = "french") -> List[str]:
        """
        Supprime les mots vides (stopwords).
        
        Args:
            tokens: Liste de tokens
            language: Langue des stopwords
        
        Returns:
            Tokens filtrés
        """
        # Stopwords français de base
        french_stopwords = {
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'en',
            'à', 'au', 'aux', 'avec', 'pour', 'par', 'sur', 'dans', 'ce',
            'cette', 'ces', 'son', 'sa', 'ses', 'mon', 'ma', 'mes', 'ton',
            'ta', 'tes', 'notre', 'votre', 'leur', 'je', 'tu', 'il', 'elle',
            'nous', 'vous', 'ils', 'elles', 'est', 'sont', 'être', 'avoir',
            'faire', 'plus', 'moins', 'très', 'trop', 'peu', 'tout', 'tous',
            'toute', 'toutes', 'autre', 'autres', 'même', 'tant', 'tel', 'telle'
        }
        
        english_stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might'
        }
        
        stopwords = french_stopwords if language == "french" else english_stopwords
        
        return [token for token in tokens if token.lower() not in stopwords and len(token) > 2]