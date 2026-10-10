---
document_id: DR-BUG-0080
document_type: defect_report
title: Defect Report — BUG-0080
application: DigitalWallet
defect_id: BUG-0080
related_failure: FAIL-0742
related_test_case: TC-0177
affected_requirement: REQ-0360
severity: Critical
priority: Critical
status: ASSIGNED
reported_date: 2024-05-25
---

# Defect Report
## BUG-0080 — Crash in Configuration Service: Process com.samsung.wallet terminated unexpected

**Application:** DigitalWallet
**Component:** Configuration Service
**Severity:** Critical
**Priority:** Critical
**Status:** ASSIGNED
**Reported:** 2024-05-25
**Resolved:** Pending
**Assigned To:** ENG-053

---

## 1. Problem Description

During execution EXEC-03865, test case TC-0177 failed with Crash. The system exhibited crash when the user revokes permissions during the operation.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0742 |
| Test Case | TC-0177 |
| Affected Requirement | REQ-0360 |

## 3. Steps to Reproduce

1. Execute test case `TC-0177`.
2. Observe the failure logged as `FAIL-0742`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

Health sensor sampling rate exceeds Bluetooth LE characteristic notification limit of 250ms intervals.

## 5. Resolution

Defect under investigation.

## 6. Verification

Pending verification after fix.

## 7. Impact Assessment

This defect affects the **Configuration Service** component and is traced back
to requirement **REQ-0360**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
