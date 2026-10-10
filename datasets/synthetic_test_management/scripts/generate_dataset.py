"""
generate_dataset.py
====================
Deterministic synthetic dataset generator for the AI-Powered Test Management
System — Hybrid RAG research project.

Run:
    python datasets/synthetic_test_management/scripts/generate_dataset.py

All output lands in datasets/synthetic_test_management/structured/ and
datasets/synthetic_test_management/graph/.

Configuration constants near the top of the file control dataset scale.
A single SEED value makes every run reproducible.
"""

import csv
import json
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# 0. PATHS
# ──────────────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_ROOT = SCRIPT_DIR.parent
STRUCTURED = DATASET_ROOT / "structured"
GRAPH = DATASET_ROOT / "graph"

# ──────────────────────────────────────────────────────────────────────────────
# 1. CONFIGURATION  (tune to scale the dataset)
# ──────────────────────────────────────────────────────────────────────────────
SEED = 42

NUM_APPLICATIONS       = 12
NUM_SOLUTIONS          = 25
NUM_ENVIRONMENTS       = 10
NUM_RELEASES           = 8
NUM_REQUIREMENTS       = 520
NUM_TEST_SUITES        = 110
NUM_TEST_CASES         = 2100
NUM_TEST_STEPS         = 8400   # ~4 per test case
NUM_TEST_RUNS          = 12
NUM_TEST_EXECUTIONS    = 5200
NUM_FAILURES           = 1100
NUM_DEFECTS            = 520
NUM_ENGINEERS          = 100
NUM_ASSIGNMENTS        = 2100
NUM_HISTORICAL_FAILURES = 2100

random.seed(SEED)

# ──────────────────────────────────────────────────────────────────────────────
# 2. DOMAIN VOCABULARY
# ──────────────────────────────────────────────────────────────────────────────
APPLICATIONS = [
    {"id": "APP-001", "name": "SmartHome",           "domain": "IoT"},
    {"id": "APP-002", "name": "MobileCommunication", "domain": "Telecom"},
    {"id": "APP-003", "name": "GalaxySearch",        "domain": "Search"},
    {"id": "APP-004", "name": "DigitalWallet",       "domain": "FinTech"},
    {"id": "APP-005", "name": "WearableHealth",      "domain": "HealthTech"},
    {"id": "APP-006", "name": "XRPlatform",          "domain": "XR"},
    {"id": "APP-007", "name": "InternetBrowser",     "domain": "Web"},
    {"id": "APP-008", "name": "VoiceAssistant",      "domain": "AI"},
    {"id": "APP-009", "name": "DeviceHub",           "domain": "IoT"},
    {"id": "APP-010", "name": "MediaPlatform",       "domain": "Media"},
    {"id": "APP-011", "name": "ConnectedDevices",    "domain": "IoT"},
    {"id": "APP-012", "name": "SecureAuthentication","domain": "Security"},
]

SOLUTION_NAMES = [
    "Pairing Service","Auth Gateway","Sync Engine","Push Notification Service",
    "Data Pipeline","Analytics Core","Search Index","Recommendation Engine",
    "Payment Processor","Health Monitor","Activity Tracker","AR Renderer",
    "VR Compositor","Browser Engine","Tab Manager","NLP Processor",
    "Wake Word Detector","Device Registry","Media Transcoder","Playlist Manager",
    "Firmware Updater","Diagnostics Agent","Configuration Manager",
    "Cloud Storage Connector","Security Vault",
]

COMPONENTS = [
    "Authentication","Network Stack","Bluetooth Module","UI Layer","Database",
    "Sync Engine","Push Service","Notification Handler","Payment Gateway",
    "Health API","Sensor Manager","Rendering Engine","Voice Pipeline",
    "Search Indexer","Media Codec","Firmware Manager","Diagnostics","Cache",
    "Configuration Service","Encryption Module",
]

REQ_TYPES = ["Functional","Performance","Security","Reliability","Compatibility",
             "Usability","Connectivity","UI Behavior","Error Handling",
             "Recovery","Battery","Network Behavior","Authentication","Data Synchronization"]

PRIORITIES  = ["Critical","High","Medium","Low"]
SEVERITIES  = ["Critical","Major","Minor","Trivial"]
TEST_TYPES  = ["Functional","Regression","Smoke","Sanity","Integration","System",
               "Performance","Security","Compatibility","Reliability","Negative",
               "Recovery","End-to-End"]
AUTO_STATUS = ["Automated","Manual","Semi-Automated"]
EXEC_STATUS = ["PASS","FAIL","BLOCKED","SKIPPED","NOT_RUN"]
DEFECT_STATUS = ["OPEN","ASSIGNED","IN_PROGRESS","FIXED","VERIFIED","CLOSED","REOPENED"]
FAILURE_TYPES = ["Timeout","Crash","Assertion Failure","Network Failure",
                 "Authentication Failure","UI Failure","Data Mismatch",
                 "Performance Degradation","Synchronization Failure",
                 "Connectivity Failure","Resource Exhaustion","Configuration Error"]
DEVICE_TYPES  = ["Mobile","Wearable","Smart TV","Hub","XR Headset","Cloud Node","Desktop"]
OS_VERSIONS   = ["Android 14","Android 13","One UI 6.0","One UI 5.1","Tizen 7.0",
                 "Wear OS 4","Windows 11","macOS Ventura","Ubuntu 22.04"]
NETWORK_TYPES = ["WiFi-6","LTE","5G","Ethernet","Bluetooth 5.3","NFC","Low-BW Sim"]

# Realistic error messages keyed by failure type
ERROR_MESSAGES = {
    "Timeout":                 "Operation timed out after {t}ms; threshold is {th}ms.",
    "Crash":                   "Process {proc} terminated unexpectedly with signal SIGSEGV (segmentation fault).",
    "Assertion Failure":       "AssertionError: expected '{exp}' but received '{got}'.",
    "Network Failure":         "SocketException: Connection reset by peer on interface {iface}.",
    "Authentication Failure":  "AuthError: JWT token validation failed — signature mismatch (alg=RS256).",
    "UI Failure":              "ElementNotFoundError: XPath '{xp}' not found after {t}ms.",
    "Data Mismatch":           "DataIntegrityError: field '{field}' expected={exp} actual={got}.",
    "Performance Degradation": "PerformanceViolation: p95 latency={lat}ms exceeds SLA of {sla}ms.",
    "Synchronization Failure": "SyncError: conflict detected on entity '{eid}'; last_modified timestamps diverge by {delta}s.",
    "Connectivity Failure":    "BluetoothException: device {dev} disconnected during pairing handshake.",
    "Resource Exhaustion":     "OOMError: heap exhausted at {used}MB/{total}MB during {op}.",
    "Configuration Error":     "ConfigError: missing required key '{key}' in environment profile '{env}'.",
}

ROOT_CAUSES = [
    "Race condition in the connection manager when two threads attempt simultaneous reconnection.",
    "Missing null-check on the device registry response before dereferencing the session token.",
    "Token expiry window mis-configured; server and client clocks diverge by more than 60 seconds.",
    "Buffer overflow in the media codec when processing H.265 streams above 4K resolution.",
    "Retry logic does not apply exponential back-off; storm of reconnection attempts saturates the gateway.",
    "Database migration v2.4 incorrectly updates the index on user_sessions, causing full table scans.",
    "UI thread blocked by synchronous network call; ANR triggered after 5 seconds.",
    "Encryption key rotation not propagated to all microservice replicas before TTL expiry.",
    "Firmware update binary not validated against checksum before flashing; partial write leaves device in boot loop.",
    "Health sensor sampling rate exceeds Bluetooth LE characteristic notification limit of 250ms intervals.",
    "Cache eviction policy evicts frequently-used configuration entries under memory pressure.",
    "OAuth2 redirect URI whitelist not updated after domain migration; authorization code flow fails.",
]

RESOLUTION_NOTES = [
    "Fixed by adding a mutex lock around the connection manager reconnect path.",
    "Added null-check guard and fallback default value; unit test added for nil response.",
    "Synchronized NTP server configuration across all microservices; clock skew reduced to <1s.",
    "Applied upstream codec patch; added resolution cap guard in pre-processing pipeline.",
    "Implemented exponential back-off with jitter in the retry middleware.",
    "Rolled back DB migration; re-wrote migration script with correct index definition.",
    "Moved network call to background thread; replaced with async/await pattern.",
    "Added key rotation broadcast to all replica nodes; integration test verifies propagation.",
    "Added CRC32 checksum validation step before OTA flash; partial-write detection added.",
    "Reduced sampling rate to 500ms; added configurable throttle in the sensor manager.",
    "Increased reserved memory for config cache; added LRU priority for config entries.",
    "Updated redirect URI whitelist; added automated check in CI pipeline.",
]

# ──────────────────────────────────────────────────────────────────────────────
# 3. HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def rdate(start="2023-01-01", end="2024-12-31"):
    """Random date string between start and end."""
    s = datetime.strptime(start, "%Y-%m-%d")
    e = datetime.strptime(end,   "%Y-%m-%d")
    return (s + timedelta(days=random.randint(0, (e - s).days))).strftime("%Y-%m-%d")

def rdatetime(start="2023-01-01", end="2024-12-31"):
    d = rdate(start, end)
    h, m, s = random.randint(0,23), random.randint(0,59), random.randint(0,59)
    return f"{d} {h:02d}:{m:02d}:{s:02d}"

def write_csv(path: Path, fieldnames: list, rows: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  ✓ {path.name:40s} {len(rows):>6,} rows")

def error_msg(ftype):
    tmpl = ERROR_MESSAGES.get(ftype, "Unexpected error during test execution.")
    return (tmpl
            .replace("{t}",     str(random.randint(5000,30000)))
            .replace("{th}",    str(random.randint(3000,10000)))
            .replace("{proc}",  random.choice(["com.samsung.health","com.samsung.wallet","com.samsung.smarthome"]))
            .replace("{exp}",   random.choice(["SUCCESS","200","true","connected"]))
            .replace("{got}",   random.choice(["TIMEOUT","404","null","disconnected"]))
            .replace("{iface}", random.choice(["wlan0","eth0","bt0"]))
            .replace("{xp}",    f"//button[@id='{random.choice(['submit','connect','pair','pay'])}']")
            .replace("{field}", random.choice(["status","token","deviceId","userId","checksum"]))
            .replace("{lat}",   str(random.randint(800,5000)))
            .replace("{sla}",   str(random.randint(500,800)))
            .replace("{eid}",   f"ENTITY-{random.randint(1000,9999)}")
            .replace("{delta}", str(random.randint(5,120)))
            .replace("{dev}",   f"DEVICE-{random.randint(100,999)}")
            .replace("{used}",  str(random.randint(512,2048)))
            .replace("{total}", "2048")
            .replace("{op}",    random.choice(["media_decode","sync_batch","index_rebuild"]))
            .replace("{key}",   random.choice(["API_ENDPOINT","OAUTH_SECRET","DB_PASSWORD","SIGNING_KEY"]))
            .replace("{env}",   random.choice(["staging","production","uat"]))
            )

FIRST_NAMES = ["Aiden","Brenda","Carlos","Diana","Ethan","Fiona","George","Helen",
               "Ivan","Julia","Kevin","Laura","Michael","Nina","Oscar","Paula",
               "Quinn","Rachel","Samuel","Tara","Uma","Victor","Wendy","Xavier",
               "Yara","Zach","Amara","Ben","Clara","David"]
LAST_NAMES  = ["Anderson","Brown","Chen","Davis","Evans","Foster","Garcia","Harris",
               "Ibrahim","Johnson","Kim","Lee","Martinez","Nelson","Ortega","Park",
               "Quinn","Rivera","Singh","Taylor","Ueda","Vargas","Wang","Xavier",
               "Yamamoto","Zhang","Okonkwo","Patel","Rossi","Schmidt"]

def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

# Realistic test-case description templates
TC_DESC_TEMPLATES = [
    "Verify that {feature} completes successfully when {condition} under {env} conditions.",
    "Confirm that the system recovers gracefully after {failure} during {feature}.",
    "Validate that {feature} returns the correct result when {condition}.",
    "Ensure that {feature} does not exceed the {metric} threshold under {load} load.",
    "Test that {feature} correctly handles invalid input when {condition}.",
    "Verify end-to-end flow of {feature} from {start} to {end} with {condition}.",
    "Confirm that {feature} triggers the expected notification when {condition}.",
    "Validate that {feature} enforces access control when {condition}.",
    "Ensure {feature} synchronizes correctly across devices when {condition}.",
    "Verify that {feature} fails gracefully with a user-friendly error when {condition}.",
]

FEATURES = [
    "device pairing","user authentication","data synchronization","payment processing",
    "health metric upload","AR scene rendering","voice command recognition",
    "search query execution","media streaming","firmware over-the-air update",
    "Bluetooth reconnection","push notification delivery","configuration reload",
    "session token refresh","biometric verification","NFC tap-to-pay",
    "background sync","playlist shuffle","diagnostics report generation",
    "secure key rotation",
]
CONDITIONS = [
    "the network connection is interrupted mid-flow",
    "the device has been offline for more than 24 hours",
    "two concurrent requests are made simultaneously",
    "the session token has expired",
    "the input data contains Unicode special characters",
    "the battery level drops below 10%",
    "the server returns a 503 Service Unavailable response",
    "Bluetooth interference is present",
    "the user revokes permissions during the operation",
    "the target device is running a legacy firmware version",
]
ENVS    = ["low-bandwidth","high-load","degraded-network","standard","stress-test"]
METRICS = ["p95 latency (500ms)","p99 latency (1s)","memory ceiling (256MB)","CPU ceiling (80%)"]
LOADS   = ["normal","peak","sustained","burst"]

def tc_description():
    tmpl = random.choice(TC_DESC_TEMPLATES)
    return (tmpl
            .replace("{feature}",   random.choice(FEATURES))
            .replace("{condition}", random.choice(CONDITIONS))
            .replace("{env}",       random.choice(ENVS))
            .replace("{failure}",   random.choice(FAILURE_TYPES))
            .replace("{metric}",    random.choice(METRICS))
            .replace("{load}",      random.choice(LOADS))
            .replace("{start}",     random.choice(["login","device discovery","cart selection"]))
            .replace("{end}",       random.choice(["logout","pairing complete","payment confirmed"]))
            )

STEP_ACTIONS = [
    "Launch the {app} application on the test device.",
    "Navigate to Settings > {section} and tap '{option}'.",
    "Enter valid credentials: username='{user}', password='[REDACTED]'.",
    "Initiate {feature} by pressing the '{button}' button.",
    "Observe the status indicator for up to {t} seconds.",
    "Simulate {condition} using the network emulator profile '{profile}'.",
    "Verify that the UI displays '{message}'.",
    "Check server logs for event code '{code}'.",
    "Disconnect the {device} and wait {t} seconds.",
    "Re-connect the {device} and confirm auto-recovery.",
    "Capture a screenshot and attach as evidence.",
    "Record response time using the built-in performance monitor.",
    "Assert that database record for entity '{eid}' has status='{status}'.",
]

def step_action():
    tmpl = random.choice(STEP_ACTIONS)
    return (tmpl
            .replace("{app}",     random.choice(["SmartHome","DigitalWallet","WearableHealth","VoiceAssistant"]))
            .replace("{section}", random.choice(["Connectivity","Account","Privacy","Bluetooth"]))
            .replace("{option}",  random.choice(["Pair Device","Enable Sync","Reset","Verify Identity"]))
            .replace("{user}",    f"testuser_{random.randint(1,50):03d}")
            .replace("{feature}", random.choice(FEATURES))
            .replace("{button}",  random.choice(["Connect","Pay","Sync","Search","Start"]))
            .replace("{t}",       str(random.randint(3,30)))
            .replace("{condition}",random.choice(["network drop","Bluetooth interference","high CPU load"]))
            .replace("{profile}", random.choice(["3G-Low","WiFi-Lossy","LTE-Throttled","Offline"]))
            .replace("{message}", random.choice(["Connection successful","Sync complete","Payment approved","Error: retry"]))
            .replace("{code}",    f"EVT-{random.randint(1000,9999)}")
            .replace("{device}",  random.choice(["wearable","phone","hub","headset"]))
            .replace("{eid}",     f"ENT-{random.randint(100,999)}")
            .replace("{status}",  random.choice(["ACTIVE","SYNCED","PENDING","FAILED"]))
            )

# ──────────────────────────────────────────────────────────────────────────────
# 4. ENTITY GENERATORS
# ──────────────────────────────────────────────────────────────────────────────

def gen_applications():
    rows = []
    for a in APPLICATIONS:
        rows.append({
            "application_id": a["id"],
            "name": a["name"],
            "domain": a["domain"],
            "version": f"{random.randint(4,6)}.{random.randint(0,5)}.{random.randint(0,9)}",
            "status": random.choice(["Active","Active","Active","Deprecated"]),
            "owner_team": f"Team-{a['name'][:4].upper()}",
            "created_date": rdate("2020-01-01","2021-12-31"),
            "description": f"Enterprise application managing {a['domain']} services across connected devices.",
        })
    return rows

def gen_solutions(app_rows):
    app_ids = [a["application_id"] for a in app_rows]
    rows = []
    for i, name in enumerate(SOLUTION_NAMES[:NUM_SOLUTIONS], 1):
        rows.append({
            "solution_id": f"SOL-{i:03d}",
            "name": name,
            "application_id": app_ids[i % len(app_ids)],
            "component": random.choice(COMPONENTS),
            "version": f"{random.randint(1,5)}.{random.randint(0,9)}",
            "status": random.choice(["Stable","Beta","Deprecated","Stable","Stable"]),
            "description": f"Provides {name.lower()} capabilities integrated with the parent application platform.",
            "created_date": rdate("2020-06-01","2022-06-01"),
        })
    return rows

def gen_environments():
    env_defs = [
        ("ENV-001","Mobile Lab",        "Mobile",     "Android 14",    "WiFi-6"),
        ("ENV-002","Wearable Lab",       "Wearable",   "Wear OS 4",     "Bluetooth 5.3"),
        ("ENV-003","Hub Lab",            "Hub",        "Tizen 7.0",     "WiFi-6"),
        ("ENV-004","XR Lab",             "XR Headset", "One UI 6.0",    "WiFi-6"),
        ("ENV-005","Infra Lab",          "Cloud Node", "Ubuntu 22.04",  "Ethernet"),
        ("ENV-006","Cloud Test Env",     "Cloud Node", "Ubuntu 22.04",  "Ethernet"),
        ("ENV-007","Staging",            "Mobile",     "Android 13",    "LTE"),
        ("ENV-008","Production-like",    "Mobile",     "One UI 6.0",    "5G"),
        ("ENV-009","Low Network Env",    "Mobile",     "Android 14",    "Low-BW Sim"),
        ("ENV-010","High Load Env",      "Cloud Node", "Ubuntu 22.04",  "Ethernet"),
    ]
    rows = []
    for eid, name, dtype, osv, net in env_defs:
        rows.append({
            "environment_id":  eid,
            "name":            name,
            "device_type":     dtype,
            "os_version":      osv,
            "network_type":    net,
            "location":        random.choice(["Bangalore Lab","Seoul Lab","Cloud-AWS","Cloud-GCP"]),
            "configuration":   f"4-core CPU, 8GB RAM, {random.randint(64,256)}GB storage",
            "status":          random.choice(["Available","Available","Busy","Maintenance"]),
        })
    return rows

def gen_releases():
    rows = []
    base_date = datetime(2023, 1, 15)
    for i in range(1, NUM_RELEASES + 1):
        rel_date = base_date + timedelta(days=(i - 1) * 45)
        rows.append({
            "release_id":    f"REL-{i:03d}",
            "name":          f"Release {4 + i//4}.{i % 4}.0",
            "version":       f"{4 + i//4}.{i % 4}.{random.randint(0,9)}",
            "status":        "Released" if i < NUM_RELEASES else "In Progress",
            "release_date":  rel_date.strftime("%Y-%m-%d"),
            "description":   f"Scheduled release targeting stability improvements and new feature delivery for Q{((i-1)//3)+1}.",
        })
    return rows

def gen_engineers():
    roles = ["QA Engineer","Senior QA Engineer","Test Lead","Automation Engineer",
             "Performance Engineer","Security Tester","DevOps Engineer","Test Architect"]
    teams = ["SmartHome QA","Mobile QA","Security QA","Platform QA","Performance QA",
             "Automation QA","Release QA","XR QA"]
    rows = []
    seen = set()
    for i in range(1, NUM_ENGINEERS + 1):
        name = random_name()
        while name in seen:
            name = random_name()
        seen.add(name)
        rows.append({
            "engineer_id":  f"ENG-{i:03d}",
            "name":         name,
            "role":         random.choice(roles),
            "team":         random.choice(teams),
            "email":        f"eng{i:03d}@synthetic-qa.dev",
            "active":       random.choice(["true","true","true","false"]),
            "joined_date":  rdate("2018-01-01","2023-06-01"),
        })
    return rows

def gen_requirements(app_rows, sol_rows):
    app_ids  = [a["application_id"] for a in app_rows]
    sol_ids  = [s["solution_id"]    for s in sol_rows]
    features = FEATURES + [
        "offline mode","dark mode","haptic feedback","multilingual support",
        "accessibility support","parental controls","battery optimization",
        "crash reporting","remote diagnostics","audit logging",
    ]
    rows = []
    for i in range(1, NUM_REQUIREMENTS + 1):
        app = random.choice(app_ids)
        rows.append({
            "requirement_id":  f"REQ-{i:04d}",
            "application_id":  app,
            "solution_id":     random.choice(sol_ids),
            "title":           f"{random.choice(REQ_TYPES)} — {random.choice(features).title()}",
            "description":     (f"The system shall {random.choice(['support','enforce','validate','provide','handle'])} "
                                f"{random.choice(features)} {random.choice(['within 200ms','without data loss','securely','reliably','consistently'])} "
                                f"under {random.choice(ENVS)} conditions."),
            "requirement_type": random.choice(REQ_TYPES),
            "priority":         random.choice(PRIORITIES),
            "severity":         random.choice(SEVERITIES),
            "version":          f"v{random.randint(1,3)}.{random.randint(0,5)}",
            "status":           random.choice(["Approved","Draft","Approved","Approved","Deprecated"]),
            "created_date":     rdate("2022-01-01","2023-06-01"),
            "updated_date":     rdate("2023-01-01","2024-06-01"),
            "source_document":  f"SRS-{app}-v{random.randint(1,5)}.pdf",
            "feature":          random.choice(features),
            "component":        random.choice(COMPONENTS),
        })
    return rows

def gen_test_suites(app_rows, rel_rows):
    app_ids = [a["application_id"] for a in app_rows]
    rel_ids = [r["release_id"]     for r in rel_rows]
    suite_types = ["Regression","Smoke","Full","Performance","Security","Integration"]
    rows = []
    for i in range(1, NUM_TEST_SUITES + 1):
        app = random.choice(app_ids)
        rows.append({
            "suite_id":       f"TS-{i:04d}",
            "application_id": app,
            "release_id":     random.choice(rel_ids),
            "name":           f"{app} — {random.choice(suite_types)} Suite {i}",
            "description":    f"Suite covering {random.choice(COMPONENTS)} scenarios for {app}.",
            "suite_type":     random.choice(suite_types),
            "priority":       random.choice(PRIORITIES),
            "created_date":   rdate("2022-06-01","2023-12-01"),
            "status":         random.choice(["Active","Active","Archived","Draft"]),
        })
    return rows

def gen_test_cases(req_rows, suite_rows, app_rows, eng_rows, env_rows):
    req_ids   = [r["requirement_id"] for r in req_rows]
    suite_ids = [s["suite_id"]       for s in suite_rows]
    app_ids   = [a["application_id"] for a in app_rows]
    eng_ids   = [e["engineer_id"]    for e in eng_rows]
    env_ids   = [e["environment_id"] for e in env_rows]
    rows = []
    for i in range(1, NUM_TEST_CASES + 1):
        rows.append({
            "test_case_id":      f"TC-{i:04d}",
            "requirement_id":    random.choice(req_ids),
            "suite_id":          random.choice(suite_ids),
            "application_id":    random.choice(app_ids),
            "title":             tc_description()[:120],
            "description":       tc_description(),
            "objective":         f"Confirm that the feature behaves correctly under {random.choice(CONDITIONS)}.",
            "preconditions":     (f"Device is enrolled, firmware >= {random.randint(4,6)}.{random.randint(0,5)}.0, "
                                  f"network profile set to {random.choice(ENVS)}."),
            "priority":          random.choice(PRIORITIES),
            "severity":          random.choice(SEVERITIES),
            "test_type":         random.choice(TEST_TYPES),
            "automation_status": random.choice(AUTO_STATUS),
            "environment_id":    random.choice(env_ids),
            "estimated_duration": random.randint(60, 1800),
            "created_by":        random.choice(eng_ids),
            "status":            random.choice(["Active","Active","Active","Deprecated","Draft"]),
        })
    return rows

def gen_test_steps(tc_rows):
    rows = []
    step_id = 1
    # Give every test case 3–6 steps; ensure total >= NUM_TEST_STEPS
    for tc in tc_rows:
        n_steps = random.randint(3, 6)
        for s in range(1, n_steps + 1):
            rows.append({
                "test_step_id":    f"STEP-{step_id:05d}",
                "test_case_id":    tc["test_case_id"],
                "step_number":     s,
                "action":          step_action(),
                "expected_result": random.choice([
                    "The UI transitions to the next screen within 3 seconds.",
                    "A success toast message is displayed.",
                    "The operation completes without error.",
                    "Server returns HTTP 200 with a valid JSON payload.",
                    "The device reconnects automatically within 10 seconds.",
                    "A confirmation notification appears on the paired device.",
                    "The performance counter logs a value below the SLA threshold.",
                    "No crash or ANR is observed.",
                    "The audit log records the event with correct metadata.",
                    "The fallback UI is displayed with a human-readable error message.",
                ]),
                "input_data": random.choice([
                    "N/A",
                    f"username=testuser_{random.randint(1,50):03d}",
                    f"payload_size={random.choice([1,10,100,1000])}KB",
                    f"retry_count={random.randint(1,5)}",
                    f"network_profile={random.choice(ENVS)}",
                    f"device_id=DEVICE-{random.randint(100,999)}",
                ]),
            })
            step_id += 1
    return rows

def gen_test_runs(rel_rows, env_rows):
    rel_ids = [r["release_id"] for r in rel_rows]
    env_ids = [e["environment_id"] for e in env_rows]
    rows = []
    for i in range(1, NUM_TEST_RUNS + 1):
        rel  = rel_ids[i % len(rel_ids)]
        ver  = f"{4 + i//4}.{i % 4}.{random.randint(0,9)}"
        rows.append({
            "run_id":          f"RUN-{i:03d}",
            "name":            f"Regression Cycle {i} — Build {ver}",
            "release_id":      rel,
            "build_version":   ver,
            "environment_id":  random.choice(env_ids),
            "status":          random.choice(["Completed","Completed","In Progress","Aborted"]),
            "start_time":      rdatetime("2023-01-01","2024-06-01"),
            # aggregates will be patched after executions are generated
            "total_tests":     0,
            "passed":          0,
            "failed":          0,
            "blocked":         0,
            "skipped":         0,
            "pass_rate":       "0.00",
            "end_time":        rdatetime("2024-01-01","2024-12-31"),
        })
    return rows

def gen_failures_pool(tc_rows, app_rows, env_rows, n):
    """Pre-generate failure records (without execution_id links — patched later)."""
    tc_ids  = [t["test_case_id"]    for t in tc_rows]
    app_ids = [a["application_id"]  for a in app_rows]
    env_ids = [e["environment_id"]  for e in env_rows]
    # Create recurring root-cause clusters (same root cause → multiple failures)
    root_cause_pool = ROOT_CAUSES * (n // len(ROOT_CAUSES) + 1)
    rows = []
    for i in range(1, n + 1):
        ftype = random.choice(FAILURE_TYPES)
        rc    = root_cause_pool[i - 1]
        rows.append({
            "failure_id":           f"FAIL-{i:04d}",
            "execution_id":         "",   # patched later
            "test_case_id":         random.choice(tc_ids),
            "application_id":       random.choice(app_ids),
            "component":            random.choice(COMPONENTS),
            "failure_type":         ftype,
            "severity":             random.choice(SEVERITIES),
            "error_message":        error_msg(ftype),
            "observed_behavior":    f"The system exhibited {ftype.lower()} when {random.choice(CONDITIONS)}.",
            "expected_behavior":    f"The system should complete {random.choice(FEATURES)} within the defined SLA.",
            "stack_trace":          (f"com.samsung.{random.choice(['smarthome','wallet','health','browser'])}"
                                     f".{random.choice(COMPONENTS).replace(' ','')}"
                                     f".execute(line {random.randint(100,800)})"),
            "log_reference":        f"LOG-{random.randint(10000,99999)}",
            "environment":          random.choice(env_ids),
            "build_version":        f"{random.randint(4,6)}.{random.randint(0,5)}.{random.randint(0,9)}",
            "timestamp":            rdatetime(),
            "root_cause":           rc,
            "resolution_status":    random.choice(["Open","In Progress","Resolved","Resolved","Wont Fix"]),
        })
    return rows

def gen_executions_and_link_failures(tc_rows, run_rows, env_rows, failure_pool):
    tc_ids     = [t["test_case_id"]   for t in tc_rows]
    run_ids    = [r["run_id"]         for r in run_rows]
    env_ids    = [e["environment_id"] for e in env_rows]
    eng_names  = [f"eng{i:03d}@synthetic-qa.dev" for i in range(1, NUM_ENGINEERS + 1)]

    fail_idx       = 0
    fail_pool_size = len(failure_pool)
    exec_rows      = []
    run_stats      = {r["run_id"]: {"total":0,"passed":0,"failed":0,"blocked":0,"skipped":0} for r in run_rows}

    for i in range(1, NUM_TEST_EXECUTIONS + 1):
        run_id  = random.choice(run_ids)
        tc_id   = random.choice(tc_ids)
        build   = run_rows[run_ids.index(run_id)]["build_version"]

        # Weighted status distribution: ~55% PASS, ~20% FAIL, rest spread
        status = random.choices(
            EXEC_STATUS,
            weights=[55, 20, 10, 8, 7],
            k=1
        )[0]

        failure_id = ""
        if status == "FAIL" and fail_idx < fail_pool_size:
            failure_id = failure_pool[fail_idx]["failure_id"]
            failure_pool[fail_idx]["execution_id"] = f"EXEC-{i:05d}"
            failure_pool[fail_idx]["test_case_id"] = tc_id
            fail_idx += 1

        exec_rows.append({
            "execution_id":        f"EXEC-{i:05d}",
            "test_case_id":        tc_id,
            "test_run_id":         run_id,
            "environment_id":      random.choice(env_ids),
            "build_version":       build,
            "execution_timestamp": rdatetime(),
            "status":              status,
            "duration_ms":         random.randint(500, 120000),
            "executed_by":         random.choice(eng_names),
            "failure_id":          failure_id,
            "defect_id":           "",   # patched in defect generation
        })

        rs = run_stats[run_id]
        rs["total"]   += 1
        rs["passed"]  += 1 if status == "PASS"    else 0
        rs["failed"]  += 1 if status == "FAIL"    else 0
        rs["blocked"] += 1 if status == "BLOCKED" else 0
        rs["skipped"] += 1 if status in ("SKIPPED","NOT_RUN") else 0

    # Patch run aggregates
    for r in run_rows:
        rs = run_stats[r["run_id"]]
        r["total_tests"] = rs["total"]
        r["passed"]      = rs["passed"]
        r["failed"]      = rs["failed"]
        r["blocked"]     = rs["blocked"]
        r["skipped"]     = rs["skipped"]
        r["pass_rate"]   = (f"{rs['passed']/rs['total']*100:.2f}"
                             if rs["total"] > 0 else "0.00")

    return exec_rows

def gen_defects(failure_pool, exec_rows, tc_rows, req_rows, eng_rows):
    # Assign ~50 % of failures a defect
    fail_with_exec = [f for f in failure_pool if f["execution_id"]]
    sampled_fails  = random.sample(fail_with_exec,
                                   min(NUM_DEFECTS, len(fail_with_exec)))
    req_ids  = [r["requirement_id"] for r in req_rows]
    eng_ids  = [e["engineer_id"]    for e in eng_rows]
    eng_map  = {e["engineer_id"]: e["email"] for e in eng_rows}

    # Build a dict to quickly look up execution → test_case → req
    exec_tc_map = {e["execution_id"]: e["test_case_id"] for e in exec_rows}
    tc_req_map  = {}
    for tc in tc_rows:
        tc_req_map[tc["test_case_id"]] = tc["requirement_id"]

    defect_rows   = []
    exec_to_defect = {}  # failure_id → defect_id

    for i, fail in enumerate(sampled_fails, 1):
        did        = f"BUG-{i:04d}"
        reported   = fail["timestamp"][:10]
        status     = random.choice(DEFECT_STATUS)
        resolved   = rdate("2023-06-01","2024-12-31") if status in ("FIXED","VERIFIED","CLOSED") else ""
        eng_id     = random.choice(eng_ids)
        tc_id      = fail["test_case_id"]
        req_id     = tc_req_map.get(tc_id, random.choice(req_ids))

        defect_rows.append({
            "defect_id":          did,
            "title":              f"{fail['failure_type']} in {fail['component']}: {fail['error_message'][:60]}…",
            "description":        (f"During execution {fail['execution_id']}, test case {tc_id} failed with "
                                   f"{fail['failure_type']}. {fail['observed_behavior']}"),
            "severity":           fail["severity"],
            "priority":           random.choice(PRIORITIES),
            "status":             status,
            "component":          fail["component"],
            "application_id":     fail["application_id"],
            "root_cause":         fail["root_cause"],
            "reported_date":      reported,
            "resolved_date":      resolved,
            "assigned_engineer":  eng_id,
            "affected_requirement": req_id,
            "related_test_case":  tc_id,
            "related_failure":    fail["failure_id"],
            "resolution":         random.choice(RESOLUTION_NOTES) if resolved else "",
        })
        exec_to_defect[fail["failure_id"]] = did

    # Back-patch exec_rows with defect_id
    fail_to_defect = exec_to_defect
    fail_exec_map  = {f["failure_id"]: f["execution_id"] for f in failure_pool if f["execution_id"]}
    exec_defect    = {}
    for fid, did in fail_to_defect.items():
        eid = fail_exec_map.get(fid)
        if eid:
            exec_defect[eid] = did
    for ex in exec_rows:
        if ex["execution_id"] in exec_defect:
            ex["defect_id"] = exec_defect[ex["execution_id"]]

    return defect_rows

def gen_assignments(tc_rows, run_rows, eng_rows):
    tc_ids  = [t["test_case_id"] for t in tc_rows]
    run_ids = [r["run_id"]       for r in run_rows]
    eng_ids = [e["engineer_id"]  for e in eng_rows]
    rows    = []
    for i in range(1, NUM_ASSIGNMENTS + 1):
        rows.append({
            "assignment_id":  f"ASGN-{i:04d}",
            "test_case_id":   random.choice(tc_ids),
            "run_id":         random.choice(run_ids),
            "engineer_id":    random.choice(eng_ids),
            "assigned_date":  rdate(),
            "role":           random.choice(["Executor","Reviewer","Owner"]),
            "status":         random.choice(["Pending","In Progress","Completed","Skipped"]),
        })
    return rows

def gen_historical_failures(failure_pool, tc_rows, app_rows, env_rows):
    tc_ids  = [t["test_case_id"] for t in tc_rows]
    app_ids = [a["application_id"] for a in app_rows]
    env_ids = [e["environment_id"] for e in env_rows]
    rows    = []
    # Cluster some recurring root causes
    for i in range(1, NUM_HISTORICAL_FAILURES + 1):
        src_fail = failure_pool[i % len(failure_pool)]
        rows.append({
            "hist_failure_id":  f"HIST-{i:04d}",
            "original_failure": src_fail["failure_id"],
            "test_case_id":     random.choice(tc_ids),
            "application_id":   random.choice(app_ids),
            "component":        src_fail["component"],
            "failure_type":     src_fail["failure_type"],
            "root_cause":       src_fail["root_cause"],
            "build_version":    f"{random.randint(3,6)}.{random.randint(0,5)}.{random.randint(0,9)}",
            "environment":      random.choice(env_ids),
            "occurrence_date":  rdate("2021-01-01","2024-06-01"),
            "recurrence_count": random.randint(1, 15),
            "resolution_status":random.choice(["Resolved","Resolved","Wont Fix","Open"]),
            "notes":            f"Recurring issue linked to root cause cluster #{(i % len(ROOT_CAUSES)) + 1}.",
        })
    return rows

# ──────────────────────────────────────────────────────────────────────────────
# 5. GRAPH GENERATION
# ──────────────────────────────────────────────────────────────────────────────

def gen_graph(app_rows, sol_rows, req_rows, suite_rows, tc_rows,
              exec_rows, fail_rows, defect_rows, eng_rows, env_rows,
              run_rows, rel_rows):
    nodes = []
    rels  = []
    rel_id = 1

    def add_node(node_id, node_type, name, description, source_id):
        nodes.append({
            "node_id":    node_id,
            "node_type":  node_type,
            "name":       name,
            "description":description,
            "source_id":  source_id,
        })

    def add_rel(src, rtype, tgt, conf=1.0, ref=""):
        nonlocal rel_id
        rels.append({
            "relationship_id": f"REL-{rel_id:06d}",
            "source_node":     src,
            "relationship_type": rtype,
            "target_node":     tgt,
            "confidence":      conf,
            "source_reference": ref,
        })
        rel_id += 1

    # --- Nodes ---
    for a in app_rows:
        add_node(a["application_id"],"APPLICATION", a["name"], a["description"], a["application_id"])
    for s in sol_rows:
        add_node(s["solution_id"],"SOLUTION", s["name"], s["description"], s["solution_id"])
    for r in rel_rows:
        add_node(r["release_id"],"RELEASE", r["name"], r["description"], r["release_id"])
    for e in env_rows:
        add_node(e["environment_id"],"ENVIRONMENT", e["name"], e["configuration"], e["environment_id"])
    for e in eng_rows:
        add_node(e["engineer_id"],"ENGINEER", e["name"], e["role"], e["engineer_id"])
    for r in req_rows:
        add_node(r["requirement_id"],"REQUIREMENT", r["title"], r["description"], r["requirement_id"])
    for s in suite_rows:
        add_node(s["suite_id"],"TEST_SUITE", s["name"], s["description"], s["suite_id"])
    for t in tc_rows:
        add_node(t["test_case_id"],"TEST_CASE", t["title"][:80], t["description"][:120], t["test_case_id"])
    for r in run_rows:
        add_node(r["run_id"],"TEST_RUN", r["name"], f"Build {r['build_version']}", r["run_id"])
    for ex in exec_rows[:NUM_TEST_EXECUTIONS]:   # cap nodes for graph
        add_node(ex["execution_id"],"TEST_EXECUTION",
                 f"Exec {ex['execution_id']}",
                 f"Status={ex['status']} build={ex['build_version']}", ex["execution_id"])
    for f in fail_rows:
        add_node(f["failure_id"],"FAILURE", f["failure_type"],
                 f["error_message"][:120], f["failure_id"])
    for d in defect_rows:
        add_node(d["defect_id"],"DEFECT", d["title"][:80], d["description"][:120], d["defect_id"])

    # --- Relationships ---
    # Solution BELONGS_TO Application
    for s in sol_rows:
        add_rel(s["solution_id"],"BELONGS_TO", s["application_id"], 1.0, s["solution_id"])

    # Requirement BELONGS_TO Application
    for r in req_rows:
        add_rel(r["requirement_id"],"BELONGS_TO", r["application_id"], 1.0, r["requirement_id"])

    # Test suite BELONGS_TO Application
    for s in suite_rows:
        add_rel(s["suite_id"],"BELONGS_TO", s["application_id"], 1.0, s["suite_id"])

    # Test case IMPLEMENTS Requirement
    for t in tc_rows:
        add_rel(t["test_case_id"],"IMPLEMENTS", t["requirement_id"], 1.0, t["test_case_id"])

    # Test case CONTAINS (suite)
    for t in tc_rows:
        add_rel(t["suite_id"],"CONTAINS", t["test_case_id"], 1.0, t["test_case_id"])

    # Test execution EXECUTED_DURING TestRun
    for ex in exec_rows:
        add_rel(ex["execution_id"],"EXECUTED_DURING", ex["test_run_id"], 1.0, ex["execution_id"])
        add_rel(ex["test_case_id"],"HAS_EXECUTION",   ex["execution_id"], 1.0, ex["execution_id"])
        add_rel(ex["execution_id"],"EXECUTED_IN",     ex["environment_id"], 1.0, ex["execution_id"])

    # Execution PRODUCED Failure
    for ex in exec_rows:
        if ex["failure_id"]:
            add_rel(ex["execution_id"],"PRODUCED", ex["failure_id"], 1.0, ex["execution_id"])

    # Failure LINKED_TO Defect
    fail_to_defect = {d["related_failure"]: d["defect_id"] for d in defect_rows}
    for f in fail_rows:
        if f["failure_id"] in fail_to_defect:
            did = fail_to_defect[f["failure_id"]]
            add_rel(f["failure_id"],"LINKED_TO", did, 1.0, f["failure_id"])

    # Defect AFFECTS Requirement
    for d in defect_rows:
        add_rel(d["defect_id"],"AFFECTS", d["affected_requirement"], 1.0, d["defect_id"])

    # Defect ASSIGNED_TO Engineer
    for d in defect_rows:
        add_rel(d["defect_id"],"ASSIGNED_TO", d["assigned_engineer"], 1.0, d["defect_id"])

    # TestRun PART_OF Release
    for r in run_rows:
        add_rel(r["run_id"],"PART_OF", r["release_id"], 1.0, r["run_id"])

    # Engineer ASSIGNED_TO TestCase (sample)
    tc_ids  = [t["test_case_id"] for t in tc_rows]
    eng_ids = [e["engineer_id"]  for e in eng_rows]
    for i in range(min(500, len(tc_ids))):
        add_rel(eng_ids[i % len(eng_ids)],"ASSIGNED_TO", tc_ids[i], 0.9, "assignments")

    # Defect DEPENDS_ON (another defect, ~10% of defects)
    d_ids = [d["defect_id"] for d in defect_rows]
    for d in random.sample(defect_rows, min(50, len(defect_rows))):
        other = random.choice(d_ids)
        if other != d["defect_id"]:
            add_rel(d["defect_id"],"DEPENDS_ON", other, 0.7, "defect_dependency")

    # Failure OCCURRED_IN Environment (already via execution, add direct for quick lookup)
    for f in fail_rows:
        add_rel(f["failure_id"],"OCCURRED_IN", f["environment"], 1.0, f["failure_id"])

    return nodes, rels

# ──────────────────────────────────────────────────────────────────────────────
# 6. MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("\n=== Synthetic Test Management Dataset Generator ===")
    print(f"    Seed: {SEED}\n")

    print("Generating entities…")
    apps    = gen_applications()
    sols    = gen_solutions(apps)
    envs    = gen_environments()
    rels_   = gen_releases()
    engs    = gen_engineers()
    reqs    = gen_requirements(apps, sols)
    suites  = gen_test_suites(apps, rels_)
    tcs     = gen_test_cases(reqs, suites, apps, engs, envs)
    steps   = gen_test_steps(tcs)
    runs    = gen_test_runs(rels_, envs)
    fails   = gen_failures_pool(tcs, apps, envs, NUM_FAILURES)
    execs   = gen_executions_and_link_failures(tcs, runs, envs, fails)
    defects = gen_defects(fails, execs, tcs, reqs, engs)
    assigns = gen_assignments(tcs, runs, engs)
    hist    = gen_historical_failures(fails, tcs, apps, envs)

    print("\nWriting structured CSVs…")
    write_csv(STRUCTURED/"applications.csv",
              ["application_id","name","domain","version","status","owner_team","created_date","description"], apps)
    write_csv(STRUCTURED/"solutions.csv",
              ["solution_id","name","application_id","component","version","status","description","created_date"], sols)
    write_csv(STRUCTURED/"environments.csv",
              ["environment_id","name","device_type","os_version","network_type","location","configuration","status"], envs)
    write_csv(STRUCTURED/"releases.csv",
              ["release_id","name","version","status","release_date","description"], rels_)
    write_csv(STRUCTURED/"engineers.csv",
              ["engineer_id","name","role","team","email","active","joined_date"], engs)
    write_csv(STRUCTURED/"requirements.csv",
              ["requirement_id","application_id","solution_id","title","description",
               "requirement_type","priority","severity","version","status",
               "created_date","updated_date","source_document","feature","component"], reqs)
    write_csv(STRUCTURED/"test_suites.csv",
              ["suite_id","application_id","release_id","name","description",
               "suite_type","priority","created_date","status"], suites)
    write_csv(STRUCTURED/"test_cases.csv",
              ["test_case_id","requirement_id","suite_id","application_id","title",
               "description","objective","preconditions","priority","severity",
               "test_type","automation_status","environment_id","estimated_duration",
               "created_by","status"], tcs)
    write_csv(STRUCTURED/"test_steps.csv",
              ["test_step_id","test_case_id","step_number","action","expected_result","input_data"], steps)
    write_csv(STRUCTURED/"test_runs.csv",
              ["run_id","name","release_id","build_version","environment_id","status",
               "start_time","total_tests","passed","failed","blocked","skipped",
               "pass_rate","end_time"], runs)
    write_csv(STRUCTURED/"test_executions.csv",
              ["execution_id","test_case_id","test_run_id","environment_id","build_version",
               "execution_timestamp","status","duration_ms","executed_by",
               "failure_id","defect_id"], execs)
    write_csv(STRUCTURED/"failures.csv",
              ["failure_id","execution_id","test_case_id","application_id","component",
               "failure_type","severity","error_message","observed_behavior",
               "expected_behavior","stack_trace","log_reference","environment",
               "build_version","timestamp","root_cause","resolution_status"], fails)
    write_csv(STRUCTURED/"defects.csv",
              ["defect_id","title","description","severity","priority","status",
               "component","application_id","root_cause","reported_date","resolved_date",
               "assigned_engineer","affected_requirement","related_test_case",
               "related_failure","resolution"], defects)
    write_csv(STRUCTURED/"assignments.csv",
              ["assignment_id","test_case_id","run_id","engineer_id","assigned_date","role","status"], assigns)
    write_csv(STRUCTURED/"historical_failures.csv",
              ["hist_failure_id","original_failure","test_case_id","application_id",
               "component","failure_type","root_cause","build_version","environment",
               "occurrence_date","recurrence_count","resolution_status","notes"], hist)

    # execution_steps — a view of steps per execution (sample)
    exec_steps = []
    tc_steps_map = {}
    for step in steps:
        tc_steps_map.setdefault(step["test_case_id"], []).append(step)
    for ex in execs[:3000]:  # sample to keep size manageable
        for step in tc_steps_map.get(ex["test_case_id"], []):
            exec_steps.append({
                "exec_step_id":  f"ES-{len(exec_steps)+1:06d}",
                "execution_id":  ex["execution_id"],
                "test_step_id":  step["test_step_id"],
                "step_number":   step["step_number"],
                "status":        ex["status"] if step["step_number"] == 1 else random.choice(["PASS","PASS","FAIL","SKIP"]),
                "actual_result": random.choice([
                    "Step completed as expected.",
                    "UI transition delayed by 2s.",
                    "Server returned 503.",
                    "Device did not reconnect.",
                    "Notification not received.",
                    "Test skipped due to prior failure.",
                ]),
            })
            if len(exec_steps) >= 15000:
                break
        if len(exec_steps) >= 15000:
            break

    write_csv(STRUCTURED/"execution_steps.csv",
              ["exec_step_id","execution_id","test_step_id","step_number","status","actual_result"],
              exec_steps)

    print("\nGenerating knowledge graph…")
    nodes, graph_rels = gen_graph(apps, sols, reqs, suites, tcs,
                                   execs, fails, defects, engs, envs, runs, rels_)
    write_csv(GRAPH/"nodes.csv",
              ["node_id","node_type","name","description","source_id"], nodes)
    write_csv(GRAPH/"relationships.csv",
              ["relationship_id","source_node","relationship_type","target_node",
               "confidence","source_reference"], graph_rels)

    # Graph schema
    schema = {
        "node_types": ["APPLICATION","SOLUTION","REQUIREMENT","TEST_SUITE","TEST_CASE",
                       "TEST_STEP","TEST_RUN","TEST_EXECUTION","FAILURE","DEFECT",
                       "ENGINEER","ENVIRONMENT","RELEASE","COMPONENT"],
        "relationship_types": ["BELONGS_TO","IMPLEMENTS","COVERS","CONTAINS","EXECUTED_IN",
                               "EXECUTED_DURING","PRODUCED","CAUSED_BY","LINKED_TO","AFFECTS",
                               "ASSIGNED_TO","FIXED_BY","VERIFIED_BY","DEPENDS_ON","RELATED_TO",
                               "BLOCKS","REPRODUCES","OCCURRED_IN","PART_OF","HAS_EXECUTION"],
        "multi_hop_examples": [
            "REQUIREMENT → (IMPLEMENTS) → TEST_CASE → (HAS_EXECUTION) → TEST_EXECUTION → (PRODUCED) → FAILURE → (LINKED_TO) → DEFECT → (AFFECTS) → REQUIREMENT",
            "TEST_RUN → (PART_OF) → RELEASE",
            "DEFECT → (ASSIGNED_TO) → ENGINEER",
        ],
    }
    with open(GRAPH/"graph_schema.json","w",encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"  ✓ graph_schema.json")

    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    print(f"  Applications       : {len(apps):>6,}")
    print(f"  Solutions          : {len(sols):>6,}")
    print(f"  Environments       : {len(envs):>6,}")
    print(f"  Releases           : {len(rels_):>6,}")
    print(f"  Engineers          : {len(engs):>6,}")
    print(f"  Requirements       : {len(reqs):>6,}")
    print(f"  Test Suites        : {len(suites):>6,}")
    print(f"  Test Cases         : {len(tcs):>6,}")
    print(f"  Test Steps         : {len(steps):>6,}")
    print(f"  Test Runs          : {len(runs):>6,}")
    print(f"  Test Executions    : {len(execs):>6,}")
    print(f"  Execution Steps    : {len(exec_steps):>6,}")
    print(f"  Failures           : {len(fails):>6,}")
    print(f"  Defects            : {len(defects):>6,}")
    print(f"  Assignments        : {len(assigns):>6,}")
    print(f"  Historical Failures: {len(hist):>6,}")
    print(f"  Graph Nodes        : {len(nodes):>6,}")
    print(f"  Graph Relationships: {len(graph_rels):>6,}")
    print(f"\nOutput → {STRUCTURED}")
    print(f"Output → {GRAPH}")
    print("\nDataset generation complete.\n")

if __name__ == "__main__":
    main()
