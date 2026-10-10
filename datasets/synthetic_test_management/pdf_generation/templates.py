"""
templates.py
============
ReportLab PDF templates for all six document types.

Each render_* function accepts a context dict (from relationship_resolver.py)
and a file path, and writes a complete multi-section PDF.
"""

from pathlib import Path
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

# ── Colour palette ────────────────────────────────────────────────────────────
BLUE_DARK   = colors.HexColor("#1A3A5C")
BLUE_MID    = colors.HexColor("#2E6DA4")
BLUE_LIGHT  = colors.HexColor("#D6E8F7")
GREY_LIGHT  = colors.HexColor("#F4F4F4")
GREY_MID    = colors.HexColor("#CCCCCC")
RED_SOFT    = colors.HexColor("#C0392B")
GREEN_SOFT  = colors.HexColor("#27AE60")
ORANGE_SOFT = colors.HexColor("#E67E22")
WHITE       = colors.white
BLACK       = colors.black

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm

# ── Style sheet ───────────────────────────────────────────────────────────────
_base = getSampleStyleSheet()

def _style(name, parent="Normal", **kw):
    s = ParagraphStyle(name, parent=_base[parent], **kw)
    return s

STYLES = {
    "doc_title":   _style("doc_title",   "Title",
                          fontSize=20, textColor=BLUE_DARK, spaceAfter=6,
                          leading=24, alignment=TA_CENTER),
    "doc_subtitle":_style("doc_subtitle","Normal",
                          fontSize=11, textColor=BLUE_MID, spaceAfter=2,
                          alignment=TA_CENTER),
    "section":     _style("section","Normal",
                          fontSize=12, textColor=WHITE,
                          backColor=BLUE_DARK, spaceBefore=10, spaceAfter=4,
                          leftIndent=4, leading=16, fontName="Helvetica-Bold"),
    "subsection":  _style("subsection","Normal",
                          fontSize=10, textColor=BLUE_DARK, spaceBefore=6,
                          spaceAfter=2, fontName="Helvetica-Bold"),
    "body":        _style("body","Normal",
                          fontSize=9, leading=13, spaceAfter=4),
    "body_small":  _style("body_small","Normal",
                          fontSize=8, leading=12, spaceAfter=3),
    "label":       _style("label","Normal",
                          fontSize=9, fontName="Helvetica-Bold",
                          textColor=BLUE_DARK),
    "mono":        _style("mono","Normal",
                          fontSize=7.5, fontName="Courier",
                          backColor=GREY_LIGHT, leading=11,
                          leftIndent=6, rightIndent=6, spaceAfter=4),
    "footer":      _style("footer","Normal",
                          fontSize=7, textColor=GREY_MID,
                          alignment=TA_CENTER),
    "badge_pass":  _style("badge_pass","Normal",
                          fontSize=9, textColor=GREEN_SOFT,
                          fontName="Helvetica-Bold"),
    "badge_fail":  _style("badge_fail","Normal",
                          fontSize=9, textColor=RED_SOFT,
                          fontName="Helvetica-Bold"),
    "badge_open":  _style("badge_open","Normal",
                          fontSize=9, textColor=ORANGE_SOFT,
                          fontName="Helvetica-Bold"),
}


def _status_style(status: str) -> str:
    s = (status or "").upper()
    if s in ("PASS", "CLOSED", "FIXED", "VERIFIED", "RESOLVED"):
        return "badge_pass"
    if s in ("FAIL", "OPEN", "CRITICAL", "REOPENED"):
        return "badge_fail"
    return "badge_open"


def _kv_table(pairs: List[tuple], col_widths=None) -> Table:
    """Two-column key-value table."""
    if col_widths is None:
        col_widths = [4.5 * cm, 11 * cm]
    data = []
    for k, v in pairs:
        data.append([
            Paragraph(str(k), STYLES["label"]),
            Paragraph(str(v) if v else "—", STYLES["body"]),
        ])
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), BLUE_LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, GREY_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, GREY_MID),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    return t


def _header_table(headers: List[str], rows: List[List[str]],
                   col_widths=None) -> Table:
    data = [[Paragraph(h, STYLES["label"]) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c) if c else "—", STYLES["body_small"]) for c in row])
    if col_widths is None:
        w = (PAGE_W - 2 * MARGIN) / len(headers)
        col_widths = [w] * len(headers)
    t = Table(data, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE_DARK),
        ("TEXTCOLOR",  (0, 0), (-1, 0), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GREY_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, GREY_MID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    return t


def _section(title: str) -> Paragraph:
    return Paragraph(f"  {title}", STYLES["section"])


def _body(text: str) -> Paragraph:
    return Paragraph(text, STYLES["body"])


def _mono(text: str) -> Paragraph:
    # escape XML special chars
    safe = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(safe, STYLES["mono"])


def _space(h=0.3) -> Spacer:
    return Spacer(1, h * cm)


def _hr() -> HRFlowable:
    return HRFlowable(width="100%", thickness=0.5, color=BLUE_MID, spaceAfter=4)


def _make_doc(out_path: Path) -> BaseDocTemplate:
    def _header_footer(canvas, doc):
        canvas.saveState()
        # Header bar
        canvas.setFillColor(BLUE_DARK)
        canvas.rect(MARGIN, PAGE_H - 1.2 * cm, PAGE_W - 2 * MARGIN,
                    0.6 * cm, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(MARGIN + 5, PAGE_H - 0.85 * cm,
                          "Synthetic QA Dataset — For Research Purposes Only")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(PAGE_W - MARGIN - 5, PAGE_H - 0.85 * cm,
                               f"Page {doc.page}")
        # Footer
        canvas.setFillColor(GREY_MID)
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(PAGE_W / 2, 0.8 * cm,
                                 "SYNTHETIC DATA — No real Samsung confidential information")
        canvas.restoreState()

    frame = Frame(MARGIN, 1.5 * cm, PAGE_W - 2 * MARGIN,
                  PAGE_H - 3.5 * cm, id="main")
    template = PageTemplate(id="main", frames=[frame],
                             onPage=_header_footer)
    doc = BaseDocTemplate(str(out_path), pagesize=A4,
                          pageTemplates=[template],
                          rightMargin=MARGIN, leftMargin=MARGIN,
                          topMargin=2.2 * cm, bottomMargin=2 * cm)
    return doc


def _truncate(s: str, n: int = 80) -> str:
    # Remove common encoding artifacts from CSV (e.g. â€" = em-dash, Î" = Gamma etc.)
    s = str(s or "").strip()
    # replace common Windows-1252 mis-decoded sequences
    for bad, good in [
        ("\u0393\u00c7\u00f6", "—"),  # â€" misread
        ("\u0393\u00c7\u00ab", "'"),
        ("\u0393\u00c7\u00bb", "'"),
        ("\ufffd", "?"),
    ]:
        s = s.replace(bad, good)
    return s[:n] + "..." if len(s) > n else s


# ── REQUIREMENT PDF ────────────────────────────────────────────────────────────
def render_requirement(ctx: Dict, out_path: Path):
    req  = ctx["requirement"]
    app  = ctx["application"]
    sol  = ctx["solution"]
    tcs  = ctx["related_test_cases"]
    defs = ctx["related_defects"]

    doc   = _make_doc(out_path)
    story = []

    story += [
        Paragraph(f"Requirement Specification", STYLES["doc_title"]),
        Paragraph(f"{req.get('requirement_id','N/A')} — {_truncate(req.get('title',''), 70)}",
                  STYLES["doc_subtitle"]),
        _hr(), _space(0.4),
    ]

    story += [_section("1. Identification")]
    story += [_kv_table([
        ("Requirement ID",  req.get("requirement_id","—")),
        ("Title",           _truncate(req.get("title",""),80)),
        ("Type",            req.get("requirement_type","—")),
        ("Priority",        req.get("priority","—")),
        ("Severity",        req.get("severity","—")),
        ("Status",          req.get("status","—")),
        ("Version",         req.get("version","—")),
        ("Created",         req.get("created_date","—")),
        ("Updated",         req.get("updated_date","—")),
        ("Source Document", req.get("source_document","—")),
    ]), _space()]

    story += [_section("2. Application & Solution")]
    story += [_kv_table([
        ("Application ID",  app.get("application_id","—")),
        ("Application",     app.get("name","—")),
        ("Domain",          app.get("domain","—")),
        ("App Version",     app.get("version","—")),
        ("Solution ID",     sol.get("solution_id","—")),
        ("Solution",        sol.get("name","—")),
        ("Component",       req.get("component","—")),
        ("Feature",         req.get("feature","—")),
    ]), _space()]

    story += [_section("3. Requirement Description")]
    story += [_body(req.get("description","No description provided.")), _space(0.2)]

    story += [_section("4. Acceptance Criteria")]
    ac_items = [
        f"The system shall satisfy the requirement within the defined performance SLA (p95 &lt; 500ms).",
        f"All failure scenarios must return a human-readable error message to the user.",
        f"All events must be logged to the audit trail with a valid timestamp and user context.",
        f"The feature must operate correctly in all supported environments (Mobile, Wearable, Cloud).",
        f"Security constraints: all data in transit must be encrypted using TLS 1.3 or higher.",
    ]
    for i, ac in enumerate(ac_items, 1):
        story.append(_body(f"AC-{i}: {ac}"))
    story.append(_space())

    story += [_section("5. Dependencies")]
    story += [_body(f"This requirement depends on the {sol.get('name','N/A')} "
                    f"({sol.get('solution_id','N/A')}) being operational and at version "
                    f"{sol.get('version','N/A')} or above."), _space()]

    if tcs:
        story += [_section("6. Related Test Cases")]
        tc_rows = [[t.get("test_case_id",""), _truncate(t.get("title",""),60),
                    t.get("test_type",""), t.get("priority",""), t.get("status","")]
                   for t in tcs]
        story += [_header_table(
            ["TC ID", "Title", "Type", "Priority", "Status"],
            tc_rows,
            [2.8*cm, 8.5*cm, 2.5*cm, 2*cm, 1.8*cm]
        ), _space()]

    if defs:
        story += [_section("7. Related Defects")]
        def_rows = [[d.get("defect_id",""), _truncate(d.get("title",""),55),
                     d.get("severity",""), d.get("priority",""), d.get("status","")]
                    for d in defs]
        story += [_header_table(
            ["Defect ID", "Title", "Severity", "Priority", "Status"],
            def_rows,
            [2.5*cm, 8.5*cm, 2.3*cm, 2*cm, 2.3*cm]
        ), _space()]

    story += [_section("8. Synthetic Data Notice")]
    story += [_body(
        "This document is entirely synthetic and was generated for AI/RAG research "
        "purposes only. No real Samsung internal data, credentials, or confidential "
        "information is included."
    )]

    doc.build(story)


# ── TEST PLAN PDF ──────────────────────────────────────────────────────────────
def render_test_plan(ctx: Dict, out_path: Path):
    suite = ctx["suite"]
    app   = ctx["application"]
    rel   = ctx["release"]
    tcs   = ctx["test_cases"]
    reqs  = ctx["requirements"]
    engs  = ctx["engineers"]

    doc   = _make_doc(out_path)
    story = []

    story += [
        Paragraph("Test Plan", STYLES["doc_title"]),
        Paragraph(f"{suite.get('suite_id','N/A')} — {_truncate(suite.get('name',''),70)}",
                  STYLES["doc_subtitle"]),
        _hr(), _space(0.4),
    ]

    story += [_section("1. Test Plan Overview")]
    story += [_kv_table([
        ("Suite ID",        suite.get("suite_id","—")),
        ("Suite Name",      suite.get("name","—")),
        ("Suite Type",      suite.get("suite_type","—")),
        ("Priority",        suite.get("priority","—")),
        ("Status",          suite.get("status","—")),
        ("Application",     f"{app.get('application_id','—')} — {app.get('name','—')}"),
        ("Release",         f"{rel.get('release_id','—')} — {rel.get('name','—')}"),
        ("Release Version", rel.get("version","—")),
        ("Release Date",    rel.get("release_date","—")),
        ("Created Date",    suite.get("created_date","—")),
    ]), _space()]

    story += [_section("2. Scope & Objectives")]
    story += [_body(
        f"This test plan covers {suite.get('suite_type','regression').lower()} "
        f"testing for the {app.get('name','N/A')} application. "
        f"{suite.get('description','')}"
    ), _space()]

    story += [_section("3. Test Strategy")]
    story += [_body(
        f"Testing will follow a risk-based approach with priority on "
        f"{suite.get('priority','High')} severity scenarios. "
        f"Automated test cases will be executed first to detect regressions early, "
        f"followed by manual exploratory testing for edge cases. "
        f"Performance and security test cases will run in parallel in dedicated environments."
    ), _space()]

    story += [_section("4. Requirements Under Test")]
    if reqs:
        req_rows = [[r.get("requirement_id",""), _truncate(r.get("title",""),55),
                     r.get("requirement_type",""), r.get("priority",""), r.get("status","")]
                    for r in reqs]
        story += [_header_table(
            ["REQ ID", "Title", "Type", "Priority", "Status"],
            req_rows,
            [2.5*cm, 8.5*cm, 2.8*cm, 2*cm, 2*cm]
        ), _space()]

    story += [_section("5. Test Cases Summary")]
    if tcs:
        tc_rows = [[t.get("test_case_id",""), _truncate(t.get("title",""),50),
                    t.get("test_type",""), t.get("automation_status",""), t.get("priority","")]
                   for t in tcs]
        story += [_header_table(
            ["TC ID", "Title", "Type", "Automation", "Priority"],
            tc_rows,
            [2.8*cm, 8.2*cm, 2.5*cm, 2.8*cm, 1.7*cm]
        ), _space()]

    story += [_section("6. Test Environments")]
    story += [_kv_table([
        ("Primary",   "Mobile Lab — Android 14 — WiFi-6 (ENV-001)"),
        ("Secondary", "Staging — Android 13 — LTE (ENV-007)"),
        ("Extended",  "Low Network Env — Android 14 — Low-BW Sim (ENV-009)"),
        ("Performance","High Load Env — Ubuntu 22.04 — Ethernet (ENV-010)"),
    ]), _space()]

    story += [_section("7. Entry & Exit Criteria")]
    story += [_kv_table([
        ("Entry — Build", "Smoke suite must pass 100% before full regression begins."),
        ("Entry — Env",   "All required environments must be Available status."),
        ("Entry — Defects","No Critical-severity open defects from the previous cycle."),
        ("Exit — Pass Rate","Overall pass rate >= 95%."),
        ("Exit — Critical","Zero open Critical-severity defects."),
        ("Exit — Coverage","All Priority=High test cases executed."),
    ]), _space()]

    story += [_section("8. Risks")]
    risk_rows = [
        ["Network instability in low-BW env", "Medium", "Reserve stable WiFi fallback"],
        ["Device unavailability",              "Low",    "Reserve backup devices 48h ahead"],
        ["Build quality regression",           "Medium", "Execute smoke before full regression"],
        ["Flaky automation scripts",           "Low",    "Quarantine flaky TCs, re-run 3x"],
    ]
    story += [_header_table(
        ["Risk", "Probability", "Mitigation"],
        risk_rows, [7*cm, 3*cm, 7.8*cm]
    ), _space()]

    if engs:
        story += [_section("9. Responsible Engineers")]
        eng_rows = [[e.get("engineer_id",""), e.get("name",""),
                     e.get("role",""), e.get("team","")]
                    for e in engs]
        story += [_header_table(
            ["Eng ID", "Name", "Role", "Team"],
            eng_rows, [2.5*cm, 4.5*cm, 5*cm, 5.8*cm]
        ), _space()]

    story += [_section("10. Synthetic Data Notice")]
    story += [_body("This document is entirely synthetic and intended for AI/RAG research only.")]

    doc.build(story)


# ── TEST CASE PDF ──────────────────────────────────────────────────────────────
def render_test_case(ctx: Dict, out_path: Path):
    tc   = ctx["test_case"]
    req  = ctx["requirement"]
    app  = ctx["application"]
    env  = ctx["environment"]
    eng  = ctx["engineer"]
    steps= ctx["steps"]
    execs= ctx["recent_executions"]
    fails= ctx["failures"]
    defs = ctx["defects"]

    doc   = _make_doc(out_path)
    story = []

    status_sty = _status_style(tc.get("status",""))

    story += [
        Paragraph("Test Case Specification", STYLES["doc_title"]),
        Paragraph(f"{tc.get('test_case_id','N/A')} — {_truncate(tc.get('title',''),70)}",
                  STYLES["doc_subtitle"]),
        _hr(), _space(0.4),
    ]

    story += [_section("1. Test Case Identity")]
    story += [_kv_table([
        ("Test Case ID",        tc.get("test_case_id","—")),
        ("Title",               _truncate(tc.get("title",""),80)),
        ("Type",                tc.get("test_type","—")),
        ("Priority",            tc.get("priority","—")),
        ("Severity",            tc.get("severity","—")),
        ("Automation Status",   tc.get("automation_status","—")),
        ("Estimated Duration",  f"{tc.get('estimated_duration','—')} seconds"),
        ("Status",              tc.get("status","—")),
        ("Created By",          f"{eng.get('engineer_id','—')} — {eng.get('name','—')}"),
    ]), _space()]

    story += [_section("2. Application & Requirement")]
    story += [_kv_table([
        ("Application ID",  app.get("application_id","—")),
        ("Application",     app.get("name","—")),
        ("Domain",          app.get("domain","—")),
        ("Suite ID",        tc.get("suite_id","—")),
        ("Requirement ID",  req.get("requirement_id","—")),
        ("Req Title",       _truncate(req.get("title",""),70)),
        ("Req Type",        req.get("requirement_type","—")),
        ("Req Priority",    req.get("priority","—")),
    ]), _space()]

    story += [_section("3. Test Environment")]
    story += [_kv_table([
        ("Environment ID",  env.get("environment_id","—")),
        ("Environment",     env.get("name","—")),
        ("Device Type",     env.get("device_type","—")),
        ("OS Version",      env.get("os_version","—")),
        ("Network Type",    env.get("network_type","—")),
        ("Location",        env.get("location","—")),
    ]), _space()]

    story += [_section("4. Objective")]
    story += [_body(tc.get("objective","No objective specified.")), _space(0.2)]

    story += [_section("5. Preconditions")]
    story += [_body(tc.get("preconditions","No preconditions specified.")), _space(0.2)]

    if steps:
        story += [_section("6. Test Steps")]
        step_rows = [[str(s.get("step_number","")),
                      _truncate(s.get("action",""),70),
                      _truncate(s.get("expected_result",""),70),
                      _truncate(s.get("input_data","N/A"),30)]
                     for s in steps]
        story += [_header_table(
            ["#", "Action", "Expected Result", "Input Data"],
            step_rows, [1*cm, 6.8*cm, 6.8*cm, 3.2*cm]
        ), _space()]

    story += [_section("7. Description & Objective Detail")]
    story += [_body(tc.get("description","No description provided.")), _space()]

    if execs:
        story += [_section("8. Recent Execution History")]
        exec_rows = [[e.get("execution_id",""),
                      e.get("execution_timestamp","")[:16],
                      e.get("status",""),
                      e.get("build_version",""),
                      e.get("environment_id",""),
                      f"{int(e.get('duration_ms',0))//1000}s"]
                     for e in execs]
        story += [_header_table(
            ["Exec ID", "Timestamp", "Status", "Build", "Env", "Duration"],
            exec_rows, [3.5*cm, 4.2*cm, 2*cm, 2.3*cm, 2*cm, 1.8*cm]
        ), _space()]

    if fails:
        story += [_section("9. Associated Failures")]
        fail_rows = [[f.get("failure_id",""), f.get("failure_type",""),
                      f.get("severity",""), _truncate(f.get("error_message",""),55)]
                     for f in fails]
        story += [_header_table(
            ["Failure ID", "Type", "Severity", "Error Message"],
            fail_rows, [2.5*cm, 3.5*cm, 2.5*cm, 9.3*cm]
        ), _space()]

    if defs:
        story += [_section("10. Associated Defects")]
        def_rows = [[d.get("defect_id",""), _truncate(d.get("title",""),55),
                     d.get("severity",""), d.get("status","")]
                    for d in defs]
        story += [_header_table(
            ["Defect ID", "Title", "Severity", "Status"],
            def_rows, [2.5*cm, 9.5*cm, 2.5*cm, 2.5*cm]
        ), _space()]

    story += [_section("11. Synthetic Data Notice")]
    story += [_body("This document is entirely synthetic and intended for AI/RAG research only.")]
    doc.build(story)


# ── EXECUTION REPORT PDF ───────────────────────────────────────────────────────
def render_execution_report(ctx: Dict, out_path: Path):
    ex   = ctx["execution"]
    tc   = ctx["test_case"]
    run  = ctx["test_run"]
    env  = ctx["environment"]
    req  = ctx["requirement"]
    rel  = ctx["release"]
    fail = ctx["failure"]
    defect = ctx["defect"]
    steps  = ctx["steps"]

    doc   = _make_doc(out_path)
    story = []

    status_sty = _status_style(ex.get("status",""))

    story += [
        Paragraph("Test Execution Report", STYLES["doc_title"]),
        Paragraph(f"{ex.get('execution_id','N/A')} — Status: {ex.get('status','N/A')}",
                  STYLES["doc_subtitle"]),
        _hr(), _space(0.4),
    ]

    story += [_section("1. Execution Summary")]
    story += [_kv_table([
        ("Execution ID",    ex.get("execution_id","—")),
        ("Status",          ex.get("status","—")),
        ("Build Version",   ex.get("build_version","—")),
        ("Timestamp",       ex.get("execution_timestamp","—")),
        ("Duration",        f"{int(ex.get('duration_ms',0))//1000} seconds ({ex.get('duration_ms',0)} ms)"),
        ("Executed By",     ex.get("executed_by","—")),
        ("Test Run",        f"{run.get('run_id','—')} — {run.get('name','—')}"),
        ("Release",         f"{rel.get('release_id','—')} — {rel.get('version','—')}"),
        ("Environment",     f"{env.get('environment_id','—')} — {env.get('name','—')}"),
    ]), _space()]

    story += [_section("2. Test Case Reference")]
    story += [_kv_table([
        ("Test Case ID",    tc.get("test_case_id","—")),
        ("Title",           _truncate(tc.get("title",""),80)),
        ("Test Type",       tc.get("test_type","—")),
        ("Priority",        tc.get("priority","—")),
        ("Automation",      tc.get("automation_status","—")),
        ("Requirement",     f"{req.get('requirement_id','—')} — {_truncate(req.get('title',''),60)}"),
    ]), _space()]

    story += [_section("3. Environment Details")]
    story += [_kv_table([
        ("Environment ID",  env.get("environment_id","—")),
        ("Name",            env.get("name","—")),
        ("Device Type",     env.get("device_type","—")),
        ("OS Version",      env.get("os_version","—")),
        ("Network Type",    env.get("network_type","—")),
        ("Location",        env.get("location","—")),
        ("Configuration",   env.get("configuration","—")),
    ]), _space()]

    if steps:
        story += [_section("4. Executed Steps")]
        step_rows = [[str(s.get("step_number","")),
                      _truncate(s.get("action",""),65),
                      _truncate(s.get("expected_result",""),65),
                      "PASS" if ex.get("status") != "FAIL" else
                      ("FAIL" if int(s.get("step_number",1)) == len(steps) else "PASS")]
                     for s in steps]
        story += [_header_table(
            ["Step", "Action", "Expected Result", "Result"],
            step_rows, [1.2*cm, 7*cm, 7*cm, 1.8*cm]
        ), _space()]

    if fail:
        story += [_section("5. Failure Details")]
        story += [_kv_table([
            ("Failure ID",      fail.get("failure_id","—")),
            ("Failure Type",    fail.get("failure_type","—")),
            ("Severity",        fail.get("severity","—")),
            ("Component",       fail.get("component","—")),
            ("Error Message",   _truncate(fail.get("error_message",""),100)),
            ("Observed",        _truncate(fail.get("observed_behavior",""),100)),
            ("Expected",        _truncate(fail.get("expected_behavior",""),100)),
            ("Resolution",      fail.get("resolution_status","—")),
        ]), _space()]
        story += [Paragraph("Error Log Excerpt:", STYLES["subsection"])]
        story += [_mono(fail.get("stack_trace","N/A")), _space(0.2)]
        if defect:
            story += [_kv_table([
                ("Linked Defect", f"{defect.get('defect_id','—')} — {_truncate(defect.get('title',''),60)}"),
                ("Defect Status", defect.get("status","—")),
            ]), _space()]

    story += [_section("6. Synthetic Data Notice")]
    story += [_body("This document is entirely synthetic and intended for AI/RAG research only.")]
    doc.build(story)


# ── FAILURE REPORT PDF ─────────────────────────────────────────────────────────
def render_failure_report(ctx: Dict, out_path: Path):
    fail = ctx["failure"]
    ex   = ctx["execution"]
    tc   = ctx["test_case"]
    app  = ctx["application"]
    env  = ctx["environment"]
    req  = ctx["requirement"]
    run  = ctx.get("test_run", {})
    defect = ctx["defect"]
    hist   = ctx["historical_similar"]
    steps  = ctx["steps"]

    doc   = _make_doc(out_path)
    story = []

    story += [
        Paragraph("Failure Analysis Report", STYLES["doc_title"]),
        Paragraph(f"{fail.get('failure_id','N/A')} — {fail.get('failure_type','N/A')}",
                  STYLES["doc_subtitle"]),
        _hr(), _space(0.4),
    ]

    story += [_section("1. Failure Summary")]
    story += [_kv_table([
        ("Failure ID",      fail.get("failure_id","—")),
        ("Failure Type",    fail.get("failure_type","—")),
        ("Severity",        fail.get("severity","—")),
        ("Component",       fail.get("component","—")),
        ("Application",     f"{app.get('application_id','—')} — {app.get('name','—')}"),
        ("Build Version",   fail.get("build_version","—")),
        ("Timestamp",       fail.get("timestamp","—")),
        ("Environment",     f"{env.get('environment_id','—')} — {env.get('name','—')}"),
        ("OS Version",      env.get("os_version","—")),
        ("Network",         env.get("network_type","—")),
        ("Resolution",      fail.get("resolution_status","—")),
    ]), _space()]

    story += [_section("2. Test Case Reference")]
    story += [_kv_table([
        ("Test Case ID",    tc.get("test_case_id","—")),
        ("Title",           _truncate(tc.get("title",""),80)),
        ("Execution ID",    ex.get("execution_id","—") if ex else "—"),
        ("Test Run",        f"{run.get('run_id','—')} — {run.get('name','—')}"),
        ("Requirement",     f"{req.get('requirement_id','—')} — {_truncate(req.get('title',''),60)}"),
    ]), _space()]

    story += [_section("3. Expected vs Observed Behaviour")]
    story += [_kv_table([
        ("Expected Behaviour", _truncate(fail.get("expected_behavior",""),100)),
        ("Observed Behaviour", _truncate(fail.get("observed_behavior",""),100)),
    ], col_widths=[4*cm, 13.8*cm]), _space()]

    story += [_section("4. Error Details")]
    story += [_body("Error Message:")]
    story += [_mono(fail.get("error_message","N/A")), _space(0.2)]
    story += [_body("Stack Trace / Log Excerpt:")]
    story += [_mono(fail.get("stack_trace","N/A")), _space(0.2)]
    story += [_kv_table([
        ("Log Reference", fail.get("log_reference","—")),
    ]), _space()]

    if steps:
        story += [_section("5. Executed Steps at Time of Failure")]
        step_rows = [[str(s.get("step_number","")),
                      _truncate(s.get("action",""),65),
                      _truncate(s.get("expected_result",""),65)]
                     for s in steps]
        story += [_header_table(
            ["Step", "Action", "Expected Result"],
            step_rows, [1.2*cm, 8.3*cm, 8.3*cm]
        ), _space()]

    story += [_section("6. Root Cause Analysis")]
    story += [_body(fail.get("root_cause","Root cause analysis pending.")), _space()]

    if defect:
        story += [_section("7. Linked Defect")]
        story += [_kv_table([
            ("Defect ID",    defect.get("defect_id","—")),
            ("Title",        _truncate(defect.get("title",""),80)),
            ("Severity",     defect.get("severity","—")),
            ("Priority",     defect.get("priority","—")),
            ("Status",       defect.get("status","—")),
            ("Root Cause",   _truncate(defect.get("root_cause",""),80)),
            ("Resolution",   _truncate(defect.get("resolution","Pending"),80)),
            ("Assigned To",  f"{defect.get('assigned_engineer','—')}"),
        ]), _space()]

    if hist:
        story += [_section("8. Historical Similar Failures")]
        hist_rows = [[h.get("hist_failure_id",""), h.get("original_failure",""),
                      h.get("failure_type",""), h.get("build_version",""),
                      h.get("occurrence_date",""), str(h.get("recurrence_count","1")),
                      h.get("resolution_status","")]
                     for h in hist]
        story += [_header_table(
            ["Hist ID", "Orig Failure", "Type", "Build", "Date", "Count", "Status"],
            hist_rows, [2.5*cm, 2.8*cm, 3.5*cm, 2*cm, 2.5*cm, 1.5*cm, 2.5*cm]
        ), _space()]

    story += [_section("9. Synthetic Data Notice")]
    story += [_body("This document is entirely synthetic and intended for AI/RAG research only.")]
    doc.build(story)


# ── DEFECT REPORT PDF ──────────────────────────────────────────────────────────
def render_defect_report(ctx: Dict, out_path: Path):
    defect = ctx["defect"]
    app    = ctx["application"]
    req    = ctx["requirement"]
    tc     = ctx["test_case"]
    fail   = ctx["failure"]
    eng    = ctx["engineer"]
    ex     = ctx["execution"]
    env    = ctx["environment"]
    run    = ctx.get("test_run", {})
    rel    = ctx.get("release", {})
    hist   = ctx["historical_similar"]
    steps  = ctx["steps"]

    doc   = _make_doc(out_path)
    story = []

    story += [
        Paragraph("Defect Report", STYLES["doc_title"]),
        Paragraph(f"{defect.get('defect_id','N/A')} — {_truncate(defect.get('title',''),70)}",
                  STYLES["doc_subtitle"]),
        _hr(), _space(0.4),
    ]

    story += [_section("1. Defect Summary")]
    story += [_kv_table([
        ("Defect ID",       defect.get("defect_id","—")),
        ("Title",           _truncate(defect.get("title",""),80)),
        ("Severity",        defect.get("severity","—")),
        ("Priority",        defect.get("priority","—")),
        ("Status",          defect.get("status","—")),
        ("Component",       defect.get("component","—")),
        ("Application",     f"{app.get('application_id','—')} — {app.get('name','—')}"),
        ("Reported Date",   defect.get("reported_date","—")),
        ("Resolved Date",   defect.get("resolved_date","Pending") or "Pending"),
        ("Assigned To",     f"{eng.get('engineer_id','—')} — {eng.get('name','—')}"),
    ]), _space()]

    story += [_section("2. Traceability")]
    story += [_kv_table([
        ("Release",          f"{rel.get('release_id','—')} — {rel.get('version','—')}"),
        ("Test Run",         f"{run.get('run_id','—')} — {run.get('name','—')}"),
        ("Requirement",      f"{req.get('requirement_id','—')} — {_truncate(req.get('title',''),60)}"),
        ("Req Priority",     req.get("priority","—")),
        ("Test Case ID",     tc.get("test_case_id","—")),
        ("Test Case Title",  _truncate(tc.get("title",""),70)),
        ("Execution ID",     ex.get("execution_id","—") if ex else "—"),
        ("Failure ID",       fail.get("failure_id","—")),
        ("Failure Type",     fail.get("failure_type","—")),
        ("Environment",      f"{env.get('environment_id','—')} — {env.get('name','—')}"),
        ("Build Version",    fail.get("build_version","—")),
    ]), _space()]

    story += [_section("3. Problem Description")]
    story += [_body(defect.get("description","No description provided.")), _space()]

    story += [_section("4. Reproduction Steps")]
    if steps:
        for i, s in enumerate(steps, 1):
            story.append(_body(f"{i}. {s.get('action','N/A')}"))
    else:
        story.append(_body(
            f"1. Deploy build {fail.get('build_version','N/A')} to {env.get('name','test environment')}.\n"
            f"2. Execute test case {tc.get('test_case_id','N/A')}.\n"
            f"3. Observe the failure at the step described in the failure report {fail.get('failure_id','N/A')}."
        ))
    story.append(_space())

    story += [_section("5. Expected vs Actual Behaviour")]
    story += [_kv_table([
        ("Expected", _truncate(fail.get("expected_behavior","—"),100)),
        ("Actual",   _truncate(fail.get("observed_behavior","—"),100)),
    ], col_widths=[3.5*cm, 14.3*cm]), _space()]

    story += [_section("6. Root Cause")]
    story += [_body(defect.get("root_cause","Root cause analysis pending.")), _space()]

    story += [_section("7. Resolution")]
    res = defect.get("resolution","") or "Resolution pending investigation."
    story += [_body(res), _space()]

    if hist:
        story += [_section("8. Related Historical Failures")]
        hist_rows = [[h.get("hist_failure_id",""), h.get("failure_type",""),
                      h.get("build_version",""), h.get("occurrence_date",""),
                      str(h.get("recurrence_count","1")), h.get("resolution_status","")]
                     for h in hist]
        story += [_header_table(
            ["Hist ID", "Type", "Build", "Date", "Count", "Status"],
            hist_rows, [2.5*cm, 3.5*cm, 2.5*cm, 3*cm, 1.8*cm, 4.5*cm]
        ), _space()]

    story += [_section("9. Synthetic Data Notice")]
    story += [_body("This document is entirely synthetic and intended for AI/RAG research only.")]
    doc.build(story)
