# Evaluation Metrics Reference

This document defines the metrics used to evaluate the Hybrid RAG pipeline
against the synthetic test-management dataset.

---

## 1. Retrieval Metrics (Vanilla RAG)

| Metric | Description | Target |
|--------|-------------|--------|
| Recall@5 | Fraction of relevant docs in top-5 results | ≥ 0.80 |
| Precision@5 | Fraction of top-5 results that are relevant | ≥ 0.70 |
| MRR | Mean Reciprocal Rank of first relevant document | ≥ 0.75 |
| NDCG@10 | Normalised Discounted Cumulative Gain at rank 10 | ≥ 0.72 |
| Hit Rate@1 | Fraction of queries where top-1 is relevant | ≥ 0.65 |

## 2. Graph Retrieval Metrics (Graph RAG)

| Metric | Description | Target |
|--------|-------------|--------|
| Entity Recall | Fraction of expected entities retrieved | ≥ 0.85 |
| Relationship Recall | Fraction of expected relationships traversed | ≥ 0.80 |
| Path Accuracy | Whether the correct multi-hop path was followed | ≥ 0.75 |
| Node Precision | Fraction of retrieved nodes that are expected | ≥ 0.70 |

## 3. Answer Quality Metrics (LLM)

| Metric | Description | Target |
|--------|-------------|--------|
| ROUGE-L | Longest common subsequence overlap with reference | ≥ 0.45 |
| BERTScore F1 | Semantic similarity to reference answer | ≥ 0.80 |
| Faithfulness | Answer grounded in retrieved context (0–1) | ≥ 0.85 |
| Completeness | All required aspects addressed (0–1) | ≥ 0.75 |
| Hallucination Rate | Fraction of answers with unsupported claims | ≤ 0.10 |

## 4. Hybrid RAG Specific Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Evidence Integration | Both graph + document evidence used | ≥ 0.80 |
| Multi-hop Accuracy | Correct traversal of ≥2 relationship hops | ≥ 0.70 |
| Traceability Completeness | Full requirement→defect chain recovered | ≥ 0.75 |
| Context Relevance | Retrieved context relevant to query | ≥ 0.82 |

## 5. Query Type Distribution

| Type | Count | Purpose |
|------|-------|---------|
| Semantic | 100 | Tests pure vector retrieval quality |
| Graph | 100 | Tests knowledge-graph traversal accuracy |
| Hybrid | 100 | Tests combined retrieval and reasoning |
| **Total** | **300** | |

## 6. Scoring Procedure

1. Run the RAG pipeline against `questions.jsonl`.
2. Compare generated answers to `ground_truth.jsonl`.
3. Compute all metrics above using the evaluation harness.
4. Report per-query-type and aggregate scores.
5. Flag any query where faithfulness < 0.6 for manual review.

## 7. Baseline Targets

A pipeline scoring below the targets in section 1–4 should be considered
under-optimised and requires further tuning of:
- Chunk size and overlap parameters.
- Embedding model selection.
- Graph traversal depth limit.
- LLM prompt template for context integration.

---
*This document is synthetic and created for AI/RAG research purposes only.*
