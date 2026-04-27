from typing import List

import httpx


def embed_texts(texts: List[str], model: str, host: str = "http://localhost:11434") -> List[List[float]]:
    embeddings = []
    with httpx.Client(timeout=60.0) as client:
        for text in texts:
            response = client.post(
                f"{host}/api/embeddings",
                json={"model": model, "prompt": text},
            )
            response.raise_for_status()
            embeddings.append(response.json()["embedding"])
    return embeddings
