# Prototype: Robot Management Refactor — Form Design Exploration

## Question Answered

**"Can we build a shared component library for admin and portal, and does progressive disclosure on the robot creation form actually reduce perceived complexity for operators?"**

## Finding

### Shared Components: FEASIBLE with current architecture

Both admin and portal use Vue 3 + Element Plus + TypeScript. The pnpm workspace already supports `workspace:*` dependencies. A `@roboease/shared` package under `frontend/shared/` already exists with HTTP client, auth, and token storage — proving the extraction pattern works. Adding UI components (StatusBadge, table wrappers, composables) follows the same pattern.

**Priority extraction order:** types → composables (usePagination, useDialog) → simple UI components (StatusBadge, SearchBar) → complex components (DataTable, CURD).

**Risk:** Admin uses UnoCSS while portal uses scoped SCSS → shared components must avoid framework-specific styling or ship their own scoped styles.

### Progressive Disclosure: ACCORDION variant is the strongest candidate

Three form-design variants were built, all shareable via `?variant=` URL param and a floating bottom bar:

| Variant | Visible Fields | Strengths | Weaknesses |
|---------|---------------|-----------|------------|
| **Baseline** (current) | 8 at once | Familiar, fast for experts | Overwhelming for new operators; no guidance |
| **Step Wizard** | 2-3 per step | Good for first-time creation; clear progress | Adds friction for edits (must click through all steps); over-engineered for experienced users |
| **Accordion Panels** | 1 group at a time | Users see full structure but focus on one group; panel badges show completion; experts can expand all; natural grouping with field hints | Slightly more markup than baseline |

**The Accordion variant strikes the best balance:**
- Groups fields into logical sections (Basic Info → Connection → Type Config)
- Each panel shows a completion badge (✓ / 待填写)
- Progress bar summarizes overall completion
- Experienced operators can expand all panels; new operators get progressive guidance
- Field-level hints reduce mistakes without adding clutter

## What This Prototype Does NOT Tell Us

- Whether the accordion pattern works for robot types with >3 field groups (tested with 3 groups)
- Performance impact of shared package at scale (no complex components extracted)
- Whether the accordion pattern translates well to mobile/tablet (desktop-only)
- Backend API compatibility with new form structure (mock data)
- Whether field hints actually reduce operator errors (needs usability test)
- How the robot config drawer should be redesigned
- Whether portal can meaningfully reuse admin-extracted components beyond StatusBadge

## Recommended Next Step: PROCEED

1. Extract `@roboease/shared` package with types + StatusBadge first (lowest risk, highest reuse)
2. Implement accordion-based form for robot creation/edit in admin
3. Usability test the accordion form with 3-5 operators before wider rollout
4. Keep wizard variant as an option for first-time robot onboarding flows
5. Apply shared components to portal after admin validation

## Shortcuts Taken (Labeled)

- [HARDCODED] All form data is in-memory mock — no API calls
- [HARDCODED] Form validation is minimal (name + code required)
- [HARDCODED] Shared package has stub components only (not production-ready)
- [NO_ERROR_HANDLING] No error states beyond happy-path demo needs
- [HARDCODED] Variant picker floating bar is debug-only UI
- [HARDCODED] State inspector is debug-only — exposes internal state
- [HARDCODED] 6 mock robots hardcoded in the list

## Throwaway Boundary

This entire `__prototype__/` directory is throwaway code. The only durable artifact is this finding. The directory should be deleted after the design decision is recorded (ADR, issue, or commit message).

The `frontend/shared/src/components/` and `composables/` stubs may be kept as scaffolding for real implementation, but must be rewritten to production quality.

## Demo Path (How to Run)

```bash
cd frontend/admin && pnpm dev
# Visit http://localhost:5173/#/robot-prototype?variant=baseline
# Click the floating bottom bar to switch between baseline / wizard / accordion
# Create/edit/delete robots to test each variant
# The state inspector at the bottom-left shows all form state changes
```

## Completion Report

```yaml
completion_report:
  what_was_done: |
    Built a throwaway prototype in admin at /#/robot-prototype with three
    radically different robot-creation form designs (baseline/wizard/accordion),
    switchable via URL param and floating bottom bar. Also built a @roboease/shared
    package skeleton with stub components proving the shared-library extraction
    pattern. The accordion variant with progressive disclosure, panel completion
    badges, and field hints emerged as the strongest candidate.
  key_decisions:
    - decision: Use accordion panels for progressive disclosure in robot creation form
      rationale: Best balance — shows structure while reducing visible fields; scales
        for both new and experienced operators; matches UX spec recommendation.
    - decision: Shared package extraction order: types → composables → simple components → complex
      rationale: Minimizes risk by extracting low-complexity, high-reuse items first.
    - decision: Keep wizard variant as a future option for onboarding flows
      rationale: Different use case (first-time setup) than day-to-day create/edit.
  handoff_focus:
    - architect: Shared component library design decisions (styling strategy, extraction order)
    - senior-engineer: Implementation plan for accordion form in the real robot page
    - ui-designer: Usability test plan for accordion vs wizard forms
  open_questions:
    - How should the robot config drawer (separate from create/edit) be redesigned?
    - What is the styling strategy for shared components (UnoCSS vs scoped SCSS)?
    - Should we use a generic form-renderer or keep explicit form markup?
  known_constraints:
    - Admin uses UnoCSS, portal uses scoped SCSS — shared components need styling strategy
    - Backend API must remain unchanged during form redesign (mock data used)
    - Prototype route must be removed before production deploy
  confidence_differential: 0.65
  dissent_if_alone: null
  iteration_context: |
    First prototype iteration. If accordion passes usability testing, move to
    implementation. If operators prefer wizard for creation but accordion for
    editing, consider a hybrid approach.
```