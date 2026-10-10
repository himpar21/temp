---
document_id: DR-BUG-0325
document_type: defect_report
title: Defect Report — BUG-0325
application: SmartHome
defect_id: BUG-0325
related_failure: FAIL-0504
related_test_case: TC-0685
affected_requirement: REQ-0007
severity: Minor
priority: Medium
status: FIXED
reported_date: 2023-05-01
---

# Defect Report
## BUG-0325 — Resource Exhaustion in Authentication: OOMError: heap exhausted at 659MB/2048MB 

**Application:** SmartHome
**Component:** Authentication
**Severity:** Minor
**Priority:** Medium
**Status:** FIXED
**Reported:** 2023-05-01
**Resolved:** 2024-04-05
**Assigned To:** ENG-081

---

## 1. Problem Description

During execution EXEC-02526, test case TC-0685 failed with Resource Exhaustion. The system exhibited resource exhaustion when the server returns a 503 Service Unavailable response.

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | FAIL-0504 |
| Test Case | TC-0685 |
| Affected Requirement | REQ-0007 |

## 3. Steps to Reproduce

1. Execute test case `TC-0685`.
2. Observe the failure logged as `FAIL-0504`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

OAuth2 redirect URI whitelist not updated after domain migration; authorization code flow fails.

## 5. Resolution

Implemented exponential back-off with jitter in the retry middleware.

## 6. Verification

Verified by re-executing test case `TC-0685` after fix deployment.

## 7. Impact Assessment

This defect affects the **Authentication** component and is traced back
to requirement **REQ-0007**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
