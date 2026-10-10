---
document_id: DR-BUG-0468
document_type: defect_report
title: Defect Report — BUG-0468
application: DigitalWallet
defect_id: BUG-0468
related_failure: FAIL-0495
related_test_case: TC-0732
affected_requirement: REQ-0401
severity: Trivial
priority: Medium
status: CLOSED
reported_date: 2024-04-25
---

# Defect Report
## BUG-0468 — Resource Exhaustion in Voice Pipeline: OOMError: heap exhausted at 1786MB/2048MB

**Application:** DigitalWallet
**Component:** Voice Pipeline
**Severity:** Trivial
**Priority:** Medium
**Status:** CLOSED
**Reported:** 2024-04-25
**Resolved:** 2024-03-23
**Assigned To:** ENG-007

---

## 1. Problem Description

During execution EXEC-02493, test case TC-0732 failed with Resource Exhaustion. The system exhibited resource exhaustion when the network connection is interrupted mid-flow.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0495 |
| Test Case | TC-0732 |
| Affected Requirement | REQ-0401 |

## 3. Steps to Reproduce

1. Execute test case `TC-0732`.
2. Observe the failure logged as `FAIL-0495`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

Token expiry window mis-configured; server and client clocks diverge by more than 60 seconds.

## 5. Resolution

Reduced sampling rate to 500ms; added configurable throttle in the sensor manager.

## 6. Verification

Verified by re-executing test case `TC-0732` after fix deployment.

## 7. Impact Assessment

This defect affects the **Voice Pipeline** component and is traced back
to requirement **REQ-0401**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
