"""
data_loader.py
==============
Loads all existing structured CSVs from the dataset branch into memory.

Because the dataset lives on the `dataset/complete-test-management-synthetic-data`
branch (not yet merged to main), this module reads files from that branch via
git-show if they are not present on disk, OR reads them directly if present.

Usage:
    from data_loader import DataLoader
    dl = DataLoader()
    dl.load()
    apps = dl.applications   # list[dict]
"""

import csv
import io
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

# Root of the repo
REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET_BASE = REPO_ROOT / "datasets" / "synthetic_test_management"
STRUCTURED = DATASET_BASE / "structured"

# Branch where the base dataset lives (may not be on disk if not checked out)
SOURCE_BRANCH = "dataset/complete-test-management-synthetic-data"


def _git_show(branch: str, rel_path: str) -> Optional[str]:
    """Return file content from a git branch, or None if unavailable."""
    try:
        result = subprocess.run(
            ["git", "show", f"{branch}:{rel_path}"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", cwd=str(REPO_ROOT)
        )
        if result.returncode == 0:
            return result.stdout
    except Exception:
        pass
    return None


def _load_csv_from_text(text: str) -> List[Dict]:
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def _load_csv_file(path: Path) -> List[Dict]:
    with open(path, encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def _get_table(table_name: str) -> List[Dict]:
    """Load a CSV table — from disk if available, else from git branch."""
    disk_path = STRUCTURED / table_name
    if disk_path.exists():
        return _load_csv_file(disk_path)
    rel = f"datasets/synthetic_test_management/structured/{table_name}"
    text = _git_show(SOURCE_BRANCH, rel)
    if text:
        return _load_csv_from_text(text)
    raise FileNotFoundError(
        f"Cannot find {table_name} on disk or branch {SOURCE_BRANCH!r}. "
        f"Ensure the base dataset branch is available."
    )


class DataLoader:
    """Loads all structured tables and builds fast look-up indexes."""

    def __init__(self):
        self.applications:       List[Dict] = []
        self.solutions:          List[Dict] = []
        self.environments:       List[Dict] = []
        self.releases:           List[Dict] = []
        self.engineers:          List[Dict] = []
        self.requirements:       List[Dict] = []
        self.test_suites:        List[Dict] = []
        self.test_cases:         List[Dict] = []
        self.test_steps:         List[Dict] = []
        self.test_runs:          List[Dict] = []
        self.test_executions:    List[Dict] = []
        self.failures:           List[Dict] = []
        self.defects:            List[Dict] = []
        self.historical_failures:List[Dict] = []

        # indexes
        self.app_by_id:     Dict[str, Dict] = {}
        self.sol_by_id:     Dict[str, Dict] = {}
        self.env_by_id:     Dict[str, Dict] = {}
        self.rel_by_id:     Dict[str, Dict] = {}
        self.eng_by_id:     Dict[str, Dict] = {}
        self.req_by_id:     Dict[str, Dict] = {}
        self.suite_by_id:   Dict[str, Dict] = {}
        self.tc_by_id:      Dict[str, Dict] = {}
        self.run_by_id:     Dict[str, Dict] = {}
        self.exec_by_id:    Dict[str, Dict] = {}
        self.fail_by_id:    Dict[str, Dict] = {}
        self.defect_by_id:  Dict[str, Dict] = {}

        # relational indexes
        self.tc_by_req:     Dict[str, List[str]] = {}   # req_id -> [tc_id]
        self.exec_by_tc:    Dict[str, List[Dict]] = {}  # tc_id  -> [exec]
        self.fail_by_tc:    Dict[str, List[Dict]] = {}  # tc_id  -> [fail]
        self.defect_by_fail:Dict[str, Dict] = {}        # fail_id -> defect
        self.steps_by_tc:   Dict[str, List[Dict]] = {}  # tc_id  -> [step]
        self.hist_by_ftype: Dict[str, List[Dict]] = {}  # ftype  -> [hist]
        self.req_by_app:    Dict[str, List[str]] = {}   # app_id -> [req_id]
        self.tc_by_app:     Dict[str, List[str]] = {}   # app_id -> [tc_id]

        self._loaded = False

    def load(self):
        if self._loaded:
            return
        print("  Loading structured tables...")
        self.applications        = _get_table("applications.csv")
        self.solutions           = _get_table("solutions.csv")
        self.environments        = _get_table("environments.csv")
        self.releases            = _get_table("releases.csv")
        self.engineers           = _get_table("engineers.csv")
        self.requirements        = _get_table("requirements.csv")
        self.test_suites         = _get_table("test_suites.csv")
        self.test_cases          = _get_table("test_cases.csv")
        self.test_steps          = _get_table("test_steps.csv")
        self.test_runs           = _get_table("test_runs.csv")
        self.test_executions     = _get_table("test_executions.csv")
        self.failures            = _get_table("failures.csv")
        self.defects             = _get_table("defects.csv")
        self.historical_failures = _get_table("historical_failures.csv")

        self._build_indexes()
        self._loaded = True
        print(f"  Loaded: {len(self.applications)} apps, "
              f"{len(self.requirements)} reqs, "
              f"{len(self.test_cases)} TCs, "
              f"{len(self.test_executions)} execs, "
              f"{len(self.failures)} failures, "
              f"{len(self.defects)} defects")

    def _build_indexes(self):
        for r in self.applications:        self.app_by_id[r["application_id"]]    = r
        for r in self.solutions:           self.sol_by_id[r["solution_id"]]        = r
        for r in self.environments:        self.env_by_id[r["environment_id"]]     = r
        for r in self.releases:            self.rel_by_id[r["release_id"]]         = r
        for r in self.engineers:           self.eng_by_id[r["engineer_id"]]        = r
        for r in self.requirements:        self.req_by_id[r["requirement_id"]]     = r
        for r in self.test_suites:         self.suite_by_id[r["suite_id"]]         = r
        for r in self.test_cases:          self.tc_by_id[r["test_case_id"]]        = r
        for r in self.test_runs:           self.run_by_id[r["run_id"]]             = r
        for r in self.test_executions:     self.exec_by_id[r["execution_id"]]      = r
        for r in self.failures:            self.fail_by_id[r["failure_id"]]        = r
        for r in self.defects:             self.defect_by_id[r["defect_id"]]       = r

        for tc in self.test_cases:
            self.tc_by_req.setdefault(tc["requirement_id"], []).append(tc["test_case_id"])
            self.tc_by_app.setdefault(tc["application_id"], []).append(tc["test_case_id"])

        for req in self.requirements:
            self.req_by_app.setdefault(req["application_id"], []).append(req["requirement_id"])

        for ex in self.test_executions:
            self.exec_by_tc.setdefault(ex["test_case_id"], []).append(ex)

        for f in self.failures:
            self.fail_by_tc.setdefault(f["test_case_id"], []).append(f)

        for d in self.defects:
            if d.get("related_failure"):
                self.defect_by_fail[d["related_failure"]] = d

        for s in self.test_steps:
            self.steps_by_tc.setdefault(s["test_case_id"], []).append(s)
        # sort steps by step number
        for tc_id in self.steps_by_tc:
            self.steps_by_tc[tc_id].sort(key=lambda x: int(x.get("step_number", 0)))

        for h in self.historical_failures:
            self.hist_by_ftype.setdefault(h.get("failure_type", ""), []).append(h)
