---
document_id: DR-BUG-0454
document_type: defect_report
title: Defect Report — BUG-0454
application: XRPlatform
defect_id: BUG-0454
related_failure: FAIL-0537
related_test_case: TC-0404
affected_requirement: REQ-0358
severity: Minor
priority: High
status: VERIFIED
reported_date: 2024-12-29
---

# Defect Report
## BUG-0454 — Connectivity Failure in Cache: BluetoothException: device DEVICE-243 disconnecte

**Application:** XRPlatform
**Component:** Cache
**Severity:** Minor
**Priority:** High
**Status:** VERIFIED
**Reported:** 2024-12-29
**Resolved:** 2024-04-25
**Assigned To:** ENG-087

---

## 1. Problem Description

During execution EXEC-02746, test case TC-0404 failed with Connectivity Failure. The system exhibited connectivity failure when Bluetooth interference is present.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0537 |
| Test Case | TC-0404 |
| Affected Requirement | REQ-0358 |

## 3. Steps to Reproduce

1. Execute test case `TC-0404`.
2. Observe the failure logged as `FAIL-0537`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

Firmware update binary not validated against checksum before flashing; partial write leaves device in boot loop.

## 5. Resolution

Fixed by adding a mutex lock around the connection manager reconnect path.

## 6. Verification

Verified by re-executing test case `TC-0404` after fix deployment.

## 7. Impact Assessment

This defect affects the **Cache** component and is traced back
to requirement **REQ-0358**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
