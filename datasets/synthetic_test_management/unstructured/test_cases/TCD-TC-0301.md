---
document_id: TCD-TC-0301
document_type: test_case
title: Validate that firmware over-the-air update enforces access control when the user revokes permissions
application: GalaxySearch
test_case_id: TC-0301
requirement_id: REQ-0144
suite_id: TS-0025
priority: High
test_type: Security
automation_status: Manual
---

# Test Case Specification
## Validate that firmware over-the-air update enforces access control when the user revokes permissions

**Test Case ID:** TC-0301
**Application:** GalaxySearch
**Requirement:** REQ-0144 — Authentication — Remote Diagnostics
**Suite:** TS-0025
**Type:** Security
**Priority:** High
**Automation:** Manual
**Estimated Duration:** 1401 seconds

---

## 1. Objective

Confirm that the feature behaves correctly under the session token has expired.

## 2. Preconditions

Device is enrolled, firmware >= 6.4.0, network profile set to standard.

## 3. Test Steps

| Step | Action | Expected Result | Input Data |
|------|--------|----------------|------------|
| 1 | Enter valid credentials: username='testuser_035', password='[REDACTED]'. | The device reconnects automatically within 10 seconds. | `N/A` |
| 2 | Record response time using the built-in performance monitor. | The device reconnects automatically within 10 seconds. | `retry_count=4` |
| 3 | Record response time using the built-in performance monitor. | A confirmation notification appears on the paired device. | `network_profile=high-load` |
| 4 | Re-connect the hub and confirm auto-recovery. | Server returns HTTP 200 with a valid JSON payload. | `device_id=DEVICE-157` |
| 5 | Capture a screenshot and attach as evidence. | No crash or ANR is observed. | `network_profile=standard` |

## 4. Post-conditions

- System returns to a stable state after test execution.
- No residual data corruption or side-effects on subsequent tests.

## 5. Related Requirement

**REQ-0144:** The system shall support Bluetooth reconnection reliably under degraded-network conditions.

---
*This document is synthetic and created for AI/RAG research purposes only.*
