# Architecture Decision Record: Manastone Install & Brand Independence Optimization

## Context

Manastone is a robot agent platform that lets users control and diagnose robots via natural language, with a single install command and zero configuration. The scope-prosecutor has validated 14 features as KEEP, 3 as DEFER, and 1 as CUT. The core constraints are:
- Must hide pi brand and present Manastone as independent.
- Install must include all dependencies (pi coding agent).
- User guidance must be optimized for clarity.

The existing codebase has a bootstrap/install.sh with 7 phases, a runtime/io layer with CLI/TUI/MCP, and a roboonto ontology system. The pi coding agent is a dependency that must be silently installed and brand-hidden.

## Decision: Brand Independence via Wrapper Layer

**Decision**: Introduce a `manastone` CLI wrapper that intercepts all user-facing commands and presents Manastone branding. The pi coding agent is installed as a hidden dependency under `~/.manastone/engine/` and is never exposed to the user.

**Rationale**:
- The pi coding agent provides the conversation engine but must be invisible. A wrapper layer ensures all user touchpoints (CLI, TUI, logs, error messages) show Manastone.
- The wrapper is thin and does not modify pi internals, making upgrades safe.
- This pattern is proven by openclaw/pi relationship.

**Alternatives Considered**:
1. Fork pi and rebrand internally — rejected due to maintenance burden and upgrade complexity.
2. Use environment variables to hide pi — rejected because it doesn't cover all touchpoints (logs, errors).
3. No wrapper, just rename — rejected because pi's own CLI would still show its brand.

**Consequences**:
- Positive: Clean separation, easy to audit brand touchpoints, pi upgrades are independent.
- Negative: Slight indirection in command execution; must ensure wrapper passes all arguments correctly.
- Risk: If pi changes its CLI interface, wrapper may need updates.

## Decision: Unified Install Script with Dependency Bundling

**Decision**: The `bootstrap/install.sh` script will be the single entry point. It will:
- Install pi coding agent silently to `~/.manastone/engine/` (phase 2).
- Install Manastone Python package with robot-specific extras (phase 3).
- Register robot tools with the engine (phase 4).
- Create launcher scripts `manastone-chat` and `manastone-launcher` (phase 5).
- Auto-detect robot model and write config (phase 6).
- Run verification including `manastone doctor` (phase 7).

**Rationale**:
- Single command reduces user confusion.
- All dependencies are bundled, no separate steps.
- Phased approach gives feedback during install.

**Alternatives Considered**:
1. Separate install steps for pi and Manastone — rejected because it increases user confusion.
2. Docker-based install — rejected because it adds complexity and hides the robot interaction.
3. Package manager (apt/brew) — rejected because it's not cross-platform enough.

**Consequences**:
- Positive: Simple, guided experience.
- Negative: Script must handle multiple OSes and robot models; error handling must be robust.
- Risk: If pi changes its install method, script must be updated.

## Decision: User Guidance via `manastone doctor` and Inline Help

**Decision**: After install, the primary guidance is:
- `manastone doctor` — comprehensive health check (already exists in runtime/io/cli_handlers/doctor.py).
- `manastone --help` — shows available commands.
- `manastone-chat` — launches the chat interface with a welcome message.
- A `GETTING_STARTED.md` in the repo root, also displayed on first run.

**Rationale**:
- Users need immediate feedback on install success and how to proceed.
- `manastone doctor` is already implemented and can be extended.
- Inline help is always available without reading docs.

**Alternatives Considered**:
1. Separate documentation website — rejected because users may not visit it.
2. Video tutorial — rejected because it's hard to maintain.
3. Interactive wizard — rejected because it's overkill for a CLI tool.

**Consequences**:
- Positive: Low friction, always available.
- Negative: Must keep help text and doctor checks up to date.

## Decision: Brand Audit via Centralized Brand Constants

**Decision**: All user-facing strings (CLI descriptions, error messages, log prefixes, TUI titles) will reference a single `BRAND` constant in `runtime/constants.py`. A script `scripts/brand_audit.py` will scan the codebase for any remaining pi references and flag them.

**Rationale**:
- Centralized brand string makes rebranding trivial.
- Audit script ensures no pi brand leaks.

**Alternatives Considered**:
1. Manual search — rejected because it's error-prone.
2. Pre-commit hook — rejected because it's too early; audit script is sufficient for now.

**Consequences**:
- Positive: Easy to maintain brand consistency.
- Negative: Must remember to use the constant in new code.

## Data Flow

1. User runs `bash bootstrap/install.sh`.
2. Script installs pi engine to `~/.manastone/engine/` (hidden).
3. Script installs Manastone Python package via pip.
4. Script creates `~/.manastone/config.yaml` with robot model.
5. Script creates launcher scripts in PATH.
6. User runs `manastone-chat` → wrapper calls pi engine with Manastone branding.
7. All CLI output goes through `runtime/io/cli.py` which uses BRAND constant.
8. `manastone doctor` checks engine, config, robot connection.

## Failure Modes

- **Pi engine install fails**: Script should print "Engine installation failed. Check network." and exit non-zero.
- **Robot detection fails**: Script should print "Could not auto-detect robot. You can manually set model in ~/.manastone/config.yaml." and continue.
- **Launcher script creation fails**: Script should warn but not block.
- **Manastone doctor fails after install**: Should print specific error and suggest reinstall.

## Downstream Constraints

- **senior-engineer**: Must implement the CLI wrapper and update install script.
- **api-designer**: Must ensure all API responses use BRAND constant.
- **database-engineer**: No database changes needed.

## Completion Report

```yaml
completion_report:
  what_was_done: Designed architecture for Manastone install optimization, brand independence, and user guidance. Produced ADR with four key decisions: wrapper layer for brand hiding, unified install script, doctor-based guidance, and centralized brand constants.
  key_decisions:
    - decision: Introduce manastone CLI wrapper to hide pi brand
      rationale: Clean separation, easy audit, safe pi upgrades
    - decision: Single install script bundles all dependencies
      rationale: Reduces user confusion, single entry point
    - decision: User guidance via manastone doctor and inline help
      rationale: Always available, low friction
    - decision: Centralized BRAND constant in runtime/constants.py
      rationale: Easy brand consistency, audit script catches leaks
  handoff_focus:
    - Implement CLI wrapper in runtime/io/cli.py
    - Update bootstrap/install.sh to install pi silently
    - Create brand_audit.py script
    - Extend manastone doctor checks
  open_questions:
    - What specific user guidance materials are needed beyond the install script?
    - How will brand independence be audited across all touchpoints?
  known_constraints:
    - Must hide pi brand and present Manastone as independent
    - Install must include all dependencies (pi coding agent)
    - User guidance must be optimized for clarity
    - Internal build tools and daemon deployment are deferred to v1.1
  confidence_differential: 0.85
  dissent_if_alone: null
  iteration_context: null
```