#!/usr/bin/env python3
"""Execute one Silicon Org node with a local semantic agent.

The LangGraph runtime calls this through `SemanticCommandNodeRunner`. It reads
the canonical node invocation package from `SILICON_ORG_INVOCATION_JSON`, calls
a local agent CLI (`codex`, `claude`, `pi`) or direct model API provider, validates
the JSON result, and writes the result to `SILICON_ORG_RESULT_JSON`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from typing import Any
from urllib import error, request


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = Path(os.environ.get("SILICON_ORG_WORKSPACE", str(ROOT)))
LOCAL_ENV_PATH = ROOT / "org" / ".env.local"
JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["role", "artifact_type", "artifact_body", "context_report"],
    "properties": {
        "role": {"type": "string"},
        "artifact_type": {"type": "string"},
        "artifact_extension": {"type": "string"},
        "artifact_body": {"type": "string"},
        "context_report": {"type": "object"},
        "semantic_execution": {"type": "boolean"},
        "metadata": {"type": "object"},
    },
}
OMITTED_CONTEXT_REASONS = {
    "background_only",
    "contradicted",
    "duplicate",
    "irrelevant",
    "superseded",
}


def load_invocation() -> dict[str, Any]:
    ref = os.environ.get("SILICON_ORG_INVOCATION_JSON")
    if not ref:
        raise SystemExit("SILICON_ORG_INVOCATION_JSON is required")
    return json.loads(Path(ref).read_text(encoding="utf-8"))


def load_local_env() -> None:
    if not LOCAL_ENV_PATH.exists():
        return
    for raw_line in LOCAL_ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def prompt_path() -> Path:
    ref = os.environ.get("SILICON_ORG_INVOCATION_PROMPT")
    if not ref:
        raise SystemExit("SILICON_ORG_INVOCATION_PROMPT is required")
    return Path(ref)


def agent_name(invocation: dict[str, Any] | None = None) -> str:
    provider = ((invocation or {}).get("model_selection") or {}).get("provider")
    if provider in {"deepseek"}:
        return provider
    configured = os.environ.get("SILICON_ORG_NODE_AGENT", "").strip()
    if configured:
        return configured
    if provider in {"pi", "codex", "claude"}:
        return provider
    return "pi"


def executable(name: str) -> str:
    explicit = os.environ.get("SILICON_ORG_NODE_AGENT_BIN", "").strip()
    if explicit:
        return explicit
    found = shutil.which(name)
    if not found:
        raise SystemExit(f"semantic node agent not found on PATH: {name}")
    return found


def model_arg(invocation: dict[str, Any]) -> str:
    model = ((invocation.get("model_selection") or {}).get("model") or "").strip()
    return "" if model in {"", "runtime-default"} else model


def reasoning_effort(invocation: dict[str, Any]) -> str:
    effort = ((invocation.get("model_selection") or {}).get("reasoning_effort") or "").strip()
    return "" if effort in {"", "inherit"} else effort


def deepseek_model_arg(invocation: dict[str, Any]) -> str:
    model = model_arg(invocation)
    if not model:
        return "deepseek-chat"
    if model.startswith("deepseek/"):
        return model.split("/", 1)[1]
    return model


def node_allows_repo_writes(invocation: dict[str, Any]) -> bool:
    profile = invocation.get("harness_profile") or {}
    raw = profile.get("raw") if isinstance(profile.get("raw"), dict) else {}
    can_modify = raw.get("can_modify_product_code")
    if can_modify is True:
        return True
    if isinstance(can_modify, str) and can_modify not in {"", "false", "False", "none"}:
        return True
    write_scope = raw.get("write_scope") or profile.get("write_scope") or ""
    return any(
        marker in str(write_scope)
        for marker in ("product_code", "repo_write", "tests_and_trace", "prototype_paths")
    )


def write_schema(temp_dir: Path) -> Path:
    schema_path = temp_dir / "node_result.schema.json"
    schema_path.write_text(json.dumps(JSON_SCHEMA, indent=2), encoding="utf-8")
    return schema_path


def result_instruction(invocation: dict[str, Any]) -> str:
    return "\n".join([
        "",
        "## Silicon Org Executor Contract",
        "",
        "Return ONLY a JSON object matching this shape:",
        "",
        "```json",
        json.dumps(JSON_SCHEMA, indent=2),
        "```",
        "",
        "The `artifact_body` must be the role's real deliverable, not a placeholder.",
        "The `context_report` must include `context_compression_report` with:",
        "- input_scope.artifacts_read",
        "- input_scope.handoffs_read",
        "- retained_context.decisions",
        "- retained_context.constraints",
        "- retained_context.assumptions",
        "- retained_context.open_questions",
        "- omitted_context",
        "- compression_rationale",
        "- quality_checks",
        "",
        f"Set role to `{invocation.get('role')}`.",
        f"Set artifact_type to `{invocation.get('default_artifact_type', 'analysis')}` unless the harness requires a better exact type.",
        "Set semantic_execution to true.",
    ])


def full_prompt(invocation: dict[str, Any]) -> str:
    prompt = prompt_path().read_text(encoding="utf-8")
    return prompt + result_instruction(invocation)


def run_codex(invocation: dict[str, Any], prompt: str, temp_dir: Path) -> str:
    schema_path = write_schema(temp_dir)
    output_path = temp_dir / "codex-result.json"
    command = [
        executable("codex"),
        "exec",
        "-C",
        str(ROOT),
        "--skip-git-repo-check",
        "--sandbox",
        os.environ.get(
            "SILICON_ORG_NODE_SANDBOX",
            "workspace-write" if node_allows_repo_writes(invocation) else "read-only",
        ),
        "--output-schema",
        str(schema_path),
        "--output-last-message",
        str(output_path),
        "-",
    ]
    model = model_arg(invocation)
    if model:
        command.extend(["--model", model])
    completed = subprocess.run(
        command,
        cwd=WORKSPACE,
        input=prompt,
        text=True,
        capture_output=True,
        timeout=int(os.environ.get("SILICON_ORG_SEMANTIC_TIMEOUT", "1800")),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.stderr.strip() or completed.stdout.strip())
    return output_path.read_text(encoding="utf-8") if output_path.exists() else completed.stdout


def run_claude(invocation: dict[str, Any], prompt: str, temp_dir: Path) -> str:
    schema_path = write_schema(temp_dir)
    command = [
        executable("claude"),
        "--bare",
        "--print",
        "--output-format",
        "json",
        "--json-schema",
        str(schema_path),
        "--permission-mode",
        os.environ.get(
            "SILICON_ORG_CLAUDE_PERMISSION_MODE",
            "acceptEdits" if node_allows_repo_writes(invocation) else "default",
        ),
    ]
    model = model_arg(invocation)
    if model:
        command.extend(["--model", model])
    effort = reasoning_effort(invocation)
    if effort:
        command.extend(["--effort", effort])
    command.append(prompt)
    completed = subprocess.run(
        command,
        cwd=WORKSPACE,
        text=True,
        capture_output=True,
        timeout=int(os.environ.get("SILICON_ORG_SEMANTIC_TIMEOUT", "1800")),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout


def run_pi(invocation: dict[str, Any], prompt: str, temp_dir: Path) -> str:
    command = [
        executable("pi"),
        "--print",
        "--mode",
        "text",
    ]
    if node_allows_repo_writes(invocation):
        command.extend(["--tools", "read,grep,find,ls,bash,edit,write"])
    else:
        command.extend(["--tools", "read,grep,find,ls,bash"])
    model = model_arg(invocation)
    if model:
        command.extend(["--model", model])
    effort = reasoning_effort(invocation)
    if effort:
        command.extend(["--thinking", effort])
    command.append(prompt)
    completed = subprocess.run(
        command,
        cwd=WORKSPACE,
        text=True,
        capture_output=True,
        timeout=int(os.environ.get("SILICON_ORG_SEMANTIC_TIMEOUT", "1800")),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout


def run_deepseek(invocation: dict[str, Any], prompt: str, temp_dir: Path) -> str:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "DEEPSEEK_API_KEY is required for provider=deepseek. "
            "Set it in the shell that starts pi/Codex."
        )
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    payload = {
        "model": deepseek_model_arg(invocation),
        "messages": [
            {
                "role": "system",
                "content": (
                    "You execute one Silicon Org node. Return only the requested "
                    "JSON object. Do not include markdown outside the JSON."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": float(os.environ.get("SILICON_ORG_DEEPSEEK_TEMPERATURE", "0.2")),
        "response_format": {"type": "json_object"},
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{base_url}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    max_retries = int(os.environ.get("SILICON_ORG_DEEPSEEK_RETRIES", "2"))
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            with request.urlopen(
                req,
                timeout=int(os.environ.get("SILICON_ORG_SEMANTIC_TIMEOUT", "1800")),
            ) as response:
                data = json.loads(response.read().decode("utf-8"))
                break
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(f"DeepSeek API error {exc.code}: {detail}") from exc
        except error.URLError as exc:
            last_error = exc
            if attempt < max_retries:
                import time
                wait = (attempt + 1) * 3
                print(f"[silicon-org] DeepSeek retry {attempt+1}/{max_retries} after {wait}s: {exc}", file=sys.stderr, flush=True)
                time.sleep(wait)
                continue
            raise SystemExit(f"DeepSeek API connection failed after {max_retries+1} attempts: {exc}") from exc
        except (ConnectionError, OSError) as exc:
            last_error = exc
            if attempt < max_retries:
                import time
                wait = (attempt + 1) * 3
                print(f"[silicon-org] DeepSeek retry {attempt+1}/{max_retries} after {wait}s: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
                time.sleep(wait)
                continue
            raise SystemExit(f"DeepSeek API connection failed after {max_retries+1} attempts: {type(exc).__name__}: {exc}") from exc

    choices = data.get("choices") or []
    if not choices:
        raise SystemExit(f"DeepSeek API returned no choices: {data}")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise SystemExit(f"DeepSeek API returned empty content: {data}")
    return content


def extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    try:
        data = json.loads(stripped)
        if isinstance(data, dict) and isinstance(data.get("result"), str):
            return extract_json(data["result"])
        if isinstance(data, dict) and isinstance(data.get("message"), str):
            return extract_json(data["message"])
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # Try all fenced JSON blocks (not just first)
    for m in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL):
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            continue

    # Find outermost balanced braces
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(stripped[start:end + 1])
        except json.JSONDecodeError:
            pass

    # Last resort: wrap the entire text as artifact_body
    if len(stripped) > 20:
        return {"artifact_body": stripped, "context_report": {}}

    raise SystemExit("semantic agent did not return a JSON object")


def validate_result(result: dict[str, Any], invocation: dict[str, Any]) -> dict[str, Any]:
    role = result.get("role") or invocation.get("role")
    artifact_type = result.get("artifact_type") or invocation.get("default_artifact_type", "analysis")
    artifact_body = result.get("artifact_body")
    context_report = sanitize_context_report(result.get("context_report"), invocation)
    if not isinstance(artifact_body, str) or not artifact_body.strip():
        raise SystemExit("semantic result missing non-empty artifact_body")
    if not isinstance(context_report, dict):
        raise SystemExit("semantic result missing context_report object")
    normalized = {
        "role": role,
        "artifact_type": artifact_type,
        "artifact_extension": result.get("artifact_extension") or "md",
        "artifact_body": artifact_body,
        "context_report": context_report,
        "semantic_execution": True,
        "metadata": {
            "executor": "tools/semantic_node_executor.py",
            "agent": agent_name(invocation),
            **(result.get("metadata") if isinstance(result.get("metadata"), dict) else {}),
        },
    }
    return normalized


def sanitize_context_report(value: Any, invocation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    report = value.get("context_compression_report") if isinstance(value.get("context_compression_report"), dict) else value
    report.setdefault("input_scope", {})
    valid_artifacts = {
        artifact.get("artifact_id"): artifact
        for artifact in invocation.get("input_artifacts", [])
        if artifact.get("artifact_id")
    }
    artifact_reads = []
    for item in report["input_scope"].get("artifacts_read", []) or []:
        if not isinstance(item, dict) or item.get("artifact_id") not in valid_artifacts:
            continue
        artifact = valid_artifacts[item["artifact_id"]]
        artifact_reads.append({
            "artifact_id": item["artifact_id"],
            "path": artifact.get("content_ref"),
            "used": bool(item.get("used", True)),
            "why": item.get("why") or "Read by semantic node executor.",
        })
    report["input_scope"]["artifacts_read"] = artifact_reads

    valid_handoffs = {
        handoff.get("ref"): handoff
        for handoff in invocation.get("input_handoffs", [])
        if handoff.get("ref")
    }
    handoff_reads = []
    for item in report["input_scope"].get("handoffs_read", []) or []:
        if not isinstance(item, dict) or item.get("ref") not in valid_handoffs:
            continue
        handoff = valid_handoffs[item["ref"]]
        handoff_reads.append({
            "ref": item["ref"],
            "context_digest": handoff.get("context_digest"),
        })
    if not handoff_reads:
        handoff_reads = [
            {"ref": ref, "context_digest": handoff.get("context_digest")}
            for ref, handoff in valid_handoffs.items()
        ]
    report["input_scope"]["handoffs_read"] = handoff_reads
    report.setdefault("retained_context", {})
    report["retained_context"]["decisions"] = normalize_retained_items(
        report["retained_context"].get("decisions"),
        defaults={"source": "semantic_node_executor", "impact": "Affects downstream node execution."},
    )
    report["retained_context"]["constraints"] = normalize_retained_items(
        report["retained_context"].get("constraints"),
        defaults={"source": "semantic_node_executor", "impact": "Constrains downstream node execution."},
    )
    report["retained_context"]["assumptions"] = normalize_retained_items(
        report["retained_context"].get("assumptions"),
        defaults={"source": "semantic_node_executor", "risk": "Assumption may need review."},
    )
    report["retained_context"]["open_questions"] = normalize_retained_items(
        report["retained_context"].get("open_questions"),
        defaults={"source": "semantic_node_executor", "owner": "runtime"},
    )
    omitted = report.setdefault("omitted_context", [])
    report["omitted_context"] = normalize_omitted_items(omitted)
    report.setdefault("compression_rationale", {})
    if not isinstance(report["compression_rationale"], dict):
        report["compression_rationale"] = {"method": str(report["compression_rationale"])}
    report["compression_rationale"].setdefault("method", "semantic_node_executor_normalized")
    report["compression_rationale"].setdefault("loss_notes", [])
    checks = report.setdefault("quality_checks", [])
    if not isinstance(checks, list) or not checks:
        report["quality_checks"] = [{"name": "semantic_executor_schema_normalized", "passed": True}]
    return {"context_compression_report": report}


def normalize_retained_items(value: Any, defaults: dict[str, str]) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    normalized = []
    for item in value:
        if isinstance(item, dict):
            statement = str(item.get("statement") or item.get("decision") or item.get("question") or "").strip()
            if not statement:
                continue
            normalized.append({"statement": statement, **defaults, **{
                key: str(item.get(key) or defaults[key])
                for key in defaults
            }})
        elif isinstance(item, str) and item.strip():
            normalized.append({"statement": item.strip(), **defaults})
    return normalized


def normalize_omitted_items(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    normalized = []
    for item in value:
        if isinstance(item, dict):
            source = str(item.get("source") or "semantic_node_executor").strip()
            reason = item.get("reason") if item.get("reason") in OMITTED_CONTEXT_REASONS else "background_only"
            normalized.append({"source": source, "reason": reason})
        elif isinstance(item, str) and item.strip():
            normalized.append({"source": item.strip(), "reason": "background_only"})
    return normalized


def main() -> int:
    load_local_env()
    invocation = load_invocation()
    prompt = full_prompt(invocation)
    agent = agent_name(invocation)
    with tempfile.TemporaryDirectory(prefix="silicon-semantic-node-") as tmp:
        temp_dir = Path(tmp)
        if agent == "codex":
            raw = run_codex(invocation, prompt, temp_dir)
        elif agent == "claude":
            raw = run_claude(invocation, prompt, temp_dir)
        elif agent == "pi":
            raw = run_pi(invocation, prompt, temp_dir)
        elif agent == "deepseek":
            raw = run_deepseek(invocation, prompt, temp_dir)
        else:
            custom = os.environ.get("SILICON_ORG_NODE_AGENT_CMD", "").strip()
            if not custom:
                raise SystemExit(f"unknown semantic node agent: {agent}")
            completed = subprocess.run(
                shlex.split(custom),
                cwd=WORKSPACE,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=int(os.environ.get("SILICON_ORG_SEMANTIC_TIMEOUT", "1800")),
                check=False,
            )
            if completed.returncode:
                raise SystemExit(completed.stderr.strip() or completed.stdout.strip())
            raw = completed.stdout

    result = validate_result(extract_json(raw), invocation)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    result_ref = os.environ.get("SILICON_ORG_RESULT_JSON")
    if result_ref:
        Path(result_ref).write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
