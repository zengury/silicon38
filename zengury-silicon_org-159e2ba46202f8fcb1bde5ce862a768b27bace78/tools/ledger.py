#!/usr/bin/env python3
"""Silicon Org — Ledger CLI. All state writes go through this tool."""

import sys
import yaml
import hashlib
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from learning.proposals import (  # noqa: E402
    aggregate_learning_proposals,
    trace_learning_proposals,
)
from learning.signals import relation_signal, role_signal  # noqa: E402
from tools.policy import (  # noqa: E402
    ACTIVATION_DECISIONS,
    ACTIVATION_RELATION_TYPES,
    EVALUATION_RELATION_TYPES,
    candidate_activations,
    context_report_issues,
    context_report_source_issues,
    enforce_activation_allowed,
    enforce_activation_decision_allowed,
    enforce_completion_allowed,
    enforce_context_report_sources_valid,
    enforce_context_report_valid,
    enforce_delivery_policy,
    get_node,
    handoff_relation_matches,
    load_handoffs,
    load_relations,
    load_nodes,
    role_artifact_ids,
    role_has_artifact,
    stable_digest,
    valid_handoff_payload,
    valid_handoffs_for_activation,
)

TRACES_DIR = ROOT_DIR / "traces"
CONTEXT_BLOCK_PATH = ROOT_DIR / "org" / "CONTEXT_BLOCK.md"

def now():
    return datetime.now(timezone.utc).isoformat()

def load_yaml(path):
    if Path(path).exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}

def save_yaml(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    with os.fdopen(fd, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def learning_index_path():
    return TRACES_DIR / "index_learning_proposals.yaml"


def load_learning_index():
    return load_yaml(learning_index_path())


def save_learning_index(data):
    save_yaml(learning_index_path(), data)

def context_block_snapshot():
    if not CONTEXT_BLOCK_PATH.exists():
        fail("missing org/CONTEXT_BLOCK.md; cannot initialize trace without continuity anchor")
    body = CONTEXT_BLOCK_PATH.read_bytes()
    return {
        "ref": str(CONTEXT_BLOCK_PATH.relative_to(ROOT_DIR)),
        "sha256": hashlib.sha256(body).hexdigest(),
    }

def add_event(task_id, event_type, payload):
    events = load_yaml(TRACES_DIR / task_id / "events.yaml")
    events.setdefault("events", [])
    ev_id = f"ev-{len(events.get('events', [])) + 1:03d}"
    events["events"].append({
        "event_id": ev_id,
        "timestamp": now(),
        "event_type": event_type,
        "payload": payload,
    })
    save_yaml(TRACES_DIR / task_id / "events.yaml", events)
    print(f"Event {ev_id}: {event_type}")

def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(2)

def cmd_init(args):
    """ledger init <task_id> <task_type> <summary>"""
    task_id, task_type, summary = args[0], args[1], ' '.join(args[2:])
    task_dir = TRACES_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "artifacts").mkdir(exist_ok=True)
    (task_dir / "handoffs").mkdir(exist_ok=True)

    manifest = {
        "task_id": task_id,
        "timestamp_start": now(),
        "timestamp_end": None,
        "task_summary": summary,
        "task_type": task_type,
        "entry_nodes": [],
        "terminal_nodes": [],
        "outcome": None,
        "context_block": context_block_snapshot(),
        "artifact_index": [],
        "context_report_index": [],
        "handoff_trail": [],
    }
    save_yaml(task_dir / "manifest.yaml", manifest)

    state = {
        "task_id": task_id,
        "task_status": "initializing",
        "node_states": {},
        "artifact_registry": {},
        "context_compression_reports": {},
        "loop_states": [],
        "join_gates": [],
        "convergence": {
            "all_non_loop_nodes_settled": False,
            "all_loops_resolved": False,
            "all_blocking_evals_resolved": False,
            "all_joins_passed": False,
            "all_artifacts_resolved": False,
            "no_undecided_activation_candidates": False,
            "settled_at": None,
        },
    }
    save_yaml(task_dir / "state.yaml", state)

    events = {
        "task_id": task_id,
        "events": [{
            "event_id": "ev-001",
            "timestamp": now(),
            "event_type": "task_started",
            "payload": {"detail": summary},
        }],
    }
    save_yaml(task_dir / "events.yaml", events)

    print(f"Ledger initialized: {task_dir}")


def cmd_event(args):
    """ledger event <task_id> <event_type> <detail>"""
    task_id, event_type, detail = args[0], args[1], ' '.join(args[2:])
    add_event(task_id, event_type, {"detail": detail})


def cmd_context(args):
    """ledger context — print the current Context Block reference and digest"""
    print(yaml.dump(context_block_snapshot(), default_flow_style=False, sort_keys=False).strip())


def cmd_node(args):
    """ledger node <task_id> <role> <status> [--set-entry]"""
    task_id, role, status = args[0], args[1], args[2]
    set_entry = "--set-entry" in args

    state = load_yaml(TRACES_DIR / task_id / "state.yaml")
    previous_task_status = state.get("task_status")
    if "node_states" not in state:
        state["node_states"] = {}

    node = get_node(role)

    if status == "activated":
        enforce_activation_allowed(task_id, state, role, set_entry)

    if status == "completed":
        enforce_completion_allowed(state, role)

    ts = now()
    previous_node_state = state["node_states"].get(role, {})
    iteration = previous_node_state.get("iteration", 0)
    if status == "activated":
        iteration += 1
    elif iteration == 0:
        iteration = 1

    node_state = {
        "status": status,
        "updated_at": ts,
        "activated_at": previous_node_state.get("activated_at"),
        "completed_at": previous_node_state.get("completed_at"),
        "iteration": iteration,
        "output_artifact_ids": previous_node_state.get("output_artifact_ids", []),
        "blocked_reason": previous_node_state.get("blocked_reason"),
    }
    if status == "activated":
        node_state["activated_at"] = ts
        node_state["completed_at"] = None
        node_state["blocked_reason"] = None
    elif status == "completed":
        node_state["completed_at"] = ts
        node_state["output_artifact_ids"] = role_artifact_ids(state, role)
        node_state["blocked_reason"] = None
    elif status == "blocked":
        node_state["blocked_reason"] = " ".join(
            a for a in args[3:] if a != "--set-entry"
        ) or previous_node_state.get("blocked_reason")
    state["node_states"][role] = node_state
    if previous_node_state.get("entry_node"):
        state["node_states"][role]["entry_node"] = True

    if status == "completed":
        manifest = load_yaml(TRACES_DIR / task_id / "manifest.yaml")
        if role not in manifest.get("terminal_nodes", []):
            manifest.setdefault("terminal_nodes", []).append(role)
        save_yaml(TRACES_DIR / task_id / "manifest.yaml", manifest)

    if set_entry:
        manifest = load_yaml(TRACES_DIR / task_id / "manifest.yaml")
        if role not in manifest.get("entry_nodes", []):
            manifest.setdefault("entry_nodes", []).append(role)
        save_yaml(TRACES_DIR / task_id / "manifest.yaml", manifest)
        state["node_states"][role]["entry_node"] = True

    if not (node.get("meta") and previous_task_status == "delivered"):
        state["task_status"] = "propagating"
    save_yaml(TRACES_DIR / task_id / "state.yaml", state)

    # Auto-event
    cmd_event([task_id, f"node_{status}", f"{role}: {status}"])


def cmd_artifact(args):
    """ledger artifact <task_id> <role> <artifact_type> <file_path> [--iteration N]"""
    task_id, role, atype, file_path = args[0], args[1], args[2], args[3]
    get_node(role)
    iteration = 1
    for a in args:
        if a.startswith("--iteration="):
            iteration = int(a.split("=")[1])

    artifact_id = f"{role}-{atype}-v{iteration}"

    state = load_yaml(TRACES_DIR / task_id / "state.yaml")
    state.setdefault("artifact_registry", {})
    state["artifact_registry"][artifact_id] = {
        "type": atype,
        "producer": role,
        "version": iteration,
        "status": "draft",
        "superseded_by": None,
        "content_ref": file_path,
        "consumers_pending": [],
        "registered_at": now(),
    }
    if role in state.get("node_states", {}):
        state["node_states"][role].setdefault("output_artifact_ids", [])
        if artifact_id not in state["node_states"][role]["output_artifact_ids"]:
            state["node_states"][role]["output_artifact_ids"].append(artifact_id)
    save_yaml(TRACES_DIR / task_id / "state.yaml", state)

    # Write provenance sidecar
    provenance = {
        "artifact_id": artifact_id,
        "producer": role,
        "task_id": task_id,
        "version": iteration,
        "timestamp": now(),
        "input_artifacts": [],
        "quality_checks": [],
        "status": "draft",
    }
    artifact_path = TRACES_DIR / task_id / "artifacts" / f"{artifact_id}.provenance.yaml"
    save_yaml(artifact_path, provenance)

    # Update manifest artifact index
    manifest = load_yaml(TRACES_DIR / task_id / "manifest.yaml")
    manifest.setdefault("artifact_index", []).append({
        "artifact_id": artifact_id,
        "type": atype,
        "producer": role,
        "version": iteration,
        "status": "draft",
        "path": file_path,
        "ref": file_path,
        "provenance_ref": f"artifacts/{artifact_id}.provenance.yaml",
    })
    save_yaml(TRACES_DIR / task_id / "manifest.yaml", manifest)

    print(f"Artifact registered: {artifact_id}")


def cmd_artifact_status(args):
    """ledger artifact-status <task_id> <artifact_id> <status>"""
    task_id, artifact_id, status = args[0], args[1], args[2]
    state = load_yaml(TRACES_DIR / task_id / "state.yaml")
    if artifact_id not in state.get("artifact_registry", {}):
        fail(f"unknown artifact_id: {artifact_id}")

    manifest = load_yaml(TRACES_DIR / task_id / "manifest.yaml")
    found_manifest_artifact = False
    for artifact in manifest.get("artifact_index", []):
        if artifact.get("artifact_id") == artifact_id:
            artifact["status"] = status
            found_manifest_artifact = True
    if not found_manifest_artifact:
        fail(f"artifact_id {artifact_id} is missing from manifest artifact_index")
    save_yaml(TRACES_DIR / task_id / "manifest.yaml", manifest)

    # Update provenance
    prov_path = TRACES_DIR / task_id / "artifacts" / f"{artifact_id}.provenance.yaml"
    if not prov_path.exists():
        fail(f"provenance sidecar missing: artifacts/{artifact_id}.provenance.yaml")

    state["artifact_registry"][artifact_id]["status"] = status
    save_yaml(TRACES_DIR / task_id / "state.yaml", state)
    prov = load_yaml(prov_path)
    prov["status"] = status
    save_yaml(prov_path, prov)
    print(f"{artifact_id} → {status}")


def resolve_task_ref(task_id, file_path):
    path = Path(file_path)
    if path.is_absolute() and path.exists():
        return path, str(path)
    task_relative = TRACES_DIR / task_id / file_path
    if task_relative.exists():
        return task_relative, file_path
    repo_relative = ROOT_DIR / file_path
    if repo_relative.exists():
        return repo_relative, file_path
    fail(f"file does not exist for task {task_id}: {file_path}")


def cmd_context_report(args):
    """ledger context-report <task_id> <role> <file_path>"""
    if len(args) < 3:
        fail("usage: ledger context-report <task_id> <role> <file_path>")
    task_id, role, file_path = args[0], args[1], args[2]
    get_node(role)
    path, ref = resolve_task_ref(task_id, file_path)
    report = enforce_context_report_valid(load_yaml(path))

    state = load_yaml(TRACES_DIR / task_id / "state.yaml")
    if not role_has_artifact(state, role):
        fail(
            f"cannot register context report for {role}: register an artifact "
            "from this role first"
        )
    enforce_context_report_sources_valid(task_id, state, report)
    state.setdefault("context_compression_reports", {})[role] = {
        "ref": ref,
        "registered_at": now(),
        "digest": stable_digest(report),
        "status": "valid",
    }
    save_yaml(TRACES_DIR / task_id / "state.yaml", state)
    manifest = load_yaml(TRACES_DIR / task_id / "manifest.yaml")
    reports = [
        item for item in manifest.get("context_report_index", [])
        if item.get("role") != role
    ]
    reports.append({
        "role": role,
        "ref": ref,
        "digest": stable_digest(report),
        "status": "valid",
    })
    manifest["context_report_index"] = reports
    save_yaml(TRACES_DIR / task_id / "manifest.yaml", manifest)
    add_event(task_id, "context_report_registered", {
        "role": role,
        "ref": ref,
        "digest": stable_digest(report),
    })
    print(f"Context compression report registered: {role}")


def load_context_report_for_role(task_id, state, role):
    registered = state.get("context_compression_reports", {}).get(role)
    if not registered:
        fail(
            f"cannot hand off from {role}: register a context compression "
            "report first with `ledger context-report`"
        )
    path, _ = resolve_task_ref(task_id, registered.get("ref"))
    report = enforce_context_report_valid(load_yaml(path))
    digest = stable_digest(report)
    if digest != registered.get("digest"):
        fail(
            f"context compression report digest changed for {role}: "
            f"{registered.get('digest')} != {digest}"
        )
    enforce_context_report_sources_valid(task_id, state, report)
    return report, registered


def artifact_summaries(state, artifact_refs):
    summaries = []
    for artifact_id in artifact_refs:
        artifact = state.get("artifact_registry", {}).get(artifact_id, {})
        summaries.append({
            "artifact_id": artifact_id,
            "producer": artifact.get("producer"),
            "type": artifact.get("type"),
            "version": artifact.get("version"),
            "status": artifact.get("status"),
            "content_ref": artifact.get("content_ref"),
        })
    return summaries


def build_handoff_context_block(
    task_id,
    state,
    from_role,
    to_role,
    rel_type,
    focus,
    artifact_refs,
    report,
    report_ref,
):
    """Create the compressed upstream context carried by every handoff.

    Each handoff is a small block in a provenance chain: it carries the direct
    deliverable plus a digest-linked summary of the context the producer
    received from its own upstream handoffs.
    """
    incoming_handoffs = [
        handoff for handoff in load_handoffs(task_id)
        if handoff.get("to") == from_role
    ]
    previous_blocks = []
    inherited_artifacts = set()
    for handoff in incoming_handoffs:
        block = handoff.get("context_block") or {}
        deliverable = handoff.get("deliverable") or {}
        refs = (
            deliverable.get("artifact_refs")
            or handoff.get("artifact_refs")
            or []
        )
        inherited_artifacts.update(refs)
        for ref in block.get("inherited_artifact_refs", []):
            inherited_artifacts.add(ref)
        previous_blocks.append({
            "ref": handoff.get("_ref"),
            "from": handoff.get("from"),
            "to": handoff.get("to"),
            "relation_type": handoff.get("relation_type"),
            "focus": handoff.get("focus"),
            "context_digest": block.get("context_digest"),
            "deliverable_artifact_refs": refs,
        })

    block = {
        "schema": "silicon_org.context_chain.v1",
        "task_id": task_id,
        "from": from_role,
        "to": to_role,
        "relation_type": rel_type,
        "focus": focus,
        "source": {
            "producer_role": from_role,
            "context_compression_report_ref": report_ref,
            "input_handoffs": report.get("input_scope", {}).get("handoffs_read", []),
            "input_artifacts": report.get("input_scope", {}).get("artifacts_read", []),
        },
        "compressed_context": report.get("retained_context", {}),
        "omitted_context": report.get("omitted_context", []),
        "compression_rationale": report.get("compression_rationale", {}),
        "quality_checks": report.get("quality_checks", []),
        "producer_output_artifact_refs": artifact_refs,
        "inherited_artifact_refs": sorted(inherited_artifacts),
        "previous_blocks": previous_blocks,
    }
    block["context_digest"] = stable_digest(block)
    return block


def cmd_handoff(args):
    """ledger handoff <task_id> <from_role> <to_role> <relation_type> <focus_summary>"""
    task_id, from_role, to_role, rel_type = args[0], args[1], args[2], args[3]
    focus = ' '.join(args[4:]) if len(args) > 4 else ""

    get_node(from_role)
    get_node(to_role)
    if not handoff_relation_matches(from_role, to_role, rel_type):
        fail(f"no {rel_type} relation exists from {from_role} to {to_role}")

    state = load_yaml(TRACES_DIR / task_id / "state.yaml")
    predecessor = state.get("node_states", {}).get(from_role, {})
    if predecessor.get("status") != "completed":
        fail(f"cannot hand off from {from_role}: predecessor is not completed")
    if not role_has_artifact(state, from_role):
        fail(f"cannot hand off from {from_role}: predecessor has no registered artifact")

    ts = now().replace(":", "").replace("-", "").replace("T", "-")[:15]
    filename = f"{from_role}→{to_role}-{ts}.yaml"
    artifact_refs = role_artifact_ids(state, from_role)
    report, registered_report = load_context_report_for_role(task_id, state, from_role)
    deliverable = {
        "producer": from_role,
        "artifact_refs": artifact_refs,
        "artifacts": artifact_summaries(state, artifact_refs),
    }
    context_block = build_handoff_context_block(
        task_id,
        state,
        from_role,
        to_role,
        rel_type,
        focus,
        artifact_refs,
        report,
        registered_report.get("ref"),
    )
    handoff = {
        "from": from_role,
        "to": to_role,
        "relation_type": rel_type,
        "timestamp": now(),
        "focus": focus,
        "artifact_refs": artifact_refs,
        "deliverable": deliverable,
        "context_block": context_block,
    }
    if get_node(to_role).get("carries_soul"):
        handoff["soul_ref"] = "org/soul.md"
    save_yaml(TRACES_DIR / task_id / "handoffs" / filename, handoff)

    manifest = load_yaml(TRACES_DIR / task_id / "manifest.yaml")
    manifest.setdefault("handoff_trail", []).append({
        "ref": f"handoffs/{filename}",
        "from": from_role,
        "to": to_role,
        "relation_type": rel_type,
        "timestamp": handoff["timestamp"],
        "artifact_refs": artifact_refs,
        "context_block_digest": context_block["context_digest"],
    })
    if handoff.get("soul_ref"):
        manifest["handoff_trail"][-1]["soul_ref"] = handoff["soul_ref"]
    save_yaml(TRACES_DIR / task_id / "manifest.yaml", manifest)

    if rel_type in ACTIVATION_RELATION_TYPES | EVALUATION_RELATION_TYPES:
        add_event(task_id, "activation_decision", {
            "from": from_role,
            "to": to_role,
            "relation_type": rel_type,
            "decision": "activate",
            "detail": focus,
        })
    print(f"Handoff written: {filename}")


def cmd_converge(args):
    """ledger converge <task_id> — check and update convergence state"""
    task_id = args[0]
    state = load_yaml(TRACES_DIR / task_id / "state.yaml")
    node_states = state.get("node_states", {})

    # Get the graph to know expected nodes
    # For now, simple heuristic: all activated nodes completed or failed
    all_settled = all(
        s.get("status") in ("completed", "failed", "skipped")
        for s in node_states.values()
    ) if node_states else False

    # Check loops
    loops = state.get("loop_states", [])
    all_loops_resolved = all(
        l.get("status") in ("converged", "exhausted")
        for l in loops
    ) if loops else True

    # Check blocking evals: any evaluates relation with blocking=required
    # whose producer is completed but whose evaluator has not completed.
    all_evals_resolved = True
    for rel in load_relations():
        if rel.get("type") != "evaluates":
            continue
        blocking = rel.get("weights", {}).get("blocking")
        blocking_value = blocking.get("value") if isinstance(blocking, dict) else blocking
        if blocking_value != "required":
            continue
        evaluator = rel.get("from")
        producer = rel.get("to")
        producer_state = node_states.get(producer, {})
        if producer_state.get("status") != "completed":
            continue
        evaluator_state = node_states.get(evaluator, {})
        evaluator_completed = evaluator_state.get("completed_at")
        producer_completed = producer_state.get("completed_at")
        if evaluator_state.get("status") == "completed" and \
                evaluator_completed and producer_completed and \
                evaluator_completed >= producer_completed:
            continue
        all_evals_resolved = False
        break

    # Check joins
    all_joins_passed = len(state.get("join_gates", [])) == 0

    # Check unresolved artifacts
    artifacts = state.get("artifact_registry", {})
    any_unresolved = any(
        a.get("status") in ("draft", "under_review")
        for a in artifacts.values()
    )
    undecided_candidates = candidate_activations(task_id, include_decided=False)

    conv = {
        "all_non_loop_nodes_settled": all_settled,
        "all_loops_resolved": all_loops_resolved,
        "all_blocking_evals_resolved": all_evals_resolved,
        "all_joins_passed": all_joins_passed,
        "all_artifacts_resolved": not any_unresolved,  # True when no draft/under_review remain
        "no_undecided_activation_candidates": len(undecided_candidates) == 0,
    }
    state["convergence"] = conv

    settled = all(conv.values())
    if settled:
        settled_at = now()
        state["task_status"] = "settled"
        state["convergence"]["settled_at"] = settled_at
        state["timestamp_end"] = settled_at

    save_yaml(TRACES_DIR / task_id / "state.yaml", state)

    if settled:
        manifest = load_yaml(TRACES_DIR / task_id / "manifest.yaml")
        manifest["timestamp_end"] = state["timestamp_end"]
        manifest["terminal_nodes"] = [
            role for role, info in node_states.items()
            if info.get("status") == "completed"
        ]
        save_yaml(TRACES_DIR / task_id / "manifest.yaml", manifest)
        cmd_event([task_id, "task_settled", "all convergence gates met"])
        print("CONVERGED")
    else:
        status = []
        for k, v in conv.items():
            status.append(f"  {k}: {'✅' if v else '❌'}")
        print("NOT CONVERGED:\n" + "\n".join(status))


def cmd_status(args):
    """ledger status <task_id>"""
    task_id = args[0]
    state = load_yaml(TRACES_DIR / task_id / "state.yaml")
    manifest = load_yaml(TRACES_DIR / task_id / "manifest.yaml")

    print(f"Task: {task_id}")
    print(f"Status: {state.get('task_status', 'unknown')}")
    print(f"Type: {manifest.get('task_type', 'unknown')}")
    print(f"\nNodes ({len(state.get('node_states', {}))}):")
    for role, info in state.get("node_states", {}).items():
        status = info.get("status", "unknown")
        icon = {"completed": "✅", "active": "🔄", "failed": "❌", "blocked": "🔒"}.get(status, "⚪")
        print(f"  {icon} {role}: {status}")
    print(f"\nArtifacts ({len(state.get('artifact_registry', {}))}):")
    for aid, info in state.get("artifact_registry", {}).items():
        print(f"  {info.get('status', '?')} {aid} ({info.get('type', '?')})")
    print(f"\nConvergence: {'SETTLED' if state.get('convergence', {}).get('settled_at') else 'pending'}")


def cmd_weights(args):
    """ledger weights <task_id> — update weight learning indices"""
    task_id = args[0]
    manifest = load_yaml(TRACES_DIR / task_id / "manifest.yaml")
    state = load_yaml(TRACES_DIR / task_id / "state.yaml")
    outcome = manifest.get("outcome", {}).get("status", "unknown") if manifest.get("outcome") else "unknown"
    ts = manifest.get("timestamp_end") or now()

    index_dir = TRACES_DIR
    # By role
    role_index = load_yaml(index_dir / "index_by_role.yaml")
    for role in manifest.get("terminal_nodes", []):
        existing_role_tasks = {
            entry.get("task_id")
            for entry in role_index.get(role, [])
        }
        if task_id in existing_role_tasks:
            continue
        signal = role_signal(manifest, role)
        role_index.setdefault(role, []).append({
            "task_id": task_id,
            "timestamp": ts,
            "outcome": outcome,
            "signal": signal.value,
            "confidence": signal.confidence,
            "signal_source": signal.source,
            "detail": signal.detail,
        })
    save_yaml(index_dir / "index_by_role.yaml", role_index)

    # By relation
    rel_index = load_yaml(index_dir / "index_by_relation.yaml")
    for h in manifest.get("handoff_trail", []):
        signal = relation_signal(manifest, h)
        key = f"{h.get('from')}→{h.get('to')}/{h.get('relation_type')}"
        existing_relation_tasks = {
            entry.get("task_id")
            for entry in rel_index.get(key, [])
        }
        if task_id in existing_relation_tasks:
            continue
        rel_index.setdefault(key, []).append({
            "task_id": task_id,
            "timestamp": ts,
            "signal": signal.value,
            "confidence": signal.confidence,
            "signal_source": signal.source,
            "detail": signal.detail,
        })
    save_yaml(index_dir / "index_by_relation.yaml", rel_index)

    proposal_index = load_yaml(index_dir / "index_learning_proposals.yaml")
    existing_keys = {
        proposal.get("proposal_key")
        for proposal in proposal_index.get("proposals", [])
    }
    for proposal in trace_learning_proposals(task_id, manifest, state):
        if proposal.get("proposal_key") in existing_keys:
            continue
        proposal["timestamp"] = ts
        proposal_index.setdefault("proposals", []).append(proposal)
        existing_keys.add(proposal.get("proposal_key"))
    for proposal in aggregate_learning_proposals(ROOT_DIR, task_id, manifest, state):
        if proposal.get("proposal_key") in existing_keys:
            continue
        proposal["timestamp"] = ts
        proposal_index.setdefault("proposals", []).append(proposal)
        existing_keys.add(proposal.get("proposal_key"))
    save_yaml(index_dir / "index_learning_proposals.yaml", proposal_index)

    print(f"Weight indices updated — outcome: {outcome}, learning=v0")


def task_manifest(task_id):
    return load_yaml(TRACES_DIR / task_id / "manifest.yaml")


def overlay_id(kind, task_type, role):
    return f"{kind}:{task_type}:{role}"


def proposal_to_overlay(proposal):
    proposal_type = proposal.get("type")
    task_type = proposal.get("task_type") or "unknown"
    evidence = proposal.get("evidence") or {}
    if proposal_type in {"verification_gap", "verification_gap_cluster"}:
        role = "delivery-prover"
        return {
            "overlay_id": overlay_id("require_role_on_success", task_type, role),
            "kind": "require_role_on_success",
            "task_types": [task_type],
            "role": role,
            "source_proposal_key": proposal.get("proposal_key"),
            "status": "active",
            "created_at": now(),
            "finding": proposal.get("finding"),
        }
    if proposal_type in {"skip_policy_review", "skip_policy_cluster"} and evidence.get("role"):
        role = evidence.get("role")
        return {
            "overlay_id": overlay_id("forbid_skip_on_task", task_type, role),
            "kind": "forbid_skip_on_task",
            "task_types": [task_type],
            "role": role,
            "relation_type": "evaluates",
            "source_proposal_key": proposal.get("proposal_key"),
            "status": "active",
            "created_at": now(),
            "finding": proposal.get("finding"),
        }
    return None


def find_proposal(index, proposal_key):
    for proposal in index.get("proposals", []):
        if proposal.get("proposal_key") == proposal_key:
            return proposal
    return None


def upsert_policy_overlay(index, overlay):
    overlays = index.setdefault("policy_overlays", [])
    for existing in overlays:
        if existing.get("overlay_id") == overlay.get("overlay_id"):
            existing.update(overlay)
            return existing
    overlays.append(overlay)
    return overlay


def cmd_proposals(args):
    """ledger proposals [list|review] ..."""
    action = args[0] if args else "list"
    index = load_learning_index()
    if action == "list":
        proposals = index.get("proposals", [])
        overlays = index.get("policy_overlays", [])
        if not proposals:
            print("No learning proposals")
        else:
            for proposal in proposals:
                print(
                    f"{proposal.get('proposal_key')} "
                    f"[{proposal.get('status', 'proposed')}] "
                    f"type={proposal.get('type')} "
                    f"task_type={proposal.get('task_type', 'unknown')} "
                    f"severity={proposal.get('severity')}"
                )
        if overlays:
            print("\nActive policy overlays:")
            for overlay in overlays:
                print(
                    f"{overlay.get('overlay_id')} "
                    f"[{overlay.get('status', 'active')}] "
                    f"kind={overlay.get('kind')} "
                    f"task_types={','.join(overlay.get('task_types') or [])} "
                    f"role={overlay.get('role')}"
                )
        return

    if action != "review" or len(args) < 3:
        fail("usage: ledger proposals [list|review <proposal_key> <accepted|rejected> [notes]]")

    proposal_key, status = args[1], args[2]
    notes = ' '.join(args[3:]).strip() if len(args) > 3 else ""
    if status not in {"accepted", "rejected"}:
        fail("proposal review status must be accepted or rejected")
    proposal = find_proposal(index, proposal_key)
    if not proposal:
        fail(f"unknown proposal_key: {proposal_key}")

    proposal["status"] = status
    proposal["reviewed_at"] = now()
    if notes:
        proposal["review_notes"] = notes

    overlay = None
    if status == "accepted":
        overlay = proposal_to_overlay(proposal)
        if overlay:
            upsert_policy_overlay(index, overlay)
    save_learning_index(index)

    if overlay:
        print(
            f"Reviewed: {proposal_key} -> {status}; "
            f"activated overlay {overlay.get('overlay_id')}"
        )
        return
    print(f"Reviewed: {proposal_key} -> {status}")


def blocking_evaluation_skip_issues(state, role):
    issues = []
    for rel in load_relations():
        if rel.get("type") != "evaluates" or rel.get("from") != role:
            continue
        blocking = rel.get("weights", {}).get("blocking")
        blocking_value = blocking.get("value") if isinstance(blocking, dict) else blocking
        if blocking_value != "required":
            continue
        producer = rel.get("to")
        producer_state = state.get("node_states", {}).get(producer, {})
        if producer_state.get("status") == "completed":
            issues.append(
                f"{role} is a required evaluator for completed producer {producer}"
            )
    return issues


def previous_role_skip_count(task_id, role):
    count = 0
    for state_path in TRACES_DIR.glob("task-*/state.yaml"):
        if state_path.parent.name == task_id:
            continue
        state = load_yaml(state_path)
        info = state.get("node_states", {}).get(role, {})
        if info.get("status") == "skipped":
            count += 1
    return count


def skip_cost_for_role(task_id, state, role):
    prior_skips = previous_role_skip_count(task_id, role)
    node = get_node(role)
    relation_roles = {
        rel.get("from")
        for rel in load_relations()
        if rel.get("type") == "evaluates"
    }
    evaluator = role in relation_roles
    severity = "free"
    if prior_skips == 1:
        severity = "warning"
    elif prior_skips >= 2:
        severity = "review_required"

    penalty = 0.0
    reasons = []
    if node.get("carries_soul"):
        penalty += 0.08
        reasons.append("soul-bearing node skipped")
    if evaluator:
        penalty += 0.05
        reasons.append("evaluator skipped")
    if prior_skips >= 1:
        penalty += min(0.10, 0.03 * prior_skips)
        reasons.append(f"prior skips for role: {prior_skips}")

    return {
        "severity": severity,
        "prior_role_skips": prior_skips,
        "quality_penalty": round(min(0.20, penalty), 3),
        "reasons": reasons,
    }


def cmd_skip(args):
    """ledger skip <task_id> <role> <reason>

    Register that a node was considered and rejected. Reason is required and
    must be non-empty; max 200 chars. Writes a node_skipped event so trace
    readers can distinguish "never considered" from "considered, declined".
    """
    if len(args) < 3:
        fail("usage: ledger skip <task_id> <role> <reason>")
    task_id, role = args[0], args[1]
    reason = ' '.join(args[2:]).strip()
    if not reason:
        fail("skip reason is required and must be non-empty")
    if len(reason) > 200:
        fail(f"skip reason exceeds 200 chars ({len(reason)})")
    get_node(role)
    state = load_yaml(TRACES_DIR / task_id / "state.yaml")
    blocking_issues = blocking_evaluation_skip_issues(state, role)
    if blocking_issues:
        fail(
            f"cannot skip {role}: " + "; ".join(blocking_issues)
        )
    skip_cost = skip_cost_for_role(task_id, state, role)
    if skip_cost["severity"] == "review_required" and len(reason) < 60:
        fail(
            f"repeated skip of {role} requires a detailed justification "
            "(at least 60 chars)"
        )
    existing = state.get("node_states", {}).get(role)
    if existing and existing.get("status") not in (None, "skipped"):
        fail(f"cannot skip {role}: already {existing.get('status')}")
    state.setdefault("node_states", {})[role] = {
        "status": "skipped",
        "updated_at": now(),
        "skip_reason": reason,
        "skip_cost": skip_cost,
    }
    save_yaml(TRACES_DIR / task_id / "state.yaml", state)
    add_event(task_id, "node_skipped", {
        "role": role,
        "reason": reason,
        "skip_cost": skip_cost,
    })


def cmd_runtime_fallback(args):
    """ledger runtime-fallback <task_id> <role> <reason>

    Register that the Runtime produced an artifact on behalf of a node
    instead of activating the subagent. RUNTIME.md forbids silent
    self-implementation; this event makes the violation auditable.

    Allowed reason vocabulary (free-text but should describe one of):
      - subagent_quota_exhausted
      - subagent_failed_twice
      - graph_topology_dead_end
      - explicit_user_override
    """
    if len(args) < 3:
        fail("usage: ledger runtime-fallback <task_id> <role> <reason>")
    task_id, role = args[0], args[1]
    reason = ' '.join(args[2:]).strip()
    if not reason:
        fail("runtime-fallback reason is required and must be non-empty")
    get_node(role)
    add_event(task_id, "runtime_fallback", {"role": role, "reason": reason})


def cmd_activation_decision(args):
    """ledger activation-decision <task_id> <from_role> <to_role> <relation_type> <activate|skip|defer> <reason>"""
    task_id, from_role, to_role, rel_type, decision = args[0], args[1], args[2], args[3], args[4]
    reason = ' '.join(args[5:]).strip() if len(args) > 5 else ""
    if decision not in ACTIVATION_DECISIONS:
        fail(f"decision must be one of: {', '.join(sorted(ACTIVATION_DECISIONS))}")
    if decision in {"skip", "defer"} and len(reason) < 20:
        fail(
            f"{decision} decisions require a concrete reason "
            "(at least 20 chars)"
        )
    get_node(from_role)
    get_node(to_role)
    if rel_type not in ACTIVATION_RELATION_TYPES | EVALUATION_RELATION_TYPES:
        fail(f"{rel_type} is not an activation-capable relation type")
    if not handoff_relation_matches(from_role, to_role, rel_type):
        fail(f"no activation-capable {rel_type} relation exists from {from_role} to {to_role}")
    enforce_activation_decision_allowed(task_id, from_role, to_role, rel_type, decision)
    add_event(task_id, "activation_decision", {
        "from": from_role,
        "to": to_role,
        "relation_type": rel_type,
        "decision": decision,
        "detail": reason,
        "decision_quality": {
            "reason_chars": len(reason),
            "requires_review": decision in {"skip", "defer"},
        },
    })


def cmd_candidates(args):
    """ledger candidates <task_id> [--all] — list undecided graph activation candidates"""
    task_id = args[0]
    include_decided = "--all" in args
    candidates = candidate_activations(task_id, include_decided=include_decided)
    if not candidates:
        print("No activation candidates")
        return
    for candidate in candidates:
        probability = candidate.get("probability")
        probability_text = f" p={probability}" if probability is not None else ""
        condition = candidate.get("condition")
        condition_text = f" condition={condition}" if condition else ""
        decided = " decided" if candidate.get("decided") else ""
        print(
            f"{candidate['from']} -> {candidate['to']} "
            f"{candidate['relation_type']}{probability_text}"
            f" [{candidate['direction']}]{condition_text}{decided}"
        )


CONVERGENCE_KEYS = [
    "all_non_loop_nodes_settled",
    "all_loops_resolved",
    "all_blocking_evals_resolved",
    "all_joins_passed",
    "all_artifacts_resolved",
    "no_undecided_activation_candidates",
]


def unmet_convergence_gates(state):
    convergence = state.get("convergence") or {}
    return [key for key in CONVERGENCE_KEYS if convergence.get(key) is not True]


def approved_artifacts_for_role(state, role):
    return [
        artifact_id
        for artifact_id, artifact in state.get("artifact_registry", {}).items()
        if artifact.get("producer") == role and artifact.get("status") == "approved"
    ]


def skip_quality_penalty(state):
    penalty = 0.0
    details = []
    for role, info in state.get("node_states", {}).items():
        if info.get("status") != "skipped":
            continue
        skip_cost = info.get("skip_cost") or {}
        role_penalty = float(skip_cost.get("quality_penalty") or 0.0)
        if role_penalty <= 0:
            continue
        penalty += role_penalty
        details.append(f"{role}:{role_penalty:.2f}")
    return min(0.40, penalty), details


def delivery_quality_signal(state, status, summary):
    if status == "failed":
        return {
            "source": "runtime_decoder",
            "value": 0.0,
            "detail": summary,
        }
    if status == "partial":
        return {
            "source": "runtime_decoder",
            "value": 0.5,
            "detail": summary,
        }

    skip_penalty, skip_details = skip_quality_penalty(state)
    penalty_detail = (
        f"; skip_penalty={skip_penalty:.2f} ({', '.join(skip_details)})"
        if skip_details
        else ""
    )

    delivery_proofs = approved_artifacts_for_role(state, "delivery-prover")
    if delivery_proofs:
        return {
            "source": "delivery-prover",
            "value": max(0.0, 1.0 - skip_penalty),
            "detail": (
                "approved delivery proof(s): "
                + ", ".join(delivery_proofs)
                + penalty_detail
            ),
        }

    return {
        "source": "runtime_decoder_unverified",
        "value": max(0.0, 0.7 - skip_penalty),
        "detail": (
            "success delivered without an approved delivery-prover artifact; "
            "quality confidence capped. " + summary
        ).strip() + penalty_detail,
    }


def cmd_deliver(args):
    """ledger deliver <task_id> <success|partial|failed> <decoder_summary>"""
    task_id, status = args[0], args[1]
    summary = ' '.join(args[2:]) if len(args) > 2 else ""
    if status not in ("success", "partial", "failed"):
        fail("status must be success, partial, or failed")
    state = load_yaml(TRACES_DIR / task_id / "state.yaml")
    unresolved = [
        artifact_id for artifact_id, artifact in state.get("artifact_registry", {}).items()
        if artifact.get("status") in ("draft", "under_review")
    ]
    if unresolved and status == "success":
        fail(
            "cannot deliver success with unresolved artifacts: "
            + ", ".join(unresolved)
        )
    undecided = candidate_activations(task_id, include_decided=False)
    if undecided and status == "success":
        fail(
            "cannot deliver success with undecided activation candidates: "
            + ", ".join(
                f"{c['from']}->{c['to']}/{c['relation_type']}"
                for c in undecided
            )
        )
    unmet_gates = unmet_convergence_gates(state)
    if unmet_gates and status == "success":
        fail(
            "cannot deliver success before convergence gates pass: "
            + ", ".join(unmet_gates)
            + ". Run `ledger converge` and resolve the open gates."
        )
    if status == "success":
        enforce_delivery_policy(task_id, state)
    manifest = load_yaml(TRACES_DIR / task_id / "manifest.yaml")
    timestamp = now()
    manifest["timestamp_end"] = timestamp
    manifest["terminal_nodes"] = [
        role for role, info in state.get("node_states", {}).items()
        if info.get("status") == "completed"
    ]
    manifest["outcome"] = {
        "status": status,
        "decoder_notes": summary,
        "quality_signal": delivery_quality_signal(state, status, summary),
    }
    save_yaml(TRACES_DIR / task_id / "manifest.yaml", manifest)
    state["task_status"] = "delivered"
    state["timestamp_end"] = timestamp
    save_yaml(TRACES_DIR / task_id / "state.yaml", state)
    add_event(task_id, "task_completed", {
        "detail": summary,
        "status": status,
    })
    print(f"Delivered: {status}")


def cmd_validate(args):
    """ledger validate <task_id> — audit graph-routing invariants"""
    task_id = args[0]
    state = load_yaml(TRACES_DIR / task_id / "state.yaml")
    manifest = load_yaml(TRACES_DIR / task_id / "manifest.yaml")
    nodes = load_nodes()
    issues = []

    entry_nodes = set(manifest.get("entry_nodes", []))
    for role in entry_nodes:
        node = nodes.get(role)
        if not node:
            issues.append(f"entry node {role} is not defined in ontology/nodes.yaml")
        elif node.get("layer") != 1:
            issues.append(f"entry node {role} is layer {node.get('layer')}; expected layer 1")
        if role not in state.get("node_states", {}):
            issues.append(f"entry node {role} is missing from state")

    for role, info in state.get("node_states", {}).items():
        node = nodes.get(role)
        if not node:
            issues.append(f"node state references unknown role {role}")
            continue

        if info.get("entry_node") and role not in entry_nodes:
            issues.append(f"{role} is marked entry_node in state but missing from manifest")
        if info.get("entry_node") and node.get("layer") != 1:
            issues.append(f"{role} is marked entry_node but is layer {node.get('layer')}")

        if role in entry_nodes:
            continue

        if info.get("status") in ("activated", "completed"):
            if not valid_handoffs_for_activation(task_id, state, role):
                issues.append(
                    f"{role} is {info.get('status')} without a valid predecessor handoff "
                    "through triggers, may_trigger, or reverse evaluates"
                )

    for handoff in load_handoffs(task_id):
        from_role = handoff.get("from")
        to_role = handoff.get("to")
        rel_type = handoff.get("relation_type")
        if not handoff_relation_matches(from_role, to_role, rel_type):
            issues.append(f"handoff {handoff.get('_ref')} has no matching ontology relation")
        predecessor = state.get("node_states", {}).get(from_role, {})
        if predecessor.get("status") != "completed":
            issues.append(f"handoff {handoff.get('_ref')} source {from_role} is not completed")
        if not role_has_artifact(state, from_role):
            issues.append(f"handoff {handoff.get('_ref')} source {from_role} has no artifact")
        if not valid_handoff_payload(handoff):
            issues.append(
                f"handoff {handoff.get('_ref')} is missing deliverable/context_block "
                "or has an invalid context digest"
            )

    for role, registered in state.get("context_compression_reports", {}).items():
        ref = registered.get("ref")
        candidate_paths = []
        if ref:
            ref_path = Path(ref)
            if ref_path.is_absolute():
                candidate_paths.append(ref_path)
            candidate_paths.extend([
                TRACES_DIR / task_id / ref,
                ROOT_DIR / ref,
            ])
        path = next((p for p in candidate_paths if p.exists()), None)
        if not path:
            issues.append(f"context report for {role} is missing: {ref}")
            continue
        report = load_yaml(path)
        schema_issues = context_report_issues(report)
        for issue in schema_issues:
            issues.append(f"context report for {role}: {issue}")
        digest = stable_digest(report.get("context_compression_report") or report)
        if digest != registered.get("digest"):
            issues.append(
                f"context report for {role} digest mismatch: "
                f"{registered.get('digest')} != {digest}"
            )
        source_issues = context_report_source_issues(task_id, state, report)
        for issue in source_issues:
            issues.append(f"context report for {role}: {issue}")

    for candidate in candidate_activations(task_id, include_decided=False):
        issues.append(
            f"undecided activation candidate: {candidate['from']} -> {candidate['to']} "
            f"{candidate['relation_type']}"
        )

    manifest_status = manifest.get("outcome", {}).get("status") if manifest.get("outcome") else None
    if state.get("task_status") == "delivered" and not manifest_status:
        issues.append("task is delivered but manifest.outcome is missing")

    if issues:
        print("INVALID")
        for issue in issues:
            print(f"- {issue}")
        sys.exit(1)

    print("VALID")


COMMANDS = {
    "init": cmd_init,
    "context": cmd_context,
    "event": cmd_event,
    "node": cmd_node,
    "artifact": cmd_artifact,
    "artifact-status": cmd_artifact_status,
    "context-report": cmd_context_report,
    "activation-decision": cmd_activation_decision,
    "skip": cmd_skip,
    "runtime-fallback": cmd_runtime_fallback,
    "candidates": cmd_candidates,
    "deliver": cmd_deliver,
    "handoff": cmd_handoff,
    "converge": cmd_converge,
    "status": cmd_status,
    "validate": cmd_validate,
    "weights": cmd_weights,
    "proposals": cmd_proposals,
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ledger.py <command> [args...]")
        print("Commands:", ", ".join(COMMANDS.keys()))
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd in COMMANDS:
        COMMANDS[cmd](sys.argv[2:])
    else:
        print(f"Unknown command: {cmd}")
        print("Available:", ", ".join(COMMANDS.keys()))
        sys.exit(1)
