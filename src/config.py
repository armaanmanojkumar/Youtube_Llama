import os
from pathlib import Path

from dotenv import load_dotenv

_ENV_FILE = Path(__file__).parent.parent / ".env"


def _reload() -> None:
    load_dotenv(_ENV_FILE, override=True)


# Load once on import
_reload()


class Settings:
    # Static — these don't change between requests
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    embed_model: str = os.getenv("EMBED_MODEL", "nomic-embed-text")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "400"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    top_k: int = int(os.getenv("TOP_K", "4"))
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    temperature: float = float(os.getenv("TEMPERATURE", "0.2"))

    # Dynamic — re-read from .env on every access
    @property
    def model(self) -> str:
        _reload()
        return os.getenv("MODEL", "llama3.1:latest")


settings = Settings()
