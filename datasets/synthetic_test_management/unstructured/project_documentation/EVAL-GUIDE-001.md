# Hybrid RAG Evaluation Guide

## Purpose

This guide describes how to evaluate the retrieval quality and answer quality
of the Hybrid RAG pipeline using the provided evaluation dataset.

## Evaluation Dataset Structure

- `evaluation/questions.jsonl` — 300 queries (semantic, graph, hybrid)
- `evaluation/ground_truth.jsonl` — expected answers keyed by query_id
- `evaluation/expected_entities.jsonl` — entities that must be retrieved
- `evaluation/expected_relationships.jsonl` — graph paths that must be traversed

## Metrics

### Retrieval Metrics (Vanilla RAG)
- **Recall@k** — fraction of expected documents retrieved in top-k results.
- **Precision@k** — fraction of retrieved documents that are relevant.
- **MRR** — Mean Reciprocal Rank of the first relevant document.
- **NDCG** — Normalised Discounted Cumulative Gain.

### Graph Retrieval Metrics (Graph RAG)
- **Entity Recall** — fraction of expected entities found in the subgraph context.
- **Relationship Recall** — fraction of expected relationships traversed.
- **Path Accuracy** — whether the correct multi-hop path was followed.

### Answer Quality Metrics (LLM)
- **ROUGE-L** — longest common subsequence overlap with reference answer.
- **BERTScore** — semantic similarity between generated and reference answer.
- **Faithfulness** — whether the answer is grounded in the retrieved context.
- **Completeness** — whether the answer addresses all aspects of the question.

## Running an Evaluation

```python
from evaluation import HybridRAGEvaluator
evaluator = HybridRAGEvaluator(pipeline=hybrid_rag_pipeline)
results = evaluator.run(questions_path="evaluation/questions.jsonl",
                        ground_truth_path="evaluation/ground_truth.jsonl")
evaluator.report(results)
```

*This document is synthetic and created for AI/RAG research purposes only.*
