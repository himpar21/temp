---
document_id: DR-BUG-0181
document_type: defect_report
title: Defect Report — BUG-0181
application: XRPlatform
defect_id: BUG-0181
related_failure: FAIL-0245
related_test_case: TC-1125
affected_requirement: REQ-0179
severity: Minor
priority: Medium
status: FIXED
reported_date: 2024-07-02
---

# Defect Report
## BUG-0181 — Timeout in UI Layer: Operation timed out after 25989ms; threshold is 9582ms.…

**Application:** XRPlatform
**Component:** UI Layer
**Severity:** Minor
**Priority:** Medium
**Status:** FIXED
**Reported:** 2024-07-02
**Resolved:** 2024-03-09
**Assigned To:** ENG-025

---

## 1. Problem Description

During execution EXEC-01151, test case TC-1125 failed with Timeout. The system exhibited timeout when the session token has expired.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0245 |
| Test Case | TC-1125 |
| Affected Requirement | REQ-0179 |

## 3. Steps to Reproduce

1. Execute test case `TC-1125`.
2. Observe the failure logged as `FAIL-0245`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

Retry logic does not apply exponential back-off; storm of reconnection attempts saturates the gateway.

## 5. Resolution

Synchronized NTP server configuration across all microservices; clock skew reduced to <1s.

## 6. Verification

Verified by re-executing test case `TC-1125` after fix deployment.

## 7. Impact Assessment

This defect affects the **UI Layer** component and is traced back
to requirement **REQ-0179**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
