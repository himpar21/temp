"""
generate_evaluation.py
=======================
Generates the evaluation dataset for the Hybrid RAG pipeline.

Produces 300 queries (100 semantic, 100 graph, 100 hybrid) each with
ground-truth answers, expected entities, expected relationships, and
expected graph paths.  All IDs are drawn from the already-generated
structured CSVs so every reference resolves.

Run:
    python datasets/synthetic_test_management/scripts/generate_evaluation.py
"""

import csv
import json
import random
from pathlib import Path

SCRIPT_DIR   = Path(__file__).resolve().parent
DATASET_ROOT = SCRIPT_DIR.parent
STRUCTURED   = DATASET_ROOT / "structured"
EVAL         = DATASET_ROOT / "evaluation"
EVAL.mkdir(parents=True, exist_ok=True)

SEED = 42
random.seed(SEED)

# ──────────────────────────────────────────────────────────────────────────────
def load_csv(name):
    p = STRUCTURED / name
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  ✓ {path.name:45s} {len(rows):>5} records")

# ──────────────────────────────────────────────────────────────────────────────
# Load all tables
# ──────────────────────────────────────────────────────────────────────────────
apps    = load_csv("applications.csv")
reqs    = load_csv("requirements.csv")
tcs     = load_csv("test_cases.csv")
runs    = load_csv("test_runs.csv")
execs   = load_csv("test_executions.csv")
fails   = load_csv("failures.csv")
defects = load_csv("defects.csv")
engs    = load_csv("engineers.csv")
envs    = load_csv("environments.csv")
suites  = load_csv("test_suites.csv")
hist    = load_csv("historical_failures.csv")

# Build quick look-ups
app_map     = {a["application_id"]: a["name"]            for a in apps}
req_map     = {r["requirement_id"]: r                    for r in reqs}
tc_map      = {t["test_case_id"]:   t                    for t in tcs}
fail_map    = {f["failure_id"]:     f                    for f in fails}
defect_map  = {d["defect_id"]:      d                    for d in defects}
exec_map    = {e["execution_id"]:   e                    for e in execs}
run_map     = {r["run_id"]:         r                    for r in runs}
eng_map     = {e["engineer_id"]:    e["name"]            for e in engs}

# Indexes for relational lookups
tc_by_req   = {}
for t in tcs:
    tc_by_req.setdefault(t["requirement_id"], []).append(t["test_case_id"])

exec_by_tc  = {}
for e in execs:
    exec_by_tc.setdefault(e["test_case_id"], []).append(e)

fail_execs  = [e for e in execs if e.get("failure_id")]
defect_by_fail = {d["related_failure"]: d for d in defects}

# Sample pools
fail_sample    = random.sample(fails,   min(200, len(fails)))
defect_sample  = random.sample(defects, min(200, len(defects)))
tc_sample      = random.sample(tcs,     min(200, len(tcs)))
req_sample     = random.sample(reqs,    min(200, len(reqs)))
run_sample     = random.sample(runs,    min(12,  len(runs)))
app_sample     = random.sample(apps,    len(apps))

# ──────────────────────────────────────────────────────────────────────────────
# SEMANTIC QUERIES  (100)
# ──────────────────────────────────────────────────────────────────────────────

SEMANTIC_TEMPLATES = [
    # Failure analysis
    ("What are the common causes of {ftype} failures in the {app} application?",
     "The most common causes of {ftype} failures in {app} include: {root_cause}. "
     "These failures typically occur under {condition} conditions and are documented "
     "in failure reports {fail_ids}."),
    # Troubleshooting
    ("What troubleshooting steps are recommended for {ftype} failures?",
     "For {ftype} failures, the recommended steps are: (1) check network/environment stability, "
     "(2) review error logs for patterns, (3) verify configuration settings, "
     "(4) consult the troubleshooting guide for the {component} component."),
    # Test case discovery
    ("Which test cases validate {feature} functionality?",
     "The following test cases validate {feature}: {tc_ids}. "
     "They are classified as {test_type} tests and are part of suite {suite_id}."),
    # Failure pattern
    ("What failure patterns were observed in the {run_name} regression cycle?",
     "In {run_name}, {failed} tests failed out of {total} executed (pass rate: {pass_rate}%). "
     "The dominant failure types were {ftype} and network-related failures. "
     "Key defects raised: {defect_ids}."),
    # Defect description
    ("Describe the root cause of defect {defect_id}.",
     "Defect {defect_id} affects the {component} component of {app}. "
     "Root cause: {root_cause}. "
     "It was detected during execution of test case {tc_id} and linked to failure {fail_id}."),
    # Requirements
    ("What are the security requirements for the {app} application?",
     "{app} has {count} security requirements covering authentication, encryption, "
     "access control, and audit logging. Key requirement IDs: {req_ids}."),
    # Performance
    ("Which test cases check performance SLA compliance?",
     "{count} performance test cases validate SLA compliance. "
     "They use metrics such as p95 latency, p99 latency, and memory ceiling. "
     "Key test case IDs: {tc_ids}."),
    # Historical recurrence
    ("Which failure types have the highest recurrence in historical data?",
     "Based on historical_failures.csv, the most recurrent failure types are: "
     "Timeout ({t_count}), Authentication Failure ({a_count}), and Network Failure ({n_count}). "
     "These account for over 60% of all historical failures."),
    # Engineer assignments
    ("Which engineers are assigned to defects in the {component} component?",
     "Engineers assigned to {component} defects include: {eng_names}. "
     "They are responsible for {count} open defects in this component."),
    # Environment
    ("What test environments are used for mobile application testing?",
     "Mobile application testing uses environments: ENV-001 (Mobile Lab, Android 14, WiFi-6), "
     "ENV-007 (Staging, Android 13, LTE), ENV-008 (Production-like, One UI 6.0, 5G), "
     "and ENV-009 (Low Network Env, Android 14, Low-BW Sim)."),
]

def gen_semantic_queries():
    queries = []
    gt      = []
    qid     = 1

    for i in range(100):
        tmpl_q, tmpl_a = SEMANTIC_TEMPLATES[i % len(SEMANTIC_TEMPLATES)]
        f  = random.choice(fail_sample)
        d  = random.choice(defect_sample)
        t  = random.choice(tc_sample)
        r  = random.choice(req_sample)
        rn = random.choice(run_sample)
        app_name = app_map.get(f["application_id"], "SmartHome")
        ftype    = f["failure_type"]
        comp     = f.get("component", "Authentication")
        rc       = f.get("root_cause", "Unknown root cause")[:120]
        tc_ids_  = random.sample([x["test_case_id"] for x in tcs], min(3, len(tcs)))
        req_ids_ = random.sample([x["requirement_id"] for x in reqs], min(3, len(reqs)))
        def_ids_ = random.sample([x["defect_id"] for x in defects], min(3, len(defects)))
        fail_ids_= random.sample([x["failure_id"] for x in fails], min(3, len(fails)))
        eng_names= random.sample(list(eng_map.values()), min(3, len(eng_map)))
        feature  = random.choice(["device pairing","user authentication","data synchronisation",
                                   "payment processing","voice recognition","health metric sync"])
        suite_id = random.choice([s["suite_id"] for s in suites])
        test_type= random.choice(["Functional","Performance","Security","Regression"])

        question = (tmpl_q
            .replace("{ftype}",    ftype)
            .replace("{app}",      app_name)
            .replace("{run_name}", rn.get("name","Regression Cycle 1"))
            .replace("{defect_id}",d["defect_id"])
            .replace("{component}",comp)
            .replace("{feature}",  feature)
        )

        answer = (tmpl_a
            .replace("{ftype}",      ftype)
            .replace("{app}",        app_name)
            .replace("{root_cause}", rc)
            .replace("{condition}",  random.choice(["low-bandwidth","high-load","degraded-network"]))
            .replace("{fail_ids}",   ", ".join(fail_ids_))
            .replace("{component}",  comp)
            .replace("{tc_ids}",     ", ".join(tc_ids_))
            .replace("{test_type}",  test_type)
            .replace("{suite_id}",   suite_id)
            .replace("{run_name}",   rn.get("name","Regression Cycle 1"))
            .replace("{failed}",     rn.get("failed","10"))
            .replace("{total}",      rn.get("total_tests","100"))
            .replace("{pass_rate}",  rn.get("pass_rate","90.00"))
            .replace("{defect_ids}", ", ".join(def_ids_))
            .replace("{tc_id}",      t["test_case_id"])
            .replace("{fail_id}",    f["failure_id"])
            .replace("{count}",      str(random.randint(5,30)))
            .replace("{req_ids}",    ", ".join(req_ids_))
            .replace("{t_count}",    str(random.randint(80,200)))
            .replace("{a_count}",    str(random.randint(60,150)))
            .replace("{n_count}",    str(random.randint(50,120)))
            .replace("{eng_names}",  ", ".join(eng_names))
        )

        qobj = {
            "query_id":          f"SQ-{qid:03d}",
            "question":          question,
            "query_type":        "semantic",
            "expected_answer":   answer,
            "expected_documents": [
                f"failure_logs/{f['failure_id']}.md",
                f"defect_reports/DR-{d['defect_id']}.md",
            ],
            "expected_entities": tc_ids_ + [f["failure_id"], d["defect_id"]],
        }
        queries.append(qobj)
        gt.append({
            "query_id":        f"SQ-{qid:03d}",
            "query_type":      "semantic",
            "answer":          answer,
            "source_entities": tc_ids_ + [f["failure_id"]],
            "source_documents":[f"failure_logs/{f['failure_id']}.md"],
        })
        qid += 1

    return queries, gt

# ──────────────────────────────────────────────────────────────────────────────
# GRAPH QUERIES  (100)
# ──────────────────────────────────────────────────────────────────────────────

GRAPH_TEMPLATES = [
    ("Which requirements are affected by defect {defect_id}?",
     "Defect {defect_id} affects requirement {req_id} via the path: "
     "{defect_id} →[AFFECTS]→ {req_id}.",
     ["AFFECTS"]),
    ("Which test cases implement requirement {req_id}?",
     "Requirement {req_id} is implemented by test cases: {tc_ids}. "
     "Path: {req_id} ←[IMPLEMENTS]← {tc_id}.",
     ["IMPLEMENTS"]),
    ("Show the requirement-to-defect traceability chain for defect {defect_id}.",
     "Traceability chain: {req_id} →[IMPLEMENTS]→ {tc_id} →[HAS_EXECUTION]→ {exec_id} "
     "→[PRODUCED]→ {fail_id} →[LINKED_TO]→ {defect_id} →[AFFECTS]→ {req_id}.",
     ["IMPLEMENTS","HAS_EXECUTION","PRODUCED","LINKED_TO","AFFECTS"]),
    ("Which defects were produced by failed executions of test case {tc_id}?",
     "Test case {tc_id} produced defects through failed executions: "
     "{tc_id} →[HAS_EXECUTION]→ {exec_id} →[PRODUCED]→ {fail_id} →[LINKED_TO]→ {defect_id}.",
     ["HAS_EXECUTION","PRODUCED","LINKED_TO"]),
    ("Which engineer is assigned to defect {defect_id}?",
     "Defect {defect_id} is assigned to engineer {eng_id} ({eng_name}). "
     "Path: {defect_id} →[ASSIGNED_TO]→ {eng_id}.",
     ["ASSIGNED_TO"]),
    ("Which test run does execution {exec_id} belong to?",
     "Execution {exec_id} was performed during test run {run_id} ({run_name}). "
     "Path: {exec_id} →[EXECUTED_DURING]→ {run_id}.",
     ["EXECUTED_DURING"]),
    ("Which failures occurred in environment {env_id}?",
     "Failures that occurred in environment {env_id} include: {fail_ids}. "
     "Path: FAILURE →[OCCURRED_IN]→ {env_id}.",
     ["OCCURRED_IN"]),
    ("What is the full traceability path from requirement {req_id} to its defects?",
     "Path: {req_id} ←[IMPLEMENTS]← {tc_id} →[HAS_EXECUTION]→ {exec_id} "
     "→[PRODUCED]→ {fail_id} →[LINKED_TO]→ {defect_id} →[AFFECTS]→ {req_id}.",
     ["IMPLEMENTS","HAS_EXECUTION","PRODUCED","LINKED_TO","AFFECTS"]),
    ("Which test suites contain test case {tc_id}?",
     "Test case {tc_id} is contained in suite {suite_id}. "
     "Path: {suite_id} →[CONTAINS]→ {tc_id}.",
     ["CONTAINS"]),
    ("Which requirements belong to application {app_id}?",
     "Application {app_id} ({app_name}) has {count} requirements including: {req_ids}. "
     "Path: REQUIREMENT →[BELONGS_TO]→ {app_id}.",
     ["BELONGS_TO"]),
]

def gen_graph_queries():
    queries = []
    gt      = []
    qid     = 1

    for i in range(100):
        tmpl_q, tmpl_a, rel_types = GRAPH_TEMPLATES[i % len(GRAPH_TEMPLATES)]

        # Pick concrete entities
        d    = random.choice(defect_sample)
        t    = random.choice(tc_sample)
        r    = req_map.get(d["affected_requirement"], random.choice(req_sample))
        f    = fail_map.get(d["related_failure"], random.choice(fail_sample))
        eng  = random.choice(engs)
        env  = random.choice(envs)
        app  = random.choice(app_sample)
        rn   = random.choice(run_sample)

        # Find a real execution for the defect's failure
        exec_obj = None
        if f.get("execution_id") and f["execution_id"] in exec_map:
            exec_obj = exec_map[f["execution_id"]]
        if not exec_obj:
            exec_obj = random.choice(execs)

        tc_ids_for_req = tc_by_req.get(r["requirement_id"], [t["test_case_id"]])[:3]
        fail_ids_env   = [x["failure_id"] for x in fail_sample
                          if x.get("environment") == env["environment_id"]][:3]
        req_ids_app    = [x["requirement_id"] for x in req_sample
                          if x["application_id"] == app["application_id"]][:4]

        question = (tmpl_q
            .replace("{defect_id}", d["defect_id"])
            .replace("{req_id}",    r["requirement_id"])
            .replace("{tc_id}",     t["test_case_id"])
            .replace("{exec_id}",   exec_obj["execution_id"])
            .replace("{env_id}",    env["environment_id"])
            .replace("{app_id}",    app["application_id"])
        )

        answer = (tmpl_a
            .replace("{defect_id}", d["defect_id"])
            .replace("{req_id}",    r["requirement_id"])
            .replace("{tc_ids}",    ", ".join(tc_ids_for_req))
            .replace("{tc_id}",     t["test_case_id"])
            .replace("{exec_id}",   exec_obj["execution_id"])
            .replace("{fail_id}",   f["failure_id"])
            .replace("{eng_id}",    d.get("assigned_engineer", eng["engineer_id"]))
            .replace("{eng_name}",  eng_map.get(d.get("assigned_engineer",""), eng["name"]))
            .replace("{run_id}",    rn["run_id"])
            .replace("{run_name}",  rn["name"])
            .replace("{env_id}",    env["environment_id"])
            .replace("{fail_ids}",  ", ".join(fail_ids_env) if fail_ids_env else f["failure_id"])
            .replace("{suite_id}",  t.get("suite_id","TS-0001"))
            .replace("{app_id}",    app["application_id"])
            .replace("{app_name}",  app["name"])
            .replace("{count}",     str(len(req_ids_app)))
            .replace("{req_ids}",   ", ".join(req_ids_app) if req_ids_app else r["requirement_id"])
        )

        graph_path = " → ".join(f"[{rt}]" for rt in rel_types)

        qobj = {
            "query_id":              f"GQ-{qid:03d}",
            "question":              question,
            "query_type":            "graph",
            "expected_answer":       answer,
            "expected_nodes":        [d["defect_id"], r["requirement_id"],
                                      t["test_case_id"], f["failure_id"]],
            "expected_relationships": rel_types,
            "expected_path":         graph_path,
        }
        queries.append(qobj)
        gt.append({
            "query_id":              f"GQ-{qid:03d}",
            "query_type":            "graph",
            "answer":                answer,
            "expected_nodes":        qobj["expected_nodes"],
            "expected_relationships": rel_types,
            "expected_path":         graph_path,
        })
        qid += 1

    return queries, gt

# ──────────────────────────────────────────────────────────────────────────────
# HYBRID QUERIES  (100)
# ──────────────────────────────────────────────────────────────────────────────

HYBRID_TEMPLATES = [
    {
        "question": "Why did test case {tc_id} fail, which requirement does it affect, and has the same root cause occurred before?",
        "answer":   "Test case {tc_id} failed with a {ftype} (failure {fail_id}). "
                    "It implements requirement {req_id} ({req_title}). "
                    "Root cause: {root_cause}. "
                    "This same root cause has recurred {recurrence} times in historical data, "
                    "most recently in build {hist_build}. "
                    "Related defect: {defect_id}.",
        "graph_path": "{tc_id} →[HAS_EXECUTION]→ {exec_id} →[PRODUCED]→ {fail_id} →[LINKED_TO]→ {defect_id} →[AFFECTS]→ {req_id}",
        "required_evidence": ["failure_logs/{fail_id}.md", "defect_reports/DR-{defect_id}.md", "historical recurrence data"],
    },
    {
        "question": "What caused the regression failures for the {feature} feature in {app} and which requirements are impacted?",
        "answer":   "Regression failures for {feature} in {app} were caused by {root_cause}. "
                    "Affected requirements include {req_ids}. "
                    "The failures are of type {ftype} and were logged as {fail_ids}. "
                    "Defects {defect_ids} have been raised to track resolution.",
        "graph_path": "REQUIREMENT →[BELONGS_TO]→ {app_id} ←[AFFECTS]← DEFECT ←[LINKED_TO]← FAILURE",
        "required_evidence": ["failure_logs", "defect_reports", "requirements docs"],
    },
    {
        "question": "Find similar historical failures to {defect_id} and identify the test cases and requirements affected.",
        "answer":   "Defect {defect_id} involves a {ftype} in the {component} component. "
                    "Similar historical failures sharing the same root cause pattern: {hist_ids}. "
                    "Affected test cases: {tc_ids}. Affected requirements: {req_ids}. "
                    "All relate to root cause: {root_cause}.",
        "graph_path": "DEFECT →[LINKED_TO]← FAILURE →[PRODUCED]← EXECUTION ←[HAS_EXECUTION]← TEST_CASE →[IMPLEMENTS]→ REQUIREMENT",
        "required_evidence": ["historical_failures.csv", "defect_reports", "requirements docs"],
    },
    {
        "question": "Summarise the root cause of the latest {app} regression failures and show the affected requirement-test-defect chain.",
        "answer":   "In the latest {app} regression cycle ({run_name}), "
                    "{failed} tests failed with pass rate {pass_rate}%. "
                    "Root causes include {root_cause}. "
                    "Chain: {req_id} ←[IMPLEMENTS]← {tc_id} →[HAS_EXECUTION]→ {exec_id} "
                    "→[PRODUCED]→ {fail_id} →[LINKED_TO]→ {defect_id} →[AFFECTS]→ {req_id}.",
        "graph_path": "{req_id} ←[IMPLEMENTS]← {tc_id} →[HAS_EXECUTION]→ {exec_id} →[PRODUCED]→ {fail_id} →[LINKED_TO]→ {defect_id} →[AFFECTS]→ {req_id}",
        "required_evidence": ["execution_reports", "failure_logs", "defect_reports"],
    },
    {
        "question": "Which high-priority failures in {run_name} are linked to Critical requirements and what is their resolution status?",
        "answer":   "In {run_name}, {count} Critical-severity failures were linked to Critical requirements. "
                    "Key failures: {fail_ids}, linked to requirements {req_ids}. "
                    "Resolution status: {res_status}. "
                    "Defects {defect_ids} are currently {defect_status}.",
        "graph_path": "TEST_RUN ←[EXECUTED_DURING]← EXECUTION →[PRODUCED]→ FAILURE →[LINKED_TO]→ DEFECT →[AFFECTS]→ REQUIREMENT",
        "required_evidence": ["execution reports", "failure logs", "requirements docs"],
    },
    {
        "question": "What is the complete traceability chain for requirement {req_id} including all linked defects and their resolution?",
        "answer":   "Requirement {req_id} ({req_title}) is implemented by {count} test cases including {tc_id}. "
                    "Execution history: {exec_count} executions, {failed} failures. "
                    "Open defects: {defect_ids}. Root cause cluster: {root_cause}.",
        "graph_path": "{req_id} ←[IMPLEMENTS]← TEST_CASE →[HAS_EXECUTION]→ EXECUTION →[PRODUCED]→ FAILURE →[LINKED_TO]→ DEFECT →[AFFECTS]→ {req_id}",
        "required_evidence": ["requirements docs", "test case specs", "defect reports"],
    },
    {
        "question": "Which failures in {app} share the same root cause as {fail_id} and how many times has this pattern recurred?",
        "answer":   "Failure {fail_id} in {app} has root cause: {root_cause}. "
                    "Failures sharing this root cause: {similar_fails}. "
                    "Historical recurrence count: {recurrence} occurrences across {hist_count} regression cycles.",
        "graph_path": "FAILURE →[OCCURRED_IN]→ ENVIRONMENT, FAILURE →[LINKED_TO]→ DEFECT",
        "required_evidence": ["failure_logs", "historical_failures.csv"],
    },
    {
        "question": "For defect {defect_id}, explain the technical root cause, which component is affected, and what test cases should be added to prevent recurrence.",
        "answer":   "Defect {defect_id} affects the {component} component of {app}. "
                    "Technical root cause: {root_cause}. "
                    "Currently covered by test case {tc_id}. "
                    "Recommended additional test cases should cover: edge cases for {ftype} scenarios under {condition}.",
        "graph_path": "{defect_id} →[LINKED_TO]← {fail_id} →[PRODUCED]← {exec_id} ←[HAS_EXECUTION]← {tc_id} →[IMPLEMENTS]→ {req_id}",
        "required_evidence": ["defect_reports", "troubleshooting guides", "test case specs"],
    },
    {
        "question": "What is the pass rate trend for {app} across the last 3 regression cycles and what are the recurring failure patterns?",
        "answer":   "Pass rate trend for {app}: "
                    "cycle 1 → {pr1}%, cycle 2 → {pr2}%, cycle 3 → {pr3}%. "
                    "Recurring failure patterns: {ftype} ({fcount} occurrences) and network failures. "
                    "Most affected component: {component}.",
        "graph_path": "APPLICATION →[BELONGS_TO]← TEST_SUITE →[CONTAINS]→ TEST_CASE →[HAS_EXECUTION]→ TEST_EXECUTION →[EXECUTED_DURING]→ TEST_RUN",
        "required_evidence": ["execution_reports", "historical_failures.csv"],
    },
    {
        "question": "Which open defects in the {component} component block the release of {app} and what is their traceability to requirements?",
        "answer":   "Open defects blocking {app} release in {component}: {defect_ids}. "
                    "Requirement impact: {req_ids}. "
                    "Traceability: DEFECT →[AFFECTS]→ REQUIREMENT →[BELONGS_TO]→ APPLICATION.",
        "graph_path": "DEFECT →[AFFECTS]→ REQUIREMENT →[BELONGS_TO]→ APPLICATION",
        "required_evidence": ["defect_reports", "requirements docs"],
    },
]

def gen_hybrid_queries():
    queries = []
    gt      = []
    qid     = 1

    run_pass_rates = [r.get("pass_rate","90.00") for r in run_sample]

    for i in range(100):
        tmpl = HYBRID_TEMPLATES[i % len(HYBRID_TEMPLATES)]

        d      = random.choice(defect_sample)
        t      = random.choice(tc_sample)
        r      = req_map.get(d["affected_requirement"], random.choice(req_sample))
        f      = fail_map.get(d["related_failure"], random.choice(fail_sample))
        app    = app_map.get(d["application_id"], random.choice(list(app_map.values())))
        app_id = d["application_id"]
        rn     = random.choice(run_sample)
        env    = random.choice(envs)

        exec_obj = None
        if f.get("execution_id") and f["execution_id"] in exec_map:
            exec_obj = exec_map[f["execution_id"]]
        if not exec_obj:
            exec_obj = random.choice(execs)

        # Historical recurrence
        hist_matches = [h for h in hist if h.get("failure_type") == f["failure_type"]]
        recurrence   = sum(int(h.get("recurrence_count","1")) for h in hist_matches[:10])
        hist_build   = hist_matches[0]["build_version"] if hist_matches else "5.2.0"
        hist_ids     = [h["hist_failure_id"] for h in hist_matches[:4]]
        hist_count   = len(set(h.get("original_failure","") for h in hist_matches[:20]))

        tc_ids_req   = tc_by_req.get(r["requirement_id"], [t["test_case_id"]])[:3]
        req_ids_app  = [x["requirement_id"] for x in req_sample
                        if x["application_id"] == app_id][:4]
        fail_ids_app = [x["failure_id"] for x in fail_sample
                        if x["application_id"] == app_id][:3]
        defect_ids_  = [x["defect_id"] for x in defect_sample
                        if x["application_id"] == app_id][:3]
        similar_fails= [x["failure_id"] for x in fail_sample
                        if x.get("failure_type") == f["failure_type"]][:4]

        pr1 = run_pass_rates[i % len(run_pass_rates)]
        pr2 = run_pass_rates[(i+1) % len(run_pass_rates)]
        pr3 = run_pass_rates[(i+2) % len(run_pass_rates)]
        feature = random.choice(["device pairing","user authentication","data synchronisation",
                                  "payment processing","health metric upload","voice recognition"])
        condition = random.choice(["low-bandwidth","high-load","degraded-network","standard"])

        def fill(tmpl_str):
            return (tmpl_str
                .replace("{tc_id}",       t["test_case_id"])
                .replace("{fail_id}",     f["failure_id"])
                .replace("{defect_id}",   d["defect_id"])
                .replace("{req_id}",      r["requirement_id"])
                .replace("{req_title}",   r.get("title","")[:60])
                .replace("{exec_id}",     exec_obj["execution_id"])
                .replace("{app}",         app)
                .replace("{app_id}",      app_id)
                .replace("{run_name}",    rn["name"])
                .replace("{ftype}",       f["failure_type"])
                .replace("{component}",   f.get("component","Authentication"))
                .replace("{root_cause}",  f.get("root_cause","See root cause analysis")[:100])
                .replace("{recurrence}",  str(recurrence))
                .replace("{hist_build}",  hist_build)
                .replace("{hist_ids}",    ", ".join(hist_ids) if hist_ids else "N/A")
                .replace("{hist_count}",  str(hist_count))
                .replace("{tc_ids}",      ", ".join(tc_ids_req))
                .replace("{req_ids}",     ", ".join(req_ids_app) if req_ids_app else r["requirement_id"])
                .replace("{fail_ids}",    ", ".join(fail_ids_app) if fail_ids_app else f["failure_id"])
                .replace("{defect_ids}",  ", ".join(defect_ids_) if defect_ids_ else d["defect_id"])
                .replace("{defect_status}",d.get("status","OPEN"))
                .replace("{res_status}",  d.get("status","OPEN"))
                .replace("{failed}",      rn.get("failed","10"))
                .replace("{pass_rate}",   rn.get("pass_rate","90.00"))
                .replace("{exec_count}",  str(len(exec_by_tc.get(t["test_case_id"],[]))))
                .replace("{count}",       str(len(tc_ids_req)))
                .replace("{similar_fails}",", ".join(similar_fails) if similar_fails else f["failure_id"])
                .replace("{fcount}",      str(len(similar_fails)))
                .replace("{pr1}",         pr1)
                .replace("{pr2}",         pr2)
                .replace("{pr3}",         pr3)
                .replace("{feature}",     feature)
                .replace("{condition}",   condition)
            )

        question    = fill(tmpl["question"])
        answer      = fill(tmpl["answer"])
        graph_path  = fill(tmpl["graph_path"])
        req_evidence= [fill(e) for e in tmpl["required_evidence"]]

        qobj = {
            "query_id":              f"HQ-{qid:03d}",
            "question":              question,
            "query_type":            "hybrid",
            "expected_answer":       answer,
            "expected_documents":    [
                f"failure_logs/{f['failure_id']}.md",
                f"defect_reports/DR-{d['defect_id']}.md",
            ],
            "expected_entities":     [t["test_case_id"], f["failure_id"],
                                       d["defect_id"], r["requirement_id"]],
            "expected_relationships":["HAS_EXECUTION","PRODUCED","LINKED_TO","AFFECTS","IMPLEMENTS"],
            "expected_graph_path":   graph_path,
            "required_evidence":     req_evidence,
        }
        queries.append(qobj)
        gt.append({
            "query_id":              f"HQ-{qid:03d}",
            "query_type":            "hybrid",
            "answer":                answer,
            "source_entities":       [t["test_case_id"], f["failure_id"], d["defect_id"]],
            "source_documents":      [f"failure_logs/{f['failure_id']}.md"],
            "expected_graph_path":   graph_path,
        })
        qid += 1

    return queries, gt

# ──────────────────────────────────────────────────────────────────────────────
# EXPECTED ENTITIES & RELATIONSHIPS
# ──────────────────────────────────────────────────────────────────────────────

def gen_expected_entities(all_queries):
    rows = []
    for q in all_queries:
        entities = q.get("expected_entities") or q.get("expected_nodes", [])
        if entities:
            rows.append({
                "query_id":   q["query_id"],
                "entity_ids": entities,
            })
    return rows

def gen_expected_relationships(graph_queries, hybrid_queries):
    rows = []
    for q in graph_queries + hybrid_queries:
        rows.append({
            "query_id":         q["query_id"],
            "source_node":      q["expected_entities"][0] if q.get("expected_entities") else "",
            "target_node":      q["expected_entities"][-1] if q.get("expected_entities") else "",
            "relationship_types": q.get("expected_relationships", []),
            "graph_path":       q.get("expected_path") or q.get("expected_graph_path",""),
        })
    return rows

# ──────────────────────────────────────────────────────────────────────────────
# EVALUATION METRICS DOC
# ──────────────────────────────────────────────────────────────────────────────

EVAL_METRICS_MD = """# Evaluation Metrics Reference

This document defines the metrics used to evaluate the Hybrid RAG pipeline
against the synthetic test-management dataset.

---

## 1. Retrieval Metrics (Vanilla RAG)

| Metric | Description | Target |
|--------|-------------|--------|
| Recall@5 | Fraction of relevant docs in top-5 results | ≥ 0.80 |
| Precision@5 | Fraction of top-5 results that are relevant | ≥ 0.70 |
| MRR | Mean Reciprocal Rank of first relevant document | ≥ 0.75 |
| NDCG@10 | Normalised Discounted Cumulative Gain at rank 10 | ≥ 0.72 |
| Hit Rate@1 | Fraction of queries where top-1 is relevant | ≥ 0.65 |

## 2. Graph Retrieval Metrics (Graph RAG)

| Metric | Description | Target |
|--------|-------------|--------|
| Entity Recall | Fraction of expected entities retrieved | ≥ 0.85 |
| Relationship Recall | Fraction of expected relationships traversed | ≥ 0.80 |
| Path Accuracy | Whether the correct multi-hop path was followed | ≥ 0.75 |
| Node Precision | Fraction of retrieved nodes that are expected | ≥ 0.70 |

## 3. Answer Quality Metrics (LLM)

| Metric | Description | Target |
|--------|-------------|--------|
| ROUGE-L | Longest common subsequence overlap with reference | ≥ 0.45 |
| BERTScore F1 | Semantic similarity to reference answer | ≥ 0.80 |
| Faithfulness | Answer grounded in retrieved context (0–1) | ≥ 0.85 |
| Completeness | All required aspects addressed (0–1) | ≥ 0.75 |
| Hallucination Rate | Fraction of answers with unsupported claims | ≤ 0.10 |

## 4. Hybrid RAG Specific Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Evidence Integration | Both graph + document evidence used | ≥ 0.80 |
| Multi-hop Accuracy | Correct traversal of ≥2 relationship hops | ≥ 0.70 |
| Traceability Completeness | Full requirement→defect chain recovered | ≥ 0.75 |
| Context Relevance | Retrieved context relevant to query | ≥ 0.82 |

## 5. Query Type Distribution

| Type | Count | Purpose |
|------|-------|---------|
| Semantic | 100 | Tests pure vector retrieval quality |
| Graph | 100 | Tests knowledge-graph traversal accuracy |
| Hybrid | 100 | Tests combined retrieval and reasoning |
| **Total** | **300** | |

## 6. Scoring Procedure

1. Run the RAG pipeline against `questions.jsonl`.
2. Compare generated answers to `ground_truth.jsonl`.
3. Compute all metrics above using the evaluation harness.
4. Report per-query-type and aggregate scores.
5. Flag any query where faithfulness < 0.6 for manual review.

## 7. Baseline Targets

A pipeline scoring below the targets in section 1–4 should be considered
under-optimised and requires further tuning of:
- Chunk size and overlap parameters.
- Embedding model selection.
- Graph traversal depth limit.
- LLM prompt template for context integration.

---
*This document is synthetic and created for AI/RAG research purposes only.*
"""

# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("\n=== Evaluation Dataset Generator ===\n")

    print("Generating semantic queries…")
    sem_q, sem_gt = gen_semantic_queries()

    print("Generating graph queries…")
    gph_q, gph_gt = gen_graph_queries()

    print("Generating hybrid queries…")
    hyb_q, hyb_gt = gen_hybrid_queries()

    all_queries = sem_q + gph_q + hyb_q
    all_gt      = sem_gt + gph_gt + hyb_gt

    print("\nWriting evaluation files…")
    write_jsonl(EVAL / "questions.jsonl",        all_queries)
    write_jsonl(EVAL / "ground_truth.jsonl",     all_gt)
    write_jsonl(EVAL / "semantic_queries.jsonl", sem_q)
    write_jsonl(EVAL / "graph_queries.jsonl",    gph_q)
    write_jsonl(EVAL / "hybrid_queries.jsonl",   hyb_q)

    ee_rows = gen_expected_entities(all_queries)
    write_jsonl(EVAL / "expected_entities.jsonl", ee_rows)

    er_rows = gen_expected_relationships(gph_q, hyb_q)
    write_jsonl(EVAL / "expected_relationships.jsonl", er_rows)

    (EVAL / "evaluation_metrics.md").write_text(EVAL_METRICS_MD, encoding="utf-8")
    print(f"  ✓ {'evaluation_metrics.md':45s}     1 file")

    print(f"\nTotal queries : {len(all_queries)} ({len(sem_q)} semantic + {len(gph_q)} graph + {len(hyb_q)} hybrid)")
    print("Evaluation dataset generation complete.\n")

if __name__ == "__main__":
    main()
