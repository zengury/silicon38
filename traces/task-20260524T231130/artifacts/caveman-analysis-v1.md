# Caveman: TeamUp First Principles

## What System Is
Orchestrator + 4 workers. Tang Monk talk to user. Dispatch workers. Workers do job. Return result.

## Real Problems (not symptoms)

### 1. No feedback loop when things break
LLM call fail -> error swallowed -> user see "thinking" forever.
Tool fail -> error text mixed with normal output -> orchestrator can't tell success from failure.

### 2. Stop detection is pattern-match, not semantic
`_needs_user_input` grep keywords. LLM say "您觉得可以继续吗" -> no match -> skip checkpoint.
Should: structured output from LLM (field: `requires_user_input: bool`).

### 3. Fixed iteration cap
range(3) blind. No awareness of task completion.
Should: task_complete signal from orchestrator. Stop when done, not when counter exhausted.

### 4. State machine defined but unused
STAGES exist in session.py. orchestrator ignores them.
Should: stage gate before delegation. Can't dispatch wukong before prd approved.

### 5. Sub-agent output truncated
200 char preview -> Tang Monk decide on partial info.
Should: structured summary (status + errors + key findings).

## Fix Priority
1. Error visibility + retry (P0 — system unusable without)
2. Smart stop detection (P0 — causes wrong outputs)
3. State machine gating (P1 — prevents cascading failures)
4. Structured sub-agent reports (P1 — better decisions)
5. Remove iteration limit (P1 — complete tasks)

## UI: From Scroll to Circuit
Current: rice paper + calligraphy. Feels 16th century.
Target: neon + chrome + glitch. Feels 2077.
Same 5 agents. Same functions. Different skin.
