"""
Extraction de texte à partir de fichiers PDF.
"""

import pdfplumber
from pathlib import Path
from typing import Dict, Any


class PDFParser:
    """
    Parseur PDF utilisant pdfplumber pour extraire le texte et les métadonnées.
    """
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Extrait le texte et les métadonnées d'un PDF.
        
        Args:
            file_path: Chemin vers le fichier PDF
        
        Returns:
            Dict avec texte extrait, nombre de pages, etc.
        
        Raises:
            ValueError: Si le fichier n'est pas un PDF valide
        """
        path = Path(file_path)
        
        if not path.exists():
            raise ValueError(f"Fichier non trouvé: {file_path}")
        
        if path.suffix.lower() != ".pdf":
            raise ValueError("Le fichier doit être au format PDF")
        
        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                
                # Extraire le texte de toutes les pages
                all_text = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text.append(text)
                
                full_text = "\n\n".join(all_text)
                
                # Extraire quelques métadonnées
                metadata = {}
                if pdf.metadata:
                    metadata = {
                        "title": pdf.metadata.get("Title", ""),
                        "author": pdf.metadata.get("Author", ""),
                        "creator": pdf.metadata.get("Creator", "")
                    }
                
                return {
                    "text": full_text.strip(),
                    "page_count": total_pages,
                    "metadata": metadata,
                    "success": True
                }
                
        except Exception as e:
            raise ValueError(f"Erreur lors de l'extraction PDF: {str(e)}")
    
    def extract_first_page_text(self, file_path: str) -> str:
        """Extrait uniquement le texte de la première page."""
        try:
            with pdfplumber.open(file_path) as pdf:
                if len(pdf.pages) > 0:
                    text = pdf.pages[0].extract_text()
                    return text.strip() if text else ""
                return ""
        except Exception:
            return ""