import io
from typing import Optional
from loguru import logger


class DOCXParser:
    """Extracts text from DOCX resumes."""

    @staticmethod
    def extract_text(file_content: bytes) -> Optional[str]:
        """Extract text from DOCX bytes."""
        try:
            from docx import Document

            doc = Document(io.BytesIO(file_content))
            text_parts = []

            # Extract paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)

            # Extract from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_parts.append(" | ".join(row_text))

            # Extract from headers/footers
            for section in doc.sections:
                header = section.header
                if header:
                    for paragraph in header.paragraphs:
                        if paragraph.text.strip():
                            text_parts.insert(0, paragraph.text)

            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            return None
