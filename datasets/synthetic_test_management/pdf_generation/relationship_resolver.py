"""
relationship_resolver.py
========================
Resolves cross-entity relationships needed to build each PDF document.

For every document type, returns a rich context dict with all linked entities
already hydrated from the DataLoader indexes.
"""

from typing import Dict, List, Optional, Tuple
from data_loader import DataLoader


class RelationshipResolver:
    def __init__(self, dl: DataLoader):
        self.dl = dl

    # ------------------------------------------------------------------
    # REQUIREMENT context
    # ------------------------------------------------------------------
    def requirement_context(self, req_id: str) -> Dict:
        dl = self.dl
        req = dl.req_by_id.get(req_id, {})
        app = dl.app_by_id.get(req.get("application_id", ""), {})
        sol = dl.sol_by_id.get(req.get("solution_id", ""), {})

        tc_ids = dl.tc_by_req.get(req_id, [])[:5]
        tcs = [dl.tc_by_id[t] for t in tc_ids if t in dl.tc_by_id]

        # defects that affect this requirement
        defects = [d for d in dl.defects if d.get("affected_requirement") == req_id][:3]

        return {
            "requirement": req,
            "application": app,
            "solution": sol,
            "related_test_cases": tcs,
            "related_defects": defects,
        }

    # ------------------------------------------------------------------
    # TEST PLAN context  (suite-level)
    # ------------------------------------------------------------------
    def test_plan_context(self, suite_id: str) -> Dict:
        dl = self.dl
        suite = dl.suite_by_id.get(suite_id, {})
        app   = dl.app_by_id.get(suite.get("application_id", ""), {})
        rel   = dl.rel_by_id.get(suite.get("release_id", ""), {})

        # test cases in this suite
        tc_ids_for_suite = [t["test_case_id"] for t in dl.test_cases
                             if t.get("suite_id") == suite_id][:8]
        tcs = [dl.tc_by_id[t] for t in tc_ids_for_suite if t in dl.tc_by_id]

        # requirements covered
        req_ids = list({t.get("requirement_id","") for t in tcs if t.get("requirement_id")})[:5]
        reqs = [dl.req_by_id[r] for r in req_ids if r in dl.req_by_id]

        # engineers (from created_by on TCs)
        eng_ids = list({t.get("created_by","") for t in tcs if t.get("created_by")})[:3]
        engineers = [dl.eng_by_id[e] for e in eng_ids if e in dl.eng_by_id]

        return {
            "suite": suite,
            "application": app,
            "release": rel,
            "test_cases": tcs,
            "requirements": reqs,
            "engineers": engineers,
        }

    # ------------------------------------------------------------------
    # TEST CASE context
    # ------------------------------------------------------------------
    def test_case_context(self, tc_id: str) -> Dict:
        dl = self.dl
        tc  = dl.tc_by_id.get(tc_id, {})
        req = dl.req_by_id.get(tc.get("requirement_id", ""), {})
        app = dl.app_by_id.get(tc.get("application_id", ""), {})
        env = dl.env_by_id.get(tc.get("environment_id", ""), {})
        eng = dl.eng_by_id.get(tc.get("created_by", ""), {})
        steps = dl.steps_by_tc.get(tc_id, [])[:6]

        # execution history (last 3)
        execs = sorted(dl.exec_by_tc.get(tc_id, []),
                        key=lambda x: x.get("execution_timestamp", ""), reverse=True)[:3]

        # any failures
        fails = dl.fail_by_tc.get(tc_id, [])[:2]
        defects = [dl.defect_by_fail[f["failure_id"]]
                   for f in fails if f["failure_id"] in dl.defect_by_fail]

        return {
            "test_case": tc,
            "requirement": req,
            "application": app,
            "environment": env,
            "engineer": eng,
            "steps": steps,
            "recent_executions": execs,
            "failures": fails,
            "defects": defects,
        }

    # ------------------------------------------------------------------
    # EXECUTION REPORT context
    # ------------------------------------------------------------------
    def execution_context(self, exec_id: str) -> Dict:
        dl = self.dl
        ex  = dl.exec_by_id.get(exec_id, {})
        tc  = dl.tc_by_id.get(ex.get("test_case_id", ""), {})
        run = dl.run_by_id.get(ex.get("test_run_id", ""), {})
        env = dl.env_by_id.get(ex.get("environment_id", ""), {})
        req = dl.req_by_id.get(tc.get("requirement_id", ""), {})
        rel = dl.rel_by_id.get(run.get("release_id", ""), {})

        fail = dl.fail_by_id.get(ex.get("failure_id", ""), {}) if ex.get("failure_id") else {}
        defect = dl.defect_by_fail.get(ex.get("failure_id", ""), {}) if ex.get("failure_id") else {}

        steps = dl.steps_by_tc.get(tc.get("test_case_id", ""), [])[:6]

        return {
            "execution": ex,
            "test_case": tc,
            "test_run": run,
            "environment": env,
            "requirement": req,
            "release": rel,
            "failure": fail,
            "defect": defect,
            "steps": steps,
        }

    # ------------------------------------------------------------------
    # FAILURE REPORT context
    # ------------------------------------------------------------------
    def failure_context(self, fail_id: str) -> Dict:
        dl = self.dl
        fail = dl.fail_by_id.get(fail_id, {})
        ex   = dl.exec_by_id.get(fail.get("execution_id", ""), {}) if fail.get("execution_id") else {}
        tc   = dl.tc_by_id.get(fail.get("test_case_id", ""), {})
        app  = dl.app_by_id.get(fail.get("application_id", ""), {})
        env  = dl.env_by_id.get(fail.get("environment", ""), {})
        req  = dl.req_by_id.get(tc.get("requirement_id", ""), {})
        run  = dl.run_by_id.get(ex.get("test_run_id", ""), {}) if ex else {}
        defect = dl.defect_by_fail.get(fail_id, {})

        # historical similar failures (same failure_type, same component)
        hist = [h for h in dl.historical_failures
                if h.get("failure_type") == fail.get("failure_type")
                and h.get("component") == fail.get("component")][:3]

        steps = dl.steps_by_tc.get(tc.get("test_case_id", ""), [])[:6]

        return {
            "failure": fail,
            "execution": ex,
            "test_case": tc,
            "application": app,
            "environment": env,
            "requirement": req,
            "test_run": run,
            "defect": defect,
            "historical_similar": hist,
            "steps": steps,
        }

    # ------------------------------------------------------------------
    # DEFECT REPORT context
    # ------------------------------------------------------------------
    def defect_context(self, defect_id: str) -> Dict:
        dl = self.dl
        defect = dl.defect_by_id.get(defect_id, {})
        app    = dl.app_by_id.get(defect.get("application_id", ""), {})
        req    = dl.req_by_id.get(defect.get("affected_requirement", ""), {})
        tc     = dl.tc_by_id.get(defect.get("related_test_case", ""), {})
        fail   = dl.fail_by_id.get(defect.get("related_failure", ""), {})
        eng    = dl.eng_by_id.get(defect.get("assigned_engineer", ""), {})
        ex     = dl.exec_by_id.get(fail.get("execution_id", ""), {}) if fail.get("execution_id") else {}
        env    = dl.env_by_id.get(fail.get("environment", ""), {}) if fail else {}
        run    = dl.run_by_id.get(ex.get("test_run_id", ""), {}) if ex else {}
        rel    = dl.rel_by_id.get(run.get("release_id", ""), {}) if run else {}

        # historical failures with same root cause
        hist = [h for h in dl.historical_failures
                if h.get("failure_type") == fail.get("failure_type", "")][:3]

        steps = dl.steps_by_tc.get(tc.get("test_case_id", ""), [])[:5]

        return {
            "defect": defect,
            "application": app,
            "requirement": req,
            "test_case": tc,
            "failure": fail,
            "engineer": eng,
            "execution": ex,
            "environment": env,
            "test_run": run,
            "release": rel,
            "historical_similar": hist,
            "steps": steps,
        }
