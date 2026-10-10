---
document_id: TCD-TC-1367
document_type: test_case
title: Ensure NFC tap-to-pay synchronizes correctly across devices when the user revokes permissions during
application: WearableHealth
test_case_id: TC-1367
requirement_id: REQ-0044
suite_id: TS-0102
priority: High
test_type: End-to-End
automation_status: Manual
---

# Test Case Specification
## Ensure NFC tap-to-pay synchronizes correctly across devices when the user revokes permissions during

**Test Case ID:** TC-1367
**Application:** WearableHealth
**Requirement:** REQ-0044 — UI Behavior — Audit Logging
**Suite:** TS-0102
**Type:** End-to-End
**Priority:** High
**Automation:** Manual
**Estimated Duration:** 1126 seconds

---

## 1. Objective

Confirm that the feature behaves correctly under the input data contains Unicode special characters.

## 2. Preconditions

Device is enrolled, firmware >= 5.2.0, network profile set to low-bandwidth.

## 3. Test Steps

| Step | Action | Expected Result | Input Data |
|------|--------|----------------|------------|
| 1 | Re-connect the wearable and confirm auto-recovery. | A confirmation notification appears on the paired device. | `retry_count=5` |
| 2 | Capture a screenshot and attach as evidence. | The performance counter logs a value below the SLA threshold. | `device_id=DEVICE-715` |
| 3 | Observe the status indicator for up to 11 seconds. | The fallback UI is displayed with a human-readable error message. | `N/A` |
| 4 | Simulate network drop using the network emulator profile 'Offline'. | A success toast message is displayed. | `N/A` |
| 5 | Verify that the UI displays 'Connection successful'. | The performance counter logs a value below the SLA threshold. | `username=testuser_002` |

## 4. Post-conditions

- System returns to a stable state after test execution.
- No residual data corruption or side-effects on subsequent tests.

## 5. Related Requirement

**REQ-0044:** The system shall handle offline mode without data loss under degraded-network conditions.

---
*This document is synthetic and created for AI/RAG research purposes only.*
