// Pure-Node synthetic data generator — no external deps, deterministic (seeded RNG).
// Produces the 4 linked tables the frontend runs against until the real Samsung
// dataset arrives. Field names mirror what a real test-management export uses.
import { writeFileSync, mkdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, "..", "src", "api", "mockData");
mkdirSync(OUT, { recursive: true });

// Seeded PRNG (mulberry32) so the dataset is reproducible across runs/machines.
function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(26580826);
const pick = (arr) => arr[Math.floor(rand() * arr.length)];
const int = (min, max) => Math.floor(rand() * (max - min + 1)) + min;
const isoDaysAgo = (d) => new Date(Date.now() - d * 86400000).toISOString();

const MODULES = [
  "SmartThings > Device Pairing",
  "SmartThings > Automations",
  "Bixby > Voice Commands",
  "Bixby > Routines",
  "Wallet > Card Add",
  "Wallet > Payments",
  "Galaxy Search > Indexing",
  "Helix > Sync",
  "Samsung Internet > Bookmarks",
  "Living Labs > Feedback",
];

// Deliberately unstable module — gives the RAG demo a real, discoverable answer.
const UNSTABLE_MODULE = "SmartThings > Device Pairing";
const UNSTABLE_FAIL_RATE = 0.62;
const NORMAL_FAIL_RATE = 0.12;

const ENVIRONMENTS = ["Mobile", "Watch", "Hub", "DA", "Infra"];
const SEVERITIES = ["Critical", "High", "Medium", "Low"];
const DEFECT_STATUSES = ["Open", "In Progress", "Resolved"];

const FAILURE_MESSAGES_BY_MODULE = {
  "SmartThings > Device Pairing": [
    "pairing_timeout_error",
    "ble_handshake_failed",
    "device_not_discovered",
    "auth_token_expired_during_pairing",
  ],
  default: [
    "assertion_mismatch",
    "ui_render_null_ref",
    "network_request_timeout",
    "unexpected_state_transition",
    "config_value_missing",
  ],
};

// ---- Requirements ----
const REQUIREMENT_TITLES = [
  "User can pair a new device over Wi-Fi",
  "User can pair a new device over Bluetooth",
  "Device list refreshes after successful pairing",
  "Automation triggers fire within 2 seconds of condition match",
  "User can create a multi-device automation routine",
  "Bixby correctly parses device-control voice commands",
  "Bixby routine can be triggered by voice",
  "User can add a payment card via camera scan",
  "User can add a payment card manually",
  "Wallet transaction history loads within 1 second",
  "Galaxy Search indexes new app installs within 5 minutes",
  "Galaxy Search returns results across device and cloud content",
  "Helix syncs settings across signed-in devices",
  "Helix conflict resolution favors most recent change",
  "Samsung Internet bookmark syncs across devices",
  "Samsung Internet bookmark folder can be renamed",
  "Living Labs feedback form submits without data loss",
  "Living Labs survey respects user's opt-out setting",
  "SmartThings automation list supports reordering",
  "SmartThings device removal cleans up related automations",
  "Bixby handles interrupted voice commands gracefully",
  "Wallet payment retries once on transient network failure",
  "Galaxy Search respects content permission scopes",
  "Helix sync backs off correctly under rate limiting",
  "Samsung Internet import from external browser succeeds",
];

const requirements = REQUIREMENT_TITLES.map((title, i) => {
  const module = pick(MODULES);
  // A few requirements deliberately have zero test coverage — surfaced later
  // by the "requirements with no coverage" insight.
  const hasTestCoverage = i % 7 !== 0;
  return {
    id: `REQ-${String(i + 1).padStart(3, "0")}`,
    title,
    module,
    hasTestCoverage,
  };
});

// ---- Test cases ----
const testCases = [];
let tcCounter = 1;
const TC_PER_REQUIREMENT = 12; // ~25 reqs * 12 = ~300 test cases

for (const req of requirements) {
  if (!req.hasTestCoverage) continue;
  const count = int(TC_PER_REQUIREMENT - 4, TC_PER_REQUIREMENT + 4);
  for (let i = 0; i < count; i++) {
    const failRate = req.module === UNSTABLE_MODULE ? UNSTABLE_FAIL_RATE : NORMAL_FAIL_RATE;
    const roll = rand();
    const status = roll < failRate ? "Fail" : roll < failRate + 0.06 ? "Blocked" : roll < failRate + 0.1 ? "Not Run" : "Pass";
    testCases.push({
      id: `TC-${String(tcCounter).padStart(4, "0")}`,
      requirementId: req.id,
      module: req.module,
      description: `${req.title} — variation ${i + 1}`,
      steps: [
        "Set up the test environment and preconditions",
        `Perform the action described in "${req.title}"`,
        "Verify the expected outcome and capture logs",
      ],
      status,
      lastRunAt: isoDaysAgo(int(0, 30)),
      environment: pick(ENVIRONMENTS),
    });
    tcCounter++;
  }
}

// ---- Defects (linked to failed test cases) ----
const failedCases = testCases.filter((t) => t.status === "Fail");
const defects = [];
let defCounter = 1;
for (const tc of failedCases) {
  if (rand() > 0.55) continue; // not every failure has a logged defect yet
  const msgs = FAILURE_MESSAGES_BY_MODULE[tc.module] || FAILURE_MESSAGES_BY_MODULE.default;
  defects.push({
    id: `DEF-${String(defCounter).padStart(4, "0")}`,
    testCaseId: tc.id,
    severity: tc.module === UNSTABLE_MODULE ? pick(["Critical", "High", "High", "Medium"]) : pick(SEVERITIES),
    status: pick(DEFECT_STATUSES),
    description: `${tc.module} fails with ${pick(msgs)} during "${tc.description}"`,
    createdAt: isoDaysAgo(int(0, 45)),
  });
  defCounter++;
}

// ---- Failure logs (tied to failed runs) ----
const failureLogs = [];
let logCounter = 1;
for (const tc of failedCases) {
  const msgs = FAILURE_MESSAGES_BY_MODULE[tc.module] || FAILURE_MESSAGES_BY_MODULE.default;
  const entries = int(1, 2);
  for (let i = 0; i < entries; i++) {
    failureLogs.push({
      id: `LOG-${String(logCounter).padStart(4, "0")}`,
      testCaseId: tc.id,
      message: pick(msgs),
      timestamp: isoDaysAgo(int(0, 30)),
    });
    logCounter++;
  }
}

writeFileSync(join(OUT, "requirements.json"), JSON.stringify(requirements, null, 2));
writeFileSync(join(OUT, "testCases.json"), JSON.stringify(testCases, null, 2));
writeFileSync(join(OUT, "defects.json"), JSON.stringify(defects, null, 2));
writeFileSync(join(OUT, "failureLogs.json"), JSON.stringify(failureLogs, null, 2));

console.log(
  `Generated ${requirements.length} requirements, ${testCases.length} test cases, ` +
    `${defects.length} defects, ${failureLogs.length} failure logs.`
);
