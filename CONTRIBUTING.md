# Contributing to Silicon Org

Thanks for your interest in improving Silicon Org — *Dynamic Workflow, with a
harness*. This project is agent-agnostic (Claude Code, Codex, Cursor, pi, or any
coding agent becomes the Runtime), so contributions should keep the harness
honest, the ontology consistent, and the audit green.

## Project layout

| Path | What lives there |
|------|------------------|
| `org/` | Runtime protocol, harness spec, and the 41-role registry (`org/registry/<role>.md`) |
| `ontology/` | The graph — `nodes.yaml` (roles) and `relations.yaml` (typed edges) |
| `runtime/` | LangGraph-native execution kernel |
| `tools/` | Integrity gates and runners (`audit.py`, `langgraph_native_smoke.py`, `org_system_validation.py`, `langgraph_run.py`) |
| `learning/` | Routing weights + Thompson Sampling |
| `docs/` | Design doctrine, specs, ADRs |
| `.agents/skills/` | Pre-packaged role skills (`<role>/SKILL.md`) |
| `visualizer/` | Offline local 3D visualizer (vendored deps, no build step) |

## Adding a role (the 4–5 file protocol)

The library is curated, not closed. Adding a role touches a fixed set of files —
see `org/REGISTRY.md`'s **Expansion Protocol** for the authoritative version:

1. **Skill** — `.agents/skills/<role>/SKILL.md` (a real, usable skill, not a skeleton)
2. **Harness profile** — `org/registry/<role>.md`, following the schema in `org/HARNESS.md`
3. **Ontology node** — an entry in `ontology/nodes.yaml` with a real `skill_ref`
4. **Edges** — activation-capable or context-only edges in `ontology/relations.yaml`
5. **Registry entry** — a row in `org/REGISTRY.md` with domain, title, and trigger summary

Then run `python tools/audit.py` and fix any reachability or skill-reference
issues it reports. Keep the counts consistent: role count, typed-edge count,
and skill count are asserted across the graph and surfaced in `README.md`.

## Running the checks locally

Install the optional LangGraph-native runtime and run the three gates:

```bash
python -m pip install -e '.[langgraph-oss]'

python tools/audit.py                    # graph + file + runtime-contract + skill audit
python tools/langgraph_native_smoke.py   # native runtime smoke test
python tools/org_system_validation.py    # org system validation
```

`tools/audit.py` prints `VALID`/`INVALID` and **exits nonzero on failure** — it
is the primary integrity gate. All three run in CI on every push and pull
request (see `.github/workflows/ci.yml`), and **all CI checks must pass** before
a change can merge.

## Commit and PR conventions

- Keep commits focused and self-describing; explain *why*, not just *what*.
- One logical change per pull request. If you add a role, include all 4–5 files
  in the same PR so the audit stays green at every commit.
- Fill in the pull-request template (`.github/PULL_REQUEST_TEMPLATE.md`),
  including how you verified the change (audit / smoke / validation).
- Do not hand-edit generated traces under `traces/`.
- By contributing you agree your work is licensed under the project's
  [MIT License](LICENSE).

## Getting help

Open an issue at <https://github.com/zengury/silicon38/issues> using the bug
report or feature request template. For design context, start with
[`README.md`](README.md), then `AGENTS.md` and `org/RUNTIME.md`.
