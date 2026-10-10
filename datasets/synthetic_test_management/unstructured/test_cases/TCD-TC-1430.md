---
document_id: TCD-TC-1430
document_type: test_case
title: Validate that health metric upload enforces access control when the network connection is interrupte
application: InternetBrowser
test_case_id: TC-1430
requirement_id: REQ-0144
suite_id: TS-0077
priority: Low
test_type: Functional
automation_status: Automated
---

# Test Case Specification
## Validate that health metric upload enforces access control when the network connection is interrupte

**Test Case ID:** TC-1430
**Application:** InternetBrowser
**Requirement:** REQ-0144 — Authentication — Remote Diagnostics
**Suite:** TS-0077
**Type:** Functional
**Priority:** Low
**Automation:** Automated
**Estimated Duration:** 1740 seconds

---

## 1. Objective

Confirm that the feature behaves correctly under the user revokes permissions during the operation.

## 2. Preconditions

Device is enrolled, firmware >= 5.5.0, network profile set to degraded-network.

## 3. Test Steps

| Step | Action | Expected Result | Input Data |
|------|--------|----------------|------------|
| 1 | Check server logs for event code 'EVT-3336'. | The UI transitions to the next screen within 3 seconds. | `device_id=DEVICE-404` |
| 2 | Launch the VoiceAssistant application on the test device. | Server returns HTTP 200 with a valid JSON payload. | `N/A` |
| 3 | Initiate voice command recognition by pressing the 'Pay' button. | Server returns HTTP 200 with a valid JSON payload. | `payload_size=1000KB` |
| 4 | Observe the status indicator for up to 29 seconds. | The fallback UI is displayed with a human-readable error message. | `retry_count=1` |
| 5 | Verify that the UI displays 'Payment approved'. | The device reconnects automatically within 10 seconds. | `payload_size=1KB` |

## 4. Post-conditions

- System returns to a stable state after test execution.
- No residual data corruption or side-effects on subsequent tests.

## 5. Related Requirement

**REQ-0144:** The system shall support Bluetooth reconnection reliably under degraded-network conditions.

---
*This document is synthetic and created for AI/RAG research purposes only.*
