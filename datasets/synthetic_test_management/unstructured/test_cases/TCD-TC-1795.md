---
document_id: TCD-TC-1795
document_type: test_case
title: Ensure that biometric verification does not exceed the p95 latency (500ms) threshold under burst loa
application: MobileCommunication
test_case_id: TC-1795
requirement_id: REQ-0100
suite_id: TS-0051
priority: Low
test_type: End-to-End
automation_status: Semi-Automated
---

# Test Case Specification
## Ensure that biometric verification does not exceed the p95 latency (500ms) threshold under burst loa

**Test Case ID:** TC-1795
**Application:** MobileCommunication
**Requirement:** REQ-0100 — Reliability — Audit Logging
**Suite:** TS-0051
**Type:** End-to-End
**Priority:** Low
**Automation:** Semi-Automated
**Estimated Duration:** 969 seconds

---

## 1. Objective

Confirm that the feature behaves correctly under the user revokes permissions during the operation.

## 2. Preconditions

Device is enrolled, firmware >= 5.3.0, network profile set to stress-test.

## 3. Test Steps

| Step | Action | Expected Result | Input Data |
|------|--------|----------------|------------|
| 1 | Observe the status indicator for up to 10 seconds. | The fallback UI is displayed with a human-readable error message. | `device_id=DEVICE-373` |
| 2 | Assert that database record for entity 'ENT-186' has status='PENDING'. | A confirmation notification appears on the paired device. | `device_id=DEVICE-280` |
| 3 | Simulate network drop using the network emulator profile 'WiFi-Lossy'. | The operation completes without error. | `payload_size=10KB` |
| 4 | Verify that the UI displays 'Error: retry'. | The fallback UI is displayed with a human-readable error message. | `network_profile=high-load` |
| 5 | Check server logs for event code 'EVT-4012'. | A confirmation notification appears on the paired device. | `payload_size=10KB` |
| 6 | Simulate network drop using the network emulator profile '3G-Low'. | The fallback UI is displayed with a human-readable error message. | `device_id=DEVICE-301` |

## 4. Post-conditions

- System returns to a stable state after test execution.
- No residual data corruption or side-effects on subsequent tests.

## 5. Related Requirement

**REQ-0100:** The system shall enforce multilingual support within 200ms under standard conditions.

---
*This document is synthetic and created for AI/RAG research purposes only.*
