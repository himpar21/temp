---
document_id: DR-BUG-0467
document_type: defect_report
title: Defect Report — BUG-0467
application: DigitalWallet
defect_id: BUG-0467
related_failure: FAIL-0920
related_test_case: TC-1892
affected_requirement: REQ-0399
severity: Trivial
priority: Critical
status: REOPENED
reported_date: 2023-03-16
---

# Defect Report
## BUG-0467 — Configuration Error in Media Codec: ConfigError: missing required key 'SIGNING_K

**Application:** DigitalWallet
**Component:** Media Codec
**Severity:** Trivial
**Priority:** Critical
**Status:** REOPENED
**Reported:** 2023-03-16
**Resolved:** Pending
**Assigned To:** ENG-087

---

## 1. Problem Description

During execution EXEC-04912, test case TC-1892 failed with Configuration Error. The system exhibited configuration error when the device has been offline for more than 24 hours.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0920 |
| Test Case | TC-1892 |
| Affected Requirement | REQ-0399 |

## 3. Steps to Reproduce

1. Execute test case `TC-1892`.
2. Observe the failure logged as `FAIL-0920`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

Encryption key rotation not propagated to all microservice replicas before TTL expiry.

## 5. Resolution

Defect under investigation.

## 6. Verification

Pending verification after fix.

## 7. Impact Assessment

This defect affects the **Media Codec** component and is traced back
to requirement **REQ-0399**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
