# Scope Prosecution — Collaborative Document Editor

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
