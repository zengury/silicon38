## Triage Analysis

### Problem Statement
New users of manastone face a fragmented installation experience where the Pi coding agent brand leaks into the user interface, dependencies are not bundled, and the multi-layered functionality (bootstrap, runtime, roboonto, pilot) lacks clear guidance on how to install and use the terminal effectively, leading to confusion and low adoption.

### Scope
**In Scope:**
- Audit of all user-facing references to "pi" branding in installation scripts, READMEs, CLI help, and config files.
- Audit of dependency bundling in bootstrap/install.sh and pyproject.toml to ensure all required dependencies (including pi coding agent) are installed by default.
- Review of user onboarding flow: from first install to first successful robot control command.
- Identification of missing or unclear documentation for terminal-based usage.
- Recommendations for brand independence (manastone as primary brand, pi as internal dependency).

**Out of Scope:**
- Code changes or implementation of fixes (this is triage only).
- Changes to internal architecture or module structure.
- Performance optimization or bug fixes unrelated to onboarding.
- Redesign of the CLI or TUI interface.
- Changes to the Pi coding agent upstream.

### Recommended Agents
- `brand-audit-agent` — for systematic brand reference scanning and replacement planning.
- `install-experience-agent` — for improving bootstrap scripts and dependency management.
- `docs-agent` — for writing clear onboarding guides and CLI help text.

### Blocking Questions
- What is the exact list of dependencies that should be bundled by default? (Need to confirm with maintainer: should all optional dependency groups like `engineer`, `x2`, `g1`, `dev` be included?)
- Is there a preferred strategy for hiding pi branding? (e.g., rename packages, use aliases, or fork?)
- What is the target user persona for the "new user" experience? (Developer, robot operator, or both?)

### Priority
**High** — Brand confusion and poor onboarding directly impact user adoption and first-impression quality. The issue touches the core user experience and is a prerequisite for any future growth.

---

## Completion Report

**what_was_done:** Performed triage on the manastone repository to classify the task of comprehensive optimization focusing on user onboarding, brand independence, and installation experience. Produced a structured work item with problem statement, scope, recommended agents, and blocking questions.

**key_decisions:**
- decision: Classified as an enhancement (not a bug) because nothing is broken; the issue is about improving user experience and brand clarity.
- rationale: The repository is functional; the request is to make it more accessible and coherent for new users.
- decision: Recommended three specialized agents (brand-audit, install-experience, docs) rather than a single generalist agent.
- rationale: The task has three distinct facets that benefit from focused expertise.

**handoff_focus:**
- Confirm blocking questions with maintainer before proceeding.
- Assign brand-audit-agent to scan all user-facing files for pi references.
- Assign install-experience-agent to review bootstrap/install.sh and pyproject.toml dependency bundling.
- Assign docs-agent to draft onboarding documentation.

**open_questions:**
- Exact list of default dependencies to bundle.
- Preferred strategy for hiding pi branding.
- Target user persona for onboarding.

**known_constraints:**
- Cannot modify upstream Pi coding agent; only manastone-side changes are possible.
- Must maintain compatibility with existing users who may rely on pi branding references.
- The repository has a large file count (244+ files); scanning must be systematic.

**confidence_differential:** 0.85

**dissent_if_alone:** null

**iteration_context:** null

---

## Context Compression Report

```yaml
context_compression_report:
  input_scope:
    artifacts_read:
      - /Users/ZQ/manastone/manastone/bootstrap/README.md
      - /Users/ZQ/manastone/manastone/pilot/coding-agent/package.json
      - /Users/ZQ/manastone/manastone/pyproject.toml
      - /Users/ZQ/manastone/manastone/runtime/config.py
    handoffs_read: []
  retained_context:
    decisions:
      - Task is an enhancement, not a bug.
      - Three specialized agents recommended.
    constraints:
      - Cannot modify upstream Pi coding agent.
      - Must maintain backward compatibility.
      - Large repository requires systematic scanning.
    assumptions:
      - The maintainer wants manastone to be the primary brand, with pi as an internal dependency.
      - New users are expected to install via bootstrap/install.sh.
      - The current installation does not bundle all necessary dependencies.
    open_questions:
      - Exact list of default dependencies.
      - Preferred brand-hiding strategy.
      - Target user persona.
  omitted_context:
    - Detailed file contents of non-key files (e.g., test fixtures, examples, skills) as they are not directly relevant to the triage scope.
    - Internal architecture details of roboonto and runtime beyond what is needed for scope definition.
  compression_rationale:
    method: Relevance filtering — retained only files and information directly related to user-facing installation, branding, and onboarding. Omitted internal implementation details and robot-specific configurations.
    loss_notes:
      - Skipped detailed analysis of roboonto/core and roboonto/skills as they are not user-facing.
      - Skipped test files and fixtures as they do not impact installation or branding.
  quality_checks:
    - name: scope_boundary_present
      passed: true
    - name: done_condition_present
      passed: true
```