"""Node runner boundary for LangGraph-native Silicon Org execution.

LangGraph owns durable control flow. Silicon Org Policy owns activation.
Runners own the isolated execution of one role.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from .langgraph_native import HarnessProfile, ModelSelection


ROOT_DIR = Path(__file__).resolve().parent.parent
HEARTBEAT_SECONDS = 30


@dataclass(frozen=True)
class NodeRunRequest:
    task_id: str
    task_type: str
    task_description: str
    role: str
    harness_profile: "HarnessProfile"
    model_selection: "ModelSelection"
    candidate: dict[str, Any] = field(default_factory=dict)
    input_handoff_ref: str = ""
    input_artifacts: list[dict[str, Any]] = field(default_factory=list)
    input_handoffs: list[dict[str, Any]] = field(default_factory=list)
    registry_ref: str = ""
    registry_text: str = ""
    skill_ref: str = ""
    skill_text: str = ""
    workspace_dir: str = ""
    design_preset_id: str = ""
    design_preset_catalog_ref: str = ""
    design_preset_catalog_text: str = ""
    design_preset_text: str = ""


@dataclass(frozen=True)
class NodeRunResult:
    role: str
    artifact_type: str
    artifact_body: str
    artifact_extension: str = "md"
    context_report: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class NodeRunner(Protocol):
    def run(self, request: NodeRunRequest) -> NodeRunResult:
        """Execute one role and return its artifact payload."""


class NodeRunnerError(RuntimeError):
    """Raised when a node runner cannot produce a valid result."""


def _format_yamlish(value: Any) -> str:
    try:
        import yaml

        return yaml.dump(value, allow_unicode=True, sort_keys=False).strip()
    except Exception:
        return repr(value)


def default_artifact_type(request: NodeRunRequest) -> str:
    artifact_type = "analysis"
    for artifact in request.harness_profile.output_artifacts:
        if artifact.get("required", False):
            return artifact.get("type", artifact_type)
    if request.harness_profile.output_artifacts:
        return request.harness_profile.output_artifacts[0].get("type", artifact_type)
    return artifact_type


def node_run_request_payload(request: NodeRunRequest) -> dict[str, Any]:
    return {
        "schema": "silicon_org.node_invocation.v1",
        "task_id": request.task_id,
        "task_type": request.task_type,
        "task_description": request.task_description,
        "role": request.role,
        "candidate": request.candidate,
        "input_handoff_ref": request.input_handoff_ref,
        "input_artifacts": request.input_artifacts,
        "input_handoffs": request.input_handoffs,
        "registry": {
            "ref": request.registry_ref,
            "text": request.registry_text,
        },
        "skill": {
            "ref": request.skill_ref,
            "text": request.skill_text,
        },
        "harness_profile": {
            "role": request.harness_profile.role,
            "purpose": request.harness_profile.purpose,
            "model_profile": request.harness_profile.model_profile,
            "tool_groups": list(request.harness_profile.tool_groups),
            "write_scope": request.harness_profile.write_scope,
            "output_artifacts": list(request.harness_profile.output_artifacts),
            "completion_gates": list(request.harness_profile.completion_gates),
            "raw": request.harness_profile.raw,
        },
        "model_selection": {
            "role": request.model_selection.role,
            "model_profile": request.model_selection.model_profile,
            "runner_pool": request.model_selection.runner_pool,
            "provider": request.model_selection.provider,
            "model": request.model_selection.model,
            "reasoning_effort": request.model_selection.reasoning_effort,
            "source": request.model_selection.source,
            "raw": request.model_selection.raw,
        },
        "default_artifact_type": default_artifact_type(request),
        "design_preset": {
            "id": request.design_preset_id,
            "catalog_ref": request.design_preset_catalog_ref,
            "catalog_included": bool(request.design_preset_catalog_text),
            "preset_included": bool(request.design_preset_text),
        },
    }


def _design_preset_prompt_sections(request: NodeRunRequest) -> list[str]:
    """Stub — design preset prompt enrichment not yet implemented."""
    return []


def _workspace_code_section(request: NodeRunRequest) -> list[str]:
    """Pre-read workspace directory and inject code context for sandboxed nodes."""
    ws = request.workspace_dir
    if not ws:
        return []
    wsp = Path(ws)
    if not wsp.is_dir():
        return []
    parts: list[str] = []
    parts.append("## Workspace Code")
    parts.append("")
    parts.append(f"path: `{ws}`")
    parts.append("")
    # Directory tree (max 200 lines)
    import subprocess
    try:
        tree = subprocess.run(
            ["find", str(wsp), "-not", "-path", "*/node_modules/*",
             "-not", "-path", "*/__pycache__/*", "-not", "-path", "*/.git/*",
             "-not", "-name", "*.pyc", "-not", "-name", ".DS_Store",
             "-type", "f"],
            capture_output=True, text=True, timeout=10
        )
        files = [l for l in tree.stdout.strip().split("\n") if l][:500]
        if files:
            parts.append("### File List")
            parts.append("```text")
            for f in files[:200]:
                parts.append(f"  {f}")
            if len(files) > 200:
                parts.append(f"  ... ({len(files) - 200} more files)")
            parts.append("```")
            parts.append("")
        # Read key files for context (top configs, main entry points, up to 8KB total)
        key_patterns = [
            "main.py", "bootstrap.py", "database.py", "app.py",
            "setup.py", "pyproject.toml", "requirements.txt", "package.json",
            "docker-compose.yaml", "docker-compose.yml", "Dockerfile",
            "README.md", ".env.example", "config.py", "setting.py", "dbconfig.py",
        ]
        read_limit = 8192
        read_total = 0
        key_files = []
        for pat in key_patterns:
            for f in files:
                if f.endswith("/" + pat) or f.endswith(pat):
                    if read_total >= read_limit:
                        break
                    key_files.append(f)
                    break
        if key_files:
            parts.append("### Key Files")
            for kf in sorted(set(key_files))[:8]:
                try:
                    content = Path(kf).read_text(encoding="utf-8", errors="replace")
                    max_chars = max(200, (read_limit - read_total) // max(1, len(key_files)))
                    if len(content) > max_chars:
                        content = content[:max_chars] + "\n... (truncated)"
                    read_total += len(content)
                    parts.append(f"#### `{kf}`")
                    parts.append("```")
                    parts.append(content.rstrip())
                    parts.append("```")
                    parts.append("")
                except Exception:
                    pass
    except Exception:
        pass
    return parts


def build_node_invocation_prompt(request: NodeRunRequest) -> str:
    """Build the canonical prompt package for an isolated role executor."""

    candidate = request.candidate or {}
    output_artifacts = _format_yamlish(list(request.harness_profile.output_artifacts))
    completion_gates = _format_yamlish(list(request.harness_profile.completion_gates))
    tool_groups = _format_yamlish(list(request.harness_profile.tool_groups))
    artifact_sections = []
    for artifact in request.input_artifacts:
        artifact_sections.append(
            "\n".join([
                f"### {artifact.get('artifact_id')}",
                "",
                f"- producer: `{artifact.get('producer', '')}`",
                f"- type: `{artifact.get('type', '')}`",
                f"- ref: `{artifact.get('content_ref', '')}`",
                "",
                "```text",
                artifact.get("body", ""),
                "```",
            ])
        )

    handoff_sections = []
    for handoff in request.input_handoffs:
        handoff_sections.append(
            "\n".join([
                f"### {handoff.get('ref')}",
                "",
                f"- from: `{handoff.get('from', '')}`",
                f"- to: `{handoff.get('to', '')}`",
                f"- relation_type: `{handoff.get('relation_type', '')}`",
                f"- context_digest: `{handoff.get('context_digest', '')}`",
                "",
                "```yaml",
                _format_yamlish(handoff.get("context_block", {})),
                "```",
            ])
        )

    return "\n".join([
        f"# Silicon Org Node Invocation: {request.role}",
        "",
        "You are executing exactly one Silicon Org node. Do not activate other nodes.",
        "Do not write outside the node's harness write scope. Produce the requested",
        "deliverable plus a valid Context Compression Report.",
        "",
        "## Runtime Envelope",
        "",
        f"- task_id: `{request.task_id}`",
        f"- task_type: `{request.task_type}`",
        f"- role: `{request.role}`",
        f"- relation_type: `{candidate.get('relation_type', 'entry')}`",
        f"- from: `{candidate.get('from', '')}`",
        f"- to: `{candidate.get('to', request.role)}`",
        f"- score: `{candidate.get('score', '')}`",
        f"- decision_reason: {candidate.get('decision_reason', '')}",
        "",
        "## Model Selection",
        "",
        f"- provider: `{request.model_selection.provider}`",
        f"- model: `{request.model_selection.model}`",
        f"- model_profile: `{request.model_selection.model_profile}`",
        f"- runner_pool: `{request.model_selection.runner_pool or ''}`",
        f"- reasoning_effort: `{request.model_selection.reasoning_effort}`",
        f"- source: `{request.model_selection.source}`",
        "",
        "## Harness Profile",
        "",
        f"- purpose: {request.harness_profile.purpose}",
        f"- write_scope: `{request.harness_profile.write_scope}`",
        "",
        "tool_groups:",
        "```yaml",
        tool_groups,
        "```",
        "",
        "output_artifacts:",
        "```yaml",
        output_artifacts,
        "```",
        "",
        "completion_gates:",
        "```yaml",
        completion_gates,
        "```",
        "",
        "## Registry Harness",
        "",
        f"ref: `{request.registry_ref}`",
        "",
        request.registry_text or "(missing registry harness)",
        "",
        "## Skill",
        "",
        f"ref: `{request.skill_ref}`",
        "",
        request.skill_text or "(no skill text registered)",
        "",
        *_design_preset_prompt_sections(request),
        "## Upstream Handoffs",
        "",
        "\n\n".join(handoff_sections) or "(none)",
        "",
        "## Upstream Artifacts",
        "",
        "\n\n".join(artifact_sections) or "(none)",
        "",
        *_workspace_code_section(request),
        "## Task",
        "",
        request.task_description or "(empty task description)",
        "",
        "## Required Output Shape",
        "",
        "1. Primary deliverable matching the harness output_artifacts contract.",
        "2. Completion Report with what_was_done, key_decisions, handoff_focus,",
        "   open_questions, known_constraints, confidence_differential, and",
        "   dissent_if_alone.",
        "3. Context Compression Report YAML matching org/HARNESS.md.",
    ])


class PromptPackageNodeRunner:
    """Build a full invocation package for an external semantic executor.

    This is the bridge between LangGraph scheduling and real model/tool
    execution. It is intentionally deterministic: another runner can consume
    the package and perform the actual model call in an isolated sandbox.
    """

    def run(self, request: NodeRunRequest) -> NodeRunResult:
        artifact_type = "invocation"
        prompt = build_node_invocation_prompt(request)
        return NodeRunResult(
            role=request.role,
            artifact_type=artifact_type,
            artifact_body=prompt + "\n",
            artifact_extension="md",
            metadata={
                "runner": "prompt_package",
                "semantic_execution": False,
                "ready_for_external_executor": True,
            },
        )


class ExternalCommandNodeRunner:
    """Execute one node through a local command runner.

    The command must be local and user-controlled. Silicon Org passes a JSON
    invocation package and prompt file through environment variables. The
    command returns JSON on stdout or writes it to `SILICON_ORG_RESULT_JSON`.
    """

    def __init__(self, command: str | None = None, timeout_seconds: int = 600):
        self.command = command or os.environ.get("SILICON_ORG_NODE_EXECUTOR_CMD", "")
        self.timeout_seconds = timeout_seconds

    def run(self, request: NodeRunRequest) -> NodeRunResult:
        if not self.command:
            raise NodeRunnerError(
                "external_command runner requires SILICON_ORG_NODE_EXECUTOR_CMD "
                "or external_runner_command"
            )
        argv = shlex.split(self.command)
        if not argv:
            raise NodeRunnerError("external command is empty")

        prompt = build_node_invocation_prompt(request)
        payload = node_run_request_payload(request)
        with tempfile.TemporaryDirectory(prefix="silicon-node-") as temp_dir:
            workdir = Path(temp_dir)
            invocation_path = workdir / "invocation.json"
            prompt_path = workdir / "prompt.md"
            result_path = workdir / "result.json"
            invocation_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            prompt_path.write_text(prompt, encoding="utf-8")

            env = os.environ.copy()
            env.update({
                "SILICON_ORG_INVOCATION_JSON": str(invocation_path),
                "SILICON_ORG_INVOCATION_PROMPT": str(prompt_path),
                "SILICON_ORG_RESULT_JSON": str(result_path),
                "SILICON_ORG_WORKSPACE": request.workspace_dir or str(ROOT_DIR),
            })
            started = time.monotonic()
            print(
                f"[silicon-org] node {request.role}: executor started "
                f"(timeout={self.timeout_seconds}s, command={self.command!r})",
                file=sys.stderr,
                flush=True,
            )
            stdout_path = workdir / "executor.stdout"
            stderr_path = workdir / "executor.stderr"
            with open(stdout_path, "w+", encoding="utf-8") as stdout_file, open(
                stderr_path,
                "w+",
                encoding="utf-8",
            ) as stderr_file:
                process = subprocess.Popen(
                    argv,
                    cwd=str(request.workspace_dir or ROOT_DIR),
                    env=env,
                    text=True,
                    stdout=stdout_file,
                    stderr=stderr_file,
                )
                last_heartbeat = started
                while True:
                    returncode = process.poll()
                    elapsed = time.monotonic() - started
                    if returncode is not None:
                        break
                    if elapsed >= self.timeout_seconds:
                        process.kill()
                        process.wait()
                        stderr_tail = stderr_path.read_text(encoding="utf-8")[-4000:]
                        raise NodeRunnerError(
                            f"external node executor timed out for {request.role} "
                            f"after {self.timeout_seconds}s. stderr_tail={stderr_tail}"
                        )
                    if time.monotonic() - last_heartbeat >= HEARTBEAT_SECONDS:
                        print(
                            f"[silicon-org] node {request.role}: still running "
                            f"({int(elapsed)}s elapsed)",
                            file=sys.stderr,
                            flush=True,
                        )
                        last_heartbeat = time.monotonic()
                    time.sleep(1)
                elapsed = time.monotonic() - started
                print(
                    f"[silicon-org] node {request.role}: executor exited "
                    f"(code={returncode}, elapsed={int(elapsed)}s)",
                    file=sys.stderr,
                    flush=True,
                )

            stdout_text = stdout_path.read_text(encoding="utf-8")
            stderr_text = stderr_path.read_text(encoding="utf-8")
            if returncode != 0:
                raise NodeRunnerError(
                    "external node executor failed "
                    f"({returncode}) for {request.role}: {stderr_text[-4000:].strip()}"
                )
            if result_path.exists():
                result_text = result_path.read_text(encoding="utf-8")
            else:
                result_text = stdout_text
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError as exc:
                raise NodeRunnerError(
                    "external node executor did not return JSON"
                ) from exc

        if not isinstance(result, dict):
            raise NodeRunnerError("external node executor result must be a JSON object")
        artifact_body = result.get("artifact_body")
        if not isinstance(artifact_body, str) or not artifact_body.strip():
            raise NodeRunnerError("external node executor result missing artifact_body")
        metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
        metadata = {
            "runner": "external_command",
            "semantic_execution": bool(result.get("semantic_execution", True)),
            **metadata,
        }
        return NodeRunResult(
            role=result.get("role") or request.role,
            artifact_type=result.get("artifact_type") or default_artifact_type(request),
            artifact_body=artifact_body,
            artifact_extension=result.get("artifact_extension") or "md",
            context_report=result.get("context_report"),
            metadata=metadata,
        )


class SemanticCommandNodeRunner(ExternalCommandNodeRunner):
    """Execute one node with the configured local semantic agent CLI.

    This is the production local runner boundary. It uses the same invocation
    package as `external_command`, but defaults to `tools/semantic_node_executor.py`
    so the role is performed by Codex/Claude/pi instead of the deterministic
    contract validator.
    """

    def __init__(self, command: str | None = None, timeout_seconds: int = 1800):
        executor_path = str(ROOT_DIR / "tools" / "semantic_node_executor.py")
        super().__init__(
            command=command or os.environ.get(
                "SILICON_ORG_SEMANTIC_EXECUTOR_CMD",
                f"{sys.executable} {executor_path}",
            ),
            timeout_seconds=timeout_seconds,
        )


class HarnessDryRunNodeRunner:
    """Deterministic local runner used before real subagent isolation is wired.

    It proves the runtime/ledger contract without claiming to perform the
    semantic work of the role. Production deployments should replace this with
    a runner that invokes an isolated subagent or model/tool sandbox.
    """

    def run(self, request: NodeRunRequest) -> NodeRunResult:
        artifact_type = default_artifact_type(request)

        candidate = request.candidate or {}
        body = "\n".join(
            [
                f"# {request.role} Harness Execution Stub",
                "",
                "This artifact was produced by the local harness dry-run runner.",
                "It validates LangGraph control flow, model routing, and Ledger",
                "transactions, but it is not a semantic substitute for an",
                "isolated subagent execution.",
                "",
                f"- task_id: `{request.task_id}`",
                f"- task_type: `{request.task_type}`",
                f"- role: `{request.role}`",
                f"- purpose: {request.harness_profile.purpose}",
                f"- model_profile: `{request.model_selection.model_profile}`",
                f"- model_source: `{request.model_selection.source}`",
                f"- provider: `{request.model_selection.provider}`",
                f"- model: `{request.model_selection.model}`",
                f"- relation_type: `{candidate.get('relation_type', 'entry')}`",
                f"- from: `{candidate.get('from', '')}`",
                f"- to: `{candidate.get('to', request.role)}`",
                "",
                "## Task",
                "",
                request.task_description or "(empty task description)",
            ]
        )
        return NodeRunResult(
            role=request.role,
            artifact_type=artifact_type,
            artifact_body=body + "\n",
            artifact_extension="md",
            metadata={
                "runner": "harness_dry_run",
                "semantic_execution": False,
            },
        )
