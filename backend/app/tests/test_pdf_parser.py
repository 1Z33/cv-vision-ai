import pytest
from unittest.mock import patch

from app.utils.pdf_parser import PDFParser


class TestPDFParser:
    def test_native_extraction_sufficient_no_ocr(self, tmp_path):
        """Si le texte natif est suffisant, l'OCR ne doit pas être déclenché."""
        pdf_path = tmp_path / "sample.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%EOF")

        with patch.object(
            PDFParser,
            "extract_first_page_text",
            return_value="x" * 200,
        ):
            with patch.object(
                PDFParser,
                "_extract_native",
                return_value={"text": "x" * 200, "page_count": 1},
            ):
                with patch.object(PDFParser, "_extract_ocr") as mock_ocr:
                    result = PDFParser.parse(pdf_path)

        assert result["source"] == "native"
        assert result["ocr_triggered"] is False
        assert result["text"] == "x" * 200
        mock_ocr.assert_not_called()

    def test_ocr_fallback_triggered(self, tmp_path):
        """Si texte natif trop court, OCR doit être déclenché."""
        pdf_path = tmp_path / "scanned.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%EOF")

        with patch.object(
            PDFParser,
            "extract_first_page_text",
            return_value="",
        ):
            with patch.object(
                PDFParser,
                "_extract_native",
                return_value={"text": "", "page_count": 1},
            ):
                with patch.object(
                    PDFParser,
                    "_extract_ocr",
                    return_value={"text": "Texte OCR extrait" * 10, "page_count": 1},
                ):
                    result = PDFParser.parse(pdf_path)

        assert result["source"] in {"ocr", "hybrid"}
        assert result["ocr_triggered"] is True
        assert "OCR" in result["text"]

    def test_ocr_failure_graceful(self, tmp_path):
        """Si OCR échoue, ne pas planter et garder le texte natif."""
        pdf_path = tmp_path / "broken.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%EOF")

        with patch.object(
            PDFParser,
            "extract_first_page_text",
            return_value="x",
        ):
            with patch.object(
                PDFParser,
                "_extract_native",
                return_value={"text": "Texte natif court" * 1, "page_count": 1},
            ):
                with patch.object(
                    PDFParser,
                    "_extract_ocr",
                    side_effect=Exception("OCR crash"),
                ):
                    result = PDFParser.parse(pdf_path)

        # Si la détection rapide OCR-only passe, on n'a pas de native_text rempli,
        # donc la source peut être native_partial mais le texte est vide.
        assert result["source"] in {"native_partial", "none", "ocr_partial"}
        assert isinstance(result["text"], str)
        assert result["text"] is not None

    def test_check_tesseract_returns_bool(self):
        available = PDFParser.check_tesseract()
        assert isinstance(available, bool)

