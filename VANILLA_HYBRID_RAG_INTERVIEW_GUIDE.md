# Easy Interview Guide: Vanilla Hybrid RAG

This guide explains only the repository’s non-graph RAG pipeline. Here, “hybrid” means that retrieval uses semantic similarity together with simple keyword coverage and exact artifact-ID matching. It does not use BM25.

Labels:

- **[MUST REVISE]** — the 15 most important questions.
- **[SCENARIO]** — the 5 situation-based questions.

## Two-minute project explanation

“During my Samsung PRISM AI/ML research internship, I have been contributing to an AI-powered test-management project. The aim is to help testers find useful information from test cases, requirements, execution reports, failure logs, and defect reports.

The system first accepts files such as CSV, JSON, Markdown, PDF, Excel, Word, text, and images. The backend cleans the data, removes exact duplicates, extracts IDs such as test-case or defect IDs, and divides long documents into smaller chunks. PostgreSQL stores the documents, chunks, structured records, and ingestion status.

For retrieval, the project uses the local `nomic-embed-text` model through Ollama. It converts each chunk into a 768-dimensional embedding and stores it in Qdrant. When a user asks a question, the same model converts the question into an embedding. Qdrant finds semantically similar chunks.

The system then improves the ranking by combining 85% semantic similarity with 15% keyword coverage. It also gives extra importance to an exact ID mentioned in the question, such as `BUG-0026`. This is the vanilla hybrid part of the pipeline: it combines semantic, keyword, and ID-based signals.

Finally, the best chunks are sent to the local `qwen2.5-coder:1.5b` model. The prompt tells the model to answer only from the retrieved information and to say when the evidence is insufficient. FastAPI provides the backend APIs, and the frontend is built with React and TypeScript. The repository currently uses synthetic test-management data, so it should be described as a research prototype rather than a finished production system.”

## 1. Project Basics & Workflow

### 1. **[MUST REVISE] What does this project do?**

It helps testers find useful information from test cases, failures, reports, requirements, and defects. It then uses that information to generate a clear answer.

### 2. Why was this project created?

Testing data can be spread across many files. The project makes it easier to search and understand that data.

### 3. **[MUST REVISE] What is RAG?**

RAG means Retrieval-Augmented Generation. It first finds relevant information and then gives it to an AI model to generate an answer.

### 4. What does “vanilla hybrid RAG” mean in this project?

It combines semantic search with keyword matching and exact artifact-ID matching. It does not use a graph database in this interview guide.

### 5. **[MUST REVISE] Explain the complete workflow.**

A file is uploaded, cleaned, divided into chunks, embedded, and stored. A question is then embedded, relevant chunks are retrieved and reranked, and the language model creates an answer from those chunks.

### 6. What type of testing data is used?

The repository contains synthetic requirements, test cases, executions, failure logs, reports, test plans, and defects.

### 7. Which files can users upload?

The backend supports CSV, JSON, JSONL, Markdown, text, PDF, Excel, Word, PNG, JPG, and JPEG files.

### 8. What happens when a file is uploaded?

The backend checks the file, cleans its content, extracts metadata and IDs, creates chunks, saves the data, and indexes the chunks for search.

### 9. How does the system find duplicate files?

It creates a SHA-256 hash of the file. If the same hash already exists, the file is treated as an exact duplicate.

### 10. What happens if vector indexing fails?

The document and chunks remain saved in PostgreSQL. The job is marked `PARTIAL`, and indexing can be tried again later.

### 11. Which API is used for vanilla RAG questions?

The client sends a `POST` request to `/api/v1/rag/query` with the question and the number of results required.

### 12. What does the query API return?

It returns the answer, relevant chunks, scores, generated context, embedding details, and retrieval time.

### 13. Does the project have login support?

Yes. Protected routes require a valid login session stored in an HTTP-only cookie.

### 14. Is the complete frontend connected to the backend?

No. Upload, query, and uploaded-document pages use backend APIs, but some other pages still use local mock data.

### 15. **[SCENARIO] What would you show in a simple project demo?**

I would upload a test document, show its ingestion result, ask a question, and explain the retrieved chunks and generated answer.

### 16. How should you describe your contribution?

I contributed to retrieval pipelines, data preparation, API integration, solution design, and validation. I would not claim that I built every part alone.

## 2. Technologies & Core Concepts

### 17. **[MUST REVISE] Which main technologies are used?**

The project uses Python, FastAPI, PostgreSQL, Qdrant, Ollama, React, TypeScript, Vite, Tailwind CSS, and Docker Compose.

### 18. Why is FastAPI used?

FastAPI makes it easy to build typed REST APIs with request validation and automatic API documentation.

### 19. **[MUST REVISE] What is an embedding?**

An embedding is a numerical representation of text. Text with a similar meaning usually has similar embeddings.

### 20. Which embedding model is used?

The code uses Ollama’s `nomic-embed-text` model.

### 21. What is the embedding size?

Each embedding contains 768 numbers, so its dimension is 768.

### 22. **[MUST REVISE] What is cosine similarity?**

It compares two vectors. A higher score means the query and document are more similar in meaning.

### 23. Why must queries and documents use the same embedding model?

They must be placed in the same vector space. Otherwise, their similarity scores would not be meaningful.

### 24. What does Qdrant do?

Qdrant stores embeddings and quickly finds chunks whose vectors are similar to the query vector.

### 25. **[MUST REVISE] How is the final retrieval score calculated?**

The code uses 85% semantic similarity and 15% keyword coverage. An exact artifact-ID match can add a bonus of 0.25, with a maximum score of 1.

### 26. What is keyword coverage?

It measures how many important words from the question also appear in a chunk.

### 27. Does this project use BM25?

No. It uses simple keyword coverage together with vector similarity and ID matching.

### 28. What is artifact-ID matching?

It checks for IDs such as `BUG-0026`, `REQ-0345`, or `TC-0001` and gives matching chunks more importance.

### 29. Why are common words ignored?

Words such as “the” and “is” do not add much meaning. Ignoring them makes keyword matching more useful.

### 30. What is chunking?

Chunking means splitting a long document into smaller parts for easier search and processing.

### 31. Why do chunks overlap?

Overlap keeps information near chunk boundaries from being separated completely.

### 32. What is a grounded answer?

It is an answer based only on the retrieved evidence instead of unsupported model knowledge.

### 33. Why is Ollama used?

Ollama runs the embedding and language models locally, so the project does not require an external AI API.

### 34. **[SCENARIO] What if the question uses different words from the document?**

Semantic embeddings can still match similar meanings even when the exact words are different.

## 3. Architecture & System Design

### 35. **[MUST REVISE] Explain the system architecture.**

The React frontend calls the FastAPI backend. PostgreSQL stores source data, Qdrant stores vectors, and Ollama creates embeddings and answers.

### 36. Why are PostgreSQL and Qdrant both needed?

PostgreSQL stores documents and job information. Qdrant is designed for fast vector similarity search.

### 37. What information is stored in Qdrant?

It stores a chunk’s vector, text, document ID, filename, entity IDs, and other metadata.

### 38. How is the Qdrant collection configured?

The default collection is `test_management_chunks`. It uses 768-dimensional vectors and cosine distance.

### 39. Why are Qdrant point IDs deterministic?

The same document chunk gets the same point ID during re-indexing. This helps prevent duplicate vector entries.

### 40. **[MUST REVISE] What happens when the user asks a question?**

The system cleans and embeds the question, searches Qdrant, reranks the results, selects the best chunks, builds context, and sends it to the language model.

### 41. Why does the system retrieve extra candidates first?

It gives the reranker more choices before selecting the final top results.

### 42. How are repeated search results removed?

The code stores candidates in a dictionary using the Qdrant point ID as the key.

### 43. How is the final context created?

The backend joins the selected chunk text with its filename, score, and entity IDs.

### 44. How does the project limit context size?

The prompt manager keeps at most 6,000 context characters by default and trims extra text.

### 45. How does the backend call the language model?

It sends chat messages to Ollama’s `/v1/chat/completions` endpoint.

### 46. Which language model is used?

The default model is `qwen2.5-coder:1.5b`.

### 47. Why is the temperature set to 0.2?

A low temperature makes answers more stable and less creative, which is useful for factual QA.

### 48. What does an ingestion job store?

It stores the filename, hash, status, record counts, timestamps, and any error message.

### 49. What are the main ingestion statuses?

They include `PROCESSING`, `COMPLETED`, `PARTIAL`, `DUPLICATE`, and `FAILED`.

### 50. How does the frontend connect during development?

Vite runs the frontend on port 5173 and proxies `/api` requests to FastAPI on port 8000.

### 51. Which services are needed for this pipeline?

The pipeline uses FastAPI, PostgreSQL, Qdrant, and Ollama. Ollama runs on the host in the provided Docker setup.

## 4. Implementation & Code Explanation

### 52. How is a query checked before searching?

It must contain letters or numbers, have a valid length, and request between 1 and 10 results.

### 53. **[MUST REVISE] How does document chunking work?**

The code first separates text by headings. It then creates chunks of up to 350 words with a 50-word overlap.

### 54. How is a chunk ID created?

It combines the document ID, source type, and chunk number.

### 55. Why does each chunk have a hash?

The hash gives the chunk a content fingerprint that can help with checking changes or duplicates.

### 56. How is text cleaned?

The code fixes some encoding problems, removes null characters, normalizes Unicode and line endings, and removes extra blank lines.

### 57. **[MUST REVISE] How are artifact IDs found?**

A regular expression searches the document text and metadata for known patterns such as `REQ-`, `TC-`, `FAIL-`, and `BUG-`.

### 58. How is Markdown metadata read?

The parser reads simple metadata written between `---` lines at the start of a Markdown file.

### 59. How are PDF files read?

The project uses `pypdf` to extract text from PDFs. The upload stack also includes Tesseract support for image OCR.

### 60. How are CSV and Excel files handled?

Their rows are cleaned and stored as structured records. Their content is also converted into text for retrieval.

### 61. **[SCENARIO] What happens if the same CSV is uploaded twice?**

The second file is detected using its hash. The existing document is reused, and the system checks that its vector index exists.

### 62. Can Qdrant search be filtered?

Yes. The wrapper can filter results by document ID or entity ID.

### 63. What does a Qdrant search result contain?

It contains an ID, score, chunk text, document ID, filename, entity IDs, and metadata.

### 64. **[MUST REVISE] Give a simple reranking example.**

If semantic similarity is 0.80 and keyword coverage is 0.60, the blended score is `0.85×0.80 + 0.15×0.60 = 0.77`.

### 65. What if a question contains an exact defect ID?

The retriever performs an extra search for that ID and boosts chunks containing it.

### 66. Is the query embedded more than once?

No. The query is embedded once, and the same vector is reused for searches.

### 67. What does `candidates_scanned` mean in the response?

It currently reports the total vector count in Qdrant. It is not the exact number checked internally during search.

### 68. How does the prompt reduce hallucinations?

It tells the model to use only the provided context and to say when information is missing.

### 69. What happens if no useful context is found?

The model is asked to tell the user that the current data does not contain enough evidence.

### 70. What happens if Ollama is unavailable?

The backend catches the error and returns a message explaining that the language model is unavailable.

### 71. Does the API stream the answer?

No. It waits for the complete answer and returns it in one response.

### 72. What is the difference between `/query` and `/rag/query`?

`/query` uses PostgreSQL text search. `/rag/query` uses embeddings, Qdrant, and reranking.

### 73. What happens if the frontend cannot reach the query backend?

For a network fetch failure, it can use bundled mock data and a simple local keyword scorer. This is only a frontend fallback.

## 5. Testing, Evaluation & Performance

### 74. What is tested in the vanilla retriever?

Tests cover result ranking, query cleaning, embedding reuse, context creation, empty queries, and invalid `top_k` values.

### 75. What is tested in the Qdrant wrapper?

The test checks the Qdrant method call and verifies that returned payload fields are mapped correctly.

### 76. **[MUST REVISE] What parts of ingestion are tested?**

Tests cover cleaning, ID extraction, heading-based chunks, duplicate CSV rows, Markdown metadata, encoding repair, and ignored benchmark folders.

### 77. Is failed indexing retry tested?

Yes. Tests check both a failed retry that stays `PARTIAL` and a successful retry that becomes `COMPLETED`.

### 78. Is exact artifact-ID extraction tested?

Yes. Tests check simple IDs and compound IDs such as `DR-BUG-0026`.

### 79. Which retrieval metrics are listed in the repository?

The evaluation document lists Recall@5, Precision@5, MRR, NDCG@10, and Hit Rate@1.

### 80. Has the project proved those target scores?

No. They are target values, and the metric implementation files are still empty placeholders.

### 81. Which answer-quality metrics are suggested?

The repository suggests ROUGE-L, BERTScore, faithfulness, completeness, and hallucination rate.

### 82. Which performance details does the API return?

It returns retrieval time, embedding model, embedding dimension, and the total Qdrant vector count.

### 83. **[MUST REVISE] How would you test retrieval quality?**

I would run known questions with expected documents and calculate metrics such as Recall@k, Precision@k, MRR, and NDCG.

### 84. How would you check answer faithfulness?

I would compare each answer with its retrieved chunks and mark any claim that is not supported by those chunks.

### 85. **[SCENARIO] Search becomes slow after adding more data. What would you check?**

I would separately measure embedding time, Qdrant search time, reranking time, and answer-generation time to find the slow stage.

### 86. Why do unit tests use fake models and databases?

Fakes make the tests fast and repeatable without requiring live Ollama or Qdrant services.

### 87. Did the selected tests run in the current local environment?

No. Test collection stopped because the local Python environment does not have the `qdrant_client` package installed.

### 88. How large is the synthetic dataset?

Its metadata lists 2,100 test cases, 5,200 test executions, 1,100 failures, 520 defects, 520 requirements, and 238 unstructured documents.

## 6. Challenges, Limitations & Improvements

### 89. What is the main data limitation?

The repository uses only synthetic data. Results on real company data may be different.

### 90. Is this a complete production-ready search system?

No. It is a research prototype and still needs full evaluation, scaling tests, and production hardening.

### 91. What is confusing about the returned scores?

After reranking, the API uses the blended score as both similarity and relevance. It should return raw cosine similarity and final relevance separately.

### 92. What is a limitation of embedding many chunks?

The code sends one embedding request at a time. Real batching or safe parallel requests would make ingestion faster.

### 93. What is a limitation of context trimming?

The code trims by character count, so it can cut a sentence or remove useful information.

### 94. **[MUST REVISE] What would you improve first?**

I would finish the evaluation code, separate raw and final scores, test better keyword retrieval, and clearly separate real backend data from frontend mocks.

### 95. How would you improve search quality?

I would test different chunk sizes, embedding models, score weights, metadata filters, and reranking methods using the same ground-truth questions.

### 96. **[SCENARIO] The system returns the wrong document for an exact ID. What would you do?**

I would check ID extraction and Qdrant metadata, strongly prioritize exact-ID results, and add a test for that ID format.

### 97. How would you make the system more reliable?

I would add health checks, retries, better logs, monitoring, and integration tests with the real services.

### 98. How would you improve security?

I would change development passwords, restrict CORS, scan uploaded files, add stronger access control, and avoid returning unnecessary sensitive data.

### 99. How would you support more data?

I would use background workers, batch embeddings, tune Qdrant, add caching, and load-test the system.

### 100. How would you describe the current project honestly?

It is a working research prototype with ingestion, storage, vector search, reranking, answer generation, APIs, and a frontend. It still needs complete evaluation and production-level testing.
