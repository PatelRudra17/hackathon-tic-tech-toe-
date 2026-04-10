import io
from typing import Optional
from loguru import logger


class PDFParser:
    """Extracts text from PDF resumes using pdfplumber with PyMuPDF fallback."""

    @staticmethod
    def extract_text(file_content: bytes) -> Optional[str]:
        """Extract text from PDF bytes."""
        text = PDFParser._extract_with_pdfplumber(file_content)
        if not text or len(text.strip()) < 50:
            logger.info("pdfplumber extraction insufficient, trying PyMuPDF")
            text = PDFParser._extract_with_pymupdf(file_content)
        return text

    @staticmethod
    def _extract_with_pdfplumber(file_content: bytes) -> Optional[str]:
        try:
            import pdfplumber

            text_parts = []
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                    # Also try extracting from tables
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if row:
                                row_text = " | ".join([cell or "" for cell in row])
                                if row_text.strip():
                                    text_parts.append(row_text)

            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return None

    @staticmethod
    def _extract_with_pymupdf(file_content: bytes) -> Optional[str]:
        try:
            import fitz  # PyMuPDF

            text_parts = []
            doc = fitz.open(stream=file_content, filetype="pdf")
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            return None
