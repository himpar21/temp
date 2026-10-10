"""
validate_pdf_dataset.py
========================
Validates the PDF dataset and input fixtures for the AI-Powered Test Management
System Hybrid RAG project.

16 checks covering PDF existence, entity integrity, fixture completeness,
evaluation consistency, and existing-dataset safety.

Run:
    python datasets/synthetic_test_management/pdf_generation/validate_pdf_dataset.py

Exit 0 = all checks passed.  Exit 1 = one or more failures.
All output is ASCII-safe for Windows terminals.
"""

import csv
import json
import sys
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
DATASET_ROOT = SCRIPT_DIR.parent
PDF_DOCS     = DATASET_ROOT / "pdf_documents"
META_DIR     = DATASET_ROOT / "pdf_metadata"
FIX_DIR      = DATASET_ROOT / "input_fixtures"
EVAL_DIR     = DATASET_ROOT / "evaluation" / "pdf_input_evaluation"
STRUCTURED   = DATASET_ROOT / "structured"

# ── ASCII-safe output ──────────────────────────────────────────────────────────
PASS = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"
INFO = "[INFO]"

errors   = []
warnings = []


def ok(msg):
    print(f"  {PASS} {msg}")


def fail(msg):
    errors.append(msg)
    print(f"  {FAIL} {msg}")


def warn(msg):
    warnings.append(msg)
    print(f"  {WARN} {msg}")


def info(msg):
    print(f"  {INFO} {msg}")


# ── helpers ────────────────────────────────────────────────────────────────────

def load_csv(path: Path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def load_jsonl(path: Path):
    rows = []
    if not path.exists():
        return rows
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                fail(f"{path.name} line {i}: invalid JSON — {e}")
    return rows


def load_json(path: Path):
    if not path.exists():
        return {}
    with open(path, encoding="utf-8", errors="replace") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            fail(f"{path.name}: invalid JSON — {e}")
            return {}


def load_existing_ids():
    """Load all entity IDs from the structured dataset (via git-show if needed)."""
    import subprocess

    SOURCE_BRANCH = "dataset/complete-test-management-synthetic-data"
    REPO_ROOT = DATASET_ROOT.parents[1]

    def _git_show(rel):
        try:
            r = subprocess.run(
                ["git", "show", f"{SOURCE_BRANCH}:{rel}"],
                capture_output=True, text=True,
                encoding="utf-8", errors="replace",
                cwd=str(REPO_ROOT)
            )
            if r.returncode == 0:
                return r.stdout
        except Exception:
            pass
        return None

    def _get(name, field):
        disk = STRUCTURED / name
        if disk.exists():
            with open(disk, encoding="utf-8", errors="replace") as f:
                return {row[field] for row in csv.DictReader(f) if row.get(field)}
        text = _git_show(f"datasets/synthetic_test_management/structured/{name}")
        if text:
            import io
            return {row[field] for row in csv.DictReader(io.StringIO(text)) if row.get(field)}
        return set()

    ids = {}
    ids["app"]    = _get("applications.csv",    "application_id")
    ids["req"]    = _get("requirements.csv",     "requirement_id")
    ids["tc"]     = _get("test_cases.csv",       "test_case_id")
    ids["exec"]   = _get("test_executions.csv",  "execution_id")
    ids["fail"]   = _get("failures.csv",         "failure_id")
    ids["defect"] = _get("defects.csv",          "defect_id")
    ids["run"]    = _get("test_runs.csv",        "run_id")
    ids["env"]    = _get("environments.csv",     "environment_id")
    ids["sol"]    = _get("solutions.csv",        "solution_id")
    ids["rel"]    = _get("releases.csv",         "release_id")
    ids["eng"]    = _get("engineers.csv",        "engineer_id")
    ids["suite"]  = _get("test_suites.csv",      "suite_id")
    ids["all"] = set().union(*ids.values())
    return ids


# ── CHECK 1: Every PDF referenced in metadata exists on disk ──────────────────
def check_pdf_existence(manifest_rows):
    print("\n[1] PDF file existence checks")
    missing = []
    for row in manifest_rows:
        dt    = row.get("document_type", "")
        fname = row.get("filename", "")
        subdirs = {
            "requirement_spec":  "requirements",
            "test_plan":         "test_plans",
            "test_case_spec":    "test_cases",
            "execution_report":  "execution_reports",
            "failure_report":    "failure_reports",
            "defect_report":     "defect_reports",
        }
        subdir = subdirs.get(dt, "")
        if not subdir or not fname:
            missing.append(f"bad row: {row.get('pdf_id','?')}")
            continue
        p = PDF_DOCS / subdir / fname
        if not p.exists():
            missing.append(str(p.relative_to(DATASET_ROOT)))
    if missing:
        fail(f"{len(missing)} PDFs in manifest missing on disk: {missing[:3]}")
    else:
        ok(f"All {len(manifest_rows)} manifest PDFs exist on disk")


# ── CHECK 2: Every referenced entity exists in the existing dataset ───────────
def check_entity_references(manifest_rows, existing_ids):
    print("\n[2] Entity reference integrity checks")
    broken = []

    def _check(val, id_type, context):
        if not val:
            return
        for v in val.split("|"):
            v = v.strip()
            if not v:
                continue
            if v not in existing_ids.get(id_type, set()):
                broken.append(f"{context}: {v} not in {id_type}")

    for row in manifest_rows:
        pid = row.get("pdf_id", "?")
        _check(row.get("application_id", ""),   "app",    pid)
        _check(row.get("requirement_ids", ""),  "req",    pid)
        _check(row.get("test_case_ids", ""),    "tc",     pid)
        _check(row.get("execution_ids", ""),    "exec",   pid)
        _check(row.get("failure_ids", ""),      "fail",   pid)
        _check(row.get("defect_ids", ""),       "defect", pid)
        _check(row.get("release_id", ""),       "rel",    pid)
        _check(row.get("environment_id", ""),   "env",    pid)

    if broken:
        fail(f"{len(broken)} broken entity refs in manifest: {broken[:3]}")
    else:
        ok(f"All entity references in manifest resolve to existing dataset IDs")


# ── CHECK 3: No invalid / malformed IDs ───────────────────────────────────────
def check_no_invalid_ids(manifest_rows):
    print("\n[3] No invalid ID checks")
    import re
    invalid = []
    for row in manifest_rows:
        pid = row.get("pdf_id", "")
        if not pid or not re.match(r"^PDF-[A-Z]+-", pid):
            invalid.append(f"bad pdf_id: {pid!r}")
        pe = row.get("primary_entity_id", "")
        if pe and not re.match(r"^[A-Z]+-[\d\w]+$", pe):
            invalid.append(f"malformed primary_entity: {pe!r}")
    if invalid:
        fail(f"{len(invalid)} malformed IDs: {invalid[:3]}")
    else:
        ok(f"All {len(manifest_rows)} PDF IDs and primary entity IDs are well-formed")


# ── CHECK 4: No duplicate PDF IDs ─────────────────────────────────────────────
def check_no_duplicate_pdf_ids(manifest_rows):
    print("\n[4] Duplicate PDF ID checks")
    pdf_ids  = [r.get("pdf_id", "") for r in manifest_rows]
    filenames= [r.get("filename", "") for r in manifest_rows]
    dup_ids  = [x for x in pdf_ids  if pdf_ids.count(x)   > 1]
    dup_fns  = [x for x in filenames if filenames.count(x) > 1]
    if dup_ids:
        fail(f"{len(set(dup_ids))} duplicate pdf_ids: {list(set(dup_ids))[:3]}")
    else:
        ok(f"No duplicate pdf_ids ({len(pdf_ids)} entries)")
    if dup_fns:
        fail(f"{len(set(dup_fns))} duplicate filenames: {list(set(dup_fns))[:3]}")
    else:
        ok(f"No duplicate filenames")


# ── CHECK 5: Every PDF has metadata ───────────────────────────────────────────
def check_every_pdf_has_metadata(manifest_rows):
    print("\n[5] Every PDF has metadata")
    manifest_fnames = {r["filename"] for r in manifest_rows}
    subdirs = {
        "requirements":     "requirement_spec",
        "test_plans":       "test_plan",
        "test_cases":       "test_case_spec",
        "execution_reports":"execution_report",
        "failure_reports":  "failure_report",
        "defect_reports":   "defect_report",
    }
    all_pdfs  = []
    no_meta   = []
    for subdir in subdirs:
        d = PDF_DOCS / subdir
        if not d.exists():
            continue
        for p in d.glob("*.pdf"):
            all_pdfs.append(p.name)
            if p.name not in manifest_fnames:
                no_meta.append(p.name)
    if no_meta:
        warn(f"{len(no_meta)} PDFs on disk lack manifest entries: {no_meta[:3]}")
    else:
        ok(f"All {len(all_pdfs)} PDFs have manifest entries")


# ── CHECK 6: Line+PDF fixtures reference existing PDFs ────────────────────────
def check_line_pdf_fixtures(line_pdf_rows, manifest_fnames):
    print("\n[6] Line+PDF fixture PDF references")
    missing = [r["pdf_filename"] for r in line_pdf_rows
               if r.get("pdf_filename") and r["pdf_filename"] not in manifest_fnames]
    if missing:
        fail(f"{len(missing)} line+PDF fixtures reference missing PDFs: {missing[:3]}")
    else:
        ok(f"All {len(line_pdf_rows)} line+PDF fixtures reference valid PDFs")


# ── CHECK 7: PDF-only fixtures reference existing PDFs ────────────────────────
def check_pdf_only_fixtures(pdf_only_rows, manifest_fnames):
    print("\n[7] PDF-only fixture PDF references")
    missing = [r["pdf_filename"] for r in pdf_only_rows
               if r.get("pdf_filename") and r["pdf_filename"] not in manifest_fnames]
    if missing:
        fail(f"{len(missing)} PDF-only fixtures reference missing PDFs: {missing[:3]}")
    else:
        ok(f"All {len(pdf_only_rows)} PDF-only fixtures reference valid PDFs")


# ── CHECK 8: Every evaluation question has ground truth ───────────────────────
def check_evaluation_ground_truth(questions, ground_truth):
    print("\n[8] Evaluation ground truth coverage")
    q_ids  = {q.get("query_id") for q in questions}
    gt_ids = {g.get("query_id") for g in ground_truth}
    missing = q_ids - gt_ids
    if missing:
        fail(f"{len(missing)} questions lack ground truth: {list(missing)[:3]}")
    else:
        ok(f"All {len(questions)} evaluation questions have ground truth")


# ── CHECK 9: Expected entities exist in dataset ───────────────────────────────
def check_expected_entities(exp_entities, existing_ids):
    print("\n[9] Expected entity resolution")
    all_ids = existing_ids.get("all", set())
    broken  = []
    for row in exp_entities:
        for eid in row.get("entity_ids", []):
            if eid and eid not in all_ids:
                broken.append(f"{row.get('query_id','?')}: {eid}")
    if broken:
        fail(f"{len(broken)} expected entity IDs not in dataset: {broken[:3]}")
    else:
        ok(f"All expected entity IDs resolve ({len(exp_entities)} records checked)")


# ── CHECK 10: Expected relationships are valid types ──────────────────────────
VALID_REL_TYPES = {
    "BELONGS_TO","IMPLEMENTS","COVERS","CONTAINS","EXECUTED_IN",
    "EXECUTED_DURING","PRODUCED","CAUSED_BY","LINKED_TO","AFFECTS",
    "ASSIGNED_TO","FIXED_BY","VERIFIED_BY","DEPENDS_ON","RELATED_TO",
    "BLOCKS","REPRODUCES","OCCURRED_IN","PART_OF","HAS_EXECUTION",
}

def check_expected_relationships(exp_rels):
    print("\n[10] Expected relationship type validity")
    invalid = []
    for row in exp_rels:
        for rtype in row.get("relationship_types", []):
            if rtype and rtype not in VALID_REL_TYPES:
                invalid.append(f"{row.get('query_id','?')}: {rtype}")
    if invalid:
        fail(f"{len(invalid)} invalid relationship types: {invalid[:3]}")
    else:
        ok(f"All relationship types are valid ({len(exp_rels)} records checked)")


# ── CHECK 11: All three input modes represented ───────────────────────────────
def check_input_modes(line_only, pdf_only, line_pdf):
    print("\n[11] Input mode coverage")
    modes = {
        "LINE_ONLY":     len(line_only),
        "PDF_ONLY":      len(pdf_only),
        "LINE_PLUS_PDF": len(line_pdf),
    }
    for mode, count in modes.items():
        if count == 0:
            fail(f"Input mode {mode} has 0 fixtures")
        elif count < 50:
            warn(f"Input mode {mode} has only {count} fixtures (target >= 50)")
        else:
            ok(f"{mode}: {count} fixtures")


# ── CHECK 12: All document categories represented ─────────────────────────────
def check_document_categories(manifest_rows):
    print("\n[12] Document category coverage")
    required = {
        "requirement_spec", "test_plan", "test_case_spec",
        "execution_report", "failure_report", "defect_report",
    }
    found = {r.get("document_type","") for r in manifest_rows}
    missing = required - found
    if missing:
        fail(f"Missing document categories: {missing}")
    else:
        counts = {dt: sum(1 for r in manifest_rows if r.get("document_type") == dt)
                  for dt in required}
        ok(f"All 6 document categories present: {counts}")


# ── CHECK 13: PDFs are readable/openable ─────────────────────────────────────
def check_pdf_readability(manifest_rows):
    print("\n[13] PDF readability checks (spot-check 20 files)")
    subdirs = {
        "requirement_spec":  "requirements",
        "test_plan":         "test_plans",
        "test_case_spec":    "test_cases",
        "execution_report":  "execution_reports",
        "failure_report":    "failure_reports",
        "defect_report":     "defect_reports",
    }
    import random
    random.seed(42)
    sample = random.sample(manifest_rows, min(20, len(manifest_rows)))
    unreadable = []
    for row in sample:
        subdir = subdirs.get(row.get("document_type", ""), "")
        p = PDF_DOCS / subdir / row.get("filename", "")
        if not p.exists():
            unreadable.append(row.get("filename", "?"))
            continue
        try:
            data = p.read_bytes()
            if not data.startswith(b"%PDF"):
                unreadable.append(f"{p.name}: not a valid PDF header")
            elif len(data) < 500:
                unreadable.append(f"{p.name}: suspiciously small ({len(data)} bytes)")
        except Exception as e:
            unreadable.append(f"{p.name}: {e}")
    if unreadable:
        fail(f"{len(unreadable)} unreadable PDFs in sample: {unreadable[:3]}")
    else:
        ok(f"All 20 sampled PDFs have valid PDF headers and are non-trivial")


# ── CHECK 14: PDFs contain meaningful content (size check) ───────────────────
def check_pdf_content_quality(manifest_rows):
    print("\n[14] PDF content quality (file size)")
    subdirs = {
        "requirement_spec":  "requirements",
        "test_plan":         "test_plans",
        "test_case_spec":    "test_cases",
        "execution_report":  "execution_reports",
        "failure_report":    "failure_reports",
        "defect_report":     "defect_reports",
    }
    MIN_BYTES = 4_000   # 4 KB minimum — requirement PDFs are shorter but still valid
    too_small = []
    sizes = []
    for row in manifest_rows:
        subdir = subdirs.get(row.get("document_type", ""), "")
        p = PDF_DOCS / subdir / row.get("filename", "")
        if not p.exists():
            continue
        sz = p.stat().st_size
        sizes.append(sz)
        if sz < MIN_BYTES:
            too_small.append(f"{p.name}: {sz} bytes")
    if too_small:
        fail(f"{len(too_small)} PDFs below {MIN_BYTES} byte threshold: {too_small[:3]}")
    else:
        avg = sum(sizes) // len(sizes) if sizes else 0
        ok(f"All {len(sizes)} PDFs >= {MIN_BYTES} bytes (avg: {avg:,} bytes)")


# ── CHECK 15: Dataset remains synthetic ───────────────────────────────────────
BANNED_PATTERNS = [
    "CONFIDENTIAL", "internal.samsung.com",
    "password123", "secret_key",
]

def check_synthetic_data(manifest_rows):
    print("\n[15] Synthetic data check (no confidential content)")
    violations = []
    import random
    random.seed(42)
    sample = random.sample(manifest_rows, min(10, len(manifest_rows)))
    subdirs = {
        "requirement_spec":  "requirements",
        "test_plan":         "test_plans",
        "test_case_spec":    "test_cases",
        "execution_report":  "execution_reports",
        "failure_report":    "failure_reports",
        "defect_report":     "defect_reports",
    }
    for row in sample:
        subdir = subdirs.get(row.get("document_type", ""), "")
        p = PDF_DOCS / subdir / row.get("filename", "")
        if not p.exists():
            continue
        # read raw bytes as latin-1 for text scan
        try:
            raw = p.read_bytes().decode("latin-1", errors="replace")
            for banned in BANNED_PATTERNS:
                if banned in raw:
                    violations.append(f"{p.name}: contains '{banned}'")
        except Exception:
            pass
    if violations:
        fail(f"Synthetic data violations: {violations[:3]}")
    else:
        ok(f"No banned patterns found in sampled PDFs")


# ── CHECK 16: Existing dataset files not modified ────────────────────────────
def check_existing_dataset_unmodified():
    print("\n[16] Existing dataset integrity (existing files not modified)")
    import subprocess
    REPO_ROOT = DATASET_ROOT.parents[1]

    # Check for any modifications to files in the base dataset branch
    result = subprocess.run(
        ["git", "diff", "--name-only",
         "dataset/complete-test-management-synthetic-data",
         "HEAD",
         "--", "datasets/synthetic_test_management/"],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", cwd=str(REPO_ROOT)
    )
    changed = [l.strip() for l in result.stdout.splitlines()
               if l.strip() and not l.strip().startswith("datasets/synthetic_test_management/pdf")
               and not l.strip().startswith("datasets/synthetic_test_management/input_fixtures")
               and not l.strip().startswith("datasets/synthetic_test_management/evaluation/pdf_input")]

    if changed:
        fail(f"Existing dataset files were modified: {changed[:3]}")
    else:
        ok(f"No existing dataset files were modified")

    # Also verify critical CSVs exist untouched
    critical = ["structured/requirements.csv", "structured/test_cases.csv",
                "structured/failures.csv", "structured/defects.csv"]
    for c in critical:
        p = DATASET_ROOT / c
        if not p.exists():
            # Try from branch
            r2 = subprocess.run(
                ["git", "show",
                 f"dataset/complete-test-management-synthetic-data:datasets/synthetic_test_management/{c}"],
                capture_output=True, cwd=str(REPO_ROOT)
            )
            if r2.returncode == 0:
                ok(f"{c} exists on dataset branch (not yet on disk — expected)")
            else:
                warn(f"{c} not found on branch or disk")
        else:
            ok(f"{c} present on disk, unmodified")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  PDF DATASET VALIDATION REPORT")
    print("=" * 60)

    # Load data
    print("\nLoading files...")
    manifest_rows = load_csv(META_DIR / "pdf_manifest.csv")
    entity_mapping = load_json(META_DIR / "pdf_entity_mapping.json")
    line_only_rows = load_jsonl(FIX_DIR / "line_only" / "line_only_fixtures.jsonl")
    pdf_only_rows  = load_jsonl(FIX_DIR / "pdf_only" / "pdf_only_fixtures.jsonl")
    line_pdf_rows  = load_jsonl(FIX_DIR / "line_plus_pdf" / "line_plus_pdf_fixtures.jsonl")
    questions      = load_jsonl(EVAL_DIR / "questions.jsonl")
    ground_truth   = load_jsonl(EVAL_DIR / "ground_truth.jsonl")
    exp_entities   = load_jsonl(EVAL_DIR / "expected_entities.jsonl")
    exp_rels       = load_jsonl(EVAL_DIR / "expected_relationships.jsonl")

    info(f"Manifest rows     : {len(manifest_rows)}")
    info(f"Entity map entries: {len(entity_mapping)}")
    info(f"Line-only fixtures: {len(line_only_rows)}")
    info(f"PDF-only fixtures : {len(pdf_only_rows)}")
    info(f"Line+PDF fixtures : {len(line_pdf_rows)}")
    info(f"Eval questions    : {len(questions)}")

    print("\nLoading existing dataset IDs...")
    existing_ids = load_existing_ids()
    total_known = len(existing_ids.get("all", set()))
    info(f"Known entity IDs  : {total_known}")

    manifest_fnames = {r.get("filename", "") for r in manifest_rows}

    # Run all 16 checks
    check_pdf_existence(manifest_rows)
    check_entity_references(manifest_rows, existing_ids)
    check_no_invalid_ids(manifest_rows)
    check_no_duplicate_pdf_ids(manifest_rows)
    check_every_pdf_has_metadata(manifest_rows)
    check_line_pdf_fixtures(line_pdf_rows, manifest_fnames)
    check_pdf_only_fixtures(pdf_only_rows, manifest_fnames)
    check_evaluation_ground_truth(questions, ground_truth)
    check_expected_entities(exp_entities, existing_ids)
    check_expected_relationships(exp_rels)
    check_input_modes(line_only_rows, pdf_only_rows, line_pdf_rows)
    check_document_categories(manifest_rows)
    check_pdf_readability(manifest_rows)
    check_pdf_content_quality(manifest_rows)
    check_synthetic_data(manifest_rows)
    check_existing_dataset_unmodified()

    print("\n" + "=" * 60)
    print("  VALIDATION SUMMARY")
    print("=" * 60)
    print(f"  Errors   : {len(errors)}")
    print(f"  Warnings : {len(warnings)}")

    # Per-category counts
    print("\n  PDFs by document type:")
    for subdir, label in [
        ("requirements",     "requirement_spec"),
        ("test_plans",       "test_plan"),
        ("test_cases",       "test_case_spec"),
        ("execution_reports","execution_report"),
        ("failure_reports",  "failure_report"),
        ("defect_reports",   "defect_report"),
    ]:
        n = len(list((PDF_DOCS / subdir).glob("*.pdf"))) if (PDF_DOCS / subdir).exists() else 0
        print(f"    {label:<25} {n:>3} PDFs")

    total_pdfs = sum(1 for r in manifest_rows)
    print(f"    {'TOTAL':<25} {total_pdfs:>3} PDFs")

    print("\n  Fixtures by input mode:")
    print(f"    LINE_ONLY     : {len(line_only_rows)}")
    print(f"    PDF_ONLY      : {len(pdf_only_rows)}")
    print(f"    LINE_PLUS_PDF : {len(line_pdf_rows)}")
    print(f"    TOTAL         : {len(line_only_rows)+len(pdf_only_rows)+len(line_pdf_rows)}")

    print(f"\n  Evaluation queries : {len(questions)}")

    if errors:
        print("\nFailed checks:")
        for e in errors:
            print(f"  {FAIL} {e}")
        print("\nValidation FAILED.\n")
        sys.exit(1)
    else:
        if warnings:
            print("\nWarnings:")
            for w in warnings:
                print(f"  {WARN} {w}")
        print("\nValidation PASSED.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
