---
name: epic-design
description: Builds immersive, cinematic scroll-driven and 2.5D web experiences with performance-safe motion; use when a task needs parallax depth, cinematic animation, or Apple-style product reveals.
---

## Purpose

Design and build immersive, cinematic experiences.
This skill translates brand and product narrative into scroll-driven 2.5D scenes and parallax depth layers.
It composes cinematic text reveals and Apple-style product sequences.
Its motion is always in service of story and constrained by the design system's tokens.
It hands off clean, well-scoped code to the frontend role.

## When to use

- A task needs scroll storytelling driven by GSAP ScrollTrigger or CSS scroll-timeline.
- Parallax depth composition across foreground, midground, and background is required.
- Cinematic text animation such as split-text, word-by-word reveals, or opacity waves is wanted.
- 3D card effects, depth blur, or perspective transforms serve a product reveal.
- An Apple.com-style product reveal sequence must be composed and implemented.
- A narrative brief must be turned into an ordered set of animated scenes.

## Method

1. Start from the narrative brief and establish the product story and the emotional beats each scene must land.
2. If no narrative brief exists, or the design tokens are undefined, block and report the gap rather than decorating.
3. Storyboard the scenes: break the experience into ordered beats.
4. For each beat, define the depth layers and what enters, moves, or reveals.
5. Assign every animation a narrative purpose; if an effect carries no story function, cut it.
6. Compose motion with the right tool: ScrollTrigger or CSS scroll-timeline for scroll binding.
7. Use transform and opacity for parallax, split-text for reveals, and perspective for 3D cards.
8. Pull all colors, typography, and spacing from the design system tokens, never off-system values.
9. Engineer for performance: target 60fps on mid-range hardware and drive GPU compositing via transform and opacity.
10. Apply will-change deliberately and keep layout-triggering properties out of the animation loop.
11. Provide a prefers-reduced-motion alternative for every animated element, then verify frame timing before handoff.

## Quality bar

- Every animation has a narrative purpose — no decoration for its own sake.
- Animations hold 60fps on mid-range hardware, with frame-timing evidence.
- A prefers-reduced-motion fallback exists for every animated element.
- All colors, typography, and spacing come from design system tokens.
- The handoff to the frontend role is clean, well-scoped code.
- No layout-triggering property is animated inside the render loop.

## Output

An immersive experience implementation in HTML, CSS, and JS or a framework component.
It may be paired with a Markdown animation narrative that breaks the scenes down.
Evidence accompanies it that the performance budget is met.
The reduced-motion fallback is present for every animated element.
Design system tokens are used throughout for color, type, and spacing.

## Anti-patterns

- Adding cinematic effects that carry no narrative function.
- Exceeding the performance budget or animating layout-triggering properties.
- Shipping without a reduced-motion fallback.
- Hardcoding colors or type instead of using design system tokens.
- Handing off tangled code that the frontend role must rewrite.
- Building scenes without an ordered storyboard tied to narrative beats.
- Claiming a performance budget is met without frame-timing evidence.
