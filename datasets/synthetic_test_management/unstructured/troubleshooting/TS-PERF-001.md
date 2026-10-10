---
document_id: TS-PERF-001
document_type: troubleshooting
title: Performance Degradation Troubleshooting Guide
application: GalaxySearch
topic: application performance
---

# Performance Degradation Troubleshooting Guide

**Application:** GalaxySearch
**Topic:** Application Performance

---

## 1. Symptoms

The following symptoms indicate a **application performance** failure:

- `p95 latency exceeds 500ms SLA`
- `ANR detected in main thread`
- `Memory usage exceeds 256MB ceiling`

## 2. Diagnostic Steps

1. Profile the application using the built-in performance monitor.
2. Check for synchronous network calls on the main UI thread.
3. Review recent code changes for new blocking operations.
4. Increase available heap if memory ceiling is hit consistently.
5. Reduce the search index rebuild interval to off-peak hours.
6. Enable query caching to reduce repeat index lookups.

## 3. When to Escalate

Escalate to the GalaxySearch platform team if:

- The issue recurs across more than 3 consecutive regression cycles.
- More than 10% of test executions in a run exhibit this failure type.
- The root cause cannot be reproduced in an isolated test environment.

## 4. Related Failure Reports

Search `failure_logs/` for documents where `failure_type` matches the symptom pattern above.

## 5. Related Defects

Known defects related to this issue are tracked in `defect_reports/`.
Filter by `component` matching the affected service.

## 6. Prevention

- Add automated monitoring for this failure pattern to the CI pipeline.
- Include a dedicated test case in the smoke suite to catch regressions early.
- Review the root cause cluster in `historical_failures.csv` for recurring patterns.

---
*This document is synthetic and created for AI/RAG research purposes only.*
