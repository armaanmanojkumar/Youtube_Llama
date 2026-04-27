import logging
from typing import List

import httpx

logger = logging.getLogger("rag.embedder")


def embed_texts(texts: List[str], model: str, host: str = "http://localhost:11434") -> List[List[float]]:
    """Embed a list of texts using Ollama's batch /api/embed endpoint."""
    logger.info(f"Embedding {len(texts)} texts with model '{model}'...")
    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            f"{host}/api/embed",
            json={"model": model, "input": texts},
        )
        response.raise_for_status()
        embeddings = response.json()["embeddings"]
    logger.info(f"Embedding complete — got {len(embeddings)} vectors of dim {len(embeddings[0])}")
    return embeddings
