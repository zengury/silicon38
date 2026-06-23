"""Silicon Org — Node runner adapter interface.

Silicon Org's identity is "agent governance layer", not "agent execution
runtime." A runner is the thing that actually invokes a node and returns its
artifact body. Today's only concrete runner boundary is the Claude Agent tool
inside Claude Code.

This module defines the Protocol that every runner implements, plus a
"prepare" helper that returns the invocation package without executing it.
No other runner is registered until it has a real implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Invocation:
    """The prepared invocation package for a node.

    A runner receives this and is responsible for delivering the prompt to
    its execution backend, collecting the artifact body, and returning it.
    The runner does NOT write to the ledger — the caller (Runtime or
    scheduler) is responsible for `ledger.py artifact` and `ledger.py node
    completed`. This keeps the runner pure.
    """

    role: str
    task_id: str
    prompt: str
    model: str
    expected_artifact_path: Path


@dataclass(frozen=True)
class InvocationResult:
    """The result of a successful runner invocation.

    `artifact_body` is the full text the node produced. The caller writes
    it to `Invocation.expected_artifact_path`. `usage` is optional and
    runner-specific (token counts, latency, model fingerprint).
    """

    role: str
    task_id: str
    artifact_body: str
    usage: dict[str, object] | None = None


class NodeRunner(Protocol):
    """The interface every node runner satisfies.

    Conformance is structural (typing.Protocol). A runner does ONE thing:
    invoke a node and return its artifact body. It does not manage state,
    write to the ledger, or decide whether to activate.
    """

    name: str  # short identifier, e.g. "claude-agent"

    def invoke(self, invocation: Invocation) -> InvocationResult:
        """Run the node and return its artifact body.

        Raises:
            RunnerUnavailableError: backend not configured or reachable.
            RunnerExecutionError: backend ran but returned a failure.
        """
        ...


class RunnerError(Exception):
    """Base class for runner failures."""


class RunnerUnavailableError(RunnerError):
    """Runner cannot be reached or is not configured."""


class RunnerExecutionError(RunnerError):
    """Runner reached its backend but the invocation failed."""


# ── ClaudeAgentRunner ──────────────────────────────────────────────────────
# In Claude Code, subagent invocation happens through the Agent tool, which
# is only available inside the Claude Code Runtime, NOT as a regular Python
# subprocess. This runner therefore cannot call itself; it can only PREPARE
# the invocation for the Runtime to consume.
#
# `invoke()` raises RunnerExecutionError with a structured message that
# tells the caller to use the Agent tool with the prepared payload. This
# is deliberate: it makes the "Runtime is the executor today" boundary
# explicit instead of hiding it behind a fake implementation.


class ClaudeAgentRunner:
    """Prepares Agent-tool invocations for Claude Code Runtime to execute.

    Today's execution path: Runtime reads the prepared Invocation, calls
    the Agent tool itself, then registers the result via ledger.py.
    When a standalone executor (e.g. via Anthropic SDK from a separate
    process) is added, this class is the seam to swap.
    """

    name = "claude-agent"

    def invoke(self, invocation: Invocation) -> InvocationResult:
        raise RunnerExecutionError(
            "ClaudeAgentRunner.invoke() cannot run inside a tools.runners "
            "subprocess. The Agent tool lives in the Claude Code Runtime. "
            "Use prepare(invocation) and have Runtime call the Agent tool "
            "with the returned payload, then register via ledger.py."
        )

    def prepare(self, invocation: Invocation) -> dict[str, object]:
        """Return the payload the Runtime should pass to the Agent tool."""
        return {
            "subagent_type": "general-purpose",
            "description": f"Silicon Org node: {invocation.role}",
            "model": invocation.model,
            "prompt": invocation.prompt,
            "expected_artifact_path": str(invocation.expected_artifact_path),
        }


# ── Registry ───────────────────────────────────────────────────────────────


def available_runners() -> dict[str, type]:
    """Map runner name → class. Useful for `--runner <name>` selection."""
    return {
        ClaudeAgentRunner.name: ClaudeAgentRunner,
    }


def get_runner(name: str = "claude-agent") -> NodeRunner:
    """Return an instance of the requested runner, defaulting to Claude."""
    runners = available_runners()
    if name not in runners:
        raise RunnerUnavailableError(
            f"unknown runner {name!r}; available: {sorted(runners)}"
        )
    return runners[name]()


__all__ = [
    "Invocation",
    "InvocationResult",
    "NodeRunner",
    "RunnerError",
    "RunnerUnavailableError",
    "RunnerExecutionError",
    "ClaudeAgentRunner",
    "available_runners",
    "get_runner",
]
