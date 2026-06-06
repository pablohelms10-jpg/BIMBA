from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----
    app_env: str = "development"
    log_level: str = "INFO"
    debug: bool = False

    # ---- Database ----
    database_url: str = "postgresql+asyncpg://bimba:bimba_password@postgres:5432/bimba"

    # ---- Redis ----
    redis_url: str = "redis://redis:6379/0"

    # ---- Qdrant ----
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "bimba_embeddings"
    embedding_dim: int = 384  # all-MiniLM-L6-v2

    # ---- MinIO ----
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "bimba-files"
    minio_secure: bool = False

    # ---- AI / LLM ----
    anthropic_api_key: str = ""
    openai_api_key: Optional[str] = None

    # ---- Security ----
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # ---- CORS ----
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ---- Upload ----
    max_upload_size_mb: int = 2048

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    # ---- Processing ----
    chunk_duration_seconds: int = 300
    chunk_overlap_seconds: int = 10
    whisper_model: str = "large-v2"
    whisper_language: Optional[str] = None
    slide_change_threshold: int = 10
    semantic_similarity_threshold: float = 0.3

    # ---- Celery ----
    worker_concurrency: int = 4
    celery_queue_high: str = "high_priority"
    celery_queue_transcription: str = "transcription"
    celery_queue_ocr: str = "ocr"
    celery_queue_llm: str = "llm"
    celery_queue_export: str = "export"

    # ---- Flower ----
    flower_user: str = "admin"
    flower_password: str = "flowerpassword"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
