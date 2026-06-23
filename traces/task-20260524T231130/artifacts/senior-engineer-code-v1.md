# Implementation — TeamUp v2077 Refactor

## Files Modified

| File | Change | Purpose |
|------|--------|---------|
| `teamup_core/orchestrator.py` | Major rework | Structured markers, auto-advance, error handling |
| `teamup_core/llm.py` | Retry logic | Exponential backoff for LLM calls |
| `teamup_core/agent.py` | Error visibility | Push error events to WebSocket |
| `teamup_core/config.py` | Cyberpunk TEAM | New titles & icons |
| `prompts/tangseng.md` | Marker protocol | [NEEDS_INPUT], [TASK_COMPLETE] markers |
| `prompts/wukong.md` | Cyberpunk + markers | Silicon Ape identity, [TASK_STATUS] |
| `prompts/bajie.md` | Cyberpunk + markers | Glitch Pig identity, [TASK_STATUS] |
| `prompts/shawujing.md` | Cyberpunk + markers | Iron Monk identity, [TASK_STATUS] |
| `prompts/bailongma.md` | Cyberpunk + markers | Chrome Dragon identity, [TASK_STATUS] |
| `static/index.html` | Complete rewrite | Cyberpunk dark theme, HUD elements |
| `static/style.css` | Complete rewrite | Neon color system, scanlines, glitch FX |
| `static/app.js` | Major adaptation | Particle background, cyberpunk UX |

## Key Architectural Decisions

1. **Structured output markers** instead of keyword matching for stop detection
2. **Exponential backoff retry** (1s/2s/4s, max 3) for LLM API resilience
3. **Auto-advance 3→8 rounds** with staleness detection (consecutive_no_progress >= 2)
4. **Sub-agent status parsing** — orchestrator reads [TASK_STATUS] and [ERROR] from outputs
5. **Error glitch animation** — agent cards flash red on error events via CSS + JS
6. **GPU-compatible animations** — only transform, opacity, and CSS clip-path are animated

## [TASK_STATUS: SUCCESS]
