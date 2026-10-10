---
document_id: DR-BUG-0284
document_type: defect_report
title: Defect Report — BUG-0284
application: ConnectedDevices
defect_id: BUG-0284
related_failure: FAIL-0284
related_test_case: TC-0366
affected_requirement: REQ-0231
severity: Major
priority: Critical
status: REOPENED
reported_date: 2023-05-28
---

# Defect Report
## BUG-0284 — Performance Degradation in Diagnostics: PerformanceViolation: p95 latency=2547ms

**Application:** ConnectedDevices
**Component:** Diagnostics
**Severity:** Major
**Priority:** Critical
**Status:** REOPENED
**Reported:** 2023-05-28
**Resolved:** Pending
**Assigned To:** ENG-092

---

## 1. Problem Description

During execution EXEC-01357, test case TC-0366 failed with Performance Degradation. The system exhibited performance degradation when the device has been offline for more than 24 hours.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0284 |
| Test Case | TC-0366 |
| Affected Requirement | REQ-0231 |

## 3. Steps to Reproduce

1. Execute test case `TC-0366`.
2. Observe the failure logged as `FAIL-0284`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

Encryption key rotation not propagated to all microservice replicas before TTL expiry.

## 5. Resolution

Defect under investigation.

## 6. Verification

Pending verification after fix.

## 7. Impact Assessment

This defect affects the **Diagnostics** component and is traced back
to requirement **REQ-0231**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
