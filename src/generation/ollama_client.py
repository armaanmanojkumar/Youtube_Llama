import json
from typing import Iterator, List

import httpx


def chat(
    messages: list,
    model: str,
    host: str = "http://localhost:11434",
    temperature: float = 0.2,
) -> str:
    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            f"{host}/api/chat",
            json={"model": model, "messages": messages, "stream": False, "options": {"temperature": temperature}},
        )
        response.raise_for_status()
        return response.json()["message"]["content"]


def chat_stream(
    messages: list,
    model: str,
    host: str = "http://localhost:11434",
    temperature: float = 0.2,
) -> Iterator[str]:
    with httpx.Client(timeout=120.0) as client:
        with client.stream(
            "POST",
            f"{host}/api/chat",
            json={"model": model, "messages": messages, "stream": True, "options": {"temperature": temperature}},
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if not data.get("done"):
                        yield data["message"]["content"]


def embed(text: str, model: str, host: str = "http://localhost:11434") -> List[float]:
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            f"{host}/api/embeddings",
            json={"model": model, "prompt": text},
        )
        response.raise_for_status()
        return response.json()["embedding"]
