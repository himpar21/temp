"""
generate_pdfs.py
================
Deterministic synthetic PDF generator for the AI-Powered Test Management
System — Hybrid RAG research project.

Reads existing structured CSVs (from the base dataset branch), selects entity
samples using a fixed seed, renders ReportLab PDFs, writes manifest CSV and
entity-mapping JSON, and generates all three input-fixture JSONL files plus
the evaluation dataset.

Run from the repo root:
    python datasets/synthetic_test_management/pdf_generation/generate_pdfs.py

All output lands inside:
    datasets/synthetic_test_management/pdf_documents/
    datasets/synthetic_test_management/pdf_metadata/
    datasets/synthetic_test_management/input_fixtures/
    datasets/synthetic_test_management/evaluation/pdf_input_evaluation/

Configuration constants near the top control counts.
SEED=42 makes every run identical.
"""

import csv
import io
import json
import os
import random
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Tuple

# ── Force UTF-8 for Windows console (must be first, before any other print) ──
def _force_utf8():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
_force_utf8()

# ── resolve paths ─────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
DATASET_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from data_loader import DataLoader
from relationship_resolver import RelationshipResolver
import templates as T

PDF_DOCS  = DATASET_ROOT / "pdf_documents"
META_DIR  = DATASET_ROOT / "pdf_metadata"
FIX_DIR   = DATASET_ROOT / "input_fixtures"
EVAL_DIR  = DATASET_ROOT / "evaluation" / "pdf_input_evaluation"

# ── configuration ─────────────────────────────────────────────────────────────
SEED = 42

N_REQ_PDFS   = 40
N_PLAN_PDFS  = 30
N_TC_PDFS    = 50
N_EXEC_PDFS  = 40
N_FAIL_PDFS  = 50
N_DEF_PDFS   = 40

N_LINE_ONLY   = 100
N_PDF_ONLY    = 50
N_LINE_PDF    = 150

random.seed(SEED)

# ── helpers ───────────────────────────────────────────────────────────────────

def _pick(lst, n):
    """Deterministic sample of up to n items."""
    random.seed(SEED)
    return random.sample(lst, min(n, len(lst)))

def _safe_pick(lst, n):
    random.seed(SEED)
    if not lst:
        return []
    return random.sample(lst, min(n, len(lst)))

def write_csv(path: Path, fieldnames: List[str], rows: List[Dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

def write_jsonl(path: Path, rows: List[Dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def _fid(filename: str) -> str:
    """Derive PDF-ID from filename stem."""
    return filename.replace(".pdf", "").upper().replace("-", "_")

# ── PDF generation ────────────────────────────────────────────────────────────

def gen_requirement_pdfs(dl: DataLoader, rr: RelationshipResolver) -> List[Dict]:
    records = []
    req_ids = _pick([r["requirement_id"] for r in dl.requirements], N_REQ_PDFS)
    for req_id in req_ids:
        ctx  = rr.requirement_context(req_id)
        req  = ctx["requirement"]
        fname = f"req_{req_id.lower().replace('-','_')}.pdf"
        out   = PDF_DOCS / "requirements" / fname
        try:
            T.render_requirement(ctx, out)
        except Exception as e:
            print(f"    [WARN] {fname}: {e}")
            continue
        tc_ids  = [t["test_case_id"] for t in ctx["related_test_cases"]]
        def_ids = [d["defect_id"]    for d in ctx["related_defects"]]
        records.append({
            "pdf_id":               f"PDF-REQ-{req_id}",
            "filename":             fname,
            "document_type":        "requirement_spec",
            "primary_entity_type":  "REQUIREMENT",
            "primary_entity_id":    req_id,
            "application_id":       req.get("application_id",""),
            "solution_id":          req.get("solution_id",""),
            "requirement_ids":      req_id,
            "test_case_ids":        "|".join(tc_ids),
            "execution_ids":        "",
            "failure_ids":          "",
            "defect_ids":           "|".join(def_ids),
            "release_id":           "",
            "environment_id":       "",
        })
    print(f"  [OK] requirements/   {len(records):>3} PDFs")
    return records

def gen_test_plan_pdfs(dl: DataLoader, rr: RelationshipResolver) -> List[Dict]:
    records = []
    suite_ids = _pick([s["suite_id"] for s in dl.test_suites], N_PLAN_PDFS)
    for suite_id in suite_ids:
        ctx   = rr.test_plan_context(suite_id)
        suite = ctx["suite"]
        fname = f"plan_{suite_id.lower().replace('-','_')}.pdf"
        out   = PDF_DOCS / "test_plans" / fname
        try:
            T.render_test_plan(ctx, out)
        except Exception as e:
            print(f"    [WARN] {fname}: {e}")
            continue
        tc_ids  = [t["test_case_id"] for t in ctx["test_cases"]]
        req_ids = [r["requirement_id"] for r in ctx["requirements"]]
        records.append({
            "pdf_id":               f"PDF-PLAN-{suite_id}",
            "filename":             fname,
            "document_type":        "test_plan",
            "primary_entity_type":  "TEST_SUITE",
            "primary_entity_id":    suite_id,
            "application_id":       suite.get("application_id",""),
            "solution_id":          "",
            "requirement_ids":      "|".join(req_ids),
            "test_case_ids":        "|".join(tc_ids),
            "execution_ids":        "",
            "failure_ids":          "",
            "defect_ids":           "",
            "release_id":           suite.get("release_id",""),
            "environment_id":       "",
        })
    print(f"  [OK] test_plans/     {len(records):>3} PDFs")
    return records

def gen_test_case_pdfs(dl: DataLoader, rr: RelationshipResolver) -> List[Dict]:
    records = []
    # pick TCs that have steps (richer PDFs)
    tcs_with_steps = [tc_id for tc_id in dl.steps_by_tc if dl.steps_by_tc[tc_id]]
    tc_ids = _pick(tcs_with_steps, N_TC_PDFS)
    for tc_id in tc_ids:
        ctx  = rr.test_case_context(tc_id)
        tc   = ctx["test_case"]
        fname = f"tc_{tc_id.lower().replace('-','_')}.pdf"
        out   = PDF_DOCS / "test_cases" / fname
        try:
            T.render_test_case(ctx, out)
        except Exception as e:
            print(f"    [WARN] {fname}: {e}")
            continue
        exec_ids = [e["execution_id"] for e in ctx["recent_executions"]]
        fail_ids = [f["failure_id"]   for f in ctx["failures"]]
        def_ids  = [d["defect_id"]    for d in ctx["defects"]]
        records.append({
            "pdf_id":               f"PDF-TC-{tc_id}",
            "filename":             fname,
            "document_type":        "test_case_spec",
            "primary_entity_type":  "TEST_CASE",
            "primary_entity_id":    tc_id,
            "application_id":       tc.get("application_id",""),
            "solution_id":          "",
            "requirement_ids":      tc.get("requirement_id",""),
            "test_case_ids":        tc_id,
            "execution_ids":        "|".join(exec_ids),
            "failure_ids":          "|".join(fail_ids),
            "defect_ids":           "|".join(def_ids),
            "release_id":           "",
            "environment_id":       tc.get("environment_id",""),
        })
    print(f"  [OK] test_cases/     {len(records):>3} PDFs")
    return records

def gen_execution_pdfs(dl: DataLoader, rr: RelationshipResolver) -> List[Dict]:
    records = []
    # prefer FAIL executions — richer content
    fail_execs = [e["execution_id"] for e in dl.test_executions if e.get("failure_id")]
    pass_execs = [e["execution_id"] for e in dl.test_executions if e.get("status") == "PASS"]
    random.seed(SEED + 1)
    chosen_fail = random.sample(fail_execs, min(25, len(fail_execs)))
    chosen_pass = random.sample(pass_execs, min(15, len(pass_execs)))
    exec_ids = chosen_fail + chosen_pass
    for exec_id in exec_ids:
        ctx  = rr.execution_context(exec_id)
        ex   = ctx["execution"]
        fname = f"exec_{exec_id.lower().replace('-','_')}.pdf"
        out   = PDF_DOCS / "execution_reports" / fname
        try:
            T.render_execution_report(ctx, out)
        except Exception as e:
            print(f"    [WARN] {fname}: {e}")
            continue
        records.append({
            "pdf_id":               f"PDF-EXEC-{exec_id}",
            "filename":             fname,
            "document_type":        "execution_report",
            "primary_entity_type":  "TEST_EXECUTION",
            "primary_entity_id":    exec_id,
            "application_id":       ctx["test_case"].get("application_id",""),
            "solution_id":          "",
            "requirement_ids":      ctx["requirement"].get("requirement_id",""),
            "test_case_ids":        ex.get("test_case_id",""),
            "execution_ids":        exec_id,
            "failure_ids":          ex.get("failure_id",""),
            "defect_ids":           ex.get("defect_id",""),
            "release_id":           ctx["release"].get("release_id",""),
            "environment_id":       ex.get("environment_id",""),
        })
    print(f"  [OK] execution_reports/ {len(records):>3} PDFs")
    return records

def gen_failure_pdfs(dl: DataLoader, rr: RelationshipResolver) -> List[Dict]:
    records = []
    # pick failures that have an execution_id (linked)
    linked = [f["failure_id"] for f in dl.failures if f.get("execution_id")]
    fail_ids = _pick(linked, N_FAIL_PDFS)
    for fail_id in fail_ids:
        ctx  = rr.failure_context(fail_id)
        fail = ctx["failure"]
        fname = f"fail_{fail_id.lower().replace('-','_')}.pdf"
        out   = PDF_DOCS / "failure_reports" / fname
        try:
            T.render_failure_report(ctx, out)
        except Exception as e:
            print(f"    [WARN] {fname}: {e}")
            continue
        defect = ctx["defect"]
        records.append({
            "pdf_id":               f"PDF-FAIL-{fail_id}",
            "filename":             fname,
            "document_type":        "failure_report",
            "primary_entity_type":  "FAILURE",
            "primary_entity_id":    fail_id,
            "application_id":       fail.get("application_id",""),
            "solution_id":          "",
            "requirement_ids":      ctx["requirement"].get("requirement_id",""),
            "test_case_ids":        fail.get("test_case_id",""),
            "execution_ids":        fail.get("execution_id",""),
            "failure_ids":          fail_id,
            "defect_ids":           defect.get("defect_id","") if defect else "",
            "release_id":           ctx["test_run"].get("release_id","") if ctx.get("test_run") else "",
            "environment_id":       fail.get("environment",""),
        })
    print(f"  [OK] failure_reports/ {len(records):>3} PDFs")
    return records

def gen_defect_pdfs(dl: DataLoader, rr: RelationshipResolver) -> List[Dict]:
    records = []
    defect_ids = _pick([d["defect_id"] for d in dl.defects], N_DEF_PDFS)
    for defect_id in defect_ids:
        ctx    = rr.defect_context(defect_id)
        defect = ctx["defect"]
        fname  = f"defect_{defect_id.lower().replace('-','_')}.pdf"
        out    = PDF_DOCS / "defect_reports" / fname
        try:
            T.render_defect_report(ctx, out)
        except Exception as e:
            print(f"    [WARN] {fname}: {e}")
            continue
        records.append({
            "pdf_id":               f"PDF-DEF-{defect_id}",
            "filename":             fname,
            "document_type":        "defect_report",
            "primary_entity_type":  "DEFECT",
            "primary_entity_id":    defect_id,
            "application_id":       defect.get("application_id",""),
            "solution_id":          "",
            "requirement_ids":      defect.get("affected_requirement",""),
            "test_case_ids":        defect.get("related_test_case",""),
            "execution_ids":        ctx["execution"].get("execution_id","") if ctx.get("execution") else "",
            "failure_ids":          defect.get("related_failure",""),
            "defect_ids":           defect_id,
            "release_id":           ctx["release"].get("release_id","") if ctx.get("release") else "",
            "environment_id":       ctx["environment"].get("environment_id","") if ctx.get("environment") else "",
        })
    print(f"  [OK] defect_reports/  {len(records):>3} PDFs")
    return records

# ── manifest + entity mapping ─────────────────────────────────────────────────

def write_manifest(all_records: List[Dict]):
    fields = [
        "pdf_id","filename","document_type","primary_entity_type",
        "primary_entity_id","application_id","solution_id",
        "requirement_ids","test_case_ids","execution_ids",
        "failure_ids","defect_ids","release_id","environment_id",
    ]
    write_csv(META_DIR / "pdf_manifest.csv", fields, all_records)
    print(f"  [OK] pdf_manifest.csv          {len(all_records)} rows")

def write_entity_mapping(all_records: List[Dict], dl: DataLoader):
    mapping = {}
    for r in all_records:
        pdf_id = r["pdf_id"]
        def _split(v): return [x.strip() for x in v.split("|") if x.strip()] if v else []
        entities = (
            ([r["primary_entity_id"]] if r["primary_entity_id"] else []) +
            _split(r["requirement_ids"]) +
            _split(r["test_case_ids"]) +
            _split(r["execution_ids"]) +
            _split(r["failure_ids"]) +
            _split(r["defect_ids"])
        )
        entities = list(dict.fromkeys(e for e in entities if e))  # dedup, preserve order

        # build relationships list
        relationships = []
        if r["requirement_ids"] and r["test_case_ids"]:
            for req in _split(r["requirement_ids"]):
                for tc in _split(r["test_case_ids"]):
                    relationships.append({"source": tc, "type": "IMPLEMENTS", "target": req})
        if r["execution_ids"] and r["test_case_ids"]:
            for ex in _split(r["execution_ids"]):
                for tc in _split(r["test_case_ids"]):
                    relationships.append({"source": tc, "type": "HAS_EXECUTION", "target": ex})
        if r["failure_ids"] and r["execution_ids"]:
            for f in _split(r["failure_ids"]):
                for ex in _split(r["execution_ids"]):
                    relationships.append({"source": ex, "type": "PRODUCED", "target": f})
        if r["defect_ids"] and r["failure_ids"]:
            for d in _split(r["defect_ids"]):
                for f in _split(r["failure_ids"]):
                    relationships.append({"source": f, "type": "LINKED_TO", "target": d})
        if r["defect_ids"] and r["requirement_ids"]:
            for d in _split(r["defect_ids"]):
                for req in _split(r["requirement_ids"]):
                    relationships.append({"source": d, "type": "AFFECTS", "target": req})

        mapping[pdf_id] = {
            "filename":      r["filename"],
            "document_type": r["document_type"],
            "primary_entity_type": r["primary_entity_type"],
            "primary_entity": r["primary_entity_id"],
            "application_id": r["application_id"],
            "entities": entities,
            "relationships": relationships,
        }

    write_json(META_DIR / "pdf_entity_mapping.json", mapping)
    print(f"  [OK] pdf_entity_mapping.json   {len(mapping)} entries")
    return mapping

# ── INPUT FIXTURES ────────────────────────────────────────────────────────────

# Realistic query templates for each category
LINE_ONLY_TEMPLATES = [
    # semantic
    ("semantic",  "What are the common failure patterns observed for the {app} application?"),
    ("semantic",  "Describe the troubleshooting steps for {ftype} failures."),
    ("semantic",  "What are the security requirements for {app}?"),
    ("semantic",  "Which components are most affected by {ftype} failures?"),
    ("semantic",  "What is the pass rate trend for {app} in recent regression cycles?"),
    ("semantic",  "Which failure types have the highest recurrence in historical data?"),
    ("semantic",  "What test environments are used for {app} testing?"),
    ("semantic",  "Describe the root cause of failures in the {comp} component."),
    ("semantic",  "What acceptance criteria apply to {req_type} requirements?"),
    ("semantic",  "Which engineers are assigned to {app} defects?"),
    # test_case_lookup
    ("test_case_lookup", "Which test cases validate {req_id}?"),
    ("test_case_lookup", "Show me test cases of type {tc_type} for {app}."),
    ("test_case_lookup", "List all automated test cases for {app}."),
    ("test_case_lookup", "Which test cases cover the {comp} component?"),
    ("test_case_lookup", "Find test cases with priority Critical in {app}."),
    ("test_case_lookup", "Which smoke test cases exist for {app}?"),
    ("test_case_lookup", "What test cases are in suite {suite_id}?"),
    # requirement_lookup
    ("requirement_lookup", "What is requirement {req_id}?"),
    ("requirement_lookup", "List all Performance requirements for {app}."),
    ("requirement_lookup", "Which requirements are in status Approved for {app}?"),
    ("requirement_lookup", "What are the authentication requirements for {app}?"),
    ("requirement_lookup", "Show requirements related to the {comp} component."),
    ("requirement_lookup", "Which High-priority requirements have no passing test cases?"),
    # failure_lookup
    ("failure_lookup", "Describe failure {fail_id}."),
    ("failure_lookup", "What failures occurred in environment {env_id}?"),
    ("failure_lookup", "Which {ftype} failures were observed in build {build}?"),
    ("failure_lookup", "List failures for test case {tc_id}."),
    ("failure_lookup", "Which failures have resolution status Open?"),
    ("failure_lookup", "What failures occurred in the {app} application in the last regression?"),
    # defect_lookup
    ("defect_lookup", "What is the status of defect {bug_id}?"),
    ("defect_lookup", "Which defects are assigned to {eng_id}?"),
    ("defect_lookup", "List open defects for {app}."),
    ("defect_lookup", "Which defects affect requirement {req_id}?"),
    ("defect_lookup", "Show all Critical-severity defects for {app}."),
    ("defect_lookup", "What is the root cause of defect {bug_id}?"),
    # historical_failure
    ("historical_failure", "Have there been previous {ftype} failures in {app}?"),
    ("historical_failure", "What is the recurrence count for failures in the {comp} component?"),
    ("historical_failure", "Which historical failures share the same root cause as {fail_id}?"),
    ("historical_failure", "Show historical failure trends for {app}."),
    # execution_analysis
    ("execution_analysis", "What is the pass rate for test run {run_id}?"),
    ("execution_analysis", "Which executions failed in build {build}?"),
    ("execution_analysis", "How many tests were blocked in {run_id}?"),
    ("execution_analysis", "What is the average execution duration for {app} test cases?"),
    ("execution_analysis", "Which test cases have never passed in any regression cycle?"),
    # traceability
    ("traceability", "Show the traceability chain from requirement {req_id} to its defects."),
    ("traceability", "Which requirement does test case {tc_id} implement?"),
    ("traceability", "Which defect was raised from failure {fail_id}?"),
    ("traceability", "Trace execution {exec_id} back to its requirement."),
    # multi_hop_graph
    ("multi_hop_graph", "Which requirements are affected by failures in {run_id}?"),
    ("multi_hop_graph", "Find all defects linked to requirements in {app} via the failure chain."),
    ("multi_hop_graph", "Which engineers are responsible for open defects affecting Critical requirements in {app}?"),
    ("multi_hop_graph", "What is the full requirement-test-execution-failure-defect chain for {req_id}?"),
    ("multi_hop_graph", "Which test suites contain test cases that produced failures in {run_id}?"),
]

LINE_PDF_TEMPLATES = [
    # These explicitly reference a PDF and add a graph/hybrid question
    ("hybrid", "Based on this failure report, which requirement is affected and is there an existing defect tracking it?"),
    ("hybrid", "Does the failure described in this PDF correspond to any historical failure in the dataset?"),
    ("hybrid", "Which test case generated the failure described in this document?"),
    ("hybrid", "Find the release associated with the failed execution in this report."),
    ("hybrid", "Which engineer executed the test mentioned in this report?"),
    ("hybrid", "Are there previous failures for the same requirement mentioned in this PDF?"),
    ("hybrid", "Which other test cases cover the requirement mentioned in this PDF?"),
    ("hybrid", "Is the defect described in this PDF still open?"),
    ("hybrid", "Trace the failure in this PDF back to its originating requirement."),
    ("hybrid", "Find similar historical failures to the one described in this document and show their resolutions."),
    ("hybrid", "What is the root cause of the failure described in this PDF, and which component is affected?"),
    ("hybrid", "Summarise the execution context of this failure report including test run and build version."),
    ("hybrid", "Which requirements are at risk based on this defect report?"),
    ("hybrid", "How many times has this type of failure occurred historically according to the dataset?"),
    ("hybrid", "Which test cases in the same suite as the one in this report also failed recently?"),
    ("hybrid", "What is the overall pass rate for the regression cycle that contains this execution?"),
    ("hybrid", "Show the complete defect traceability chain for the defect described in this PDF."),
    ("hybrid", "Which engineers are assigned to defects related to this failure?"),
    ("hybrid", "Is the requirement covered by this test case still in Approved status?"),
    ("hybrid", "Find all executions of the test case in this report across all regression runs."),
    ("semantic", "What does this requirement document say about acceptance criteria?"),
    ("semantic", "Summarise the test strategy described in this test plan."),
    ("semantic", "What preconditions are required for the test case described in this PDF?"),
    ("semantic", "What error message is recorded in this failure report?"),
    ("semantic", "What resolution was applied to the defect described in this document?"),
    ("semantic", "List all test cases mentioned in this test plan."),
    ("semantic", "What is the severity of the failure described in this report?"),
    ("semantic", "Which environment was used for the execution described in this PDF?"),
    ("semantic", "What are the exit criteria in this test plan?"),
    ("semantic", "What build version is referenced in this execution report?"),
]


def _fill_template(tmpl: str, dl: DataLoader) -> str:
    """Replace template placeholders with real IDs."""
    random.seed(SEED + hash(tmpl) % 10000)
    apps   = dl.applications
    fails  = dl.failures
    defects= dl.defects
    reqs   = dl.requirements
    tcs    = dl.test_cases
    runs   = dl.test_runs
    engs   = dl.engineers
    envs   = dl.environments
    suites = dl.test_suites

    failure_types = list({f.get("failure_type","") for f in fails if f.get("failure_type")})
    components    = list({f.get("component","") for f in fails if f.get("component")})
    req_types     = list({r.get("requirement_type","") for r in reqs if r.get("requirement_type")})
    tc_types      = list({t.get("test_type","") for t in tcs if t.get("test_type")})
    builds        = list({e.get("build_version","") for e in dl.test_executions if e.get("build_version")})

    replacements = {
        "{app}":      random.choice(apps)["name"] if apps else "SmartHome",
        "{ftype}":    random.choice(failure_types) if failure_types else "Timeout",
        "{comp}":     random.choice(components) if components else "Authentication",
        "{req_type}": random.choice(req_types) if req_types else "Security",
        "{tc_type}":  random.choice(tc_types) if tc_types else "Regression",
        "{req_id}":   random.choice(reqs)["requirement_id"] if reqs else "REQ-0001",
        "{tc_id}":    random.choice(tcs)["test_case_id"] if tcs else "TC-0001",
        "{fail_id}":  random.choice(fails)["failure_id"] if fails else "FAIL-0001",
        "{bug_id}":   random.choice(defects)["defect_id"] if defects else "BUG-0001",
        "{run_id}":   random.choice(runs)["run_id"] if runs else "RUN-001",
        "{eng_id}":   random.choice(engs)["engineer_id"] if engs else "ENG-001",
        "{env_id}":   random.choice(envs)["environment_id"] if envs else "ENV-001",
        "{suite_id}": random.choice(suites)["suite_id"] if suites else "TS-0001",
        "{build}":    random.choice(builds) if builds else "5.1.0",
        "{exec_id}":  random.choice(dl.test_executions)["execution_id"] if dl.test_executions else "EXEC-00001",
    }
    result = tmpl
    for ph, val in replacements.items():
        result = result.replace(ph, val)
    return result


def _resolve_entities_for_query(q_text: str, dl: DataLoader) -> List[str]:
    """Extract entity IDs that appear in a query string."""
    import re
    ids = re.findall(
        r'\b(?:REQ|TC|EXEC|FAIL|BUG|RUN|APP|ENG|ENV|TS|SOL|REL)-[\w\d]+\b',
        q_text
    )
    return list(dict.fromkeys(ids))


def gen_line_only_fixtures(dl: DataLoader, manifest_records: List[Dict]) -> List[Dict]:
    rows = []
    qid  = 1
    random.seed(SEED + 100)
    # Cycle through templates deterministically
    for i in range(N_LINE_ONLY):
        tmpl_qtype, tmpl_q = LINE_ONLY_TEMPLATES[i % len(LINE_ONLY_TEMPLATES)]
        question = _fill_template(tmpl_q, dl)
        entities = _resolve_entities_for_query(question, dl)

        rows.append({
            "fixture_id":     f"LINE-ONLY-{qid:04d}",
            "input_mode":     "LINE_ONLY",
            "query_type":     tmpl_qtype,
            "retrieval_mode": "HYBRID" if tmpl_qtype in ("multi_hop_graph","traceability") else
                              "GRAPH"  if tmpl_qtype in ("failure_lookup","defect_lookup") else
                              "SEMANTIC",
            "question":       question,
            "pdf_filename":   "",
            "expected_entities": entities,
            "expected_relationships": [],
            "notes": f"Template category: {tmpl_qtype}",
        })
        qid += 1
    write_jsonl(FIX_DIR / "line_only" / "line_only_fixtures.jsonl", rows)
    print(f"  [OK] line_only/    {len(rows):>4} fixtures")
    return rows


def gen_pdf_only_fixtures(dl: DataLoader, manifest_records: List[Dict]) -> List[Dict]:
    rows = []
    qid  = 1
    # Sample across all PDF types
    random.seed(SEED + 200)
    sample = random.sample(manifest_records, min(N_PDF_ONLY, len(manifest_records)))
    for rec in sample:
        def _split(v): return [x for x in v.split("|") if x] if v else []
        entities = list(dict.fromkeys(
            ([rec["primary_entity_id"]] if rec["primary_entity_id"] else []) +
            _split(rec["requirement_ids"]) +
            _split(rec["test_case_ids"]) +
            _split(rec["execution_ids"]) +
            _split(rec["failure_ids"]) +
            _split(rec["defect_ids"])
        ))
        answerable_facts = _answerable_facts(rec, dl)
        rows.append({
            "fixture_id":            f"PDF-ONLY-{qid:04d}",
            "input_mode":            "PDF_ONLY",
            "query_type":            "extraction",
            "retrieval_mode":        "SEMANTIC",
            "question":              "",
            "pdf_filename":          rec["filename"],
            "document_type":         rec["document_type"],
            "primary_entity_type":   rec["primary_entity_type"],
            "primary_entity_id":     rec["primary_entity_id"],
            "expected_entities":     entities,
            "expected_relationships": _rel_types_for_doc(rec),
            "answerable_facts":      answerable_facts,
            "notes": f"Pure PDF extraction — no query provided",
        })
        qid += 1
    write_jsonl(FIX_DIR / "pdf_only" / "pdf_only_fixtures.jsonl", rows)
    print(f"  [OK] pdf_only/     {len(rows):>4} fixtures")
    return rows


def _rel_types_for_doc(rec: Dict) -> List[str]:
    dt = rec.get("document_type","")
    if dt == "requirement_spec":   return ["IMPLEMENTS","BELONGS_TO","AFFECTS"]
    if dt == "test_plan":          return ["CONTAINS","BELONGS_TO","PART_OF"]
    if dt == "test_case_spec":     return ["IMPLEMENTS","HAS_EXECUTION","CONTAINS"]
    if dt == "execution_report":   return ["HAS_EXECUTION","EXECUTED_DURING","PRODUCED"]
    if dt == "failure_report":     return ["PRODUCED","LINKED_TO","OCCURRED_IN","AFFECTS"]
    if dt == "defect_report":      return ["LINKED_TO","AFFECTS","ASSIGNED_TO","IMPLEMENTS"]
    return []


def _answerable_facts(rec: Dict, dl: DataLoader) -> List[str]:
    """Return a short list of facts that can be extracted from this PDF."""
    facts = [f"Document type: {rec['document_type']}",
             f"Primary entity: {rec['primary_entity_id']}"]
    if rec.get("application_id"):
        app = dl.app_by_id.get(rec["application_id"], {})
        facts.append(f"Application: {app.get('name', rec['application_id'])}")
    if rec.get("requirement_ids"):
        first_req = rec["requirement_ids"].split("|")[0]
        req = dl.req_by_id.get(first_req, {})
        if req:
            facts.append(f"Requirement: {first_req} — {req.get('title','')[:50]}")
    if rec.get("failure_ids"):
        first_fail = rec["failure_ids"].split("|")[0]
        fail = dl.fail_by_id.get(first_fail, {})
        if fail:
            facts.append(f"Failure type: {fail.get('failure_type','')}")
            facts.append(f"Root cause: {fail.get('root_cause','')[:60]}")
    if rec.get("defect_ids"):
        first_def = rec["defect_ids"].split("|")[0]
        d = dl.defect_by_id.get(first_def, {})
        if d:
            facts.append(f"Defect status: {d.get('status','')}")
    return facts


def gen_line_pdf_fixtures(dl: DataLoader, manifest_records: List[Dict]) -> List[Dict]:
    rows = []
    qid  = 1
    random.seed(SEED + 300)
    # Weight towards failure/defect PDFs for richer hybrid questions
    fail_pdfs   = [r for r in manifest_records if r["document_type"] in ("failure_report","defect_report")]
    other_pdfs  = [r for r in manifest_records if r["document_type"] not in ("failure_report","defect_report")]
    all_pool    = fail_pdfs * 2 + other_pdfs   # upweight failure/defect PDFs
    pool        = all_pool * (N_LINE_PDF // len(all_pool) + 2)
    random.shuffle(pool)

    for i in range(N_LINE_PDF):
        rec   = pool[i % len(pool)]
        tmpl_qtype, tmpl_q = LINE_PDF_TEMPLATES[i % len(LINE_PDF_TEMPLATES)]
        question = tmpl_q  # these templates don't have {placeholders}

        # For semantic queries about specific PDF content, ensure Q matches doc type
        doc_type = rec.get("document_type","")
        if tmpl_qtype == "semantic":
            semantic_qs = {
                "requirement_spec":  "What does this requirement document say about acceptance criteria?",
                "test_plan":         "Summarise the test strategy described in this test plan.",
                "test_case_spec":    "What preconditions are required for the test case described in this PDF?",
                "execution_report":  "What build version is referenced in this execution report?",
                "failure_report":    "What error message is recorded in this failure report?",
                "defect_report":     "What resolution was applied to the defect described in this document?",
            }
            question = semantic_qs.get(doc_type, question)

        def _split(v): return [x for x in v.split("|") if x] if v else []
        entities = list(dict.fromkeys(
            ([rec["primary_entity_id"]] if rec["primary_entity_id"] else []) +
            _split(rec["requirement_ids"]) +
            _split(rec["test_case_ids"]) +
            _split(rec["execution_ids"]) +
            _split(rec["failure_ids"]) +
            _split(rec["defect_ids"])
        ))

        # Build expected answer based on entity data
        expected_answer = _build_expected_answer(question, rec, dl)

        retrieval_mode = (
            "HYBRID"   if tmpl_qtype == "hybrid" else
            "SEMANTIC" if tmpl_qtype == "semantic" else
            "GRAPH"
        )

        rows.append({
            "fixture_id":             f"PDF-LINE-{qid:04d}",
            "input_mode":             "LINE_PLUS_PDF",
            "query_type":             tmpl_qtype,
            "retrieval_mode":         retrieval_mode,
            "question":               question,
            "pdf_filename":           rec["filename"],
            "document_type":          rec["document_type"],
            "primary_entity_id":      rec["primary_entity_id"],
            "application_id":         rec["application_id"],
            "expected_entities":      entities,
            "expected_relationships": _rel_types_for_doc(rec),
            "expected_answer_summary":expected_answer,
            "required_evidence":      _required_evidence(tmpl_qtype, doc_type),
        })
        qid += 1

    write_jsonl(FIX_DIR / "line_plus_pdf" / "line_plus_pdf_fixtures.jsonl", rows)
    print(f"  [OK] line_plus_pdf/ {len(rows):>4} fixtures")
    return rows


def _build_expected_answer(question: str, rec: Dict, dl: DataLoader) -> str:
    """Build a concise expected-answer stub from entity data."""
    pid = rec.get("primary_entity_id","")
    dt  = rec.get("document_type","")
    app = dl.app_by_id.get(rec.get("application_id",""), {})
    app_name = app.get("name", rec.get("application_id","N/A"))

    if dt == "failure_report":
        fail = dl.fail_by_id.get(pid, {})
        defect = dl.defect_by_fail.get(pid, {})
        req_id = ""
        tc = dl.tc_by_id.get(fail.get("test_case_id",""), {})
        req_id = tc.get("requirement_id","") if tc else ""
        req = dl.req_by_id.get(req_id, {})
        parts = [
            f"Failure {pid} is a {fail.get('failure_type','N/A')} in the "
            f"{fail.get('component','N/A')} component of {app_name}.",
        ]
        if req_id:
            parts.append(f"It affects requirement {req_id}: {req.get('title','')[:50]}.")
        if defect:
            parts.append(f"Defect {defect.get('defect_id','N/A')} (status: {defect.get('status','N/A')}) tracks this issue.")
        parts.append(f"Root cause: {fail.get('root_cause','N/A')[:80]}.")
        return " ".join(parts)

    if dt == "defect_report":
        defect = dl.defect_by_id.get(pid, {})
        parts = [
            f"Defect {pid} has status {defect.get('status','N/A')} and severity {defect.get('severity','N/A')}.",
            f"It affects requirement {defect.get('affected_requirement','N/A')}.",
            f"Root cause: {defect.get('root_cause','N/A')[:80]}.",
        ]
        if defect.get("resolution"):
            parts.append(f"Resolution: {defect.get('resolution','')[:60]}.")
        return " ".join(parts)

    if dt == "requirement_spec":
        req = dl.req_by_id.get(pid, {})
        return (f"Requirement {pid} ({req.get('requirement_type','N/A')}, priority {req.get('priority','N/A')}) "
                f"for {app_name}: {req.get('description','N/A')[:80]}.")

    if dt == "test_case_spec":
        tc = dl.tc_by_id.get(pid, {})
        return (f"Test case {pid} is a {tc.get('test_type','N/A')} test "
                f"({tc.get('automation_status','N/A')}), priority {tc.get('priority','N/A')}. "
                f"It implements {tc.get('requirement_id','N/A')}.")

    if dt == "execution_report":
        ex = dl.exec_by_id.get(pid, {})
        return (f"Execution {pid} of test case {ex.get('test_case_id','N/A')} "
                f"resulted in {ex.get('status','N/A')} on build {ex.get('build_version','N/A')}.")

    if dt == "test_plan":
        suite = dl.suite_by_id.get(pid, {})
        return (f"Test plan for suite {pid} ({suite.get('name','N/A')}) "
                f"covers {suite.get('suite_type','N/A')} testing for {app_name}.")

    return f"See {dt} for {pid} in {app_name}."


def _required_evidence(query_type: str, doc_type: str) -> List[str]:
    base = [f"PDF content ({doc_type})"]
    if query_type == "hybrid":
        base += ["structured dataset (CSV)", "knowledge graph traversal"]
    elif query_type == "graph":
        base += ["knowledge graph traversal"]
    else:
        base += ["vector similarity search"]
    return base


# ── EVALUATION DATASET ────────────────────────────────────────────────────────

def gen_evaluation_dataset(
        line_fixtures: List[Dict],
        pdf_fixtures: List[Dict],
        line_pdf_fixtures: List[Dict],
        dl: DataLoader,
        entity_mapping: Dict):

    questions   = []
    ground_truth= []
    exp_entities= []
    exp_rels    = []

    qid = 1

    # --- LINE ONLY (100) ---
    for fx in line_fixtures[:100]:
        q = {
            "query_id":    f"EVAL-LINE-{qid:04d}",
            "fixture_id":  fx["fixture_id"],
            "input_mode":  "LINE_ONLY",
            "retrieval_mode": fx["retrieval_mode"],
            "query_type":  fx["query_type"],
            "question":    fx["question"],
            "pdf_filename":"",
        }
        gt = {
            "query_id":     f"EVAL-LINE-{qid:04d}",
            "expected_entities": fx.get("expected_entities",[]),
            "answer_hint": (f"Answer requires {fx['retrieval_mode']} retrieval. "
                            f"Entities involved: {', '.join(fx.get('expected_entities',[])[:3])}."),
        }
        ee = {"query_id": f"EVAL-LINE-{qid:04d}", "entity_ids": fx.get("expected_entities",[])}
        er = {"query_id": f"EVAL-LINE-{qid:04d}", "relationship_types": fx.get("expected_relationships",[])}
        questions.append(q); ground_truth.append(gt)
        exp_entities.append(ee); exp_rels.append(er)
        qid += 1

    # --- PDF ONLY (50) ---
    for fx in pdf_fixtures[:50]:
        q = {
            "query_id":    f"EVAL-PDF-{qid:04d}",
            "fixture_id":  fx["fixture_id"],
            "input_mode":  "PDF_ONLY",
            "retrieval_mode": "SEMANTIC",
            "query_type":  "extraction",
            "question":    "",
            "pdf_filename": fx["pdf_filename"],
        }
        gt = {
            "query_id":     f"EVAL-PDF-{qid:04d}",
            "expected_entities": fx.get("expected_entities",[]),
            "answerable_facts":  fx.get("answerable_facts",[]),
            "answer_hint": (f"Extract entities and facts from PDF {fx['pdf_filename']}. "
                            f"Primary entity: {fx.get('primary_entity_id','N/A')}."),
        }
        ee = {"query_id": f"EVAL-PDF-{qid:04d}", "entity_ids": fx.get("expected_entities",[])}
        er = {"query_id": f"EVAL-PDF-{qid:04d}", "relationship_types": fx.get("expected_relationships",[])}
        questions.append(q); ground_truth.append(gt)
        exp_entities.append(ee); exp_rels.append(er)
        qid += 1

    # --- LINE + PDF (150) ---
    for fx in line_pdf_fixtures[:150]:
        q = {
            "query_id":    f"EVAL-HYBRID-{qid:04d}",
            "fixture_id":  fx["fixture_id"],
            "input_mode":  "LINE_PLUS_PDF",
            "retrieval_mode": fx["retrieval_mode"],
            "query_type":  fx["query_type"],
            "question":    fx["question"],
            "pdf_filename": fx["pdf_filename"],
        }
        gt = {
            "query_id":     f"EVAL-HYBRID-{qid:04d}",
            "expected_entities": fx.get("expected_entities",[]),
            "expected_relationships": fx.get("expected_relationships",[]),
            "answer_summary": fx.get("expected_answer_summary",""),
            "required_evidence": fx.get("required_evidence",[]),
        }
        ee = {"query_id": f"EVAL-HYBRID-{qid:04d}", "entity_ids": fx.get("expected_entities",[])}
        er = {"query_id": f"EVAL-HYBRID-{qid:04d}",
              "relationship_types": fx.get("expected_relationships",[]),
              "primary_entity": fx.get("primary_entity_id",""),
              "pdf_filename": fx.get("pdf_filename","")}
        questions.append(q); ground_truth.append(gt)
        exp_entities.append(ee); exp_rels.append(er)
        qid += 1

    write_jsonl(EVAL_DIR / "questions.jsonl",              questions)
    write_jsonl(EVAL_DIR / "ground_truth.jsonl",           ground_truth)
    write_jsonl(EVAL_DIR / "expected_entities.jsonl",      exp_entities)
    write_jsonl(EVAL_DIR / "expected_relationships.jsonl", exp_rels)

    print(f"  [OK] questions.jsonl             {len(questions)} records")
    print(f"  [OK] ground_truth.jsonl          {len(ground_truth)} records")
    print(f"  [OK] expected_entities.jsonl     {len(exp_entities)} records")
    print(f"  [OK] expected_relationships.jsonl {len(exp_rels)} records")

    # evaluation_metrics.md
    metrics_md = """\
# PDF Input Evaluation Metrics

## 1. Input Mode Distribution

| Mode | Count | Purpose |
|------|-------|---------|
| LINE_ONLY | 100 | Baseline text-only retrieval |
| PDF_ONLY | 50 | Pure document extraction/understanding |
| LINE_PLUS_PDF | 150 | Combined semantic + graph retrieval |
| **Total** | **300** | |

## 2. Retrieval Mode Distribution

| Mode | Description |
|------|-------------|
| SEMANTIC | Vector similarity over chunked text |
| GRAPH | Knowledge-graph traversal |
| HYBRID | Both semantic + graph evidence combined |

## 3. Metrics per Mode

### LINE_ONLY
| Metric | Target |
|--------|--------|
| Answer Accuracy | >= 0.80 |
| Entity Recall | >= 0.75 |
| ROUGE-L | >= 0.40 |
| BERTScore F1 | >= 0.78 |

### PDF_ONLY
| Metric | Target |
|--------|--------|
| Entity Extraction Recall | >= 0.85 |
| Entity Extraction Precision | >= 0.80 |
| Fact Coverage | >= 0.75 |
| Relationship Extraction F1 | >= 0.70 |

### LINE_PLUS_PDF (Hybrid)
| Metric | Target |
|--------|--------|
| Answer Accuracy | >= 0.82 |
| Entity Recall | >= 0.80 |
| Graph Path Accuracy | >= 0.72 |
| Evidence Integration | >= 0.78 |
| Faithfulness (no hallucination) | >= 0.88 |
| Multi-hop Path Completion | >= 0.68 |

## 4. Query Type Coverage

| Query Type | Mode | Notes |
|-----------|------|-------|
| semantic | LINE, LINE+PDF | Semantic document retrieval |
| test_case_lookup | LINE | Graph + structured lookup |
| requirement_lookup | LINE | Graph traversal |
| failure_lookup | LINE | Structured + semantic |
| defect_lookup | LINE | Structured lookup |
| historical_failure | LINE | Historical pattern matching |
| execution_analysis | LINE | Aggregation over structured data |
| traceability | LINE | Multi-hop graph paths |
| multi_hop_graph | LINE | Deep graph traversal |
| extraction | PDF_ONLY | Entity extraction from PDF |
| hybrid | LINE+PDF | Full pipeline required |

## 5. Evaluation Procedure

1. Run the pipeline against `evaluation/pdf_input_evaluation/questions.jsonl`.
2. For LINE_PLUS_PDF, provide both the question and the referenced PDF.
3. Compare outputs to `ground_truth.jsonl`.
4. Compute per-mode and aggregate metrics.
5. Flag any answer with faithfulness < 0.6 for manual review.

---
*This document is synthetic and intended for AI/RAG research purposes only.*
"""
    (EVAL_DIR / "evaluation_metrics.md").write_text(metrics_md, encoding="utf-8")
    print(f"  [OK] evaluation_metrics.md")

    return questions, ground_truth


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("  PDF Dataset Generator — Hybrid RAG Test Management")
    print("="*60)
    print(f"  Seed: {SEED}\n")

    dl = DataLoader()
    dl.load()
    rr = RelationshipResolver(dl)

    print("\n[1] Generating PDFs...")
    req_recs  = gen_requirement_pdfs(dl, rr)
    plan_recs = gen_test_plan_pdfs(dl, rr)
    tc_recs   = gen_test_case_pdfs(dl, rr)
    exec_recs = gen_execution_pdfs(dl, rr)
    fail_recs = gen_failure_pdfs(dl, rr)
    def_recs  = gen_defect_pdfs(dl, rr)

    all_records = req_recs + plan_recs + tc_recs + exec_recs + fail_recs + def_recs
    total_pdfs  = len(all_records)
    print(f"\n  Total PDFs generated: {total_pdfs}")

    print("\n[2] Writing PDF metadata...")
    write_manifest(all_records)
    entity_mapping = write_entity_mapping(all_records, dl)

    print("\n[3] Generating input fixtures...")
    line_fxs    = gen_line_only_fixtures(dl, all_records)
    pdf_fxs     = gen_pdf_only_fixtures(dl, all_records)
    line_pdf_fxs= gen_line_pdf_fixtures(dl, all_records)

    print("\n[4] Generating evaluation dataset...")
    gen_evaluation_dataset(line_fxs, pdf_fxs, line_pdf_fxs, dl, entity_mapping)

    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    type_counts = {}
    for r in all_records:
        type_counts[r["document_type"]] = type_counts.get(r["document_type"], 0) + 1
    for dt, cnt in sorted(type_counts.items()):
        print(f"  {dt:<25} {cnt:>3} PDFs")
    print(f"  {'TOTAL':<25} {total_pdfs:>3} PDFs")
    print(f"\n  Line-only fixtures    : {len(line_fxs)}")
    print(f"  PDF-only fixtures     : {len(pdf_fxs)}")
    print(f"  Line+PDF fixtures     : {len(line_pdf_fxs)}")
    print(f"  Evaluation queries    : {len(line_fxs[:100]) + len(pdf_fxs[:50]) + len(line_pdf_fxs[:150])}")
    print(f"\nOutput: {DATASET_ROOT}")
    print("\nPDF generation complete.\n")


if __name__ == "__main__":
    main()
