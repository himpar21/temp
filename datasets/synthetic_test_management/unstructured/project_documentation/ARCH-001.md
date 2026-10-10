# System Architecture Overview

## Purpose

This document describes the high-level architecture of the AI-Powered Test
Management System using Hybrid RAG Pipelines.

## Components

### 1. Data Ingestion Layer
- Accepts structured test data (CSV) and unstructured documents (Markdown/PDF).
- Parses and chunks documents into overlapping text segments.
- Generates dense vector embeddings using a sentence-transformer model.

### 2. Vector Database
- Stores chunk embeddings alongside metadata (document_id, source entity IDs).
- Supports approximate nearest-neighbour (ANN) search for semantic retrieval.

### 3. Knowledge Graph
- Nodes: Application, Requirement, TestCase, Execution, Failure, Defect, Engineer, Environment.
- Edges: IMPLEMENTS, HAS_EXECUTION, PRODUCED, LINKED_TO, AFFECTS, ASSIGNED_TO, etc.
- Supports multi-hop traversal for traceability queries.

### 4. Hybrid RAG Pipeline
- **Vanilla RAG path:** Embeds the query → ANN search → retrieve top-k chunks → LLM answer.
- **Graph RAG path:** Entity extraction → graph traversal → subgraph context → LLM answer.
- **Hybrid path:** Runs both paths, merges context, scores evidence, generates answer.

### 5. LLM Layer
- Receives merged context from the Hybrid RAG pipeline.
- Generates natural-language insights about test execution, failures, and defects.

## Data Flow

```
Structured CSV ──► PostgreSQL ──► Graph Builder ──► Neo4j
Unstructured MD ──► Chunker ──► Embedder ──► Qdrant (Vector DB)
                                         ↓
User Query ──► Query Router ──► [Vanilla RAG | Graph RAG | Hybrid RAG]
                                         ↓
                                   LLM (Gemini / GPT)
                                         ↓
                              Test Execution Insights
```

*This document is synthetic and created for AI/RAG research purposes only.*
