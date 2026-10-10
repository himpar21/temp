"""Hybrid RAG relevance-threshold evaluation."""

from dataclasses import dataclass
import os


def _configured_threshold(name: str, default: str) -> float:
    raw = os.getenv(name, default)
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number between 0 and 1") from exc
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")
    return value


DEFAULT_RELEVANCE_THRESHOLD = _configured_threshold("RAG_RELEVANCE_THRESHOLD", "0.85")
DEFAULT_FALLBACK_THRESHOLD = _configured_threshold(
    "RAG_VANILLA_FALLBACK_THRESHOLD", "0.30"
)


@dataclass(frozen=True)
class ThresholdEvaluation:
    """Result of comparing the Vanilla RAG score with the planner threshold."""

    score: float
    threshold: float
    threshold_met: bool


def evaluate_relevance(
    score: float,
    threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
) -> ThresholdEvaluation:
    """Accept Vanilla RAG when its relevance score meets the threshold."""

    if not 0.0 <= score <= 1.0:
        raise ValueError("Relevance score must be between 0 and 1")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("Relevance threshold must be between 0 and 1")

    return ThresholdEvaluation(
        score=score,
        threshold=threshold,
        threshold_met=score >= threshold,
    )
