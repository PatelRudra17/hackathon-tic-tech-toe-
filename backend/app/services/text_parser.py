from typing import Optional
from loguru import logger


class TextParser:
    """Extracts text from plain text resumes with encoding detection."""

    @staticmethod
    def extract_text(file_content: bytes) -> Optional[str]:
        """Extract text from plain text bytes with encoding detection."""
        try:
            # Try UTF-8 first
            try:
                return file_content.decode("utf-8")
            except UnicodeDecodeError:
                pass

            # Use chardet for encoding detection
            try:
                import chardet
                detected = chardet.detect(file_content)
                encoding = detected.get("encoding", "utf-8")
                return file_content.decode(encoding)
            except Exception:
                pass

            # Fallback encodings
            for encoding in ["latin-1", "cp1252", "ascii"]:
                try:
                    return file_content.decode(encoding)
                except UnicodeDecodeError:
                    continue

            # Last resort
            return file_content.decode("utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return None
