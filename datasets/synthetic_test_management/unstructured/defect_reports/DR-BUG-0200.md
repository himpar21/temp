---
document_id: DR-BUG-0200
document_type: defect_report
title: Defect Report — BUG-0200
application: DigitalWallet
defect_id: BUG-0200
related_failure: FAIL-0727
related_test_case: TC-0302
affected_requirement: REQ-0069
severity: Critical
priority: High
status: CLOSED
reported_date: 2024-12-04
---

# Defect Report
## BUG-0200 — Network Failure in Firmware Manager: SocketException: Connection reset by peer o

**Application:** DigitalWallet
**Component:** Firmware Manager
**Severity:** Critical
**Priority:** High
**Status:** CLOSED
**Reported:** 2024-12-04
**Resolved:** 2024-06-22
**Assigned To:** ENG-100

---

## 1. Problem Description

During execution EXEC-03810, test case TC-0302 failed with Network Failure. The system exhibited network failure when the user revokes permissions during the operation.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0727 |
| Test Case | TC-0302 |
| Affected Requirement | REQ-0069 |

## 3. Steps to Reproduce

1. Execute test case `TC-0302`.
2. Observe the failure logged as `FAIL-0727`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

UI thread blocked by synchronous network call; ANR triggered after 5 seconds.

## 5. Resolution

Synchronized NTP server configuration across all microservices; clock skew reduced to <1s.

## 6. Verification

Verified by re-executing test case `TC-0302` after fix deployment.

## 7. Impact Assessment

This defect affects the **Firmware Manager** component and is traced back
to requirement **REQ-0069**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
