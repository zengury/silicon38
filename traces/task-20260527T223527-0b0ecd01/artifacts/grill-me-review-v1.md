# Grill-Me Review: Three.js Silicon Org Visualizer

## Target

PRD, architecture, and UX artifacts for the Three.js Silicon Org operations
visualizer:

- `to-prd-prd-v1`
- `architect-architecture-v1`
- `ux-researcher-designer-ux-spec-v1`

## Verdict

ISSUES_TO_ADDRESS

The direction is sound: all three artifacts preserve the core Silicon Org model
and repeatedly protect Ledger as source of truth. The risk is not conceptual
collapse. The risk is that a visually ambitious interface ships before it can
prove three boring but load-bearing facts:

1. it never presents stale or incomplete trace state as a finished run;
2. it verifies context-block and digest integrity rather than merely displaying
   digest-looking strings;
3. it has a default operational view that explains causality before spectacle.

These are fixable before implementation, but they should be treated as required
changes because the visualizer will become the user-facing explanation of how
Silicon Org works.

## Challenge Tree

| Severity | Assumption | Failure Condition | Evidence Needed | Resolution |
|---|---|---|---|---|
| CRITICAL | A selected trace can safely drive the live/replay view. | The current trace is shown as a complete demo even though `manifest.timestamp_end` and `manifest.outcome` are null, `state.task_status` is `propagating`, and downstream nodes including `grill-me` are only `activated`. | Snapshot contract exposes `run.completeness`, `convergence`, `staleness_age`, and incomplete-node counts; UI visibly labels "in progress / not converged / stale". | Required change. Do not allow "canonical demo" status unless the trace is delivered/converged, or explicitly mark it as an in-progress trace replay. |
| MAJOR | Source references are enough to protect context-block truth. | The inspector displays context digests and previous block digests, but the adapter does not define verification of digest chains or mismatch states as durable normalized data. | Adapter returns per-handoff `digestVerification: verified | missing | mismatch | not_checked` with checked refs and computed digests. | Required change. Digest integrity belongs in the adapter/Policy boundary, not in visual styling. |
| MAJOR | The first viewport can show all five surfaces plus 35 nodes and 122 edges without hiding causality. | Operators see a beautiful graph but cannot answer "why did this node activate?" within seconds because all edges, zones, rails, blocks, and halos compete at once. | UX default mode prioritizes the active run path, active candidates, and selected evidence chain; global graph and learning halos are dimmed until requested. | Required change. Add an "operator default" level-of-detail rule before frontend implementation. |
| MAJOR | Handoff block animation accurately represents transfer semantics. | A handoff file exists, but the UI animates it as "received" or causally consumed without a corresponding event/state fact. Current `events.yaml` has activation and completion events but no explicit `handoff_created` events. | Snapshot schema distinguishes `file_present`, `created_event_seen`, `received_or_consumed`, and `animated_for_replay`. | Required change. Blocks can animate from file timestamps, but the inspector must show which parts are factual and which are replay reconstruction. |
| MAJOR | Verification is covered by acceptance criteria. | AC11 says browser verification confirms desktop/mobile and nonblank canvas, but architecture does not specify Playwright, canvas pixel checks, count assertions, or source-truth assertions. | Delivery-prover checklist: graph count assertion, nonblank canvas pixel sampling, desktop/mobile screenshots, no overlap on critical panels, no invented run facts, reduced-motion check. | Required change. Make verification a concrete gate, not prose. |
| MAJOR | Read-only local viewer avoids security review. | Architecture skips security because v1 is local/read-only, but the proposed API exposes artifact content and trace files over HTTP. Binding to `127.0.0.1` helps, but path traversal and arbitrary artifact reads still matter. | API contract rejects path traversal, only serves refs registered in manifest/state, and redacts or labels missing/untrusted artifact paths. | Required change or re-activate security-engineer if the server serves file contents beyond generated snapshots. |
| MAJOR | Learning can be shown as a halo without becoming a false authority. | Weight deltas or proposals may look like current Policy truth, especially if rendered around active edges during a run. | Learning surface is off by default during live/replay, clearly marked "proposal/history", and linked to source signal/outcome only. | Advisory but important. PRD/UX already state this; implementation should encode it as default UI behavior. |
| MINOR | Five named zones are enough to teach the concept model. | New contributors may confuse Graph files, Ledger trace files, Policy gates, Runtime spine, and Learning halo as five physical systems rather than one operational loop. | One compact loop diagram or guided first-run overlay that maps Graph + Ledger -> Policy -> Runtime -> Ledger -> Learning. | Advisory. Keep it lightweight; do not add a landing page. |

## Required Changes

1. Add trace completeness to the snapshot contract.

   Required fields:

   ```ts
   type RunCompleteness = {
     taskStatus: "propagating" | "converged" | "delivered" | "failed" | "unknown";
     outcome: string | null;
     timestampEnd: string | null;
     activeNodes: string[];
     incompleteNodes: string[];
     unresolvedCandidates: number;
     staleAgeMs: number | null;
     sourceRefs: string[];
   };
   ```

   The current task trace must render as in-progress because its manifest has
   `timestamp_end: null`, `outcome: null`, and state has multiple activated
   incomplete nodes.

2. Make digest verification an adapter responsibility.

   The UI may display digest chains, but it should not imply integrity unless
   the adapter computed and returned verification status. The UX already says
   "not checked" is valid when verification cannot run; the architecture needs
   to make this explicit in schema and adapter phases.

3. Define an operator-default level-of-detail.

   First render should emphasize:

   - current active path;
   - active candidates and gates;
   - recent handoff blocks;
   - selected evidence chain;
   - incomplete or blocked nodes.

   Full 35-node/122-edge topology remains available, but context-only edges and
   learning halos should not compete with the active causal route by default.

4. Distinguish factual handoff state from replay reconstruction.

   A handoff file proves a handoff record exists. It does not by itself prove a
   live "block is currently in motion" or "target consumed it." Snapshot fields
   should separate file facts, event facts, and UI reconstruction.

5. Turn browser verification into a delivery gate.

   Add a delivery-prover or frontend acceptance checklist with:

   - YAML graph count equals rendered node/edge count;
   - canvas is nonblank by pixel sampling;
   - desktop and mobile screenshots show no critical overlap;
   - clicking node, edge, handoff block, and timeline event opens the right inspector;
   - reduced-motion mode disables continuous pulse/flight animation;
   - no operational fact appears without a source ref or "not recorded" label.

6. Reconsider the skipped security path if artifact file serving is included.

   A local read-only server is still a file server. If `/api/runs/:task_id/artifacts/:artifact_id`
   returns file contents, restrict it to manifest-registered refs and reject path
   traversal. If this is not handled by senior-engineer/api-designer, reactivate
   security-engineer.

## Advisory Changes

- Keep demo mode, replay mode, and live mode visually distinct. A generated demo
  fixture must never look like Ledger truth from an actual run.
- Delay polish-heavy effects until the snapshot adapter proves source refs,
  digest status, and replay reconstruction.
- Add a compact "why active?" path overlay for each active node: predecessor,
  relation type, handoff ref, activation_decision event, artifact refs.
- Treat `ontology/` only as a source path in UI copy; labels should say Graph,
  not Ontology.
- Keep LangGraph hidden behind Runtime or source adapters. The UI should never
  imply LangGraph is the organizational brain.

## Branches Resolved

- Core model preservation: resolved. PRD, architecture, and UX all preserve
  Graph, Policy, Ledger, Runtime, and Learning as primary concepts.
- Context-only edge semantics: resolved at artifact level. All three artifacts
  explicitly distinguish activation-capable edges from context-only relations.
- Ledger source of truth: resolved directionally. All artifacts state that the
  visualizer is a projection, not a source of truth.
- Three.js suitability: resolved. Spatial layout is justified by handoff blocks,
  typed edges, policy gates, and replay, not by visual novelty alone.
- LangGraph boundary: resolved. Architecture keeps LangGraph optional and
  subordinate to Ledger-derived facts.

## Open Questions

- Which trace becomes the canonical demo fixture? Owner: architect/prototype.
  Blocks: demo truth labeling and replay acceptance.
- Will artifact content be served over HTTP or only metadata? Owner:
  api-designer/senior-engineer. Blocks: whether security-engineer must be
  reactivated.
- Will digest verification run in the adapter for v1 or be marked `not_checked`
  until later? Owner: senior-engineer. Blocks: integrity claims in the block
  inspector.

## Recommended Next Move

Reactivate or route feedback to `architect`, `ux-researcher-designer`, and
`prototype` for a small v2 pass before senior-frontend begins final
implementation:

- architect: add trace completeness, digest verification, handoff fact/replay
  distinction, and local API file-safety constraints;
- ux-researcher-designer: add operator-default level-of-detail and mode labels;
- prototype: prove source-truth replay with one incomplete trace and one
  completed/delivered fixture.

## Completion Report

```yaml
completion_report:
  what_was_done: >
    Stress-tested the PRD, architecture, and UX artifacts for the Three.js
    Silicon Org visualizer, focusing on operational clarity, stale trace facts,
    context-block integrity, UI complexity, verification, and preservation of
    the Silicon Org conceptual model.
  key_decisions:
    - decision: "Verdict is ISSUES_TO_ADDRESS rather than ROBUST."
      rationale: "The concept is sound, but trace completeness, digest verification, handoff fact semantics, and concrete visual verification must be tightened before implementation."
    - decision: "Treat stale/incomplete trace labeling as critical."
      rationale: "The visualizer is an explanation of Silicon Org truth; showing a propagating trace as complete would undermine Ledger trust."
    - decision: "Require operator-default level-of-detail."
      rationale: "A full 35-node/122-edge 3D scene can become spectacle unless the default view prioritizes active causal paths and evidence."
    - decision: "Require concrete delivery verification."
      rationale: "Three.js scenes often fail as blank, overlapped, or inaccessible canvases unless browser and pixel checks are explicit."
  handoff_focus:
    - "Architect should add trace completeness, digest verification, replay/fact boundaries, and local API file-safety constraints."
    - "UX should add default LOD and explicit mode labels for demo, replay, and live."
    - "Prototype/delivery-prover should verify nonblank canvas, responsive layout, source refs, and inspector interactions."
  open_questions:
    - "Which trace becomes the canonical demo fixture?"
    - "Will artifact content be served over HTTP or only metadata?"
    - "Will digest verification be implemented in v1 or surfaced as not_checked?"
  known_constraints:
    - "Graph, Policy, Ledger, Runtime, and Learning remain the only top-level concepts."
    - "Ledger facts are source of truth; private runtime reasoning is not displayable fact."
    - "Context-only relations cannot activate nodes."
    - "The current trace is propagating and cannot be represented as a completed run."
  confidence_differential: 0.12
  dissent_if_alone: "Do not let the first frontend implementation start from visual polish; start from trace completeness, digest integrity, and evidence-backed replay."
  iteration_context: "Grill-me evaluation node for task-20260527T223527-0b0ecd01."
```
