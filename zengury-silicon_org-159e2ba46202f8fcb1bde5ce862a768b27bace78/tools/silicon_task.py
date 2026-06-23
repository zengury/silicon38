#!/usr/bin/env python3
"""Start a Silicon Org business task through the LangGraph-native entrypoint.

This is the stable front door used by AGENTS.md. It keeps task startup out of
the model's judgment: read the user's task text, create a task id, and delegate
to tools/langgraph_run.py with the production execution defaults.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import secrets
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

# ── Encoder task-type → entry-role mapping (mirrors org/ENCODER.md) ──
ENCODER_MAP: dict[str, list[str]] = {
    "bug_fix": ["triage"],
    "feature": ["to-prd"],
    "refactor": ["zoom-out"],
    "architecture": ["zoom-out"],
    "design": ["to-prd"],
    "ops": ["triage"],
    "infra": ["triage"],
    "security_audit": ["triage"],
    "docs": ["grill-with-docs"],
    "release": ["triage"],
    "ambiguous": ["triage"],
    "complex": ["triage", "caveman"],
    "multi-part": ["triage", "caveman"],
}


# ── Task-type keyword inference ──
# Ordered by specificity: first match wins. Each entry is (keyword_patterns, task_type).
# Patterns are matched case-insensitively against the user's task description.
TASK_TYPE_PATTERNS: list[tuple[list[str], str]] = [
    (["security audit", "security review", "vulnerability", "penetration test", "threat model"], "security_audit"),
    (["from scratch", "build a mobile app", "build an app", "build a new", "create a mobile", "create an app", "create a new", "从零构建", "新建.*app", "new mobile app", "greenfield", "brand new", "全新的"], "feature"),
    (["refactor", "重构", "clean up", "simplify", "restructure", "reorganize"], "refactor"),
    (["architecture", "system design", "design the system", "架构", "微服务", "monolith"], "architecture"),
    (["ui", "ux", "design system", "界面", "前端设计", "visual design", "mockup"], "design"),
    (["bug", "fix", "broken", "error", "regression", "crash", "修复", "故障"], "bug_fix"),
    (["deploy", "ci/cd", "pipeline", "infrastructure", "infra", "terraform", "k8s"], "ops"),
    (["documentation", "docs", "readme", "文档", "api docs"], "docs"),
    (["release", "changelog", "version bump", "发版"], "release"),
]


def infer_task_type(description: str) -> str | None:
    """Infer task type from user description keywords. Returns None if uncertain."""
    import re
    text = description.lower()
    for patterns, task_type in TASK_TYPE_PATTERNS:
        for pat in patterns:
            if re.search(pat, text):
                return task_type
    return None


def resolve_entry(task_type: str) -> list[str]:
    """Resolve entry roles from ENCODER mapping, falling back to triage."""
    key = task_type.replace("-", "_").replace(" ", "_").lower().strip()
    if key in ENCODER_MAP:
        return ENCODER_MAP[key]
    # try partial match (e.g. "bug_fix_with_logs" -> "bug_fix")
    for ek, roles in ENCODER_MAP.items():
        if ek in key or key in ek:
            return roles
    return ["triage"]


def default_task_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = secrets.token_hex(4)
    return f"task-{stamp}-{suffix}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Start a Silicon Org task through LangGraph-native runtime."
    )
    parser.add_argument("--task-id", default="")
    parser.add_argument("--task-type", default="general")
    parser.add_argument("--entry-roles", default="")
    parser.add_argument("--max-role-executions", type=int, default=12)
    parser.add_argument("--max-parallel-dispatch", type=int, default=3)
    parser.add_argument("--activation-threshold", type=float, default=0.5)
    parser.add_argument("--recursion-limit", type=int, default=120)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument(
        "description",
        nargs="*",
        help="Task description. If omitted, the description is read from stdin.",
    )
    return parser


def read_description(parts: list[str]) -> str:
    description = " ".join(parts).strip()
    if description:
        return description
    if not sys.stdin.isatty():
        description = sys.stdin.read().strip()
    if not description:
        raise SystemExit("task description is required")
    return description


def detect_workspace(description: str) -> str:
    """If the description starts with a valid directory path, use it as workspace."""
    import re
    match = re.match(r"^([/\w.\-~]+)", description.strip())
    if match:
        candidate = Path(match.group(1))
        if candidate.is_dir():
            return str(candidate)
    return ""


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    task_id = args.task_id.strip() or default_task_id()
    description = read_description(args.description)

    # Infer task_type from description if not explicitly provided.
    # This prevents the "general" default from silently gating out activation edges.
    explicit_task_type = bool(sys.argv and any("--task-type" in a for a in (argv or sys.argv)))
    inferred = infer_task_type(description)
    task_type = args.task_type if explicit_task_type else (inferred or args.task_type)
    task_type_hint = inferred if (inferred and inferred != task_type) else None

    if inferred:
        print(f"[encoder] inferred task_type={inferred} from description"
              + (f" (overriding: {args.task_type})" if inferred != args.task_type else ""),
              flush=True)

    # Record signal for learning loop — even when inference returns None
    try:
        from tools.encoder_quality import record_encoder_signal
        record_encoder_signal(task_id, description, inferred, not explicit_task_type)
    except Exception:
        pass  # never block task startup on signal recording

    entry_roles = args.entry_roles.strip() or ",".join(resolve_entry(task_type))
    workspace = detect_workspace(description)
    command = [
        sys.executable,
        "tools/langgraph_run.py",
        "--task-id",
        task_id,
        "--task-type",
        task_type,
        *(["--task-type-hint", task_type_hint] if task_type_hint else []),
        "--description",
        description,
        "--entry-roles",
        entry_roles,
        "--runner-mode",
        "semantic_command",
        "--max-role-executions",
        str(args.max_role_executions),
        "--max-parallel-dispatch",
        str(args.max_parallel_dispatch),
        "--activation-threshold",
        str(args.activation_threshold),
        "--recursion-limit",
        str(args.recursion_limit),
    ]
    if args.replace:
        command.append("--replace")
    if workspace:
        command.extend(["--workspace", workspace])
    print(f"LangGraph task started: {task_id}", flush=True)
    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
