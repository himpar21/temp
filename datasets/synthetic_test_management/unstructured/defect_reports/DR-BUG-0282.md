---
document_id: DR-BUG-0282
document_type: defect_report
title: Defect Report — BUG-0282
application: ConnectedDevices
defect_id: BUG-0282
related_failure: FAIL-0488
related_test_case: TC-1618
affected_requirement: REQ-0511
severity: Major
priority: Critical
status: OPEN
reported_date: 2023-09-18
---

# Defect Report
## BUG-0282 — Performance Degradation in Authentication: PerformanceViolation: p95 latency=219

**Application:** ConnectedDevices
**Component:** Authentication
**Severity:** Major
**Priority:** Critical
**Status:** OPEN
**Reported:** 2023-09-18
**Resolved:** Pending
**Assigned To:** ENG-009

---

## 1. Problem Description

During execution EXEC-02459, test case TC-1618 failed with Performance Degradation. The system exhibited performance degradation when the server returns a 503 Service Unavailable response.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0488 |
| Test Case | TC-1618 |
| Affected Requirement | REQ-0511 |

## 3. Steps to Reproduce

1. Execute test case `TC-1618`.
2. Observe the failure logged as `FAIL-0488`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

Encryption key rotation not propagated to all microservice replicas before TTL expiry.

## 5. Resolution

Defect under investigation.

## 6. Verification

Pending verification after fix.

## 7. Impact Assessment

This defect affects the **Authentication** component and is traced back
to requirement **REQ-0511**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
