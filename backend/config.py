"""
Central configuration for the Class 5 chatbot backend.
Values can be overridden via environment variables or a .env file.
"""
from __future__ import annotations

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root is two levels above this file: backend/config.py → backend/ → project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Paths ──────────────────────────────────────────────────────────────
    project_root: Path = PROJECT_ROOT
    vectorstore_path: Path = PROJECT_ROOT / "vectorstore" / "class5_chatbot"
    subjects_base_path: Path = PROJECT_ROOT
    upload_dir: Path = PROJECT_ROOT / "data" / "uploads"

    # ── Upload Limits ──────────────────────────────────────────────────────
    max_upload_size_bytes: int = 50 * 1024 * 1024  # 50 MB default max upload

    # ── ChromaDB ───────────────────────────────────────────────────────────
    chroma_collection_name: str = "class5_evs_chapters"
    history_collection_name: str = "history_master"
    history_pdf_path: Path = PROJECT_ROOT / "History" / "History.pdf"
    math_collection_name: str = "mathematics_master"
    math_pdf_path: Path = PROJECT_ROOT / "Maths" / "Mathematics.pdf"
    faculty_collection_name: str = "faculty_uploads"

    # ── Database ───────────────────────────────────────────────────────────
    database_path: Path = PROJECT_ROOT / "data" / "vidyaverse.db"

    # ── Embedding model ────────────────────────────────────────────────────
    embedding_model_name: str = "intfloat/multilingual-e5-small"

    # ── Ollama / LLM ───────────────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"     # Upgraded from 1.7b — ~2.5 GB Q4 quantized
    ollama_timeout: int = 180  # seconds (4b is slower; conservative for 8 GB RAM)

    # ── RAG parameters ─────────────────────────────────────────────────────
    rag_top_k: int = 5
    rag_similarity_threshold: float = 1.5   # ChromaDB uses L2 distance; lower = more similar
    rag_max_context_chars: int = 4000

    # ── Chunking ───────────────────────────────────────────────────────────
    chunk_size: int = 800        # characters
    chunk_overlap: int = 150     # characters

    # ── CORS ───────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


# Singleton instance used across all modules
settings = Settings()
