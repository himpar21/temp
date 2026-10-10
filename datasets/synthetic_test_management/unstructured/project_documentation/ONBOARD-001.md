# QA Engineer Onboarding Guide

## Welcome

This guide helps new QA engineers understand our test management processes,
tooling, and conventions.

## Test Case Naming Convention

- Format: `TC-NNNN`
- Use descriptive titles: verb + feature + condition.
- Example: "Verify that Bluetooth reconnects after a 30-second network interruption."

## Defect Reporting Convention

- Format: `BUG-NNNN`
- Title must include: component, failure type, brief description.
- Always link to: failure report, test case, affected requirement.
- Set severity and priority independently — do not conflate them.

## Failure Classification

| Type | Description |
|------|-------------|
| Timeout | Operation exceeded defined SLA threshold |
| Crash | Process terminated unexpectedly |
| Assertion Failure | Test assertion did not match expected result |
| Network Failure | Network error during execution |
| Authentication Failure | Auth token validation failed |
| UI Failure | UI element not found or incorrect state |
| Data Mismatch | Returned data does not match expected value |
| Performance Degradation | SLA violation detected |
| Synchronisation Failure | Data sync conflict or timeout |
| Connectivity Failure | Device disconnected during operation |
| Resource Exhaustion | Memory or CPU ceiling exceeded |
| Configuration Error | Missing or incorrect configuration key |

## Regression Cycle Process

1. Build is tagged and deployed to the test environment.
2. Smoke suite is executed — must pass 100% before full regression.
3. Full regression suite is executed.
4. Failures are triaged within 24 hours.
5. Defects are filed, assigned, and tracked.
6. Re-test after fix is mandatory before closing a defect.
7. Release sign-off requires pass rate ≥ 95% and zero open Critical defects.

*This document is synthetic and created for AI/RAG research purposes only.*
