---
document_id: DR-BUG-0125
document_type: defect_report
title: Defect Report — BUG-0125
application: GalaxySearch
defect_id: BUG-0125
related_failure: FAIL-0644
related_test_case: TC-0355
affected_requirement: REQ-0306
severity: Trivial
priority: High
status: IN_PROGRESS
reported_date: 2024-08-07
---

# Defect Report
## BUG-0125 — Authentication Failure in Payment Gateway: AuthError: JWT token validation faile

**Application:** GalaxySearch
**Component:** Payment Gateway
**Severity:** Trivial
**Priority:** High
**Status:** IN_PROGRESS
**Reported:** 2024-08-07
**Resolved:** Pending
**Assigned To:** ENG-046

---

## 1. Problem Description

During execution EXEC-03329, test case TC-0355 failed with Authentication Failure. The system exhibited authentication failure when the device has been offline for more than 24 hours.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0644 |
| Test Case | TC-0355 |
| Affected Requirement | REQ-0306 |

## 3. Steps to Reproduce

1. Execute test case `TC-0355`.
2. Observe the failure logged as `FAIL-0644`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

Encryption key rotation not propagated to all microservice replicas before TTL expiry.

## 5. Resolution

Defect under investigation.

## 6. Verification

Pending verification after fix.

## 7. Impact Assessment

This defect affects the **Payment Gateway** component and is traced back
to requirement **REQ-0306**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
