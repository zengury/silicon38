# Manastone Brand Independence & Install Optimization — Implementation

## Summary

Implemented all four architecture decisions from the architect's ADR:
1. **CLI wrapper brand hiding** — Engine installed to `~/.manastone/engine/`, `manastone-chat` calls engine via wrapper path
2. **Unified install with silent engine** — Single `install.sh` with guided 7-phase experience; engine installed silently
3. **User guidance via doctor + inline help** — `manastone doctor` updated, `GETTING_STARTED.md` created, next-steps in install output
4. **Centralized BRAND constant + audit** — `runtime/constants.py` centralizes brand strings; `scripts/brand_audit.py` gates CI

## Files Changed (10 modified, 2 created)

### Core Brand Infrastructure
| File | Change |
|------|--------|
| `runtime/constants.py` | Added `BRAND="Manastone"`, `ENGINE_DIR`, `ENGINE_BIN` |
| `scripts/brand_audit.py` | **NEW** — Scans for pi brand leaks with severity levels and allowlists |

### Install Script (Critical Path)
| File | Change |
|------|--------|
| `bootstrap/install.sh` | Engine → `~/.manastone/engine/` (silent), `manastone-chat` uses engine path, reordered next steps, better guidance |

### Doctor & CLI
| File | Change |
|------|--------|
| `runtime/io/cli_handlers/doctor.py` | Uses engine path constants, renamed checks, added Engine directory check, removed pi refs |
| `runtime/io/cli.py` | "Pi dialog engine" → "conversation engine" |

### Internal Comment Cleanup
| File | Change |
|------|--------|
| `runtime/brain/_chat.py` | Comments: "pi's native settings" → "engine settings" |
| `runtime/brain/backends/__init__.py` | "pi-subscription" → "engine-subscription" |
| `runtime/io/planner.py` | "pi config" → "engine config" |
| `pilot/apps/diag/launcher.py` | Uses `ENGINE_BIN` path with import fallback |
| `pyproject.toml` | Description: removed "Pi + Runtime"; cleaned X2 comment |

### User Guidance
| File | Change |
|------|--------|
| `GETTING_STARTED.md` | **NEW** — Quick start with command reference, config info, troubleshooting |

## Verification Results
- **Brand audit**: 0 findings — PASSED
- **Tests**: 98 passed, 1 skipped — PASSED
- **Shell syntax**: `bash -n install.sh` — OK
- **Python imports**: All modified modules compile and import correctly

## Design Rationale
- **Engine path (`~/.manastone/engine/`)**: Follows openclaw/pi relationship pattern; engine is a hidden dependency
- **`ENGINE_BIN` constant**: Single point of truth for the binary path; if pi changes its CLI, only constants.py needs updating
- **Brand audit allowlists**: Recognizes immutable external facts (`@mariozechner/pi-coding-agent` in package.json) while flagging user-facing leaks
- **Doctor engine check**: Checks `~/.manastone/engine/` path instead of global `which pi`; matches new install location
- **Silent install**: `npm install --prefix` with `> /dev/null 2>&1`; error messages reference "conversation engine" not package name

## Known Limitations
- `manastone-chat` still execs the engine binary (`pi`) but from the hidden path — the engine's own output may still contain pi branding (this is an upstream concern)
- Legacy `~/.pi/agent/settings.json` fallback remains in `_chat.py` and `launcher.py` for backward compatibility with existing installs
- `pilot/coding-agent/package.json` retains `"pi"` JSON key and `@mariozechner/pi-coding-agent` dependency — external API facts that cannot change