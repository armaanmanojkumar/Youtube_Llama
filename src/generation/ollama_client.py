import json
from typing import Iterator, List

import httpx


def chat(
    messages: list,
    model: str,
    host: str = "http://localhost:11434",
    temperature: float = 0.2,
) -> str:
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{host}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "think": False,
                    "options": {"temperature": temperature},
                },
            )
            if not response.is_success:
                raise RuntimeError(f"Ollama chat error {response.status_code}: {response.text}")
            return response.json()["message"]["content"]
    except httpx.ConnectError as exc:
        raise RuntimeError(f"Ollama is not reachable at {host}. Start Ollama and pull the chat model: ollama pull {model}") from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError(f"Ollama timed out while generating with model {model}.") from exc


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
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{host}/api/embeddings",
                json={"model": model, "prompt": text},
            )
            if not response.is_success:
                raise RuntimeError(f"Ollama embedding error {response.status_code}: {response.text}")
            return response.json()["embedding"]
    except httpx.ConnectError as exc:
        raise RuntimeError(f"Ollama is not reachable at {host}. Start Ollama and pull the embedding model: ollama pull {model}") from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError(f"Ollama timed out while embedding with model {model}.") from exc
