"""Prompt construction for the Hybrid RAG pipeline.

Builds structured prompts from retrieved context (vanilla RAG chunks,
graph RAG subgraph, or both) and the user's query.

The prompts are designed for Qwen but are compatible with any
instruction-tuned chat model.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ContextSource(str, Enum):
    VANILLA = "vanilla"
    GRAPH   = "graph"
    HYBRID  = "hybrid"


# ── system prompt ─────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are an expert AI assistant for a Samsung software Quality Assurance platform.
You help QA engineers, test leads, and developers understand test execution results, failure patterns, \
defect traceability, and requirement coverage.

Guidelines:
- Answer only from the provided context. Do not hallucinate facts.
- Treat every cause, resolution, status, date, and recommendation as unknown unless it is explicitly stated in the context.
- Never replace "pending", "under investigation", or another unresolved state with a proposed or completed fix.
- Do not invent likely explanations, remediation steps, placeholder fields, or recommendations.
- If the context is insufficient to answer confidently, say so clearly.
- Be concise but complete. Use bullet points for lists of findings.
- When referencing specific entities (REQ-xxxx, TC-xxxx, BUG-xxxx, FAIL-xxxx), always include their ID.
- Format your answer in plain text suitable for a web UI — avoid markdown headers.
- For entity questions, use the exact fields present in the context as clearly labeled bullet points, not one dense paragraph.
- Combine sections for the same entity and preserve reproduction steps, root cause, resolution, and traceability details.
- If the question involves traceability, trace the chain explicitly: Requirement → Test Case → Execution → Failure → Defect.
"""

# ── context block templates ───────────────────────────────────────────────────
_VANILLA_CONTEXT_HEADER = "=== Retrieved Documents (Semantic Search) ==="
_GRAPH_CONTEXT_HEADER   = "=== Retrieved Graph Paths (Knowledge Graph) ==="
_SEPARATOR = "-" * 60


@dataclass(frozen=True)
class BuiltPrompt:
    """Container returned by PromptManager.build()."""
    system: str
    user: str
    context_source: ContextSource
    context_length_chars: int

    def to_messages(self) -> list[dict[str, str]]:
        """Convert to OpenAI-style messages list."""
        return [
            {"role": "system", "content": self.system},
            {"role": "user",   "content": self.user},
        ]


class PromptManager:
    """Build LLM prompts from RAG context and user queries."""

    def __init__(self, max_context_chars: int = 6000) -> None:
        # Hard limit prevents prompt + context exceeding model context window.
        # Qwen-plus has a 32k context window; 6000 chars is safe for most cases.
        self.max_context_chars = max_context_chars

    # ------------------------------------------------------------------
    def build(
        self,
        query: str,
        *,
        vanilla_context: str | None = None,
        graph_context: str | None = None,
    ) -> BuiltPrompt:
        """Build a full prompt from query + available context.

        At least one of vanilla_context or graph_context must be provided.
        When both are provided the prompt uses HYBRID mode.
        """
        if not vanilla_context and not graph_context:
            raise ValueError("At least one context source must be provided.")

        sections: list[str] = []

        if vanilla_context and graph_context:
            source = ContextSource.HYBRID
            sections.append(_VANILLA_CONTEXT_HEADER)
            sections.append(self._trim(vanilla_context, self.max_context_chars // 2))
            sections.append(_SEPARATOR)
            sections.append(_GRAPH_CONTEXT_HEADER)
            sections.append(self._trim(graph_context, self.max_context_chars // 2))
        elif vanilla_context:
            source = ContextSource.VANILLA
            sections.append(_VANILLA_CONTEXT_HEADER)
            sections.append(self._trim(vanilla_context, self.max_context_chars))
        else:
            source = ContextSource.GRAPH
            sections.append(_GRAPH_CONTEXT_HEADER)
            sections.append(self._trim(graph_context, self.max_context_chars))  # type: ignore[arg-type]

        context_block = "\n".join(sections)
        user_message  = (
            f"{context_block}\n\n"
            f"{_SEPARATOR}\n"
            f"Question: {query}\n\n"
            f"Answer based only on the context above:"
        )

        return BuiltPrompt(
            system=_SYSTEM_PROMPT,
            user=user_message,
            context_source=source,
            context_length_chars=len(context_block),
        )

    # ------------------------------------------------------------------
    def build_no_context(self, query: str) -> BuiltPrompt:
        """Prompt used when retrieval found nothing relevant."""
        user_message = (
            "No relevant documents or graph paths were found in the knowledge base "
            f"for the following question:\n\n{query}\n\n"
            "Please inform the user that there is insufficient evidence to answer "
            "this question from the current dataset."
        )
        return BuiltPrompt(
            system=_SYSTEM_PROMPT,
            user=user_message,
            context_source=ContextSource.VANILLA,
            context_length_chars=0,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _trim(text: str, max_chars: int) -> str:
        """Trim context to fit within the character budget."""
        if len(text) <= max_chars:
            return text
        trimmed = text[:max_chars].rstrip()
        return trimmed + "\n[... context trimmed to fit model window ...]"
