import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = os.getenv("LLM_MODEL", "anthropic/claude-3.5-haiku")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "400"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    top_k: int = int(os.getenv("TOP_K", "4"))
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")


settings = Settings()
