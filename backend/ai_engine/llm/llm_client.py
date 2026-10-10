"""Ollama LLM client using httpx against the local OpenAI-compatible API.

Ollama exposes an OpenAI-compatible endpoint at http://localhost:11434/v1
No API key is required — Ollama runs entirely locally.

Environment variables (all optional — defaults work out of the box):
    OLLAMA_BASE_URL   — Ollama server URL   (default: http://localhost:11434)
    OLLAMA_MODEL      — model name          (default: qwen2.5-coder:1.5b)
    OLLAMA_TIMEOUT    — request timeout s   (default: 120)
    OLLAMA_MAX_TOKENS — max response tokens (default: 1024)
    OLLAMA_TEMPERATURE— sampling temp       (default: 0.2)
"""

from __future__ import annotations

import os
from typing import Any

import httpx

# ── defaults ──────────────────────────────────────────────────────────────────
_DEFAULT_BASE_URL    = "http://localhost:11434"
_DEFAULT_MODEL       = "qwen2.5-coder:1.5b"   # fits in 4 GB VRAM, fast
_DEFAULT_TIMEOUT     = 120
_DEFAULT_MAX_TOKENS  = 1024
_DEFAULT_TEMPERATURE = 0.2


class LLMError(RuntimeError):
    """Raised when the LLM call fails."""


class OllamaClient:
    """Thin httpx wrapper around the Ollama OpenAI-compatible endpoint."""

    def __init__(
        self,
        *,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> None:
        raw_base         = base_url or os.getenv("OLLAMA_BASE_URL", _DEFAULT_BASE_URL)
        self.base_url    = raw_base.rstrip("/") + "/v1"
        self.model       = model       or os.getenv("OLLAMA_MODEL",       _DEFAULT_MODEL)
        self.max_tokens  = max_tokens  or int(os.getenv("OLLAMA_MAX_TOKENS",  str(_DEFAULT_MAX_TOKENS)))
        self.temperature = temperature or float(os.getenv("OLLAMA_TEMPERATURE", str(_DEFAULT_TEMPERATURE)))
        self.timeout     = timeout     or int(os.getenv("OLLAMA_TIMEOUT",      str(_DEFAULT_TIMEOUT)))

    # ------------------------------------------------------------------
    def generate(self, messages: list[dict[str, str]]) -> str:
        """Send a messages list and return the assistant reply text.

        Args:
            messages: OpenAI-style messages e.g.
                [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

        Returns:
            Assistant reply as a plain string.

        Raises:
            LLMError: if the Ollama call fails.
        """
        payload: dict[str, Any] = {
            "model":       self.model,
            "messages":    messages,
            "max_tokens":  self.max_tokens,
            "temperature": self.temperature,
            "stream":      False,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                )
                response.raise_for_status()
                data    = response.json()
                content = data["choices"][0]["message"]["content"]
                if not content:
                    raise LLMError("Ollama returned an empty response.")
                return content.strip()
        except httpx.TimeoutException as exc:
            raise LLMError(
                f"Ollama request timed out after {self.timeout}s. "
                "Try a smaller model or increase OLLAMA_TIMEOUT."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise LLMError(
                f"Ollama returned HTTP {exc.response.status_code}: {exc.response.text[:200]}"
            ) from exc
        except (httpx.RequestError, KeyError, IndexError) as exc:
            raise LLMError(
                f"Ollama call failed: {exc}. "
                "Make sure Ollama is running (`ollama serve`) and "
                f"model '{self.model}' is available (`ollama pull {self.model}`)."
            ) from exc

    # ------------------------------------------------------------------
    def generate_simple(self, prompt: str) -> str:
        """Convenience wrapper for a single user-turn prompt."""
        return self.generate([{"role": "user", "content": prompt}])


# ── module-level singleton (lazy-initialized) ─────────────────────────────────
_instance: OllamaClient | None = None


def get_llm_client() -> OllamaClient:
    """Return a module-level singleton OllamaClient.

    Used as a FastAPI dependency or called directly from services.
    """
    global _instance
    if _instance is None:
        _instance = OllamaClient()
    return _instance
