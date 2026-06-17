# Encoder — Task Intake Protocol

The Encoder is the first action the Runtime takes on any task.
It does two things only: parse the task, initialize the ledger.

---

## Task Type → Entry Node Mapping

Entry nodes are **Layer 1 only**. Layer 2 and Layer 3 nodes are never selected
by the Encoder; they become eligible only after a completed predecessor writes
an artifact and a handoff that matches `ontology/relations.yaml`.

```
TASK TYPE          ENTRY NODE(S)                        RATIONALE
───────────────────────────────────────────────────────────────────────────────
bug_fix            triage                               classify severity/scope first
feature            to-prd + scope-prosecutor            scope-prosecutor blind-attacks requirements
                                                        in parallel; to-prd triggers
                                                        product-vision-anchor via graph
  + unknown scope  triage + to-prd + scope-prosecutor   triage classifies; scope-prosecutor attacks
  + UI/UX          to-prd + scope-prosecutor            same; product-vision-anchor triggers
                                                        ux-researcher-designer via graph
  + complex/multi  to-prd + scope-prosecutor + caveman  caveman simplifies framing;
                                                        scope-prosecutor cuts scope;
                                                        all three are blind to each other
refactor           zoom-out                             map impact before touching code
  + arch debt      zoom-out + caveman                   caveman finds what to cut first
architecture       zoom-out                             zoom-out triggers architect via graph
  + unknown scope  triage + zoom-out                    classify first, then map
design             to-prd + scope-prosecutor            scope before design; product-vision-anchor
                                                        triggers ux-researcher-designer via graph
  + complex/multi  to-prd + scope-prosecutor + caveman  full product intake before design begins
ops/infra          triage                               classify before execution
security audit     triage                               classify security scope before execution
docs               grill-with-docs                      research existing docs first
release            to-issues                            decompose release tasks before release-manager
ambiguous          triage                               always triage when unclear
complex/multi-part triage + caveman + scope-prosecutor  classify + simplify + cut scope in parallel
```

**scope-prosecutor packaging rule**: always blind — receives raw requirements only,
never to-prd output or prior analysis. This is the structural guarantee of independence.
scope-prosecutor and to-prd run in parallel in Wave 1; product-vision-anchor runs in
Wave 2 (same Layer 1) after both complete.

Note: ops/infra, security audit, and release previously mapped directly to Layer 2/3
nodes. These are now routed through Layer 1 so the intake layer can scope the work
before execution begins.

---

## Ledger Initialization

```bash
TASK_ID="task-$(date +%Y%m%dT%H%M%S)-$(head -c4 /dev/urandom | xxd -p)"
python tools/ledger.py init "$TASK_ID" "<task_type>" "<one sentence summary>"
```

The random suffix guards against collisions when two tasks start in the same
second. This format must match `org/RUNTIME.md` Phase 0.2.

The ledger command writes the three ledger files per the schemas in:
- `ontology/artifact_ledger.yaml` (TaskManifest, EventStream)
- `ontology/task_graph_state.yaml` (TaskGraphState)

---

## What the Encoder Does Not Do

- Does not decide which Layer 2 or Layer 3 nodes will run
- Does not route between nodes
- Does not pre-activate downstream candidates from the deliverable list
- Does not synthesize outputs
- Does not make implementation decisions

## Encoder Output

1. An initialized task ledger on disk
2. The first `node_activated` event(s) in `events.yaml`
3. `entry_nodes` populated in `manifest.yaml`
