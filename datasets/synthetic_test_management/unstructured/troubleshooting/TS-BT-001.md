---
document_id: TS-BT-001
document_type: troubleshooting
title: Bluetooth Pairing Failure Troubleshooting Guide
application: ConnectedDevices
topic: Bluetooth connectivity
---

# Bluetooth Pairing Failure Troubleshooting Guide

**Application:** ConnectedDevices
**Topic:** Bluetooth Connectivity

---

## 1. Symptoms

The following symptoms indicate a **Bluetooth connectivity** failure:

- `BluetoothException: device disconnected during pairing handshake`
- `GATT error 133`
- `Pairing rejected by remote device`

## 2. Diagnostic Steps

1. Ensure the target device is in pairing mode and within 1 metre.
2. Clear the Bluetooth cache on both devices.
3. Verify that no other device is actively connected to the same peripheral.
4. Check firmware version — update if below minimum pairing firmware.
5. Disable battery optimisation for the Bluetooth service.
6. Restart the Bluetooth stack using the diagnostic tool.

## 3. When to Escalate

Escalate to the ConnectedDevices platform team if:

- The issue recurs across more than 3 consecutive regression cycles.
- More than 10% of test executions in a run exhibit this failure type.
- The root cause cannot be reproduced in an isolated test environment.

## 4. Related Failure Reports

Search `failure_logs/` for documents where `failure_type` matches the symptom pattern above.

## 5. Related Defects

Known defects related to this issue are tracked in `defect_reports/`.
Filter by `component` matching the affected service.

## 6. Prevention

- Add automated monitoring for this failure pattern to the CI pipeline.
- Include a dedicated test case in the smoke suite to catch regressions early.
- Review the root cause cluster in `historical_failures.csv` for recurring patterns.

---
*This document is synthetic and created for AI/RAG research purposes only.*
