import logging
from typing import List

import httpx

logger = logging.getLogger("rag.embedder")


def embed_texts(texts: List[str], model: str, host: str = "http://localhost:11434") -> List[List[float]]:
    """Embed a list of texts using Ollama's batch /api/embed endpoint."""
    logger.info(f"Embedding {len(texts)} texts with model '{model}'...")
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{host}/api/embed",
                json={"model": model, "input": texts},
            )
            if not response.is_success:
                raise RuntimeError(f"Ollama embed error {response.status_code}: {response.text}")
            embeddings = response.json()["embeddings"]
    except httpx.ConnectError as exc:
        raise RuntimeError(
            f"Ollama is not reachable at {host}. Start Ollama and pull the embedding model: ollama pull {model}"
        ) from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError(f"Ollama timed out while embedding with model {model}.") from exc
    logger.info(f"Embedding complete — got {len(embeddings)} vectors of dim {len(embeddings[0])}")
    return embeddings
