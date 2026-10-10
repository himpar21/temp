"""Query request schemas."""

import re

from pydantic import BaseModel, Field, field_validator



class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("question must not be empty")
        return normalized

class VanillaRAGQuery(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("Query must contain at least two non-whitespace characters")
        if not re.search(r"[a-zA-Z0-9]", normalized):
            raise ValueError("Query must contain searchable letters or numbers")
        return normalized


class HybridRAGPlanQuery(VanillaRAGQuery):
    pass


class GraphRAGQuery(VanillaRAGQuery):
    top_k: int = Field(default=5, ge=1, le=20)
    max_hops: int = Field(default=4, ge=1, le=6)
