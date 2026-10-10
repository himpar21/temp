---
document_id: TCD-TC-0536
document_type: test_case
title: Confirm that NFC tap-to-pay triggers the expected notification when the target device is running a l
application: DigitalWallet
test_case_id: TC-0536
requirement_id: REQ-0158
suite_id: TS-0038
priority: Low
test_type: Negative
automation_status: Semi-Automated
---

# Test Case Specification
## Confirm that NFC tap-to-pay triggers the expected notification when the target device is running a l

**Test Case ID:** TC-0536
**Application:** DigitalWallet
**Requirement:** REQ-0158 — Recovery — Search Query Execution
**Suite:** TS-0038
**Type:** Negative
**Priority:** Low
**Automation:** Semi-Automated
**Estimated Duration:** 905 seconds

---

## 1. Objective

Confirm that the feature behaves correctly under the input data contains Unicode special characters.

## 2. Preconditions

Device is enrolled, firmware >= 5.4.0, network profile set to degraded-network.

## 3. Test Steps

| Step | Action | Expected Result | Input Data |
|------|--------|----------------|------------|
| 1 | Launch the VoiceAssistant application on the test device. | The audit log records the event with correct metadata. | `network_profile=standard` |
| 2 | Assert that database record for entity 'ENT-379' has status='SYNCED'. | The UI transitions to the next screen within 3 seconds. | `device_id=DEVICE-453` |
| 3 | Verify that the UI displays 'Error: retry'. | No crash or ANR is observed. | `retry_count=1` |
| 4 | Check server logs for event code 'EVT-2454'. | The fallback UI is displayed with a human-readable error message. | `retry_count=3` |
| 5 | Verify that the UI displays 'Error: retry'. | The UI transitions to the next screen within 3 seconds. | `N/A` |
| 6 | Capture a screenshot and attach as evidence. | The device reconnects automatically within 10 seconds. | `network_profile=low-bandwidth` |

## 4. Post-conditions

- System returns to a stable state after test execution.
- No residual data corruption or side-effects on subsequent tests.

## 5. Related Requirement

**REQ-0158:** The system shall support remote diagnostics securely under low-bandwidth conditions.

---
*This document is synthetic and created for AI/RAG research purposes only.*
