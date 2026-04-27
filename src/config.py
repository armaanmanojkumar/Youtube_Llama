import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model: str = os.getenv("MODEL", "gemma4:e4b")
    embed_model: str = os.getenv("EMBED_MODEL", "nomic-embed-text")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "400"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    top_k: int = int(os.getenv("TOP_K", "4"))
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    temperature: float = float(os.getenv("TEMPERATURE", "0.2"))


settings = Settings()
