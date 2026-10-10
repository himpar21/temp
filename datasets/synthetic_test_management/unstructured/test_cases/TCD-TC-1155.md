---
document_id: TCD-TC-1155
document_type: test_case
title: Test that background sync correctly handles invalid input when the target device is running a legacy
application: WearableHealth
test_case_id: TC-1155
requirement_id: REQ-0095
suite_id: TS-0092
priority: Low
test_type: Security
automation_status: Manual
---

# Test Case Specification
## Test that background sync correctly handles invalid input when the target device is running a legacy

**Test Case ID:** TC-1155
**Application:** WearableHealth
**Requirement:** REQ-0095 — Functional — Biometric Verification
**Suite:** TS-0092
**Type:** Security
**Priority:** Low
**Automation:** Manual
**Estimated Duration:** 916 seconds

---

## 1. Objective

Confirm that the feature behaves correctly under the user revokes permissions during the operation.

## 2. Preconditions

Device is enrolled, firmware >= 5.4.0, network profile set to low-bandwidth.

## 3. Test Steps

| Step | Action | Expected Result | Input Data |
|------|--------|----------------|------------|
| 1 | Disconnect the phone and wait 3 seconds. | The device reconnects automatically within 10 seconds. | `payload_size=1KB` |
| 2 | Initiate session token refresh by pressing the 'Pay' button. | The operation completes without error. | `username=testuser_019` |
| 3 | Navigate to Settings > Connectivity and tap 'Enable Sync'. | The device reconnects automatically within 10 seconds. | `username=testuser_046` |

## 4. Post-conditions

- System returns to a stable state after test execution.
- No residual data corruption or side-effects on subsequent tests.

## 5. Related Requirement

**REQ-0095:** The system shall handle dark mode within 200ms under high-load conditions.

---
*This document is synthetic and created for AI/RAG research purposes only.*
