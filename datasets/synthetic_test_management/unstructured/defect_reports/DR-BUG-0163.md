---
document_id: DR-BUG-0163
document_type: defect_report
title: Defect Report — BUG-0163
application: InternetBrowser
defect_id: BUG-0163
related_failure: FAIL-0957
related_test_case: TC-0204
affected_requirement: REQ-0314
severity: Trivial
priority: Medium
status: IN_PROGRESS
reported_date: 2023-03-03
---

# Defect Report
## BUG-0163 — Authentication Failure in Firmware Manager: AuthError: JWT token validation fail

**Application:** InternetBrowser
**Component:** Firmware Manager
**Severity:** Trivial
**Priority:** Medium
**Status:** IN_PROGRESS
**Reported:** 2023-03-03
**Resolved:** Pending
**Assigned To:** ENG-093

---

## 1. Problem Description

During execution EXEC-05115, test case TC-0204 failed with Authentication Failure. The system exhibited authentication failure when the session token has expired.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0957 |
| Test Case | TC-0204 |
| Affected Requirement | REQ-0314 |

## 3. Steps to Reproduce

1. Execute test case `TC-0204`.
2. Observe the failure logged as `FAIL-0957`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

Firmware update binary not validated against checksum before flashing; partial write leaves device in boot loop.

## 5. Resolution

Defect under investigation.

## 6. Verification

Pending verification after fix.

## 7. Impact Assessment

This defect affects the **Firmware Manager** component and is traced back
to requirement **REQ-0314**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
