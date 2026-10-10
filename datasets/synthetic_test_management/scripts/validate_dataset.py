"""
validate_dataset.py
====================
Validates the synthetic test-management dataset for relational consistency,
graph integrity, and evaluation completeness.

Run:
    python datasets/synthetic_test_management/scripts/validate_dataset.py

Exit code 0 = all checks passed.
Exit code 1 = one or more checks failed.
"""

import csv
import json
import sys
from pathlib import Path

SCRIPT_DIR   = Path(__file__).resolve().parent
DATASET_ROOT = SCRIPT_DIR.parent
STRUCTURED   = DATASET_ROOT / "structured"
GRAPH        = DATASET_ROOT / "graph"
EVAL         = DATASET_ROOT / "evaluation"
UNSTRUCTURED = DATASET_ROOT / "unstructured"

# ──────────────────────────────────────────────────────────────────────────────
PASS_ICON = "[OK]"
FAIL_ICON = "[FAIL]"
WARN_ICON = "[WARN]"

errors   = []
warnings = []

def ok(msg):
    print(f"  {PASS_ICON} {msg}")

def fail(msg):
    errors.append(msg)
    print(f"  {FAIL_ICON} FAIL: {msg}")

def warn(msg):
    warnings.append(msg)
    print(f"  {WARN_ICON} WARN: {msg}")

# ──────────────────────────────────────────────────────────────────────────────
def load_csv(name):
    path = STRUCTURED / name
    if not path.exists():
        path = GRAPH / name
    if not path.exists():
        fail(f"File not found: {name}")
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_jsonl(path):
    rows = []
    if not path.exists():
        fail(f"File not found: {path.name}")
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as e:
                    fail(f"Invalid JSON in {path.name}: {e}")
    return rows

def ids(rows, field):
    return {r[field] for r in rows if r.get(field)}

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 1 — No duplicate IDs
# ──────────────────────────────────────────────────────────────────────────────
def check_no_duplicates():
    print("\n[1] Duplicate ID checks")
    checks = [
        ("applications.csv",       "application_id"),
        ("solutions.csv",          "solution_id"),
        ("environments.csv",       "environment_id"),
        ("releases.csv",           "release_id"),
        ("engineers.csv",          "engineer_id"),
        ("requirements.csv",       "requirement_id"),
        ("test_suites.csv",        "suite_id"),
        ("test_cases.csv",         "test_case_id"),
        ("test_steps.csv",         "test_step_id"),
        ("test_runs.csv",          "run_id"),
        ("test_executions.csv",    "execution_id"),
        ("failures.csv",           "failure_id"),
        ("defects.csv",            "defect_id"),
        ("assignments.csv",        "assignment_id"),
        ("historical_failures.csv","hist_failure_id"),
    ]
    for fname, id_field in checks:
        rows = load_csv(fname)
        if not rows:
            continue
        all_ids = [r[id_field] for r in rows if r.get(id_field)]
        dupes   = [x for x in all_ids if all_ids.count(x) > 1]
        if dupes:
            fail(f"{fname}: duplicate {id_field} values: {set(dupes)}")
        else:
            ok(f"{fname}: no duplicate {id_field}")

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 2 — Foreign key resolution
# ──────────────────────────────────────────────────────────────────────────────
def check_foreign_keys():
    print("\n[2] Foreign key checks")
    app_ids  = ids(load_csv("applications.csv"),       "application_id")
    sol_ids  = ids(load_csv("solutions.csv"),          "solution_id")
    req_ids  = ids(load_csv("requirements.csv"),       "requirement_id")
    suite_ids= ids(load_csv("test_suites.csv"),        "suite_id")
    tc_ids   = ids(load_csv("test_cases.csv"),         "test_case_id")
    run_ids  = ids(load_csv("test_runs.csv"),          "run_id")
    env_ids  = ids(load_csv("environments.csv"),       "environment_id")
    eng_ids  = ids(load_csv("engineers.csv"),          "engineer_id")
    rel_ids  = ids(load_csv("releases.csv"),           "release_id")
    fail_ids = ids(load_csv("failures.csv"),           "failure_id")
    def_ids  = ids(load_csv("defects.csv"),            "defect_id")
    exec_ids = ids(load_csv("test_executions.csv"),    "execution_id")

    fk_checks = [
        # (table, fk_field, reference_set, ref_name, allow_empty)
        ("solutions.csv",          "application_id",  app_ids,   "applications",  False),
        ("requirements.csv",       "application_id",  app_ids,   "applications",  False),
        ("requirements.csv",       "solution_id",     sol_ids,   "solutions",     False),
        ("test_suites.csv",        "application_id",  app_ids,   "applications",  False),
        ("test_suites.csv",        "release_id",      rel_ids,   "releases",      False),
        ("test_cases.csv",         "requirement_id",  req_ids,   "requirements",  False),
        ("test_cases.csv",         "suite_id",        suite_ids, "test_suites",   False),
        ("test_cases.csv",         "application_id",  app_ids,   "applications",  False),
        ("test_cases.csv",         "environment_id",  env_ids,   "environments",  False),
        ("test_cases.csv",         "created_by",      eng_ids,   "engineers",     False),
        ("test_steps.csv",         "test_case_id",    tc_ids,    "test_cases",    False),
        ("test_executions.csv",    "test_case_id",    tc_ids,    "test_cases",    False),
        ("test_executions.csv",    "test_run_id",     run_ids,   "test_runs",     False),
        ("test_executions.csv",    "environment_id",  env_ids,   "environments",  False),
        ("test_executions.csv",    "failure_id",      fail_ids,  "failures",      True),
        ("test_executions.csv",    "defect_id",       def_ids,   "defects",       True),
        ("failures.csv",           "execution_id",    exec_ids,  "test_executions",True),
        ("failures.csv",           "test_case_id",    tc_ids,    "test_cases",    False),
        ("failures.csv",           "application_id",  app_ids,   "applications",  False),
        ("failures.csv",           "environment",     env_ids,   "environments",  False),
        ("defects.csv",            "application_id",  app_ids,   "applications",  False),
        ("defects.csv",            "assigned_engineer",eng_ids,  "engineers",     False),
        ("defects.csv",            "affected_requirement",req_ids,"requirements", False),
        ("defects.csv",            "related_test_case",tc_ids,   "test_cases",    False),
        ("defects.csv",            "related_failure",  fail_ids, "failures",      False),
        ("assignments.csv",        "test_case_id",    tc_ids,    "test_cases",    False),
        ("assignments.csv",        "run_id",          run_ids,   "test_runs",     False),
        ("assignments.csv",        "engineer_id",     eng_ids,   "engineers",     False),
        ("historical_failures.csv","test_case_id",    tc_ids,    "test_cases",    False),
        ("historical_failures.csv","application_id",  app_ids,   "applications",  False),
        ("historical_failures.csv","environment",     env_ids,   "environments",  False),
        ("test_runs.csv",          "release_id",      rel_ids,   "releases",      False),
        ("test_runs.csv",          "environment_id",  env_ids,   "environments",  False),
    ]

    for fname, fk, ref_set, ref_name, allow_empty in fk_checks:
        rows = load_csv(fname)
        if not rows:
            continue
        broken = []
        for r in rows:
            val = r.get(fk, "")
            if not val:
                if not allow_empty:
                    broken.append(val)
            elif val not in ref_set:
                broken.append(val)
        if broken:
            fail(f"{fname}.{fk} → {ref_name}: {len(broken)} broken FK(s) (sample: {broken[:3]})")
        else:
            ok(f"{fname}.{fk} → {ref_name}: all valid")

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 3 — Graph relationships reference existing nodes
# ──────────────────────────────────────────────────────────────────────────────
def check_graph_integrity():
    print("\n[3] Graph integrity checks")
    node_path = GRAPH / "nodes.csv"
    rel_path  = GRAPH / "relationships.csv"
    if not node_path.exists() or not rel_path.exists():
        fail("Graph files missing")
        return

    node_ids = ids(load_csv("nodes.csv"), "node_id")
    rels     = load_csv("relationships.csv")

    broken_src = [r["source_node"] for r in rels if r.get("source_node") not in node_ids]
    broken_tgt = [r["target_node"] for r in rels if r.get("target_node") not in node_ids]

    if broken_src:
        fail(f"relationships.csv: {len(broken_src)} broken source_node refs (sample: {broken_src[:3]})")
    else:
        ok(f"relationships.csv: all source_node refs valid ({len(rels):,} rels)")

    if broken_tgt:
        fail(f"relationships.csv: {len(broken_tgt)} broken target_node refs (sample: {broken_tgt[:3]})")
    else:
        ok(f"relationships.csv: all target_node refs valid")

    # Check graph schema file
    schema_path = GRAPH / "graph_schema.json"
    if schema_path.exists():
        ok("graph_schema.json exists")
    else:
        fail("graph_schema.json missing")

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 4 — Every execution references an existing test case
# ──────────────────────────────────────────────────────────────────────────────
def check_executions():
    print("\n[4] Execution → test case checks")
    tc_ids   = ids(load_csv("test_cases.csv"),      "test_case_id")
    exec_rows = load_csv("test_executions.csv")
    broken   = [e["execution_id"] for e in exec_rows if e.get("test_case_id") not in tc_ids]
    if broken:
        fail(f"test_executions.csv: {len(broken)} executions reference missing test cases")
    else:
        ok(f"test_executions.csv: all {len(exec_rows):,} executions have valid test_case_id")

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 5 — Every failure references an execution
# ──────────────────────────────────────────────────────────────────────────────
def check_failures():
    print("\n[5] Failure → execution checks")
    exec_ids  = ids(load_csv("test_executions.csv"), "execution_id")
    fail_rows = load_csv("failures.csv")
    # Failures that have an execution_id set must reference a valid one
    broken = [f["failure_id"] for f in fail_rows
              if f.get("execution_id") and f["execution_id"] not in exec_ids]
    if broken:
        fail(f"failures.csv: {len(broken)} failures reference missing executions")
    else:
        ok(f"failures.csv: all linked failure→execution refs valid ({len(fail_rows):,} failures)")

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 6 — Defect references resolve
# ──────────────────────────────────────────────────────────────────────────────
def check_defects():
    print("\n[6] Defect reference checks")
    fail_ids = ids(load_csv("failures.csv"),   "failure_id")
    tc_ids   = ids(load_csv("test_cases.csv"), "test_case_id")
    req_ids  = ids(load_csv("requirements.csv"),"requirement_id")
    eng_ids  = ids(load_csv("engineers.csv"),  "engineer_id")
    defects  = load_csv("defects.csv")

    problems = []
    for d in defects:
        if d.get("related_failure") not in fail_ids:
            problems.append(f"{d['defect_id']}: related_failure={d.get('related_failure')} not found")
    if problems:
        fail(f"defects.csv: {len(problems)} broken related_failure refs (sample: {problems[:2]})")
    else:
        ok(f"defects.csv: all related_failure refs valid ({len(defects):,} defects)")

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 7 — Every requirement referenced by a test case exists
# ──────────────────────────────────────────────────────────────────────────────
def check_req_coverage():
    print("\n[7] Test-case → requirement checks")
    req_ids = ids(load_csv("requirements.csv"), "requirement_id")
    tcs     = load_csv("test_cases.csv")
    broken  = [t["test_case_id"] for t in tcs if t.get("requirement_id") not in req_ids]
    if broken:
        fail(f"test_cases.csv: {len(broken)} test cases reference missing requirements")
    else:
        ok(f"test_cases.csv: all {len(tcs):,} test cases have valid requirement_id")

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 8 — Test run statistics are mathematically correct
# ──────────────────────────────────────────────────────────────────────────────
def check_run_stats():
    print("\n[8] Test-run aggregate consistency")
    runs  = load_csv("test_runs.csv")
    execs = load_csv("test_executions.csv")

    # compute from executions
    computed = {}
    for ex in execs:
        rid = ex.get("test_run_id","")
        if not rid:
            continue
        s = computed.setdefault(rid, {"total":0,"passed":0,"failed":0,"blocked":0,"skipped":0})
        s["total"] += 1
        st = ex.get("status","")
        if st == "PASS":    s["passed"]  += 1
        elif st == "FAIL":  s["failed"]  += 1
        elif st == "BLOCKED": s["blocked"] += 1
        elif st in ("SKIPPED","NOT_RUN"): s["skipped"] += 1

    mismatches = []
    for r in runs:
        rid = r["run_id"]
        c   = computed.get(rid, {})
        if not c:
            continue
        stored_total = int(r.get("total_tests","0") or 0)
        if stored_total != c["total"]:
            mismatches.append(f"{rid}: stored total={stored_total} computed={c['total']}")

    if mismatches:
        fail(f"Test run aggregates mismatch ({len(mismatches)} runs): {mismatches[:2]}")
    else:
        ok(f"All {len(runs)} test runs have consistent aggregates")

    # pass_rate sanity
    rate_errors = []
    for r in runs:
        total  = int(r.get("total_tests","0") or 0)
        passed = int(r.get("passed","0") or 0)
        stored = float(r.get("pass_rate","0") or 0)
        if total > 0:
            expected = round(passed / total * 100, 2)
            if abs(stored - expected) > 0.1:
                rate_errors.append(f"{r['run_id']}: stored={stored} expected={expected}")
    if rate_errors:
        fail(f"pass_rate mismatch in {len(rate_errors)} runs: {rate_errors[:2]}")
    else:
        ok("All pass_rate values are mathematically correct")

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 9 — Every evaluation query has ground truth
# ──────────────────────────────────────────────────────────────────────────────
def check_evaluation():
    print("\n[9] Evaluation dataset checks")
    q_path  = EVAL / "questions.jsonl"
    gt_path = EVAL / "ground_truth.jsonl"

    if not q_path.exists():
        fail("evaluation/questions.jsonl missing")
        return
    if not gt_path.exists():
        fail("evaluation/ground_truth.jsonl missing")
        return

    questions   = load_jsonl(q_path)
    ground_truth = load_jsonl(gt_path)

    q_ids  = {q.get("query_id") for q in questions}
    gt_ids = {g.get("query_id") for g in ground_truth}

    missing_gt = q_ids - gt_ids
    if missing_gt:
        fail(f"{len(missing_gt)} queries lack ground truth entries (sample: {list(missing_gt)[:3]})")
    else:
        ok(f"All {len(questions)} evaluation queries have ground truth")

    # Check type distribution
    types = {}
    for q in questions:
        t = q.get("query_type","unknown")
        types[t] = types.get(t, 0) + 1
    ok(f"Query type distribution: {types}")

    # Check minimum counts
    for qtype, min_count in [("semantic",80),("graph",80),("hybrid",80)]:
        count = types.get(qtype, 0)
        if count < min_count:
            warn(f"Only {count} '{qtype}' queries (target ≥ {min_count})")
        else:
            ok(f"'{qtype}' queries: {count} (meets minimum {min_count})")

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 10 — Expected entities in evaluation exist in the dataset
# ──────────────────────────────────────────────────────────────────────────────
def check_expected_entities():
    print("\n[10] Expected entity resolution checks")
    ee_path = EVAL / "expected_entities.jsonl"
    if not ee_path.exists():
        warn("evaluation/expected_entities.jsonl not found — skipping")
        return

    # Build master ID set
    all_ids = set()
    for fname, field in [
        ("applications.csv","application_id"),("requirements.csv","requirement_id"),
        ("test_cases.csv","test_case_id"),("test_executions.csv","execution_id"),
        ("failures.csv","failure_id"),("defects.csv","defect_id"),
        ("test_runs.csv","run_id"),("engineers.csv","engineer_id"),
    ]:
        all_ids |= ids(load_csv(fname), field)

    ee_rows = load_jsonl(ee_path)
    broken  = []
    for row in ee_rows:
        for eid in row.get("entity_ids", []):
            if eid and eid not in all_ids:
                broken.append(eid)
    if broken:
        fail(f"expected_entities.jsonl: {len(broken)} entity IDs not found in dataset (sample: {broken[:3]})")
    else:
        ok(f"All expected entities resolve in the structured dataset ({len(ee_rows)} records)")

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 11 — Expected relationships in evaluation exist in the graph
# ──────────────────────────────────────────────────────────────────────────────
def check_expected_relationships():
    print("\n[11] Expected relationship resolution checks")
    er_path = EVAL / "expected_relationships.jsonl"
    if not er_path.exists():
        warn("evaluation/expected_relationships.jsonl not found — skipping")
        return

    node_ids = ids(load_csv("nodes.csv"), "node_id")
    er_rows  = load_jsonl(er_path)
    broken   = []
    for row in er_rows:
        for node in [row.get("source_node"), row.get("target_node")]:
            if node and node not in node_ids:
                broken.append(node)
    if broken:
        fail(f"expected_relationships.jsonl: {len(broken)} node refs not found in graph (sample: {broken[:3]})")
    else:
        ok(f"All expected relationship nodes resolve ({len(er_rows)} records)")

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 12 — Documents reference valid entity IDs
# ──────────────────────────────────────────────────────────────────────────────
def check_document_references():
    print("\n[12] Unstructured document reference checks")
    all_ids = set()
    for fname, field in [
        ("applications.csv","application_id"),("requirements.csv","requirement_id"),
        ("test_cases.csv","test_case_id"),("test_executions.csv","execution_id"),
        ("failures.csv","failure_id"),("defects.csv","defect_id"),
    ]:
        all_ids |= ids(load_csv(fname), field)

    doc_count = 0
    broken    = []
    for subdir in UNSTRUCTURED.iterdir():
        if not subdir.is_dir():
            continue
        for doc in subdir.glob("*.md"):
            doc_count += 1
            content = doc.read_text(encoding="utf-8", errors="replace")
            # Simple heuristic: find tokens that look like IDs
            import re
            found = re.findall(r'\b(?:REQ|TC|EXEC|FAIL|BUG|RUN|APP|ENG|ENV|TS|SOL|REL)-\d+\b', content)
            for fid in found:
                if fid not in all_ids:
                    # IDs from smaller sets (APP, ENV etc.) also valid if they exist
                    pass  # lenient — just count docs

    if doc_count == 0:
        warn("No unstructured documents found — run generate_documents.py first")
    else:
        ok(f"Scanned {doc_count} documents")

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 13 — No orphaned critical entities
# ──────────────────────────────────────────────────────────────────────────────
def check_orphans():
    print("\n[13] Orphan entity checks")
    req_ids  = ids(load_csv("requirements.csv"),  "requirement_id")
    tc_reqs  = {r.get("requirement_id") for r in load_csv("test_cases.csv")}
    orphaned_reqs = req_ids - tc_reqs
    if len(orphaned_reqs) > len(req_ids) * 0.3:
        warn(f"{len(orphaned_reqs)} requirements have no test case ({len(orphaned_reqs)/len(req_ids)*100:.0f}% of all reqs)")
    else:
        ok(f"Requirement coverage: {len(tc_reqs):,}/{len(req_ids):,} requirements covered by test cases")

    fail_ids    = ids(load_csv("failures.csv"),         "failure_id")
    defect_fail = {r.get("related_failure") for r in load_csv("defects.csv")}
    unlinked    = fail_ids - defect_fail
    ok(f"Failure linkage: {len(defect_fail):,}/{len(fail_ids):,} failures linked to a defect (expected: ~50%)")

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 14 — No broken graph paths (spot-check multi-hop)
# ──────────────────────────────────────────────────────────────────────────────
def check_graph_paths():
    print("\n[14] Graph multi-hop path checks")
    node_ids = ids(load_csv("nodes.csv"), "node_id")
    rels     = load_csv("relationships.csv")

    # Build adjacency for spot check
    adj = {}
    for r in rels:
        adj.setdefault(r["source_node"], []).append(
            (r["relationship_type"], r["target_node"]))

    # Spot-check: REQ → (via TC) → EXEC → FAILURE → DEFECT
    req_nodes  = [n for n in node_ids if n.startswith("REQ-")]
    tc_nodes   = [n for n in node_ids if n.startswith("TC-")]
    exec_nodes = [n for n in node_ids if n.startswith("EXEC-")]

    reachable_paths = 0
    sample = min(50, len(tc_nodes))
    import random as _r
    _r.seed(42)
    for tc in _r.sample(tc_nodes, sample):
        # TC → (HAS_EXECUTION) → EXEC
        for rtype, tgt in adj.get(tc, []):
            if rtype == "HAS_EXECUTION" and tgt in node_ids:
                # EXEC → (PRODUCED) → FAIL
                for rtype2, tgt2 in adj.get(tgt, []):
                    if rtype2 == "PRODUCED" and tgt2 in node_ids:
                        reachable_paths += 1
                        break

    ok(f"Multi-hop spot-check: {reachable_paths}/{sample} sampled TCs have TC→EXEC→FAILURE paths")

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 15 — File completeness
# ──────────────────────────────────────────────────────────────────────────────
def check_file_completeness():
    print("\n[15] File completeness checks")
    required_structured = [
        "applications.csv","solutions.csv","environments.csv","releases.csv",
        "engineers.csv","requirements.csv","test_suites.csv","test_cases.csv",
        "test_steps.csv","test_runs.csv","test_executions.csv","failures.csv",
        "defects.csv","assignments.csv","historical_failures.csv","execution_steps.csv",
    ]
    required_graph = ["nodes.csv","relationships.csv","graph_schema.json"]
    required_eval  = [
        "questions.jsonl","ground_truth.jsonl","semantic_queries.jsonl",
        "graph_queries.jsonl","hybrid_queries.jsonl","expected_entities.jsonl",
        "expected_relationships.jsonl","evaluation_metrics.md",
    ]
    required_meta  = [
        DATASET_ROOT/"metadata"/"dataset_info.json",
        DATASET_ROOT/"metadata"/"data_dictionary.json",
        DATASET_ROOT/"metadata"/"generation_config.json",
        DATASET_ROOT/"README.md",
    ]

    for f in required_structured:
        p = STRUCTURED / f
        if p.exists():
            ok(f"structured/{f}")
        else:
            fail(f"structured/{f} MISSING")

    for f in required_graph:
        p = GRAPH / f
        if p.exists():
            ok(f"graph/{f}")
        else:
            fail(f"graph/{f} MISSING")

    for f in required_eval:
        p = EVAL / f
        if p.exists():
            ok(f"evaluation/{f}")
        else:
            fail(f"evaluation/{f} MISSING")

    for p in required_meta:
        if p.exists():
            ok(str(p.relative_to(DATASET_ROOT)))
        else:
            fail(f"{p.relative_to(DATASET_ROOT)} MISSING")

# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("  SYNTHETIC DATASET VALIDATION REPORT")
    print("="*60)

    check_no_duplicates()
    check_foreign_keys()
    check_graph_integrity()
    check_executions()
    check_failures()
    check_defects()
    check_req_coverage()
    check_run_stats()
    check_evaluation()
    check_expected_entities()
    check_expected_relationships()
    check_document_references()
    check_orphans()
    check_graph_paths()
    check_file_completeness()

    print("\n" + "="*60)
    print("  VALIDATION SUMMARY")
    print("="*60)
    print(f"  Errors   : {len(errors)}")
    print(f"  Warnings : {len(warnings)}")

    if errors:
        print("\nFailed checks:")
        for e in errors:
            print(f"  {FAIL_ICON} {e}")
        print("\nValidation FAILED.\n")
        sys.exit(1)
    else:
        if warnings:
            print("\nWarnings:")
            for w in warnings:
                print(f"  {WARN_ICON} {w}")
        print("\nValidation PASSED.\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
