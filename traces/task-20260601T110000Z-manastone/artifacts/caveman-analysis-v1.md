## Plain-Language Explanation

Manastone = robot brain + body. It lets you talk to a robot, give commands, and get status. Under the hood, it uses another tool called Pi (a chat engine) but you never see Pi. Like OpenClaw hides Pi brand.

Problem: New user installs Manastone, gets confused. Too many parts: install script, Python packages, robot tools, config files. No clear "what do I do now". Also Pi brand leaks in package.json and prompts.

## Minimum Viable Version

1. Install: one command, one pack. No --pack flags. Auto-detect robot or default to X2.
2. First run: after install, print "Manastone ready. Type `manastone` to start." No extra steps.
3. Brand: rename all Pi references to Manastone. Remove `@mariozechner/pi-coding-agent` dependency or wrap it.

## Complexity Assessment

**Unnecessary complexity:**
- Three pack types (dev, g1, x2). New user doesn't care. One pack with all robots.
- `--pack` flag in install.sh. Remove. Auto-detect or default.
- `manastone-dev.toml` separate from customer packs. Merge into one.
- Pi dependency in `pilot/coding-agent/package.json`. This leaks brand and adds install step. Replace with Manastone wrapper or inline.
- `runtime/config.py` placeholder with PR-9 comment. Dead code. Remove or implement.
- `bootstrap/README.md` mentions 7-phase install. Too many phases. Collapse to 3: prereqs, engine, verification.

**Justified complexity:**
- Robot-specific ontology and skills. Different robots need different configs. Keep.
- `roboonto` importers for URDF/AIMDK. Needed for new robot onboarding. Keep.
- `runtime/io/` modules for CLI, TUI, daemon. Different interfaces for different users. Keep.

## Recommendations

1. **Install simplification:** Single `install.sh` with no flags. Auto-detect robot model. If detection fails, install X2 pack (most common).
2. **Brand audit:** Replace all "pi" references in code, docs, package names with "manastone". Remove `@mariozechner/pi-coding-agent` dependency; embed minimal chat engine or wrap with Manastone branding.
3. **First-run experience:** After install, print clear next steps. Add `manastone --help` that lists common commands.
4. **Remove dead code:** Delete `runtime/config.py` placeholder or implement full config loader. Remove `bootstrap/packaging/manastone-dev.toml` if not used.
5. **Documentation:** Update `README.md` with single install command and quickstart. Remove references to Pi.