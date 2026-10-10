# PDF Input Evaluation Metrics

## 1. Input Mode Distribution

| Mode | Count | Purpose |
|------|-------|---------|
| LINE_ONLY | 100 | Baseline text-only retrieval |
| PDF_ONLY | 50 | Pure document extraction/understanding |
| LINE_PLUS_PDF | 150 | Combined semantic + graph retrieval |
| **Total** | **300** | |

## 2. Retrieval Mode Distribution

| Mode | Description |
|------|-------------|
| SEMANTIC | Vector similarity over chunked text |
| GRAPH | Knowledge-graph traversal |
| HYBRID | Both semantic + graph evidence combined |

## 3. Metrics per Mode

### LINE_ONLY
| Metric | Target |
|--------|--------|
| Answer Accuracy | >= 0.80 |
| Entity Recall | >= 0.75 |
| ROUGE-L | >= 0.40 |
| BERTScore F1 | >= 0.78 |

### PDF_ONLY
| Metric | Target |
|--------|--------|
| Entity Extraction Recall | >= 0.85 |
| Entity Extraction Precision | >= 0.80 |
| Fact Coverage | >= 0.75 |
| Relationship Extraction F1 | >= 0.70 |

### LINE_PLUS_PDF (Hybrid)
| Metric | Target |
|--------|--------|
| Answer Accuracy | >= 0.82 |
| Entity Recall | >= 0.80 |
| Graph Path Accuracy | >= 0.72 |
| Evidence Integration | >= 0.78 |
| Faithfulness (no hallucination) | >= 0.88 |
| Multi-hop Path Completion | >= 0.68 |

## 4. Query Type Coverage

| Query Type | Mode | Notes |
|-----------|------|-------|
| semantic | LINE, LINE+PDF | Semantic document retrieval |
| test_case_lookup | LINE | Graph + structured lookup |
| requirement_lookup | LINE | Graph traversal |
| failure_lookup | LINE | Structured + semantic |
| defect_lookup | LINE | Structured lookup |
| historical_failure | LINE | Historical pattern matching |
| execution_analysis | LINE | Aggregation over structured data |
| traceability | LINE | Multi-hop graph paths |
| multi_hop_graph | LINE | Deep graph traversal |
| extraction | PDF_ONLY | Entity extraction from PDF |
| hybrid | LINE+PDF | Full pipeline required |

## 5. Evaluation Procedure

1. Run the pipeline against `evaluation/pdf_input_evaluation/questions.jsonl`.
2. For LINE_PLUS_PDF, provide both the question and the referenced PDF.
3. Compare outputs to `ground_truth.jsonl`.
4. Compute per-mode and aggregate metrics.
5. Flag any answer with faithfulness < 0.6 for manual review.

---
*This document is synthetic and intended for AI/RAG research purposes only.*
