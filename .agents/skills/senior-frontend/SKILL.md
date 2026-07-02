---
name: senior-frontend
description: Implements production-quality frontend code from design system specs, UX flows, and platform guidelines; use when a task requires building user-facing UI, components, or browser/native application code.
---

## Purpose

Implement the interface.
This skill translates design system specs, UX flows, and Apple HIG guidance into production-quality frontend code.
It works across React, Vue, SwiftUI, or whichever framework is in play.
It is constrained by the design system and platform guidelines above it.
It ships accessible, performant components that pass review on the first pass.

## When to use

- User-facing UI, components, or pages must be implemented in code.
- A design system spec needs to be realized with its tokens and all states.
- Browser or native application code requires accessibility and performance work.
- Animations and micro-interactions must be implemented against a motion spec.
- Cross-browser or cross-device compatibility needs to be built and verified.
- Component tests with interaction coverage are needed for a UI change.

## Method

1. Read the spec fully before writing code.
2. If it is incomplete or contradictory, or required tokens are undefined, block and escalate to the design-system role.
3. Map every specified variant and state — default, hover, active, focus, disabled, error — to concrete components.
4. Implement 100% of them; silent omissions are defects, not shortcuts.
5. Wire design tokens throughout, using no hardcoded colors, spacing, or type values.
6. Build accessibility in: correct ARIA roles, full keyboard navigation, focus management, and screen-reader support.
7. Implement animation and micro-interactions per spec, honoring the reduced-motion preference.
8. Keep rendering performant: memoize where it matters and lazy-load heavy resources.
9. Avoid layout thrashing, unnecessary re-renders, and render-blocking resources.
10. Verify before handoff by running an accessibility audit and confirming no console errors or warnings.
11. Add component tests with interaction coverage where valuable, and iterate until the reviewer approves.

## Quality bar

- Components implement 100% of the spec's variants and states — no silent omissions.
- No hardcoded values; design tokens are used throughout.
- Accessibility passes an automated audit such as axe-core.
- No layout thrashing, unnecessary re-renders, or render-blocking resources.
- Code passes review without CHANGES_REQUIRED on the first pass.
- The implementation produces no console errors or warnings.

## Output

Framework-appropriate source files implementing the components or pages.
They may be accompanied by component tests in Jest, Vitest, or XCTest covering interaction states.
Token usage is consistent and free of hardcoded values.
The accessibility audit passes with no outstanding violations.
The implementation runs without console errors or warnings.

## Anti-patterns

- Guessing implementation details from a vague or incomplete spec instead of blocking.
- Hardcoding colors, spacing, or typography instead of referencing tokens.
- Implementing only the default state and omitting focus, disabled, or error.
- Treating accessibility as optional rather than an audited requirement.
- Introducing re-render churn or blocking resources that break the performance budget.
- Shipping with console errors or warnings left unresolved.
- Skipping interaction-level tests on components with meaningful state.
