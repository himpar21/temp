"""LLM response generation for the Hybrid RAG pipeline.

Orchestrates:
    PromptManager  — builds the structured prompt
    QwenClient     — calls the Qwen API
    (optionally)   — post-processes / validates the response

Usage:
    from ai_engine.llm.response_generator import ResponseGenerator

    generator = ResponseGenerator()

    # From vanilla RAG context
    answer = generator.generate(
        query="Why did TC-0042 fail?",
        vanilla_context=vanilla_result.retrieved_context,
    )

    # From graph RAG context
    answer = generator.generate(
        query="Which requirements are affected by BUG-0031?",
        graph_context=graph_result.graph_context,
    )

    # From both (hybrid)
    answer = generator.generate(
        query="...",
        vanilla_context="...",
        graph_context="...",
    )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ai_engine.llm.llm_client import LLMError, OllamaClient, get_llm_client
from ai_engine.llm.prompt_manager import BuiltPrompt, ContextSource, PromptManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeneratedResponse:
    """Full response package returned by ResponseGenerator."""
    answer: str
    context_source: ContextSource
    context_length_chars: int
    model: str
    prompt_tokens_estimate: int   # rough estimate: chars / 4


class ResponseGenerator:
    """Generate a natural-language answer from RAG context using Ollama/Qwen."""

    def __init__(
        self,
        llm_client: OllamaClient | None = None,
        prompt_manager: PromptManager | None = None,
    ) -> None:
        self._client  = llm_client     or get_llm_client()
        self._prompts = prompt_manager or PromptManager()

    # ------------------------------------------------------------------
    def generate(
        self,
        query: str,
        *,
        vanilla_context: str | None = None,
        graph_context: str | None = None,
    ) -> GeneratedResponse:
        """Generate an answer from the provided context.

        Args:
            query:           The user's natural-language question.
            vanilla_context: Context from Vanilla RAG retrieval (optional).
            graph_context:   Context from Graph RAG traversal (optional).

        Returns:
            GeneratedResponse with the answer text and metadata.
        """
        if not vanilla_context and not graph_context:
            prompt = self._prompts.build_no_context(query)
        else:
            prompt = self._prompts.build(
                query,
                vanilla_context=vanilla_context,
                graph_context=graph_context,
            )

        answer = self._call_llm(prompt)

        return GeneratedResponse(
            answer=answer,
            context_source=prompt.context_source,
            context_length_chars=prompt.context_length_chars,
            model=self._client.model,
            prompt_tokens_estimate=len(prompt.user) // 4,
        )

    # ------------------------------------------------------------------
    def _call_llm(self, prompt: BuiltPrompt) -> str:
        """Call the LLM and return the answer, with graceful fallback."""
        try:
            return self._client.generate(prompt.to_messages())
        except LLMError as exc:
            logger.error(
                "LLM call failed — model=%s base_url=%s error=%s",
                self._client.model,
                self._client.base_url,
                exc,
            )
            return (
                f"[LLM unavailable: {exc}] "
                "Make sure Ollama is running and reachable from the backend."
            )


# ── module-level singleton ────────────────────────────────────────────────────
_generator: ResponseGenerator | None = None


def get_response_generator() -> ResponseGenerator:
    """Return a module-level singleton ResponseGenerator.

    Used as a FastAPI dependency.
    """
    global _generator
    if _generator is None:
        _generator = ResponseGenerator()
    return _generator
