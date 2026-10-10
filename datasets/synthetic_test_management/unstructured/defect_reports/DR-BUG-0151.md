---
document_id: DR-BUG-0151
document_type: defect_report
title: Defect Report — BUG-0151
application: DeviceHub
defect_id: BUG-0151
related_failure: FAIL-0497
related_test_case: TC-1347
affected_requirement: REQ-0178
severity: Critical
priority: Low
status: CLOSED
reported_date: 2023-10-20
---

# Defect Report
## BUG-0151 — Timeout in Health API: Operation timed out after 27104ms; threshold is 9646ms.…

**Application:** DeviceHub
**Component:** Health API
**Severity:** Critical
**Priority:** Low
**Status:** CLOSED
**Reported:** 2023-10-20
**Resolved:** 2023-11-15
**Assigned To:** ENG-072

---

## 1. Problem Description

During execution EXEC-02504, test case TC-1347 failed with Timeout. The system exhibited timeout when the battery level drops below 10%.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0497 |
| Test Case | TC-1347 |
| Affected Requirement | REQ-0178 |

## 3. Steps to Reproduce

1. Execute test case `TC-1347`.
2. Observe the failure logged as `FAIL-0497`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

Retry logic does not apply exponential back-off; storm of reconnection attempts saturates the gateway.

## 5. Resolution

Added null-check guard and fallback default value; unit test added for nil response.

## 6. Verification

Verified by re-executing test case `TC-1347` after fix deployment.

## 7. Impact Assessment

This defect affects the **Health API** component and is traced back
to requirement **REQ-0178**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
