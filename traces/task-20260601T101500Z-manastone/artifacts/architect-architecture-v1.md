# Architecture Decision Record: Manastone v1 Install & Brand Independence

## Context

Manastone is a robot control agent that wraps Pi's coding agent. The vision requires:
- New users (unboxing Unitree G1 or Agibot X2) can install once and control robots via natural language.
- Pi brand must be hidden from end users (similar to OpenClaw-Pi relationship).
- Install must include all dependencies (Pi coding agent) automatically.
- Environment is noisy; work must be low-profile and precise.
- Defer broad multi-level functionality audit to post-v1.

Current state: The codebase has a bootstrap installer (`install.sh`), packaging scripts, and a runtime that depends on `@mariozechner/pi-coding-agent`. The Pi brand leaks via package name, documentation, and possibly UI strings.

## Decision

### 1. Installer Wraps Pi Dependency Transparently

**Decision:** The `install.sh` script will automatically install the Pi coding agent as a dependency (via npm/pip) without user awareness. The user runs one command and gets everything.

**Rationale:** The vision requires "install once" and "no manual Pi dependency setup." Wrapping Pi installation inside the bootstrap eliminates user friction and hides Pi from the user.

**Alternatives Rejected:**
- Require users to install Pi separately: Rejected because it violates the "install once" promise and exposes Pi brand.
- Bundle Pi as a vendored dependency: Rejected because it complicates updates and licensing; npm dependency is cleaner.

**Consequences:**
- Positive: Single install command, Pi hidden.
- Negative: Install script must handle npm/node version requirements; failure modes must be clear.
- Risk: Pi package may change API; need version pinning and testing.

### 2. Brand Independence via Namespace Isolation

**Decision:** All user-facing surfaces (CLI output, TUI, documentation, error messages, logs) must use "Manastone" branding only. Internal references to Pi are allowed in code comments and internal logs. The package name `manastone-coding-agent` is kept; the Pi extension mechanism is used internally.

**Rationale:** The vision explicitly states "Manastone will never expose Pi branding to end users." This requires a systematic audit of all user-facing strings.

**Alternatives Rejected:**
- Fork Pi and rebrand entirely: Rejected due to maintenance burden and upstream dependency.
- Use a proxy layer that translates Pi errors: Rejected as over-engineering for v1; simple string replacement in output formatters is sufficient.

**Consequences:**
- Positive: Clean brand separation.
- Negative: Need to maintain a mapping of Pi error messages to Manastone-friendly messages.
- Risk: Upstream Pi may change error formats; need periodic review.

### 3. Install Experience Optimization

**Decision:** The install script will provide clear progress output, check prerequisites (Python 3.10+, Node.js), and offer a post-install verification command (`manastone doctor`). The README will be rewritten with a quickstart that assumes zero prior knowledge.

**Rationale:** New robot operators are not developers; they need guided setup. The current README is in Chinese and assumes familiarity with the codebase.

**Alternatives Rejected:**
- Interactive TUI installer: Rejected for v1 due to complexity; shell script is simpler and more portable.
- Docker-based install: Rejected because it adds overhead and hides the robot control integration.

**Consequences:**
- Positive: Lower barrier for new users.
- Negative: Shell script must be robust across macOS/Linux; testing matrix needed.

### 4. Defer Multi-Level Audit to Post-v1

**Decision:** Do not restructure the entire codebase for v1. Focus only on install experience and brand independence. The existing modular structure (roboonto, runtime, pilot) remains.

**Rationale:** The vision explicitly defers "broad multi-level functionality audit" to post-v1. Scope discipline is critical.

**Alternatives Rejected:**
- Full architecture overhaul: Rejected as out of scope.

**Consequences:**
- Positive: Faster v1 delivery.
- Negative: Technical debt may accumulate; post-v1 audit will be needed.

## Data Flow

```
User runs: bash bootstrap/install.sh
  ├── Checks Python 3.10+, Node.js
  ├── pip install -e .[x2]  (or g1/dev)
  │   └── Installs manastone Python package
  ├── npm install @mariozechner/pi-coding-agent  (transparent)
  │   └── Installs Pi coding agent as dependency
  ├── Creates ~/.manastone/config.yaml with defaults
  └── Prints success message (Manastone branded)

User runs: manastone
  └── CLI/TUI loads, all output uses "Manastone"
      └── Internal calls to Pi are wrapped
```

## Failure Modes

| Component | Failure | User Impact | Mitigation |
|-----------|---------|-------------|------------|
| Install script | Missing Python/Node | Install fails with clear message | Prerequisite check at start |
| npm install | Network error | Install fails | Retry logic, offline fallback message |
| Pi dependency | API change | Robot control may break | Version pinning, integration tests |
| Brand leak | Pi name appears in output | User sees Pi brand | String audit, output formatter filter |

## Downstream Constraints

- **Senior Engineer:** Must implement install script changes, brand string audit, and `manastone doctor` command.
- **API Designer:** Must ensure all API responses use Manastone branding; no Pi references in JSON responses.
- **Database Engineer:** No database changes required for v1.

## Tradeoffs Accepted

- Hiding Pi adds a wrapping layer that may complicate debugging for internal developers.
- Deferring multi-level audit means some UX issues (e.g., confusing command hierarchy) may persist until post-v1.
- Using shell script for installer limits cross-platform polish but is pragmatic for v1.

---

# Completion Report

```yaml
completion_report:
  what_was_done: Designed architecture for Manastone v1 focusing on install experience and brand independence. Created ADR with four key decisions: transparent Pi dependency install, brand namespace isolation, install experience optimization, and deferral of multi-level audit. Documented data flow, failure modes, and downstream constraints.
  key_decisions:
    - decision: Installer wraps Pi dependency transparently
      rationale: Single install command, no manual Pi setup, hides Pi brand.
    - decision: Brand independence via namespace isolation
      rationale: All user-facing surfaces use Manastone branding only; internal Pi references allowed.
    - decision: Install experience optimization
      rationale: Prerequisite checks, progress output, post-install verification for new users.
    - decision: Defer multi-level audit to post-v1
      rationale: Scope discipline; focus on v1 critical path.
  handoff_focus:
    - Implement install script changes (prerequisite checks, transparent Pi install, progress output)
    - Audit all user-facing strings for Pi brand leaks; create output filter
    - Implement `manastone doctor` command for post-install verification
    - Rewrite README with quickstart for new robot operators
  open_questions:
    - What specific Pi branding currently leaks into the user experience? (Need string audit)
    - What is the exact install failure rate or confusion point for new users? (Need user testing)
    - How does the OpenClaw-Pi relationship model apply technically? (Need to review OpenClaw codebase)
  known_constraints:
    - Must hide Pi brand from end users
    - Install must include all dependencies (Pi coding agent) automatically
    - Environment is noisy; work must be low-profile and precise
    - Defer broad multi-level functionality audit to post-v1
  confidence_differential: 0.85
  dissent_if_alone: null
  iteration_context: null
```

---

# Context Compression Report

```yaml
context_compression_report:
  input_scope:
    artifacts_read:
      - product-vision-anchor-product-vision-statement-v1
      - bootstrap/README.md
      - pilot/coding-agent/package.json
      - pyproject.toml
      - runtime/config.py
    handoffs_read:
      - handoffs/product-vision-anchor→architect-20260601-100809.yaml
  retained_context:
    decisions:
      - Focus on install experience and brand independence as core v1 scope.
      - Defer broad multi-level functionality audit to post-v1.
      - Installer wraps Pi dependency transparently.
      - Brand independence via namespace isolation.
      - Install experience optimization with prerequisite checks and post-install verification.
    constraints:
      - Must hide Pi brand from end users.
      - Install must include all dependencies (Pi coding agent) automatically.
      - Environment is noisy; work must be low-profile and precise.
      - Defer broad multi-level functionality audit to post-v1.
    assumptions:
      - Pi coding agent is a required dependency for Manastone's agent capabilities.
      - Users are new to Manastone and need clear guidance.
      - Brand independence is achievable without breaking upstream compatibility.
    open_questions:
      - What specific Pi branding currently leaks into the user experience?
      - What is the exact install failure rate or confusion point for new users?
      - How does the OpenClaw-Pi relationship model apply technically?
  omitted_context:
    - Detailed file listings and code snippets not relevant to architecture design.
    - Prior analysis or client rationale beyond scope decisions.
  compression_rationale:
    method: Extracted only the task requirements, scope verdict, and harness constraints; omitted all workspace file details and prior analysis to maintain focus on architecture design.
    loss_notes: []
  quality_checks:
    - name: decision_record_present
      passed: true
    - name: tradeoffs_present
      passed: true
    - name: downstream_constraints_named
      passed: true
```