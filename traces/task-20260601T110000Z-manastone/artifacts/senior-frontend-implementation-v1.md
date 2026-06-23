PRIMARY ARTIFACT: manastone/docs/brand/manastone-onboarding.html (enhanced production-grade onboarding dashboard, 1667 lines, 67KB, zero dependencies, zero Pi references)

## What Was Built

Enhanced the epic-design's 4-scene cinematic onboarding dashboard with production-frontend quality improvements across 6 dimensions:

### 1. Accessibility (WCAG 2.1)
- **Skip-to-content link** (§2.4.1 Bypass Blocks) — first focusable element, appears on Tab
- **Focus-visible ring system** — purple glow ring on all interactive elements (:focus-visible)
- **ARIA live regions** — polite announcer for dynamic content, assertive toast for copy feedback
- **Semantic roles** — role="list"/"listitem" on command grid and status grid, role="img" + aria-label on robot silhouette
- **aria-labelledby** on all 4 section elements, linking headings to their regions
- **Keyboard scene navigation** — PageUp/Down and Arrow keys scroll between scenes with screen-reader announcements
- **Tab-indexed cards** — command cards and copy tags are keyboard-focusable with Enter/Space activation
- **Screen-reader-only announcer** (.sr-only live region) for terminal responses and navigation
- **prefers-reduced-motion** — all animations disabled, all text immediately visible, all transforms reset

### 2. Interactive Terminal Simulator
- Users type commands into a terminal input and receive simulated responses
- 10+ recognized commands: battery, status, walk, diagnostics, hello, help, sensors, temperature, what can you do
- Intelligent fallback for unrecognized input with explanatory response
- Realistic typing delay (600-1000ms randomized) before each response
- ARIA-live announcements for screen readers on each response
- Addresses epic-design open question: "Should we add interactive simulated-conversation mode?" — YES.

### 3. Copy-to-Clipboard
- Click any .cmd-tag to copy the command to clipboard
- Keyboard-accessible (Enter/Space activates)
- Visual feedback: green highlight + toast notification ("✓ Copied: manastone-chat")
- Fallback to execCommand for file:// contexts (navigator.clipboard requires secure context)

### 4. Responsive Design (5 Breakpoints)
- ≥1280px: 3-column command grid, wider content
- ≤1023px: 2-column grid, reduced robot silhouette
- ≤768px: 1-column grid, hidden float-geo, stacked layout
- ≤480px: stacked CTAs, single-column status, smaller terminal, hidden robot
- ≤360px: 14px base font for readability, reduced spacing
- Touch detection (pointer: coarse): disables float animations, static core-pulse
- Print stylesheet: clean output, no decorative elements, page-break-inside: avoid

### 5. Performance
- **Low-power GPU detection**: navigator.hardwareConcurrency ≤4 → reduced glow blur (40px), disabled float animations, static core pulse, simplified box-shadow, parallax skipped
- IntersectionObserver pauses content-visibility on off-screen scenes
- scroll-progress bar replaces full parallax on low-power hardware
- All animations GPU-composited (transform, opacity, filter only)
- Console log on init for debugging: version, robot model, a11y status

### 6. Brand Independence
- Zero Pi brand leakage (verified: only hardware "Raspberry Pi" in performance comments)
- All design tokens from BRAND_EXPERIENCE_DESIGN.md §5.1 used consistently
- Manastone terminology throughout: "conversation engine" not "pi", "manastone-chat" not "pi"
- Robot model registry with 7 canonical display strings (agibot_x2, unitree_g1, halfcheetah, dev, etc.)

## install.sh Integration Path

```bash
# In install.sh, after Phase 7 verification:
RUNTIME_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if command -v xdg-open &>/dev/null; then
    xdg-open "file://$RUNTIME_DIR/docs/brand/manastone-onboarding.html?robot=$ROBOT_ID" 2>/dev/null || true
elif command -v open &>/dev/null; then
    open "file://$RUNTIME_DIR/docs/brand/manastone-onboarding.html?robot=$ROBOT_ID" 2>/dev/null || true
else
    echo "→ Open this page: file://$RUNTIME_DIR/docs/brand/manastone-onboarding.html?robot=$ROBOT_ID"
fi
```

## Design Token Usage

All design tokens from BRAND_EXPERIENCE_DESIGN.md §5.1 applied:
- Surfaces: --void (#060918), --deep (#0a0e20), --surface (#0f142e), --elevated (#151b3d)
- Brand colors: --purple (#7c5cfc), --cyan (#00d4ff), --coral (#ff6b4a), --amber (#f59e0b), --success (#34d399)
- Text: --text (#e8ecf4), --text-alt (#9da4c4), --text-muted (#5b638c)
- Typography: --font (Inter/system), --mono (JetBrains Mono/system)
- No hardcoded color values in components — all via var() references

## Performance Budget Verification

- GPU-only properties: transform, opacity, filter (0 width/height/top/left animations)
- Animated elements: < 60 total
- JS bundle: ~6KB vanilla JS, no framework, no CDN
- CSS: ~10KB inline
- will-change: scoped only to active parallax handler
- IntersectionObserver: pauses content-visibility on off-screen scenes
- Low-power mode: disables parallax and reduces effects on ≤4 core systems
- Air-gapped compatible: zero CDN dependencies