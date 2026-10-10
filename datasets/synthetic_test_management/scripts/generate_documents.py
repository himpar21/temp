"""
generate_documents.py
======================
Generates realistic unstructured Markdown documents from the already-produced
structured CSV data.  Must be run AFTER generate_dataset.py.

Run:
    python datasets/synthetic_test_management/scripts/generate_documents.py

Documents land in datasets/synthetic_test_management/unstructured/<category>/
"""

import csv
import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR   = Path(__file__).resolve().parent
DATASET_ROOT = SCRIPT_DIR.parent
STRUCTURED   = DATASET_ROOT / "structured"
UNSTRUCTURED = DATASET_ROOT / "unstructured"

SEED = 42
random.seed(SEED)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def load_csv(name):
    path = STRUCTURED / name
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_doc(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def rdate(start="2023-01-01", end="2024-12-31"):
    s = datetime.strptime(start, "%Y-%m-%d")
    e = datetime.strptime(end,   "%Y-%m-%d")
    return (s + timedelta(days=random.randint(0, (e - s).days))).strftime("%Y-%m-%d")

# ──────────────────────────────────────────────────────────────────────────────
# 1. REQUIREMENT DOCUMENTS
# ──────────────────────────────────────────────────────────────────────────────

def gen_requirement_docs(reqs, apps, count=40):
    app_map = {a["application_id"]: a["name"] for a in apps}
    sampled = random.sample(reqs, min(count, len(reqs)))
    for req in sampled:
        app_name = app_map.get(req["application_id"], req["application_id"])
        doc_id   = req["requirement_id"].replace("REQ-","SRS-")
        content  = f"""---
document_id: {doc_id}
document_type: requirement
title: {req['title']}
application: {app_name}
requirement_id: {req['requirement_id']}
version: {req.get('version','v1.0')}
status: {req.get('status','Approved')}
priority: {req.get('priority','Medium')}
created_date: {req.get('created_date', rdate())}
---

# Software Requirements Specification
## {req['title']}

**Application:** {app_name}
**Requirement ID:** {req['requirement_id']}
**Type:** {req.get('requirement_type','Functional')}
**Priority:** {req.get('priority','Medium')}
**Severity:** {req.get('severity','Major')}
**Component:** {req.get('component','N/A')}

---

## 1. Overview

This requirement specifies the expected behaviour of the **{req.get('feature','feature')}**
functionality within the **{app_name}** application.

The system integrates with backend services to deliver seamless {req.get('requirement_type','').lower()} capabilities
to end users across all supported device form factors.

## 2. Requirement Statement

{req['description']}

## 3. Acceptance Criteria

| # | Criterion | Pass Condition |
|---|-----------|---------------|
| AC-1 | Feature executes within SLA | Response time < 500ms at p95 |
| AC-2 | No data loss under network interruption | All pending operations queued and retried |
| AC-3 | Correct error message shown on failure | Error code and human-readable message displayed |
| AC-4 | Feature respects user permission settings | Unauthorized requests rejected with HTTP 403 |

## 4. Dependencies

- Requires **{req.get('component','Auth Gateway')}** to be operational.
- Depends on a stable network connection or fallback offline queue.
- Requires device firmware ≥ 5.0.0.

## 5. Non-Functional Requirements

- **Performance:** Feature must complete within 200ms under normal load.
- **Reliability:** Feature must succeed in ≥ 99.5% of attempts under standard conditions.
- **Security:** All data transmitted must be encrypted with TLS 1.3.

## 6. Related Artifacts

- Source Document: `{req.get('source_document','SRS.pdf')}`
- Related Solution: `{req.get('solution_id','SOL-001')}`

---
*This document is synthetic and created for AI/RAG research purposes only.*
"""
        path = UNSTRUCTURED / "requirements" / f"{req['requirement_id']}.md"
        write_doc(path, content)
    print(f"  ✓ requirements/            {len(sampled):>4} documents")

# ──────────────────────────────────────────────────────────────────────────────
# 2. TEST PLAN DOCUMENTS
# ──────────────────────────────────────────────────────────────────────────────

def gen_test_plan_docs(suites, apps, reqs, count=20):
    app_map  = {a["application_id"]: a["name"] for a in apps}
    req_map  = {}
    for r in reqs:
        req_map.setdefault(r["application_id"], []).append(r["requirement_id"])

    sampled = random.sample(suites, min(count, len(suites)))
    for suite in sampled:
        app_name = app_map.get(suite["application_id"], suite["application_id"])
        req_sample = random.sample(req_map.get(suite["application_id"],[]), 
                                   min(5, len(req_map.get(suite["application_id"],[]))))
        content = f"""---
document_id: TP-{suite['suite_id']}
document_type: test_plan
title: Test Plan — {suite['name']}
application: {app_name}
suite_id: {suite['suite_id']}
release_id: {suite.get('release_id','REL-001')}
created_date: {suite.get('created_date', rdate())}
---

# Test Plan
## {suite['name']}

**Application:** {app_name}
**Suite ID:** {suite['suite_id']}
**Suite Type:** {suite.get('suite_type','Regression')}
**Priority:** {suite.get('priority','High')}
**Release:** {suite.get('release_id','REL-001')}

---

## 1. Scope

This test plan covers {suite.get('suite_type','regression')} testing for the **{app_name}**
application suite `{suite['suite_id']}`.

The plan encompasses all scenarios related to **{suite.get('description','component testing')}**.

## 2. Requirements Under Test

The following requirements are validated by this test suite:

{chr(10).join(f'- `{r}`' for r in req_sample)}

## 3. Entry Criteria

- Build has passed smoke tests.
- Test environment `{random.choice(["ENV-001","ENV-002","ENV-003","ENV-007"])}` is available.
- All blocking defects from the previous cycle are resolved.

## 4. Exit Criteria

- Pass rate ≥ 95%.
- No open Critical or High severity defects.
- All smoke test cases executed and passed.

## 5. Test Environment

| Property | Value |
|----------|-------|
| Environment | Mobile Lab / Cloud Test Env |
| OS Version | Android 14 / One UI 6.0 |
| Network | WiFi-6 / 5G |
| Build | Latest RC build |

## 6. Risk Assessment

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Network instability | Medium | Use stable wired environment for critical tests |
| Device unavailability | Low | Reserve backup devices 24h before execution |
| Build quality regression | Medium | Execute smoke suite before full regression |

## 7. Schedule

| Milestone | Target Date |
|-----------|-------------|
| Test case review | {rdate()} |
| Execution start | {rdate()} |
| Execution complete | {rdate()} |
| Results sign-off | {rdate()} |

---
*This document is synthetic and created for AI/RAG research purposes only.*
"""
        path = UNSTRUCTURED / "test_plans" / f"TP-{suite['suite_id']}.md"
        write_doc(path, content)
    print(f"  ✓ test_plans/              {len(sampled):>4} documents")

# ──────────────────────────────────────────────────────────────────────────────
# 3. TEST CASE DOCUMENTS
# ──────────────────────────────────────────────────────────────────────────────

def gen_test_case_docs(tcs, steps, apps, reqs, count=40):
    app_map  = {a["application_id"]: a["name"] for a in apps}
    req_map  = {r["requirement_id"]: r for r in reqs}
    tc_steps = {}
    for s in steps:
        tc_steps.setdefault(s["test_case_id"], []).append(s)

    sampled = random.sample(tcs, min(count, len(tcs)))
    for tc in sampled:
        app_name = app_map.get(tc["application_id"], tc["application_id"])
        req      = req_map.get(tc["requirement_id"], {})
        my_steps = sorted(tc_steps.get(tc["test_case_id"], []), key=lambda x: int(x["step_number"]))

        steps_md = "\n".join(
            f"| {s['step_number']} | {s['action']} | {s['expected_result']} | `{s['input_data']}` |"
            for s in my_steps
        )

        content = f"""---
document_id: TCD-{tc['test_case_id']}
document_type: test_case
title: {tc['title'][:100]}
application: {app_name}
test_case_id: {tc['test_case_id']}
requirement_id: {tc['requirement_id']}
suite_id: {tc['suite_id']}
priority: {tc.get('priority','Medium')}
test_type: {tc.get('test_type','Functional')}
automation_status: {tc.get('automation_status','Manual')}
---

# Test Case Specification
## {tc['title'][:100]}

**Test Case ID:** {tc['test_case_id']}
**Application:** {app_name}
**Requirement:** {tc['requirement_id']} — {req.get('title','(see requirements.csv)')}
**Suite:** {tc['suite_id']}
**Type:** {tc.get('test_type','Functional')}
**Priority:** {tc.get('priority','Medium')}
**Automation:** {tc.get('automation_status','Manual')}
**Estimated Duration:** {tc.get('estimated_duration','N/A')} seconds

---

## 1. Objective

{tc.get('objective', tc['description'])}

## 2. Preconditions

{tc.get('preconditions','Device is enrolled and connected to the test network.')}

## 3. Test Steps

| Step | Action | Expected Result | Input Data |
|------|--------|----------------|------------|
{steps_md if steps_md else "| 1 | Execute test case | Expected pass | N/A |"}

## 4. Post-conditions

- System returns to a stable state after test execution.
- No residual data corruption or side-effects on subsequent tests.

## 5. Related Requirement

**{tc['requirement_id']}:** {req.get('description', 'See requirements.csv for full description.')}

---
*This document is synthetic and created for AI/RAG research purposes only.*
"""
        path = UNSTRUCTURED / "test_cases" / f"TCD-{tc['test_case_id']}.md"
        write_doc(path, content)
    print(f"  ✓ test_cases/              {len(sampled):>4} documents")

# ──────────────────────────────────────────────────────────────────────────────
# 4. EXECUTION REPORT DOCUMENTS
# ──────────────────────────────────────────────────────────────────────────────

def gen_execution_report_docs(runs, execs, apps, count=15):
    app_map  = {a["application_id"]: a["name"] for a in apps}
    run_execs = {}
    for ex in execs:
        run_execs.setdefault(ex["test_run_id"], []).append(ex)

    sampled = random.sample(runs, min(count, len(runs)))
    for run in sampled:
        rex    = run_execs.get(run["run_id"], [])
        passed = int(run.get("passed","0") or 0)
        failed = int(run.get("failed","0") or 0)
        blocked= int(run.get("blocked","0") or 0)
        skipped= int(run.get("skipped","0") or 0)
        total  = int(run.get("total_tests","0") or 0)
        rate   = run.get("pass_rate","0")

        # Sample of failures in this run
        fail_execs = [e for e in rex if e.get("status") == "FAIL"][:5]
        fail_rows_md = "\n".join(
            f"| {e['execution_id']} | {e['test_case_id']} | {e.get('failure_id','—')} | {e.get('defect_id','—')} |"
            for e in fail_execs
        )

        content = f"""---
document_id: EXEC-RPT-{run['run_id']}
document_type: execution_report
title: Execution Report — {run['name']}
run_id: {run['run_id']}
build_version: {run['build_version']}
release_id: {run.get('release_id','REL-001')}
start_time: {run.get('start_time','N/A')}
end_time: {run.get('end_time','N/A')}
---

# Test Execution Report
## {run['name']}

**Run ID:** {run['run_id']}
**Build:** {run['build_version']}
**Release:** {run.get('release_id','REL-001')}
**Environment:** {run.get('environment_id','ENV-001')}
**Status:** {run.get('status','Completed')}

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| Total Tests | {total} |
| Passed | {passed} |
| Failed | {failed} |
| Blocked | {blocked} |
| Skipped | {skipped} |
| Pass Rate | {rate}% |

## 2. Execution Timeline

- **Start:** {run.get('start_time','N/A')}
- **End:** {run.get('end_time','N/A')}
- **Duration:** Approximately {random.randint(2,12)} hours

## 3. Failed Test Cases

The following test cases failed during this execution cycle:

| Execution ID | Test Case ID | Failure ID | Defect ID |
|-------------|-------------|-----------|----------|
{fail_rows_md if fail_rows_md else "| — | No failures in this run | — | — |"}

## 4. Blocked Tests

{blocked} tests were blocked due to environment instability or prerequisite failures.

## 5. Key Findings

{"- **Authentication failures** accounted for " + str(random.randint(10,30)) + "% of total failures." if failed > 0 else "- No critical failures observed."}
{"- Network-related failures detected under low-bandwidth profile." if failed > 2 else ""}
{"- Performance SLA violations observed in " + str(random.randint(1,5)) + " test cases." if failed > 1 else ""}

## 6. Recommendations

- Investigate recurring failures linked to the **{random.choice(["Authentication","Sync Engine","Network Stack"])}** component.
- Re-run blocked tests in a stable environment before release sign-off.
- Assign open defects to the responsible component team immediately.

---
*This document is synthetic and created for AI/RAG research purposes only.*
"""
        path = UNSTRUCTURED / "execution_reports" / f"EXEC-RPT-{run['run_id']}.md"
        write_doc(path, content)
    print(f"  ✓ execution_reports/       {len(sampled):>4} documents")

# ──────────────────────────────────────────────────────────────────────────────
# 5. FAILURE LOG DOCUMENTS
# ──────────────────────────────────────────────────────────────────────────────

def gen_failure_log_docs(fails, execs, apps, tcs, count=60):
    app_map = {a["application_id"]: a["name"] for a in apps}
    tc_map  = {t["test_case_id"]: t for t in tcs}
    ex_map  = {e["execution_id"]: e for e in execs}

    sampled = random.sample(fails, min(count, len(fails)))
    for fail in sampled:
        app_name = app_map.get(fail["application_id"], fail["application_id"])
        tc       = tc_map.get(fail["test_case_id"], {})
        ex       = ex_map.get(fail["execution_id"], {})

        content = f"""---
document_id: {fail['failure_id']}
document_type: failure_log
title: Failure Report — {fail['failure_id']}
application: {app_name}
failure_id: {fail['failure_id']}
test_case_id: {fail['test_case_id']}
execution_id: {fail.get('execution_id','N/A')}
build_version: {fail.get('build_version','N/A')}
timestamp: {fail.get('timestamp','N/A')}
severity: {fail.get('severity','Major')}
failure_type: {fail['failure_type']}
---

# Failure Report
## {fail['failure_id']} — {fail['failure_type']}

**Application:** {app_name}
**Build:** {fail.get('build_version','N/A')}
**Test Case:** {fail['test_case_id']} — {tc.get('title','(see test_cases.csv)')[:80]}
**Execution ID:** {fail.get('execution_id','N/A')}
**Environment:** {fail.get('environment','N/A')}
**Severity:** {fail.get('severity','Major')}
**Timestamp:** {fail.get('timestamp','N/A')}

---

## 1. Summary

A **{fail['failure_type']}** was detected during execution of test case `{fail['test_case_id']}`
in the `{app_name}` application (build `{fail.get('build_version','N/A')}`).

**Component affected:** {fail.get('component','N/A')}

## 2. Expected Behaviour

{fail.get('expected_behavior', 'The system should complete the operation successfully within the defined SLA.')}

## 3. Observed Behaviour

{fail.get('observed_behavior', 'The system produced an unexpected error during test execution.')}

## 4. Error Details

```
{fail.get('error_message','N/A')}
```

## 5. Stack Trace

```
{fail.get('stack_trace','N/A')}
```

## 6. Log Reference

Log bundle: `{fail.get('log_reference','N/A')}`

## 7. Root Cause Analysis

{fail.get('root_cause', 'Root cause analysis pending.')}

## 8. Resolution Status

**Status:** {fail.get('resolution_status','Open')}

## 9. Related Defect

This failure is tracked under defect `BUG-{int(fail['failure_id'].split('-')[1]) % 520 + 1:04d}`.

## 10. Recurrence History

This failure pattern has been observed in previous regression cycles.
Refer to `historical_failures.csv` for full recurrence data.

---
*This document is synthetic and created for AI/RAG research purposes only.*
"""
        path = UNSTRUCTURED / "failure_logs" / f"{fail['failure_id']}.md"
        write_doc(path, content)
    print(f"  ✓ failure_logs/            {len(sampled):>4} documents")

# ──────────────────────────────────────────────────────────────────────────────
# 6. DEFECT REPORT DOCUMENTS
# ──────────────────────────────────────────────────────────────────────────────

def gen_defect_report_docs(defects, apps, count=50):
    app_map = {a["application_id"]: a["name"] for a in apps}
    sampled = random.sample(defects, min(count, len(defects)))
    for defect in sampled:
        app_name = app_map.get(defect["application_id"], defect["application_id"])
        content = f"""---
document_id: DR-{defect['defect_id']}
document_type: defect_report
title: Defect Report — {defect['defect_id']}
application: {app_name}
defect_id: {defect['defect_id']}
related_failure: {defect['related_failure']}
related_test_case: {defect['related_test_case']}
affected_requirement: {defect['affected_requirement']}
severity: {defect['severity']}
priority: {defect['priority']}
status: {defect['status']}
reported_date: {defect.get('reported_date','N/A')}
---

# Defect Report
## {defect['defect_id']} — {defect['title'][:80]}

**Application:** {app_name}
**Component:** {defect['component']}
**Severity:** {defect['severity']}
**Priority:** {defect['priority']}
**Status:** {defect['status']}
**Reported:** {defect.get('reported_date','N/A')}
**Resolved:** {defect.get('resolved_date','Pending') or 'Pending'}
**Assigned To:** {defect.get('assigned_engineer','N/A')}

---

## 1. Problem Description

{defect['description']}

## 2. Traceability

| Artifact | ID |
|----------|----|
| Failure Report | {defect['related_failure']} |
| Test Case | {defect['related_test_case']} |
| Affected Requirement | {defect['affected_requirement']} |

## 3. Steps to Reproduce

1. Execute test case `{defect['related_test_case']}`.
2. Observe the failure logged as `{defect['related_failure']}`.
3. Check the logs referenced in the failure report.

## 4. Root Cause

{defect.get('root_cause','Root cause analysis in progress.')}

## 5. Resolution

{defect.get('resolution','Resolution pending.') or 'Defect under investigation.'}

## 6. Verification

{"Verified by re-executing test case `" + defect['related_test_case'] + "` after fix deployment." if defect.get('status') in ("FIXED","VERIFIED","CLOSED") else "Pending verification after fix."}

## 7. Impact Assessment

This defect affects the **{defect.get('component','N/A')}** component and is traced back
to requirement **{defect['affected_requirement']}**.

If unresolved, it may block release sign-off for the associated test suite.

---
*This document is synthetic and created for AI/RAG research purposes only.*
"""
        path = UNSTRUCTURED / "defect_reports" / f"DR-{defect['defect_id']}.md"
        write_doc(path, content)
    print(f"  ✓ defect_reports/          {len(sampled):>4} documents")

# ──────────────────────────────────────────────────────────────────────────────
# 7. RELEASE NOTES
# ──────────────────────────────────────────────────────────────────────────────

def gen_release_notes(releases, apps, defects, count=8):
    app_map = {a["application_id"]: a["name"] for a in apps}
    sampled = releases[:count]
    for rel in sampled:
        fixed_defects = random.sample(defects, min(8, len(defects)))
        fd_md = "\n".join(
            f"- [{d['defect_id']}] {d['title'][:70]} *(Component: {d['component']})*"
            for d in fixed_defects
            if d.get("status") in ("FIXED","VERIFIED","CLOSED")
        ) or "- No defect fixes in this release."

        content = f"""---
document_id: RN-{rel['release_id']}
document_type: release_notes
title: Release Notes — {rel['name']}
release_id: {rel['release_id']}
version: {rel['version']}
release_date: {rel.get('release_date','N/A')}
status: {rel.get('status','Released')}
---

# Release Notes
## {rel['name']} (v{rel['version']})

**Release ID:** {rel['release_id']}
**Release Date:** {rel.get('release_date','N/A')}
**Status:** {rel.get('status','Released')}

---

## 1. Overview

This release delivers stability improvements, security patches, and new feature
capabilities across the enterprise test management platform.

## 2. What's New

- Enhanced **{random.choice(["Bluetooth reconnection","payment processing","voice recognition","health metric sync"])}** stability.
- Improved **{random.choice(["session token management","push notification delivery","firmware update"])}** reliability.
- New **{random.choice(["diagnostics dashboard","dark mode","offline queue"])}** capability.

## 3. Defects Fixed

{fd_md}

## 4. Known Issues

- Intermittent **{random.choice(["synchronization delay","UI freeze","push notification loss"])}** under high network load — workaround available.
- **{random.choice(["Bluetooth pairing","NFC tap-to-pay","biometric verification"])}** may require a device restart on first use after upgrade.

## 5. Upgrade Notes

- Requires firmware ≥ {random.randint(4,5)}.{random.randint(0,3)}.0 on mobile devices.
- Database migration `v{rel['version']}` will run automatically on first launch.
- Clear app cache after upgrade to avoid stale configuration issues.

## 6. Test Coverage

This release was validated against **{random.randint(1800,2100)}** test cases across
**{random.randint(8,12)}** regression cycles. Pass rate: **{random.randint(94,99)}.{random.randint(0,9)}%**.

---
*This document is synthetic and created for AI/RAG research purposes only.*
"""
        path = UNSTRUCTURED / "release_notes" / f"RN-{rel['release_id']}.md"
        write_doc(path, content)
    print(f"  ✓ release_notes/           {len(sampled):>4} documents")

# ──────────────────────────────────────────────────────────────────────────────
# 8. TROUBLESHOOTING GUIDES
# ──────────────────────────────────────────────────────────────────────────────

TROUBLESHOOTING_TOPICS = [
    ("TS-BT-001",  "Bluetooth Pairing Failure Troubleshooting Guide",
     "Bluetooth connectivity", "ConnectedDevices",
     ["BluetoothException: device disconnected during pairing handshake",
      "GATT error 133","Pairing rejected by remote device"],
     ["Ensure the target device is in pairing mode and within 1 metre.",
      "Clear the Bluetooth cache on both devices.",
      "Verify that no other device is actively connected to the same peripheral.",
      "Check firmware version — update if below minimum pairing firmware.",
      "Disable battery optimisation for the Bluetooth service.",
      "Restart the Bluetooth stack using the diagnostic tool."]),
    ("TS-AUTH-001","Authentication Failure Troubleshooting Guide",
     "user authentication", "SecureAuthentication",
     ["JWT token validation failed — signature mismatch",
      "AuthError: token expired","OAuth2 redirect URI mismatch"],
     ["Verify that the device system clock is synchronised with NTP.",
      "Clear the app token cache and force a fresh token request.",
      "Check that the OAuth2 redirect URI is whitelisted in the auth server.",
      "Review server-side logs for error code EVT-4401 or EVT-4403.",
      "Ensure the signing key has not been rotated without propagating to all replicas.",
      "Re-enrol the device if the token remains invalid after the above steps."]),
    ("TS-SYNC-001","Data Synchronisation Failure Troubleshooting Guide",
     "data synchronisation", "SmartHome",
     ["SyncError: conflict detected on entity",
      "Timestamps diverge by more than 120 seconds","Sync queue overflow"],
     ["Check network connectivity and switch to a stable WiFi network.",
      "Force a manual sync from Settings > Account > Sync Now.",
      "Inspect the sync conflict log for entity IDs causing divergence.",
      "Verify that the background sync service is not battery-optimised out.",
      "If the conflict persists, reset the local sync state from the diagnostic menu.",
      "Escalate to the Sync Engine team if more than 50 entities are in conflict."]),
    ("TS-PERF-001","Performance Degradation Troubleshooting Guide",
     "application performance", "GalaxySearch",
     ["p95 latency exceeds 500ms SLA","ANR detected in main thread",
      "Memory usage exceeds 256MB ceiling"],
     ["Profile the application using the built-in performance monitor.",
      "Check for synchronous network calls on the main UI thread.",
      "Review recent code changes for new blocking operations.",
      "Increase available heap if memory ceiling is hit consistently.",
      "Reduce the search index rebuild interval to off-peak hours.",
      "Enable query caching to reduce repeat index lookups."]),
    ("TS-NET-001", "Network Failure Troubleshooting Guide",
     "network connectivity", "MobileCommunication",
     ["SocketException: Connection reset by peer",
      "HTTP 503 Service Unavailable","DNS resolution timeout"],
     ["Verify network profile is correctly set in the test environment.",
      "Check gateway health and upstream service availability.",
      "Implement exponential back-off in the retry logic.",
      "Use the network emulator to reproduce the failure reliably.",
      "Confirm firewall rules allow traffic on the required ports.",
      "Review CDN configuration for caching anomalies during peak load."]),
]

def gen_troubleshooting_docs():
    for ts_id, title, topic, app, symptoms, steps in TROUBLESHOOTING_TOPICS:
        symp_md  = "\n".join(f"- `{s}`" for s in symptoms)
        steps_md = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        content  = f"""---
document_id: {ts_id}
document_type: troubleshooting
title: {title}
application: {app}
topic: {topic}
---

# {title}

**Application:** {app}
**Topic:** {topic.title()}

---

## 1. Symptoms

The following symptoms indicate a **{topic}** failure:

{symp_md}

## 2. Diagnostic Steps

{steps_md}

## 3. When to Escalate

Escalate to the {app} platform team if:

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
"""
        path = UNSTRUCTURED / "troubleshooting" / f"{ts_id}.md"
        write_doc(path, content)
    print(f"  ✓ troubleshooting/         {len(TROUBLESHOOTING_TOPICS):>4} documents")

# ──────────────────────────────────────────────────────────────────────────────
# 9. PROJECT DOCUMENTATION
# ──────────────────────────────────────────────────────────────────────────────

def gen_project_docs():
    docs = [
        ("ARCH-001", "System Architecture Overview",
         """# System Architecture Overview

## Purpose

This document describes the high-level architecture of the AI-Powered Test
Management System using Hybrid RAG Pipelines.

## Components

### 1. Data Ingestion Layer
- Accepts structured test data (CSV) and unstructured documents (Markdown/PDF).
- Parses and chunks documents into overlapping text segments.
- Generates dense vector embeddings using a sentence-transformer model.

### 2. Vector Database
- Stores chunk embeddings alongside metadata (document_id, source entity IDs).
- Supports approximate nearest-neighbour (ANN) search for semantic retrieval.

### 3. Knowledge Graph
- Nodes: Application, Requirement, TestCase, Execution, Failure, Defect, Engineer, Environment.
- Edges: IMPLEMENTS, HAS_EXECUTION, PRODUCED, LINKED_TO, AFFECTS, ASSIGNED_TO, etc.
- Supports multi-hop traversal for traceability queries.

### 4. Hybrid RAG Pipeline
- **Vanilla RAG path:** Embeds the query → ANN search → retrieve top-k chunks → LLM answer.
- **Graph RAG path:** Entity extraction → graph traversal → subgraph context → LLM answer.
- **Hybrid path:** Runs both paths, merges context, scores evidence, generates answer.

### 5. LLM Layer
- Receives merged context from the Hybrid RAG pipeline.
- Generates natural-language insights about test execution, failures, and defects.

## Data Flow

```
Structured CSV ──► PostgreSQL ──► Graph Builder ──► Neo4j
Unstructured MD ──► Chunker ──► Embedder ──► Qdrant (Vector DB)
                                         ↓
User Query ──► Query Router ──► [Vanilla RAG | Graph RAG | Hybrid RAG]
                                         ↓
                                   LLM (Gemini / GPT)
                                         ↓
                              Test Execution Insights
```

*This document is synthetic and created for AI/RAG research purposes only.*
"""),
        ("ONBOARD-001", "QA Onboarding Guide",
         """# QA Engineer Onboarding Guide

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
"""),
        ("EVAL-GUIDE-001","Hybrid RAG Evaluation Guide",
         """# Hybrid RAG Evaluation Guide

## Purpose

This guide describes how to evaluate the retrieval quality and answer quality
of the Hybrid RAG pipeline using the provided evaluation dataset.

## Evaluation Dataset Structure

- `evaluation/questions.jsonl` — 300 queries (semantic, graph, hybrid)
- `evaluation/ground_truth.jsonl` — expected answers keyed by query_id
- `evaluation/expected_entities.jsonl` — entities that must be retrieved
- `evaluation/expected_relationships.jsonl` — graph paths that must be traversed

## Metrics

### Retrieval Metrics (Vanilla RAG)
- **Recall@k** — fraction of expected documents retrieved in top-k results.
- **Precision@k** — fraction of retrieved documents that are relevant.
- **MRR** — Mean Reciprocal Rank of the first relevant document.
- **NDCG** — Normalised Discounted Cumulative Gain.

### Graph Retrieval Metrics (Graph RAG)
- **Entity Recall** — fraction of expected entities found in the subgraph context.
- **Relationship Recall** — fraction of expected relationships traversed.
- **Path Accuracy** — whether the correct multi-hop path was followed.

### Answer Quality Metrics (LLM)
- **ROUGE-L** — longest common subsequence overlap with reference answer.
- **BERTScore** — semantic similarity between generated and reference answer.
- **Faithfulness** — whether the answer is grounded in the retrieved context.
- **Completeness** — whether the answer addresses all aspects of the question.

## Running an Evaluation

```python
from evaluation import HybridRAGEvaluator
evaluator = HybridRAGEvaluator(pipeline=hybrid_rag_pipeline)
results = evaluator.run(questions_path="evaluation/questions.jsonl",
                        ground_truth_path="evaluation/ground_truth.jsonl")
evaluator.report(results)
```

*This document is synthetic and created for AI/RAG research purposes only.*
"""),
    ]
    for doc_id, title, content in docs:
        path = UNSTRUCTURED / "project_documentation" / f"{doc_id}.md"
        write_doc(path, content)
    print(f"  ✓ project_documentation/   {len(docs):>4} documents")

# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("\n=== Unstructured Document Generator ===\n")

    # Load structured data
    apps    = load_csv("applications.csv")
    reqs    = load_csv("requirements.csv")
    suites  = load_csv("test_suites.csv")
    tcs     = load_csv("test_cases.csv")
    steps   = load_csv("test_steps.csv")
    runs    = load_csv("test_runs.csv")
    execs   = load_csv("test_executions.csv")
    fails   = load_csv("failures.csv")
    defects = load_csv("defects.csv")
    rels_   = load_csv("releases.csv")

    if not apps:
        print("ERROR: structured CSVs not found. Run generate_dataset.py first.")
        return

    print("Generating documents…")
    gen_requirement_docs(reqs, apps, count=40)
    gen_test_plan_docs(suites, apps, reqs, count=20)
    gen_test_case_docs(tcs, steps, apps, reqs, count=40)
    gen_execution_report_docs(runs, execs, apps, count=12)
    gen_failure_log_docs(fails, execs, apps, tcs, count=60)
    gen_defect_report_docs(defects, apps, count=50)
    gen_release_notes(rels_, apps, defects, count=8)
    gen_troubleshooting_docs()
    gen_project_docs()

    total = sum(
        len(list((UNSTRUCTURED / d).glob("*.md")))
        for d in ["requirements","test_plans","test_cases","execution_reports",
                  "failure_logs","defect_reports","release_notes","troubleshooting",
                  "project_documentation"]
        if (UNSTRUCTURED / d).exists()
    )
    print(f"\nTotal documents generated: {total}")
    print("\nDocument generation complete.\n")

if __name__ == "__main__":
    main()
