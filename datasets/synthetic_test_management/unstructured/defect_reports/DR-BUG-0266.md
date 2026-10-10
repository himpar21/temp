---
document_id: DR-BUG-0266
document_type: defect_report
title: Defect Report — BUG-0266
application: InternetBrowser
defect_id: BUG-0266
related_failure: FAIL-0648
related_test_case: TC-1829
affected_requirement: REQ-0351
severity: Trivial
priority: Medium
status: VERIFIED
reported_date: 2024-09-17
---

# Defect Report
## BUG-0266 — Connectivity Failure in Push Service: BluetoothException: device DEVICE-331 disc

**Application:** InternetBrowser
**Component:** Push Service
**Severity:** Trivial
**Priority:** Medium
**Status:** VERIFIED
**Reported:** 2024-09-17
**Resolved:** 2024-12-13
**Assigned To:** ENG-069

---

## 1. Problem Description

During execution EXEC-03364, test case TC-1829 failed with Connectivity Failure. The system exhibited connectivity failure when the network connection is interrupted mid-flow.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0648 |
| Test Case | TC-1829 |
| Affected Requirement | REQ-0351 |

## 3. Steps to Reproduce

1. Execute test case `TC-1829`.
2. Observe the failure logged as `FAIL-0648`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

OAuth2 redirect URI whitelist not updated after domain migration; authorization code flow fails.

## 5. Resolution

Added CRC32 checksum validation step before OTA flash; partial-write detection added.

## 6. Verification

Verified by re-executing test case `TC-1829` after fix deployment.

## 7. Impact Assessment

This defect affects the **Push Service** component and is traced back
to requirement **REQ-0351**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
