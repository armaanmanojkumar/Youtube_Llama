import os
from pathlib import Path

from dotenv import load_dotenv

_ENV_FILE = Path(__file__).parent.parent / ".env"
load_dotenv(_ENV_FILE, override=False)


class Settings:
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    embed_model: str = os.getenv("EMBED_MODEL", "nomic-embed-text")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "450"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    top_k: int = int(os.getenv("TOP_K", "4"))
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    transcript_cache_dir: str = os.getenv("TRANSCRIPT_CACHE_DIR", "./data/transcripts")
    temperature: float = float(os.getenv("TEMPERATURE", "0.15"))
    allow_origins = [origin.strip() for origin in os.getenv("ALLOW_ORIGINS", "*").split(",") if origin.strip()]

    @property
    def model(self) -> str:
        return os.getenv("MODEL", "llama3.1:latest")


settings = Settings()
