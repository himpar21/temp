---
document_id: TCD-TC-0543
document_type: test_case
title: Verify that NFC tap-to-pay completes successfully when the target device is running a legacy firmwar
application: InternetBrowser
test_case_id: TC-0543
requirement_id: REQ-0203
suite_id: TS-0010
priority: Medium
test_type: Smoke
automation_status: Manual
---

# Test Case Specification
## Verify that NFC tap-to-pay completes successfully when the target device is running a legacy firmwar

**Test Case ID:** TC-0543
**Application:** InternetBrowser
**Requirement:** REQ-0203 — Usability — Haptic Feedback
**Suite:** TS-0010
**Type:** Smoke
**Priority:** Medium
**Automation:** Manual
**Estimated Duration:** 1430 seconds

---

## 1. Objective

Confirm that the feature behaves correctly under two concurrent requests are made simultaneously.

## 2. Preconditions

Device is enrolled, firmware >= 6.0.0, network profile set to stress-test.

## 3. Test Steps

| Step | Action | Expected Result | Input Data |
|------|--------|----------------|------------|
| 1 | Observe the status indicator for up to 23 seconds. | Server returns HTTP 200 with a valid JSON payload. | `username=testuser_012` |
| 2 | Enter valid credentials: username='testuser_016', password='[REDACTED]'. | The UI transitions to the next screen within 3 seconds. | `username=testuser_034` |
| 3 | Capture a screenshot and attach as evidence. | The operation completes without error. | `retry_count=1` |
| 4 | Enter valid credentials: username='testuser_026', password='[REDACTED]'. | The performance counter logs a value below the SLA threshold. | `payload_size=10KB` |
| 5 | Observe the status indicator for up to 10 seconds. | The device reconnects automatically within 10 seconds. | `network_profile=high-load` |

## 4. Post-conditions

- System returns to a stable state after test execution.
- No residual data corruption or side-effects on subsequent tests.

## 5. Related Requirement

**REQ-0203:** The system shall support user authentication without data loss under standard conditions.

---
*This document is synthetic and created for AI/RAG research purposes only.*
