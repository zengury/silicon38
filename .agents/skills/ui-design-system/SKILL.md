---
name: ui-design-system
description: Builds and maintains the design system — tokens, component contracts, and interaction states — as the single source of truth for visual language; use when a task requires a component library, design tokens, or a code-implementable visual language.
---

## Purpose

Own the design system: the single source of truth for visual language, component contracts, and interaction states.
This skill architects tokens for color, spacing, typography, and motion, and specifies every component variant.
Its output constrains both frontend implementation and cinematic design so the product stays coherent.
It embeds accessibility at the source rather than bolting it on after the fact.
Every spec it ships is precise enough to be implemented in code without reinterpretation.

## When to use

- A component library must be built or extended with new variants and states.
- A design token system for color, spacing, typography, or motion needs architecture or revision.
- A visual language must be codified so multiple engineers implement it consistently.
- Accessibility requirements must be embedded into components at the source.
- Cross-platform consistency across web, iOS, and Android needs a shared contract.
- Ambiguous measurements or unresolved states in an existing spec must be resolved.

## Method

1. Establish design direction, derived from UX research and platform guidance such as Apple HIG.
2. If no design direction or brand guideline exists, stop and report the gap rather than inventing a language.
3. Architect tokens first: define semantic names for color, spacing, typography, and motion.
4. Give every token a documented use case, not merely a raw value.
5. Specify each component exhaustively across default, hover, active, focus, disabled, and error states.
6. Cover every required variant and size so no state is left unresolved.
7. Embed accessibility inline: WCAG AA contrast, focus visibility, touch-target sizing, and reduced motion.
8. Resolve all measurements, replacing ambiguous sizing with concrete values or token references.
9. Document usage guidelines: when to use a component, when not to, and how variants compose.
10. Verify cross-platform mappings hold, then hand a complete, unambiguous spec downstream.

## Quality bar

- Every token has a semantic name and a documented use case.
- Every component covers default, hover, active, focus, disabled, and error states.
- Accessibility criteria are embedded with references, not appended.
- No ambiguous measurements or unresolved states remain in the spec.
- Naming is consistent across the whole token and component set.
- Cross-platform mappings are stated where the system spans web and native.

## Output

A Markdown design system or component specification.
It defines the token architecture and each component's full set of variants and states.
It states accessibility requirements with references and gives clear usage guidelines.
It may include the token definitions as a YAML or JSON schema for direct consumption.
The result is implementable by a frontend engineer without further interpretation.

## Anti-patterns

- Inventing a design language instead of deriving it from research and HIG guidance.
- Shipping specs with unresolved states or ambiguous measurements.
- Naming tokens by raw value rather than semantic role.
- Treating accessibility as a later pass instead of an embedded requirement.
- Specifying only the default state and omitting hover, focus, disabled, or error.
- Letting naming drift so equivalent tokens carry inconsistent labels.
- Leaving cross-platform behavior implicit when the system spans web and native.
