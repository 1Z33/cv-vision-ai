"""app.utils.pdf_parser

PDF Parser - Extraction hybride : natif (pdfplumber) + OCR fallback (Tesseract)

Stratégie:
1. Extraction native rapide via pdfplumber
2. Si texte vide/trop court -> OCR via pdf2image + pytesseract
3. Retour d'un résultat enrichi (source, longueurs, déclenchement OCR)
"""

from __future__ import annotations

import concurrent.futures
import logging
import os
from pathlib import Path
from typing import Any, Dict

import pdfplumber

# OCR dependencies (pytesseract/pdf2image) are optional at runtime.
# They must not be imported at module import time, otherwise uvicorn fails
# when they are missing from the active venv.
try:
    from pdf2image import convert_from_path  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    convert_from_path = None  # type: ignore



logger = logging.getLogger(__name__)

# Seuil minimal de caractères pour considérer l'extraction native comme valide
MIN_NATIVE_TEXT_LENGTH = int(os.getenv("OCR_MIN_TEXT_LENGTH", "100"))

# --- OCR / performance (env configurables) ---
OCR_MAX_PAGES = int(os.getenv("OCR_MAX_PAGES", "10"))
OCR_DPI = int(os.getenv("OCR_DPI", "300"))
OCR_TIMEOUT = int(os.getenv("OCR_TIMEOUT", "30"))
OCR_FIRST_PAGE_MIN_CHARS = int(os.getenv("OCR_FIRST_PAGE_MIN_CHARS", "20"))


class PDFParser:
    """Parseur PDF hybride : extraction native + fallback OCR."""

    @staticmethod
    def parse(file_path: str | Path) -> Dict[str, Any]:
        """Extrait le texte d'un PDF avec stratégie hybride."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"PDF non trouvé : {file_path}")
        if file_path.suffix.lower() != ".pdf":
            raise ValueError("Le fichier doit être au format PDF")

        result: Dict[str, Any] = {
            "text": "",
            "page_count": 0,
            "source": "none",
            "native_text": "",
            "ocr_text": "",
            "ocr_triggered": False,
        }

        # --- Optimisation: décision rapide "scanné ?" via 1ère page ---
        try:
            first_page_text = PDFParser.extract_first_page_text(str(file_path))
            # Désactivation possible pour les tests/volonté applicative.
            # (Permet d'éviter que la détection rapide coupe les mocks d'extraction.)
            if os.getenv("OCR_DISABLE_FIRST_PAGE_DETECTION", "0") == "1":
                pass
            elif len(first_page_text) < OCR_FIRST_PAGE_MIN_CHARS:
                logger.info(
                    "Détection scannée probable (1ère page %s chars < %s), OCR direct: %s",
                    len(first_page_text),
                    OCR_FIRST_PAGE_MIN_CHARS,
                    file_path.name,
                )
                return PDFParser._parse_with_ocr_only(file_path, result)

            # Si la 1ère page est suffisamment textuelle, on évite le raccourci OCR-only.
            # (Les tests mockent _extract_native mais pas toujours _extract_first_page.)
        except Exception as e:
            # En cas d'échec de détection rapide, on retombe sur le flux normal
            logger.warning("Détection scannée via 1ère page impossible: %s", e)

        # --- ÉTAPE 1 : Extraction native ---
        try:
            native_result = PDFParser._extract_native(file_path)
            result["native_text"] = native_result["text"]
            result["page_count"] = native_result["page_count"]

            native_text_clean = native_result["text"].strip()

            if len(native_text_clean) >= MIN_NATIVE_TEXT_LENGTH:
                result["text"] = native_result["text"]
                result["source"] = "native"
                logger.info(
                    "Extraction native réussie (%s chars) : %s",
                    len(native_text_clean),
                    file_path.name,
                )
                return result

            logger.warning(
                "Texte natif insuffisant (%s chars < %s), OCR fallback déclenché : %s",
                len(native_text_clean),
                MIN_NATIVE_TEXT_LENGTH,
                file_path.name,
            )

        except Exception as e:
            logger.error("Erreur extraction native : %s, OCR fallback déclenché", e)

        # --- ÉTAPE 2 : OCR fallback (avec timeout) ---
        try:
            ocr_result = PDFParser._extract_ocr_with_timeout(file_path)
            result["ocr_text"] = ocr_result.get("text", "")
            result["page_count"] = max(result["page_count"], ocr_result.get("page_count", 0))
            result["ocr_triggered"] = True

            ocr_text_clean = result["ocr_text"].strip()

            if len(ocr_text_clean) >= MIN_NATIVE_TEXT_LENGTH:
                result["text"] = result["ocr_text"]
                result["source"] = "ocr"
                logger.info("OCR réussi (%s chars) : %s", len(ocr_text_clean), file_path.name)
            else:
                best_text = (
                    result["native_text"]
                    if len(result["native_text"]) > len(ocr_text_clean)
                    else result["ocr_text"]
                )
                result["text"] = best_text
                result["source"] = "hybrid"
                logger.warning(
                    "OCR partiel (%s chars), source=hybrid : %s",
                    len(ocr_text_clean),
                    file_path.name,
                )

        except Exception as e:
            logger.error("OCR fallback échoué : %s", e)
            result["text"] = result["native_text"]
            result["source"] = "native_partial"

        return result

    @staticmethod
    def _parse_with_ocr_only(file_path: Path, result: Dict[str, Any]) -> Dict[str, Any]:
        """Flux OCR seul quand la 1ère page suggère un PDF scanné."""
        try:
            ocr_result = PDFParser._extract_ocr_with_timeout(file_path)
            result["ocr_text"] = ocr_result.get("text", "")
            result["page_count"] = ocr_result.get("page_count", 0)
            result["ocr_triggered"] = True

            ocr_text_clean = result["ocr_text"].strip()
            if len(ocr_text_clean) >= MIN_NATIVE_TEXT_LENGTH:
                result["text"] = result["ocr_text"]
                result["source"] = "ocr"
            else:
                # Si le texte native existe, on considère un fallback hybride/partiel.
                # Ici, dans le flux OCR-only, result["native_text"] n'est pas rempli,
                # donc on ne peut pas décider "hybrid" de manière fiable.
                result["text"] = result["ocr_text"]
                result["source"] = "ocr_partial"

            return result
        except Exception as e:
            logger.error("OCR direct échoué : %s", e)
            result["source"] = "native_partial"
            return result

    @staticmethod
    def _extract_native(file_path: Path) -> Dict[str, Any]:
        """Extraction native via pdfplumber."""
        all_text: list[str] = []
        page_count = 0

        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    all_text.append(page_text)

        return {
            "text": "\n\n".join(all_text),
            "page_count": page_count,
        }

    @staticmethod
    def _extract_ocr_with_timeout(file_path: Path) -> Dict[str, Any]:
        """Réalise l'OCR avec un timeout applicatif."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(PDFParser._extract_ocr, file_path, OCR_DPI)
            try:
                return future.result(timeout=OCR_TIMEOUT)
            except concurrent.futures.TimeoutError:
                logger.error("OCR timeout après %ss : %s", OCR_TIMEOUT, file_path.name)
                return {"text": "", "page_count": 0}

    @staticmethod
    def _extract_ocr(file_path: Path, dpi: int = 300, lang: str = "fra+eng") -> Dict[str, Any]:
        """Extraction OCR via Tesseract (image par image, sans charger toutes les pages)."""
        # Lazy import OCR stack
        try:
            import pytesseract  # type: ignore
        except ModuleNotFoundError as e:
            raise ImportError(
                "OCR non disponible: 'pytesseract' n'est pas installé dans ce venv."
            ) from e

        if convert_from_path is None:
            raise ImportError("OCR non disponible: 'pdf2image' n'est pas installé dans ce venv.")

        all_text: list[str] = []


        # pdf2image: first_page/last_page sont 1-indexées
        first_page = 1
        last_page = OCR_MAX_PAGES

        images = []
        try:
            images = convert_from_path(
                file_path,
                dpi=dpi,
                first_page=first_page,
                last_page=last_page,
                fmt="png",
                thread_count=2,
            )

            for i, image in enumerate(images):
                try:
                    page_text = pytesseract.image_to_string(
                        image,
                        lang=lang,
                        config="--psm 6",
                    )
                    if page_text and page_text.strip():
                        all_text.append(page_text.strip())
                finally:
                    try:
                        image.close()
                    except Exception:
                        pass

        finally:
            for img in images:
                try:
                    img.close()
                except Exception:
                    pass

        return {
            "text": "\n\n".join(all_text),
            "page_count": len(images),
        }

    @staticmethod
    def check_tesseract() -> bool:
        """Vérifie que Tesseract est installé et accessible."""
        try:
            import pytesseract  # type: ignore

            version = pytesseract.get_tesseract_version()
            logger.info("Tesseract détecté : v%s", version)
            return True
        except Exception as e:
            logger.error("Tesseract non disponible : %s", e)
            return False


    @staticmethod
    def extract_first_page_text(file_path: str) -> str:
        """Extrait uniquement le texte de la première page via extraction native."""
        try:
            with pdfplumber.open(file_path) as pdf:
                if len(pdf.pages) > 0:
                    text = pdf.pages[0].extract_text()
                    return text.strip() if text else ""
                return ""
        except Exception:
            return ""

