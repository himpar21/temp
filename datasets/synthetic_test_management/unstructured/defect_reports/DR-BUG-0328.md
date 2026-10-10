---
document_id: DR-BUG-0328
document_type: defect_report
title: Defect Report — BUG-0328
application: DeviceHub
defect_id: BUG-0328
related_failure: FAIL-0478
related_test_case: TC-0720
affected_requirement: REQ-0203
severity: Major
priority: Low
status: ASSIGNED
reported_date: 2023-09-25
---

# Defect Report
## BUG-0328 — Data Mismatch in Network Stack: DataIntegrityError: field 'checksum' expected=co

**Application:** DeviceHub
**Component:** Network Stack
**Severity:** Major
**Priority:** Low
**Status:** ASSIGNED
**Reported:** 2023-09-25
**Resolved:** Pending
**Assigned To:** ENG-019

---

## 1. Problem Description

During execution EXEC-02425, test case TC-0720 failed with Data Mismatch. The system exhibited data mismatch when the server returns a 503 Service Unavailable response.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0478 |
| Test Case | TC-0720 |
| Affected Requirement | REQ-0203 |

## 3. Steps to Reproduce

1. Execute test case `TC-0720`.
2. Observe the failure logged as `FAIL-0478`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

Health sensor sampling rate exceeds Bluetooth LE characteristic notification limit of 250ms intervals.

## 5. Resolution

Defect under investigation.

## 6. Verification

Pending verification after fix.

## 7. Impact Assessment

This defect affects the **Network Stack** component and is traced back
to requirement **REQ-0203**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
