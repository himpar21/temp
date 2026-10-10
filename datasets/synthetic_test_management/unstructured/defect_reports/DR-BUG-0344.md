---
document_id: DR-BUG-0344
document_type: defect_report
title: Defect Report — BUG-0344
application: MobileCommunication
defect_id: BUG-0344
related_failure: FAIL-0728
related_test_case: TC-0336
affected_requirement: REQ-0390
severity: Critical
priority: Critical
status: CLOSED
reported_date: 2024-09-25
---

# Defect Report
## BUG-0344 — Data Mismatch in UI Layer: DataIntegrityError: field 'status' expected=connected

**Application:** MobileCommunication
**Component:** UI Layer
**Severity:** Critical
**Priority:** Critical
**Status:** CLOSED
**Reported:** 2024-09-25
**Resolved:** 2023-12-27
**Assigned To:** ENG-079

---

## 1. Problem Description

During execution EXEC-03812, test case TC-0336 failed with Data Mismatch. The system exhibited data mismatch when the target device is running a legacy firmware version.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0728 |
| Test Case | TC-0336 |
| Affected Requirement | REQ-0390 |

## 3. Steps to Reproduce

1. Execute test case `TC-0336`.
2. Observe the failure logged as `FAIL-0728`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

Encryption key rotation not propagated to all microservice replicas before TTL expiry.

## 5. Resolution

Added null-check guard and fallback default value; unit test added for nil response.

## 6. Verification

Verified by re-executing test case `TC-0336` after fix deployment.

## 7. Impact Assessment

This defect affects the **UI Layer** component and is traced back
to requirement **REQ-0390**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
