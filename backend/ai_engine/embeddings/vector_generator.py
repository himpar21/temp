"""Vector generation utilities."""

from ai_engine.embeddings.embedding_model import EmbeddingModel


def generate_embedding(text: str, model: EmbeddingModel | None = None) -> list[float]:
    """Generate one embedding with the supplied model or the local default."""

    return (model or EmbeddingModel()).embed(text)
