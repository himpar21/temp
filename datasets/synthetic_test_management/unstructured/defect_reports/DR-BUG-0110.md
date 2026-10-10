---
document_id: DR-BUG-0110
document_type: defect_report
title: Defect Report — BUG-0110
application: ConnectedDevices
defect_id: BUG-0110
related_failure: FAIL-0963
related_test_case: TC-1715
affected_requirement: REQ-0248
severity: Minor
priority: High
status: OPEN
reported_date: 2023-07-08
---

# Defect Report
## BUG-0110 — Crash in Configuration Service: Process com.samsung.wallet terminated unexpected

**Application:** ConnectedDevices
**Component:** Configuration Service
**Severity:** Minor
**Priority:** High
**Status:** OPEN
**Reported:** 2023-07-08
**Resolved:** Pending
**Assigned To:** ENG-004

---

## 1. Problem Description

During execution EXEC-05138, test case TC-1715 failed with Crash. The system exhibited crash when the user revokes permissions during the operation.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0963 |
| Test Case | TC-1715 |
| Affected Requirement | REQ-0248 |

## 3. Steps to Reproduce

1. Execute test case `TC-1715`.
2. Observe the failure logged as `FAIL-0963`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

Token expiry window mis-configured; server and client clocks diverge by more than 60 seconds.

## 5. Resolution

Defect under investigation.

## 6. Verification

Pending verification after fix.

## 7. Impact Assessment

This defect affects the **Configuration Service** component and is traced back
to requirement **REQ-0248**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
