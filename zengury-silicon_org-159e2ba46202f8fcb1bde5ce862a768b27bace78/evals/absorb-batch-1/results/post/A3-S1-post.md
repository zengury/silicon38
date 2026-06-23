# Scope Prosecution — Collaborative Document Editor (POST-ABSORB)

## Perspective Archetype: Adversary
Every feature on this list is guilty until proven innocent. Prosecute each one.

---

## Verdict Table

core_statement: This product exists to let multiple people write and edit a shared document together in real time — everything else is packaging.

feature_verdicts:
  - feature: Real-time collaborative editing (multiple cursors)
    verdict: KEEP
    reason: This is the product — without simultaneous multi-user editing, you have a file-sharing tool, not a collaborative editor.

  - feature: Rich text formatting (bold, italic, headers, lists)
    verdict: KEEP
    reason: Documents without structure are notes; structure is the minimum viable definition of a document.

  - feature: Document version history with restore
    verdict: DEFER
    reason: Valuable, but users can recover from mistakes via undo in v1; full version history is a trust-building feature for v2 once users have data worth protecting.

  - feature: Comments and inline annotations
    verdict: DEFER
    reason: Commenting is a separate collaboration mode (async review) that competes with the real-time editing mode for UI space and product clarity; defer until the core editing loop is proven.

  - feature: Offline mode with sync on reconnect
    verdict: CUT
    reason: Offline sync is an order-of-magnitude engineering complexity multiplier that serves an edge case — real-time collaboration requires connectivity by definition, and v1 users will accept a connectivity requirement.

  - feature: Export to PDF and DOCX
    verdict: CUT
    reason: Export serves a handoff workflow, not collaboration; it is a distribution feature that belongs after the creation problem is solved and can be shipped as a follow-on at negligible cost.

  - feature: Mobile app (iOS and Android)
    verdict: CUT
    reason: Native mobile apps double the codebase surface, require separate release pipelines, and v1 collaborative editing is a keyboard-and-cursor experience that a responsive web app serves adequately.

  - feature: Access control (owner, editor, viewer roles)
    verdict: KEEP
    reason: Without permission boundaries, the product cannot be shared safely with anyone outside a trusted group, which blocks the core use case.

kept_count: 3
cut_count: 3
deferred_count: 2
scope_reduction_summary: Strip to real-time co-editing with basic formatting and access control; cut offline, export, and mobile entirely, and defer history and comments until the editing loop has validated users.

---

## Assumption Risk Map

### KEEP 1 — Real-time collaborative editing (multiple cursors)

**Assumption A:** Operational Transformation or CRDT library behavior is predictable enough under concurrent edits that the team does not need to build a custom conflict-resolution algorithm.
Risk: HIGH
Rationale: The choice of sync algorithm (e.g., Yjs, Automerge, ShareDB) determines whether concurrent edits produce coherent documents or silent data corruption. Most teams underestimate edge cases — nested formatting, deletions at identical offsets — that only surface under real concurrent load. The team is betting that an off-the-shelf library handles their document model without bespoke tuning.
Flag: **Route to product-vision-anchor.** Before the implementation sprint, prototype with target library under concurrent-edit stress (3+ simultaneous users, overlapping edits on the same paragraph). Treat any data-corruption edge case as a blocker.

**Assumption B:** WebSocket infrastructure can sustain the expected concurrent session count at acceptable cost.
Risk: MEDIUM
Rationale: Real-time sync is stateful — each open document requires a persistent connection on a server that holds document state. Horizontal scaling is non-trivial and connection costs grow linearly with concurrent users. This assumption is medium rather than high because it is an operational risk that can be managed with load testing before launch.

---

### KEEP 2 — Rich text formatting (bold, italic, headers, lists)

**Assumption A:** The chosen rich-text editor component integrates cleanly with the real-time sync layer without requiring a custom document model.
Risk: HIGH
Rationale: Rich text state (marks, nodes, nested lists) must be represented in the CRDT or OT data structure. If the editor library (e.g., ProseMirror, TipTap, Quill) uses an opaque internal model, bridging it to the sync layer often requires either forking the editor or building a translation layer — both of which are significant unplanned scope.
Flag: **Prototype before implementation sprint.** Validate that formatting operations on the chosen editor can be serialized into the sync layer's operation format before committing to the stack.

---

### KEEP 3 — Access control (owner, editor, viewer roles)

**Assumption A:** Role enforcement can be implemented server-side at the document API boundary without requiring a dedicated authorization service.
Risk: MEDIUM
Rationale: For v1 with three roles, a simple join table (document_id, user_id, role) enforced in API middleware is sufficient. The risk is that the team underestimates the number of permission-check callsites and ships inconsistent enforcement — some endpoints checking roles, others not.

**Assumption B:** Users will self-manage sharing without an invitation email flow in v1.
Risk: MEDIUM
Rationale: If sharing requires pasting a user ID or email with no notification, adoption of the access-control system drops to near zero in practice — users will share public links instead, bypassing the permission model entirely. The team is betting that a minimal invite UX is sufficient; if users route around it, the access-control feature provides no real protection.
