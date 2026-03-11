"""Ollama REST client — chat completions and embeddings via local Qwen."""

import logging
from typing import Iterator

import httpx

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, base_url: str, chat_model: str, embed_model: str, temperature: float = 0.1) -> None:
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.embed_model = embed_model
        self.temperature = temperature
        self._http = httpx.Client(timeout=120.0)

    def chat(self, prompt: str, system: str | None = None) -> str:
        """Single-turn chat completion. Returns full response string."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._http.post(
            f"{self.base_url}/api/chat",
            json={"model": self.chat_model, "messages": messages, "stream": False,
                  "options": {"temperature": self.temperature}},
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    def chat_stream(self, prompt: str, system: str | None = None) -> Iterator[str]:
        """Streaming chat — yields token strings as they arrive."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        with self._http.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json={"model": self.chat_model, "messages": messages, "stream": True,
                  "options": {"temperature": self.temperature}},
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if not data.get("done"):
                        yield data.get("message", {}).get("content", "")

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts. Returns list of float vectors."""
        embeddings: list[list[float]] = []
        for text in texts:
            response = self._http.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.embed_model, "prompt": text},
            )
            response.raise_for_status()
            embeddings.append(response.json()["embedding"])
        logger.debug("Embedded %d texts with model %s", len(texts), self.embed_model)
        return embeddings

    def is_healthy(self) -> bool:
        """Check if Ollama is running and the chat model is available."""
        try:
            resp = self._http.get(f"{self.base_url}/api/tags")
            models = [m["name"] for m in resp.json().get("models", [])]
            return any(self.chat_model in m for m in models)
        except Exception:
            return False

    def close(self) -> None:
        self._http.close()


def make_ollama_client(
    base_url: str = "http://localhost:11434",
    chat_model: str = "qwen2.5:7b",
    embed_model: str = "nomic-embed-text",
    temperature: float = 0.1,
) -> OllamaClient:
    return OllamaClient(base_url=base_url, chat_model=chat_model, embed_model=embed_model, temperature=temperature)
