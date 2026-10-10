---
document_id: DR-BUG-0245
document_type: defect_report
title: Defect Report — BUG-0245
application: SmartHome
defect_id: BUG-0245
related_failure: FAIL-0959
related_test_case: TC-1316
affected_requirement: REQ-0480
severity: Major
priority: Critical
status: CLOSED
reported_date: 2023-05-10
---

# Defect Report
## BUG-0245 — Performance Degradation in Notification Handler: PerformanceViolation: p95 laten

**Application:** SmartHome
**Component:** Notification Handler
**Severity:** Major
**Priority:** Critical
**Status:** CLOSED
**Reported:** 2023-05-10
**Resolved:** 2023-06-20
**Assigned To:** ENG-029

---

## 1. Problem Description

During execution EXEC-05123, test case TC-1316 failed with Performance Degradation. The system exhibited performance degradation when Bluetooth interference is present.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0959 |
| Test Case | TC-1316 |
| Affected Requirement | REQ-0480 |

## 3. Steps to Reproduce

1. Execute test case `TC-1316`.
2. Observe the failure logged as `FAIL-0959`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

Cache eviction policy evicts frequently-used configuration entries under memory pressure.

## 5. Resolution

Implemented exponential back-off with jitter in the retry middleware.

## 6. Verification

Verified by re-executing test case `TC-1316` after fix deployment.

## 7. Impact Assessment

This defect affects the **Notification Handler** component and is traced back
to requirement **REQ-0480**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
