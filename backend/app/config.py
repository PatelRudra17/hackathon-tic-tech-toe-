from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache
import os

# .env lives at project root (one level above backend/)
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "TalentIntelligence"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/talent_intelligence"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/talent_intelligence"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # API
    API_KEY_HEADER: str = "X-API-Key"
    DEFAULT_API_KEY: str = "dev-api-key-change-in-production"
    RATE_LIMIT: str = "100/minute"

    # Upload
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "./uploads"

    class Config:
        env_file = str(_ENV_FILE)
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
