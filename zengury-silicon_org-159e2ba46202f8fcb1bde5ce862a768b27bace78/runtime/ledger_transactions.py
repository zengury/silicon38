"""Ledger transaction helpers for LangGraph-native runtime nodes.

This module is the runtime-facing API over the existing `tools/ledger.py`
command surface. It keeps LangGraph nodes from scattering YAML mutations while
the legacy ledger CLI is gradually factored into a library.
"""

from __future__ import annotations

from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
import fcntl
import io
from pathlib import Path
import threading
from typing import Any

import yaml

from learning.proposals import aggregate_learning_proposals, trace_learning_proposals
from learning.signals import relation_signal, role_signal
from tools import ledger

from .node_runner import NodeRunRequest, NodeRunResult


ROOT_DIR = Path(__file__).resolve().parent.parent
TRACES_DIR = ROOT_DIR / "traces"
NODES_PATH = ROOT_DIR / "ontology" / "nodes.yaml"
_LOCKS_GUARD = threading.Lock()
_TASK_LOCKS: dict[str, threading.RLock] = {}
_LOCK_DEPTH = threading.local()


class LedgerTransactionError(RuntimeError):
    """Raised when a Ledger transaction is rejected by Policy/Ledger."""


@dataclass(frozen=True)
class LedgerRoleCommit:
    role: str
    artifact_id: str
    artifact_ref: str
    context_report_ref: str
    context_report_digest: str
    status: str


@dataclass(frozen=True)
class LedgerLearningCommit:
    ref: str
    role_signal_count: int
    relation_signal_count: int
    proposal_count: int


def _safe_ext(extension: str) -> str:
    cleaned = extension.strip().lstrip(".") or "md"
    allowed = {"md", "txt", "yaml", "yml", "json"}
    return cleaned if cleaned in allowed else "md"


@contextmanager
def _ledger_lock(task_id: str | None):
    """Serialize Ledger YAML mutations during LangGraph parallel fan-out."""

    key = task_id or "global"
    with _LOCKS_GUARD:
        lock = _TASK_LOCKS.setdefault(key, threading.RLock())

    depth = getattr(_LOCK_DEPTH, "by_key", {})
    if depth.get(key, 0):
        with lock:
            depth[key] = depth.get(key, 0) + 1
            _LOCK_DEPTH.by_key = depth
            try:
                yield
            finally:
                depth[key] -= 1
        return

    lock_path = TRACES_DIR / key / ".ledger.lock" if task_id else TRACES_DIR / ".ledger.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock:
        with open(lock_path, "a", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            depth[key] = depth.get(key, 0) + 1
            _LOCK_DEPTH.by_key = depth
            try:
                yield
            finally:
                depth[key] -= 1
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _task_id_from_args(args: list[str]) -> str | None:
    return args[0] if args and isinstance(args[0], str) else None


def _call_ledger(func: Any, args: list[str]) -> str:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with _ledger_lock(_task_id_from_args(args)):
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                func(args)
            except SystemExit as exc:
                if exc.code:
                    detail = stderr.getvalue().strip() or stdout.getvalue().strip()
                    raise LedgerTransactionError(detail or f"ledger exited with {exc.code}") from exc
    return stdout.getvalue()


def _call_ledger_raw(func: Any, *args: Any) -> str:
    stdout = io.StringIO()
    stderr = io.StringIO()
    task_id = args[0] if args and isinstance(args[0], str) else None
    with _ledger_lock(task_id):
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                func(*args)
            except SystemExit as exc:
                if exc.code:
                    detail = stderr.getvalue().strip() or stdout.getvalue().strip()
                    raise LedgerTransactionError(detail or f"ledger exited with {exc.code}") from exc
    return stdout.getvalue()


class LedgerTransaction:
    """Idempotent runtime write API for one Silicon Org task."""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.task_dir = TRACES_DIR / task_id

    def manifest_path(self) -> Path:
        return self.task_dir / "manifest.yaml"

    def state_path(self) -> Path:
        return self.task_dir / "state.yaml"

    def artifact_dir(self) -> Path:
        return self.task_dir / "artifacts"

    def load_manifest(self) -> dict[str, Any]:
        return ledger.load_yaml(self.manifest_path())

    def load_state(self) -> dict[str, Any]:
        return ledger.load_yaml(self.state_path())

    def load_nodes(self) -> dict[str, dict[str, Any]]:
        data = ledger.load_yaml(NODES_PATH)
        return {node.get("role"): node for node in data.get("nodes", [])}

    def repo_text(self, ref: str | None) -> str:
        if not ref:
            return ""
        path = ROOT_DIR / ref
        if not path.exists() or not path.is_file():
            return ""
        return path.read_text(encoding="utf-8")

    def ensure_task_initialized(self, task_type: str, summary: str) -> None:
        if self.manifest_path().exists() and self.state_path().exists():
            return
        _call_ledger(ledger.cmd_init, [self.task_id, task_type, summary])

    def save_workspace_dir(self, workspace_dir: str) -> None:
        if not workspace_dir:
            return
        manifest = self.load_manifest()
        if manifest.get("workspace_dir"):
            return
        manifest["workspace_dir"] = workspace_dir
        self.manifest_path().write_text(
            yaml.dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def commit_node_activation(self, role: str, *, entry: bool = False) -> None:
        state = self.load_state()
        status = state.get("node_states", {}).get(role, {}).get("status")
        if status in {"activated", "completed"}:
            return
        args = [self.task_id, role, "activated"]
        if entry:
            args.append("--set-entry")
        _call_ledger(ledger.cmd_node, args)

    def commit_handoff(
        self,
        from_role: str,
        to_role: str,
        relation_type: str,
        focus: str,
    ) -> str:
        for handoff in ledger.load_handoffs(self.task_id):
            if (
                handoff.get("from") == from_role
                and handoff.get("to") == to_role
                and handoff.get("relation_type") == relation_type
            ):
                return handoff.get("_ref", "")
        _call_ledger(
            ledger.cmd_handoff,
            [self.task_id, from_role, to_role, relation_type, focus],
        )
        for handoff in reversed(ledger.load_handoffs(self.task_id)):
            if (
                handoff.get("from") == from_role
                and handoff.get("to") == to_role
                and handoff.get("relation_type") == relation_type
            ):
                return handoff.get("_ref", "")
        return ""

    def activation_decision_exists(
        self,
        from_role: str,
        to_role: str,
        relation_type: str,
    ) -> bool:
        events = ledger.load_yaml(self.task_dir / "events.yaml").get("events", [])
        for event in events:
            if event.get("event_type") != "activation_decision":
                continue
            payload = event.get("payload") or {}
            if (
                payload.get("from") == from_role
                and payload.get("to") == to_role
                and payload.get("relation_type") == relation_type
            ):
                return True
        return False

    def commit_activation_decision(
        self,
        from_role: str,
        to_role: str,
        relation_type: str,
        decision: str,
        reason: str,
    ) -> None:
        if self.activation_decision_exists(from_role, to_role, relation_type):
            return
        _call_ledger(
            ledger.cmd_activation_decision,
            [
                self.task_id,
                from_role,
                to_role,
                relation_type,
                decision,
                reason,
            ],
        )

    def _write_artifact_body(
        self,
        role: str,
        artifact_type: str,
        extension: str,
        body: str,
        iteration: int,
    ) -> tuple[str, str]:
        artifact_id = f"{role}-{artifact_type}-v{iteration}"
        rel_ref = f"artifacts/{artifact_id}.{_safe_ext(extension)}"
        path = self.task_dir / rel_ref
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_text(encoding="utf-8") != body:
            path.write_text(body, encoding="utf-8")
        return artifact_id, rel_ref

    def _register_artifact(
        self,
        role: str,
        artifact_type: str,
        artifact_ref: str,
        iteration: int,
    ) -> str:
        artifact_id = f"{role}-{artifact_type}-v{iteration}"
        state = self.load_state()
        if artifact_id in state.get("artifact_registry", {}):
            return artifact_id
        _call_ledger(
            ledger.cmd_artifact,
            [
                self.task_id,
                role,
                artifact_type,
                artifact_ref,
                f"--iteration={iteration}",
            ],
        )
        return artifact_id

    def _incoming_handoff_inputs(self, role: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        handoffs_read: list[dict[str, Any]] = []
        artifacts_read_by_id: dict[str, dict[str, Any]] = {}
        for handoff in ledger.load_handoffs(self.task_id):
            if handoff.get("to") != role:
                continue
            block = handoff.get("context_block") or {}
            handoffs_read.append({
                "ref": handoff.get("_ref"),
                "context_digest": block.get("context_digest"),
            })
            deliverable = handoff.get("deliverable") or {}
            for artifact in deliverable.get("artifacts") or []:
                artifact_id = artifact.get("artifact_id")
                if not artifact_id:
                    continue
                artifacts_read_by_id[artifact_id] = {
                    "artifact_id": artifact_id,
                    "path": artifact.get("content_ref"),
                    "used": True,
                    "why": f"Received through handoff {handoff.get('_ref')}",
                }
        return list(artifacts_read_by_id.values()), handoffs_read

    def incoming_execution_inputs(
        self,
        role: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        state = self.load_state()
        artifacts = state.get("artifact_registry", {})
        input_artifacts: dict[str, dict[str, Any]] = {}
        input_handoffs = []
        for handoff in ledger.load_handoffs(self.task_id):
            if handoff.get("to") != role:
                continue
            block = handoff.get("context_block") or {}
            input_handoffs.append({
                "ref": handoff.get("_ref"),
                "from": handoff.get("from"),
                "to": handoff.get("to"),
                "relation_type": handoff.get("relation_type"),
                "context_digest": block.get("context_digest"),
                "deliverable": handoff.get("deliverable"),
                "context_block": block,
            })
            refs = (
                (handoff.get("deliverable") or {}).get("artifact_refs")
                or handoff.get("artifact_refs")
                or []
            )
            for artifact_id in refs:
                artifact = artifacts.get(artifact_id) or {}
                content_ref = artifact.get("content_ref")
                body = ""
                if content_ref:
                    path = self.task_dir / content_ref
                    if path.exists() and path.is_file():
                        body = path.read_text(encoding="utf-8")
                input_artifacts[artifact_id] = {
                    "artifact_id": artifact_id,
                    "producer": artifact.get("producer"),
                    "type": artifact.get("type"),
                    "status": artifact.get("status"),
                    "content_ref": content_ref,
                    "body": body,
                }
        return list(input_artifacts.values()), input_handoffs

    def build_node_run_request(
        self,
        *,
        task_type: str,
        task_description: str,
        workspace_dir: str = "",
        role: str,
        harness_profile: Any,
        model_selection: Any,
        candidate: dict[str, Any],
        input_handoff_ref: str = "",
    ) -> NodeRunRequest:
        nodes = self.load_nodes()
        node = nodes.get(role, {})
        registry_ref = node.get("harness_ref") or f"org/registry/{role}.md"
        skill_ref = node.get("skill_ref") or ""
        skill_file = f"{skill_ref}/SKILL.md" if skill_ref else ""
        input_artifacts, input_handoffs = self.incoming_execution_inputs(role)
        return NodeRunRequest(
            task_id=self.task_id,
            task_type=task_type,
            task_description=task_description,
            role=role,
            workspace_dir=workspace_dir,
            harness_profile=harness_profile,
            model_selection=model_selection,
            candidate=candidate,
            input_handoff_ref=input_handoff_ref,
            input_artifacts=input_artifacts,
            input_handoffs=input_handoffs,
            registry_ref=registry_ref,
            registry_text=self.repo_text(registry_ref),
            skill_ref=skill_ref,
            skill_text=self.repo_text(skill_file),
        )

    def build_context_report(
        self,
        role: str,
        result: NodeRunResult,
        artifact_id: str,
    ) -> dict[str, Any]:
        if result.context_report:
            # Sanitize: ensure compression_rationale.loss_notes is a list
            report = result.context_report
            if isinstance(report, dict):
                ccr = report.get("context_compression_report", report)
                cr = ccr.get("compression_rationale", {})
                if isinstance(cr, dict) and not isinstance(cr.get("loss_notes"), list):
                    cr["loss_notes"] = [str(cr["loss_notes"])] if cr.get("loss_notes") is not None else []
            return report
        artifacts_read, handoffs_read = self._incoming_handoff_inputs(role)
        dry_run = result.metadata.get("runner") == "harness_dry_run"
        assumptions = []
        if dry_run:
            assumptions.append({
                "statement": (
                    "This execution used the harness dry-run runner instead of "
                    "an isolated semantic subagent."
                ),
                "source": "runtime/node_runner.py",
                "risk": "Artifact content proves plumbing only; replace runner before production use.",
            })
        return {
            "context_compression_report": {
                "input_scope": {
                    "artifacts_read": artifacts_read,
                    "handoffs_read": handoffs_read,
                },
                "retained_context": {
                    "decisions": [{
                        "statement": f"{role} produced artifact {artifact_id}.",
                        "source": artifact_id,
                        "impact": "Downstream nodes can consume the registered artifact.",
                    }],
                    "constraints": [],
                    "assumptions": assumptions,
                    "open_questions": [],
                },
                "omitted_context": [],
                "compression_rationale": {
                    "method": "ledger_transaction_generated_minimal_report",
                    "loss_notes": [],
                },
                "quality_checks": [{
                    "name": "context_report_schema_complete",
                    "passed": True,
                }],
            }
        }

    def register_context_report(
        self,
        role: str,
        report: dict[str, Any],
        iteration: int,
    ) -> tuple[str, str]:
        ref = f"artifacts/{role}-context-report-v{iteration}.yaml"
        path = self.task_dir / ref
        path.parent.mkdir(parents=True, exist_ok=True)
        body = yaml.dump(report, allow_unicode=True, sort_keys=False)
        if not path.exists() or path.read_text(encoding="utf-8") != body:
            path.write_text(body, encoding="utf-8")

        normalized = report.get("context_compression_report") or report
        digest = ledger.stable_digest(normalized)
        state = self.load_state()
        registered = state.get("context_compression_reports", {}).get(role, {})
        if registered.get("digest") == digest and registered.get("ref") == ref:
            return ref, digest

        _call_ledger(ledger.cmd_context_report, [self.task_id, role, ref])
        return ref, digest

    def commit_node_completion(self, role: str) -> None:
        state = self.load_state()
        if state.get("node_states", {}).get(role, {}).get("status") == "completed":
            return
        _call_ledger(ledger.cmd_node, [self.task_id, role, "completed"])

    def resolve_artifact_approvals(self) -> None:
        """Approve draft artifacts whose review requirements are satisfied.

        An artifact moves draft -> approved once its producer role has
        completed and any role with a "required" blocking `evaluates`
        edge onto the producer has also completed. Producers with no
        required evaluator are approved as soon as they complete.
        """
        state = self.load_state()
        node_states = state.get("node_states", {})
        artifacts = state.get("artifact_registry", {})

        required_evaluators: dict[str, list[str]] = {}
        for rel in ledger.load_relations():
            if rel.get("type") != "evaluates":
                continue
            blocking = rel.get("weights", {}).get("blocking")
            blocking_value = blocking.get("value") if isinstance(blocking, dict) else blocking
            if blocking_value != "required":
                continue
            required_evaluators.setdefault(rel.get("to"), []).append(rel.get("from"))

        for artifact_id, artifact in artifacts.items():
            if artifact.get("status") != "draft":
                continue
            producer = artifact.get("producer")
            if node_states.get(producer, {}).get("status") != "completed":
                continue
            evaluators = required_evaluators.get(producer, [])
            if all(node_states.get(ev, {}).get("status") == "completed" for ev in evaluators):
                _call_ledger(ledger.cmd_artifact_status, [self.task_id, artifact_id, "approved"])

    def commit_delivery(self, status: str, summary: str) -> None:
        manifest = self.load_manifest()
        if manifest.get("outcome"):
            return
        _call_ledger(ledger.cmd_deliver, [self.task_id, status, summary])

    def run_convergence_check(self) -> dict[str, Any]:
        """Recompute convergence gates (ledger.cmd_converge) and return them."""

        _call_ledger(ledger.cmd_converge, [self.task_id])
        return self.load_state().get("convergence") or {}

    def commit_learning_snapshot(self) -> LedgerLearningCommit:
        manifest = self.load_manifest()
        state = self.load_state()
        timestamp = ledger.now()

        role_signals = []
        for role in manifest.get("terminal_nodes", []):
            signal = role_signal(manifest, role)
            role_signals.append({
                "role": role,
                "signal": signal.value,
                "confidence": signal.confidence,
                "source": signal.source,
                "detail": signal.detail,
            })

        relation_signals = []
        for handoff in manifest.get("handoff_trail", []):
            signal = relation_signal(manifest, handoff)
            relation_signals.append({
                "from": handoff.get("from"),
                "to": handoff.get("to"),
                "relation_type": handoff.get("relation_type"),
                "signal": signal.value,
                "confidence": signal.confidence,
                "source": signal.source,
                "detail": signal.detail,
            })

        proposals = trace_learning_proposals(self.task_id, manifest, state)
        proposals.extend(aggregate_learning_proposals(ROOT_DIR, self.task_id, manifest, state))
        snapshot = {
            "schema": "silicon_org.trace_learning_snapshot.v1",
            "task_id": self.task_id,
            "timestamp": timestamp,
            "outcome": manifest.get("outcome"),
            "role_signals": role_signals,
            "relation_signals": relation_signals,
            "proposals": proposals,
        }
        ref = "learning.yaml"
        ledger.save_yaml(self.task_dir / ref, snapshot)
        _call_ledger_raw(ledger.add_event, self.task_id, "learning_snapshot_written", {
            "ref": ref,
            "role_signal_count": len(role_signals),
            "relation_signal_count": len(relation_signals),
            "proposal_count": len(proposals),
        })
        return LedgerLearningCommit(
            ref=ref,
            role_signal_count=len(role_signals),
            relation_signal_count=len(relation_signals),
            proposal_count=len(proposals),
        )

    def commit_role_result(
        self,
        result: NodeRunResult,
        *,
        candidate: dict[str, Any] | None = None,
        entry: bool = False,
        task_type: str = "unknown",
        task_summary: str = "",
    ) -> LedgerRoleCommit:
        with _ledger_lock(self.task_id):
            role = result.role
            self.ensure_task_initialized(task_type, task_summary)

            candidate = candidate or {}
            relation_type = candidate.get("relation_type")
            from_role = candidate.get("from")
            if not entry and relation_type and relation_type != "entry" and from_role:
                self.commit_handoff(
                    from_role,
                    role,
                    relation_type,
                    candidate.get("condition") or f"Activate {role} from {from_role}",
                )

            self.commit_node_activation(role, entry=entry)
            state = self.load_state()
            iteration = state.get("node_states", {}).get(role, {}).get("iteration") or 1
            artifact_id, artifact_ref = self._write_artifact_body(
                role,
                result.artifact_type,
                result.artifact_extension,
                result.artifact_body,
                iteration,
            )
            artifact_id = self._register_artifact(
                role,
                result.artifact_type,
                artifact_ref,
                iteration,
            )
            report = self.build_context_report(role, result, artifact_id)
            report_ref, report_digest = self.register_context_report(role, report, iteration)
            self.commit_node_completion(role)
            self.resolve_artifact_approvals()
            return LedgerRoleCommit(
                role=role,
                artifact_id=artifact_id,
                artifact_ref=artifact_ref,
                context_report_ref=report_ref,
                context_report_digest=report_digest,
                status="completed",
            )
