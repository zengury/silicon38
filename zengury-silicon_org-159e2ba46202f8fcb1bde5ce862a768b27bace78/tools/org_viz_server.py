#!/usr/bin/env python3
"""Read-only local snapshot server for the Silicon Org visualizer.

The server intentionally uses only the Python standard library. It projects the
Graph files and Ledger traces into JSON; it never writes ledger state.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import posixpath
import re
import sys
import urllib.parse
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
ONTOLOGY_DIR = ROOT_DIR / "ontology"
TRACES_DIR = ROOT_DIR / "traces"
VISUALIZER_DIR = ROOT_DIR / "visualizer"

GRAPH_NODE_REF = "ontology/nodes.yaml"
GRAPH_RELATION_REF = "ontology/relations.yaml"
GRAPH_RELATION_TYPE_REF = "ontology/relation_types.yaml"
LEARNING_INDEX_REFS = (
    "traces/index_by_relation.yaml",
    "traces/index_by_role.yaml",
)
TASK_ID_RE = re.compile(r"^task-\d{8}T\d{6}-[0-9a-fA-F]{8}$")
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "connect-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}


class SnapshotError(dict):
    def __init__(self, source_ref: str, message: str):
        super().__init__(source_ref=source_ref, message=message)


class MiniYaml:
    """Small tolerant YAML reader for the repo's trace/ontology subset.

    This is not a general YAML implementation. It supports the structures
    written by the Silicon Org ledger: nested maps, lists, quoted scalars,
    inline one-level maps/lists, anchors, aliases, and folded plain scalars.
    Malformed lines are collected as errors instead of aborting the snapshot.
    """

    KEY_RE = re.compile(r"^([^:#][^:]*):(?:\s+(.*))?$")

    def __init__(self, source_ref: str):
        self.source_ref = source_ref
        self.errors: list[SnapshotError] = []
        self.anchors: dict[str, Any] = {}

    def parse(self, text: str) -> Any:
        lines = self._prepare(text)
        if not lines:
            return {}
        value, _ = self._parse_block(lines, 0, lines[0][0])
        return value if value is not None else {}

    def _prepare(self, text: str) -> list[tuple[int, str, int]]:
        prepared: list[tuple[int, str, int]] = []
        for lineno, raw in enumerate(text.splitlines(), start=1):
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            prepared.append((indent, raw.strip(), lineno))
        return prepared

    def _parse_block(
        self, lines: list[tuple[int, str, int]], index: int, indent: int
    ) -> tuple[Any, int]:
        if index >= len(lines):
            return {}, index
        if lines[index][1].startswith("- "):
            return self._parse_list(lines, index, indent)
        return self._parse_map(lines, index, indent)

    def _parse_map(
        self, lines: list[tuple[int, str, int]], index: int, indent: int
    ) -> tuple[dict[str, Any], int]:
        result: dict[str, Any] = {}
        last_key: str | None = None
        while index < len(lines):
            current_indent, text, lineno = lines[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                if last_key and isinstance(result.get(last_key), str):
                    folded, index = self._consume_folded_scalar(lines, index, current_indent)
                    result[last_key] = f"{result[last_key]} {folded}".strip()
                    continue
                self._error(lineno, f"unexpected indentation: {text}")
                index += 1
                continue
            if text.startswith("- "):
                break

            match = self.KEY_RE.match(text)
            if not match:
                if last_key and isinstance(result.get(last_key), str):
                    result[last_key] = f"{result[last_key]} {text}".strip()
                else:
                    self._error(lineno, f"cannot parse mapping line: {text}")
                index += 1
                continue

            key = match.group(1).strip()
            raw_value = (match.group(2) or "").strip()
            index += 1
            if raw_value in ("|", ">"):
                if index < len(lines) and lines[index][0] > current_indent:
                    child, index = self._consume_folded_scalar(lines, index, lines[index][0])
                else:
                    child = ""
                result[key] = child
            elif raw_value == "" or raw_value.startswith("&"):
                anchor = raw_value[1:].strip() if raw_value.startswith("&") else None
                if index < len(lines) and (
                    lines[index][0] > current_indent
                    or (lines[index][0] == current_indent and lines[index][1].startswith("- "))
                ):
                    child, index = self._parse_block(lines, index, lines[index][0])
                else:
                    child = None
                if anchor:
                    self.anchors[anchor] = child
                result[key] = child
            else:
                result[key] = self._parse_scalar(raw_value)
            last_key = key
        return result, index

    def _parse_list(
        self, lines: list[tuple[int, str, int]], index: int, indent: int
    ) -> tuple[list[Any], int]:
        result: list[Any] = []
        while index < len(lines):
            current_indent, text, lineno = lines[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                if result and isinstance(result[-1], dict):
                    if not text.startswith("- ") and not self.KEY_RE.match(text):
                        self._append_to_last_string(result[-1], text)
                        index += 1
                        continue
                    child, index = self._parse_map(lines, index, current_indent)
                    result[-1].update(child)
                    continue
                if result and isinstance(result[-1], str):
                    result[-1] = f"{result[-1]} {text}".strip()
                    index += 1
                    continue
                self._error(lineno, f"unexpected list indentation: {text}")
                index += 1
                continue
            if not text.startswith("- "):
                break

            item_text = text[2:].strip()
            index += 1
            if item_text == "":
                if index < len(lines) and (
                    lines[index][0] > current_indent
                    or (lines[index][0] == current_indent and lines[index][1].startswith("- "))
                ):
                    child, index = self._parse_block(lines, index, lines[index][0])
                else:
                    child = None
                result.append(child)
                continue

            match = self.KEY_RE.match(item_text)
            if match:
                key = match.group(1).strip()
                raw_value = (match.group(2) or "").strip()
                item: dict[str, Any] = {}
                if raw_value in ("|", ">"):
                    if index < len(lines) and lines[index][0] > current_indent:
                        child, index = self._consume_folded_scalar(lines, index, lines[index][0])
                    else:
                        child = ""
                    item[key] = child
                elif raw_value == "" or raw_value.startswith("&"):
                    anchor = raw_value[1:].strip() if raw_value.startswith("&") else None
                    if index < len(lines) and (
                        lines[index][0] > current_indent
                        or (lines[index][0] == current_indent and lines[index][1].startswith("- "))
                    ):
                        child, index = self._parse_block(lines, index, lines[index][0])
                    else:
                        child = None
                    if anchor:
                        self.anchors[anchor] = child
                    item[key] = child
                else:
                    item[key] = self._parse_scalar(raw_value)
                result.append(item)
            else:
                result.append(self._parse_scalar(item_text))
        return result, index

    def _consume_folded_scalar(
        self, lines: list[tuple[int, str, int]], index: int, indent: int
    ) -> tuple[str, int]:
        parts: list[str] = []
        while index < len(lines) and lines[index][0] >= indent:
            parts.append(lines[index][1])
            index += 1
        return " ".join(parts), index

    def _append_to_last_string(self, mapping: dict[str, Any], text: str) -> None:
        for key in reversed(list(mapping.keys())):
            if isinstance(mapping.get(key), str):
                mapping[key] = f"{mapping[key]} {text}".strip()
                return

    def _parse_scalar(self, value: str) -> Any:
        value = value.strip()
        if value.startswith("*"):
            return self.anchors.get(value[1:], value)
        if " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        if value in ("null", "Null", "NULL", "~"):
            return None
        if value in ("true", "True", "TRUE"):
            return True
        if value in ("false", "False", "FALSE"):
            return False
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            return value[1:-1]
        if value.startswith("{") and value.endswith("}"):
            return self._parse_inline_map(value[1:-1])
        if value.startswith("[") and value.endswith("]"):
            body = value[1:-1].strip()
            if not body:
                return []
            return [self._parse_scalar(part) for part in self._split_inline(body)]
        try:
            if re.fullmatch(r"[-+]?\d+", value):
                return int(value)
            if re.fullmatch(r"[-+]?\d+\.\d+", value):
                return float(value)
        except ValueError:
            pass
        return value

    def _parse_inline_map(self, body: str) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for part in self._split_inline(body):
            if ":" not in part:
                continue
            key, value = part.split(":", 1)
            result[key.strip()] = self._parse_scalar(value.strip())
        return result

    def _split_inline(self, body: str) -> list[str]:
        parts: list[str] = []
        quote: str | None = None
        depth = 0
        start = 0
        for index, char in enumerate(body):
            if quote:
                if char == quote:
                    quote = None
                continue
            if char in ("'", '"'):
                quote = char
            elif char in "{[":
                depth += 1
            elif char in "}]":
                depth -= 1
            elif char == "," and depth == 0:
                parts.append(body[start:index].strip())
                start = index + 1
        parts.append(body[start:].strip())
        return [part for part in parts if part]

    def _error(self, lineno: int, message: str) -> None:
        self.errors.append(SnapshotError(f"{self.source_ref}:{lineno}", message))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel_ref(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


def read_text(path: Path) -> tuple[str | None, SnapshotError | None]:
    try:
        return path.read_text(encoding="utf-8"), None
    except FileNotFoundError:
        return None, SnapshotError(rel_ref(path), "file not found")
    except UnicodeDecodeError as exc:
        return None, SnapshotError(rel_ref(path), f"cannot decode utf-8: {exc}")
    except OSError as exc:
        return None, SnapshotError(rel_ref(path), f"cannot read file: {exc}")


def read_yaml(path: Path, errors: list[SnapshotError]) -> Any:
    text, error = read_text(path)
    if error:
        errors.append(error)
        return {}
    parser = MiniYaml(rel_ref(path))
    data = parser.parse(text or "")
    errors.extend(parser.errors)
    return data


def list_task_dirs() -> list[Path]:
    if not TRACES_DIR.exists():
        return []
    return sorted(
        (path for path in TRACES_DIR.iterdir() if path.is_dir() and path.name.startswith("task-")),
        key=lambda path: path.name,
    )


def is_valid_task_id(task_id: str) -> bool:
    return bool(TASK_ID_RE.fullmatch(task_id))


def task_dir_for_id(task_id: str) -> Path | None:
    if not is_valid_task_id(task_id):
        return None
    try:
        candidate = (TRACES_DIR / task_id).resolve()
        candidate.relative_to(TRACES_DIR.resolve())
    except (OSError, ValueError):
        return None
    return candidate if candidate.is_dir() else None


def task_timestamp(task_dir: Path, manifest: dict[str, Any] | None = None) -> str:
    if manifest:
        for key in ("timestamp_start", "timestamp_end"):
            value = manifest.get(key)
            if isinstance(value, str) and value:
                return value
    try:
        return datetime.fromtimestamp(task_dir.stat().st_mtime, timezone.utc).isoformat()
    except OSError:
        return ""


def resolve_task_id(task_id: str | None, errors: list[SnapshotError]) -> str | None:
    requested = task_id or "latest"
    if requested != "latest":
        if not is_valid_task_id(requested):
            errors.append(SnapshotError("task_id", "invalid task id"))
            return None
        if not task_dir_for_id(requested):
            errors.append(SnapshotError(f"traces/{requested}", "trace not found"))
            return None
        return requested
    tasks = list_task_dirs()
    if not tasks:
        errors.append(SnapshotError("traces/", "no task traces found"))
        return None

    best: tuple[str, str] | None = None
    for task_dir in tasks:
        local_errors: list[SnapshotError] = []
        manifest = read_yaml(task_dir / "manifest.yaml", local_errors)
        stamp = task_timestamp(task_dir, manifest if isinstance(manifest, dict) else None)
        candidate = (stamp, task_dir.name)
        if best is None or candidate > best:
            best = candidate
    return best[1] if best else tasks[-1].name


def extract_weight(edge: dict[str, Any]) -> float | None:
    weights = edge.get("weights")
    if not isinstance(weights, dict):
        return None
    for key in ("probability", "strictness", "necessity"):
        metric = weights.get(key)
        if isinstance(metric, dict):
            value = metric.get("value")
            if isinstance(value, (int, float)):
                return float(value)
        elif isinstance(metric, (int, float)):
            return float(metric)
    return None


def extract_confidence(edge: dict[str, Any]) -> float | None:
    weights = edge.get("weights")
    if not isinstance(weights, dict):
        return None
    for metric in weights.values():
        if isinstance(metric, dict) and isinstance(metric.get("confidence"), (int, float)):
            return float(metric["confidence"])
    return None


def activation_capable(relation_type: str | None) -> bool:
    return relation_type in {"triggers", "may_trigger", "evaluates"}


def normalize_graph(errors: list[SnapshotError]) -> dict[str, Any]:
    nodes_doc = read_yaml(ONTOLOGY_DIR / "nodes.yaml", errors)
    relations_doc = read_yaml(ONTOLOGY_DIR / "relations.yaml", errors)
    relation_types_doc = read_yaml(ONTOLOGY_DIR / "relation_types.yaml", errors)

    raw_nodes = nodes_doc.get("nodes", []) if isinstance(nodes_doc, dict) else []
    raw_edges = relations_doc.get("relations", []) if isinstance(relations_doc, dict) else []
    relation_types = relation_types_doc.get("relation_types", relation_types_doc)

    nodes: list[dict[str, Any]] = []
    if isinstance(raw_nodes, list):
        for index, node in enumerate(raw_nodes):
            if not isinstance(node, dict):
                errors.append(SnapshotError(GRAPH_NODE_REF, f"invalid node at index {index}"))
                continue
            role = node.get("role") or f"node-{index}"
            nodes.append(
                {
                    "id": role,
                    "role": role,
                    "title": node.get("title"),
                    "layer": node.get("layer"),
                    "domain": node.get("domain"),
                    "carriesSoul": bool(node.get("carries_soul", False)),
                    "skillRef": node.get("skill_ref"),
                    "harnessRef": node.get("harness_ref"),
                    "sourceRef": GRAPH_NODE_REF,
                    "raw": node,
                }
            )

    edges: list[dict[str, Any]] = []
    if isinstance(raw_edges, list):
        for index, edge in enumerate(raw_edges):
            if not isinstance(edge, dict):
                errors.append(SnapshotError(GRAPH_RELATION_REF, f"invalid relation at index {index}"))
                continue
            source = edge.get("from")
            target = edge.get("to")
            relation_type = edge.get("type")
            edge_id = f"{source}->{target}:{relation_type}:{index}"
            edges.append(
                {
                    "id": edge_id,
                    "from": source,
                    "to": target,
                    "relationType": relation_type,
                    "activationCapable": activation_capable(relation_type),
                    "evaluationReverseAware": relation_type == "evaluates",
                    "weight": extract_weight(edge),
                    "confidence": extract_confidence(edge),
                    "condition": (edge.get("weights") or {}).get("condition")
                    if isinstance(edge.get("weights"), dict)
                    else None,
                    "sourceRef": GRAPH_RELATION_REF,
                    "raw": edge,
                }
            )

    return {
        "nodes": nodes,
        "edges": edges,
        "relationTypes": relation_types if isinstance(relation_types, (dict, list)) else {},
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges),
            "activationCapableEdges": sum(1 for edge in edges if edge["activationCapable"]),
        },
        "sourceRefs": [GRAPH_NODE_REF, GRAPH_RELATION_REF, GRAPH_RELATION_TYPE_REF],
    }


def detail_to_role(detail: Any) -> str | None:
    if not isinstance(detail, str) or ":" not in detail:
        return None
    return detail.split(":", 1)[0].strip() or None


def normalize_events(raw: Any, source_ref: str, errors: list[SnapshotError]) -> list[dict[str, Any]]:
    if isinstance(raw, dict):
        raw_events = raw.get("events", [])
    elif isinstance(raw, list):
        raw_events = raw
    else:
        raw_events = []
    events: list[dict[str, Any]] = []
    for index, event in enumerate(raw_events if isinstance(raw_events, list) else []):
        if not isinstance(event, dict):
            errors.append(SnapshotError(source_ref, f"invalid event at index {index}"))
            continue
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        event_type = event.get("event_type") or event.get("type") or "unknown"
        node_id = payload.get("role") or payload.get("node") or payload.get("to")
        if not node_id and event_type in {"node_activated", "node_completed", "node_skipped"}:
            node_id = detail_to_role(payload.get("detail"))
        events.append(
            {
                "sequence": index + 1,
                "eventId": event.get("event_id") or f"ev-{index + 1:03d}",
                "timestamp": event.get("timestamp"),
                "eventType": event_type,
                "nodeId": node_id,
                "edge": {
                    "from": payload.get("from"),
                    "to": payload.get("to"),
                    "relationType": payload.get("relation_type"),
                }
                if any(key in payload for key in ("from", "to", "relation_type"))
                else None,
                "artifactId": payload.get("artifact_id"),
                "payload": payload,
                "sourceRef": source_ref,
            }
        )
    return events


def normalize_handoff(path: Path, errors: list[SnapshotError]) -> dict[str, Any]:
    data = read_yaml(path, errors)
    if not isinstance(data, dict):
        errors.append(SnapshotError(rel_ref(path), "handoff is not a mapping"))
        data = {}
    context = data.get("context_block") if isinstance(data.get("context_block"), dict) else {}
    deliverable = data.get("deliverable") if isinstance(data.get("deliverable"), dict) else {}
    return {
        "id": path.stem,
        "from": data.get("from"),
        "to": data.get("to"),
        "relationType": data.get("relation_type"),
        "timestamp": data.get("timestamp"),
        "focus": data.get("focus"),
        "artifactRefs": data.get("artifact_refs", []),
        "deliverable": deliverable,
        "contextBlock": {
            "schema": context.get("schema"),
            "taskId": context.get("task_id"),
            "from": context.get("from"),
            "to": context.get("to"),
            "relationType": context.get("relation_type"),
            "focus": context.get("focus"),
            "contextDigest": context.get("context_digest"),
            "previousBlocks": context.get("previous_blocks", []),
            "source": context.get("source", {}),
            "compressedContext": context.get("compressed_context", {}),
            "omittedContext": context.get("omitted_context", []),
        },
        "status": "created" if data else "invalid",
        "sourceRef": rel_ref(path),
        "raw": data,
    }


def normalize_artifacts(task_dir: Path, manifest: dict[str, Any], errors: list[SnapshotError]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    seen: set[str] = set()
    raw_index = manifest.get("artifact_index", [])
    if isinstance(raw_index, list):
        for item in raw_index:
            if not isinstance(item, dict):
                continue
            artifact_id = item.get("artifact_id")
            if artifact_id:
                seen.add(str(artifact_id))
            artifacts.append({"source": "manifest", "sourceRef": "manifest.yaml", **item})

    artifact_dir = task_dir / "artifacts"
    for path in sorted(artifact_dir.glob("*.provenance.yaml")) if artifact_dir.exists() else []:
        provenance = read_yaml(path, errors)
        if not isinstance(provenance, dict):
            continue
        artifact_id = provenance.get("artifact_id")
        if artifact_id and str(artifact_id) in seen:
            continue
        artifacts.append({"source": "provenance", "sourceRef": rel_ref(path), **provenance})
    return artifacts


def activation_decisions(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for event in events:
        if event.get("eventType") != "activation_decision":
            continue
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        decisions.append(
            {
                "sequence": event.get("sequence"),
                "timestamp": event.get("timestamp"),
                "from": payload.get("from"),
                "to": payload.get("to"),
                "relationType": payload.get("relation_type"),
                "decision": payload.get("decision", "undecided"),
                "detail": payload.get("detail"),
                "sourceRef": event.get("sourceRef"),
            }
        )
    return decisions


def summarize_learning_index(path: Path, errors: list[SnapshotError]) -> dict[str, Any]:
    data = read_yaml(path, errors)
    ref = rel_ref(path)
    summary = {
        "sourceRef": ref,
        "exists": path.exists(),
        "topLevelType": type(data).__name__,
        "entryCount": 0,
        "keys": [],
        "sample": None,
    }
    if isinstance(data, dict):
        summary["entryCount"] = len(data)
        summary["keys"] = list(data.keys())[:20]
        if data:
            first_key = next(iter(data))
            summary["sample"] = {first_key: data[first_key]}
    elif isinstance(data, list):
        summary["entryCount"] = len(data)
        summary["sample"] = data[:3]
    return summary


def build_snapshot(task_id: str | None = None) -> dict[str, Any]:
    errors: list[SnapshotError] = []
    resolved_task_id = resolve_task_id(task_id, errors)
    graph = normalize_graph(errors)

    if not resolved_task_id:
        return {
            "schema": "silicon_org.visualizer.snapshot.v1",
            "generatedAt": utc_now(),
            "taskId": None,
            "graph": graph,
            "trace": {},
            "policy": {"decisions": [], "candidates": [], "convergence": {}},
            "learning": {
                "indexes": [
                    summarize_learning_index(ROOT_DIR / ref, errors) for ref in LEARNING_INDEX_REFS
                ]
            },
            "errors": errors,
        }

    task_dir = TRACES_DIR / resolved_task_id
    manifest = read_yaml(task_dir / "manifest.yaml", errors)
    state = read_yaml(task_dir / "state.yaml", errors)
    raw_events = read_yaml(task_dir / "events.yaml", errors)
    if not isinstance(manifest, dict):
        manifest = {}
    if not isinstance(state, dict):
        state = {}

    events = normalize_events(raw_events, f"traces/{resolved_task_id}/events.yaml", errors)
    handoff_dir = task_dir / "handoffs"
    handoffs = [
        normalize_handoff(path, errors)
        for path in sorted(handoff_dir.glob("*.yaml"))
    ] if handoff_dir.exists() else []
    artifacts = normalize_artifacts(task_dir, manifest, errors)
    decisions = activation_decisions(events)

    convergence = state.get("convergence", {}) if isinstance(state.get("convergence"), dict) else {}
    return {
        "schema": "silicon_org.visualizer.snapshot.v1",
        "generatedAt": utc_now(),
        "taskId": resolved_task_id,
        "graph": graph,
        "trace": {
            "taskDir": rel_ref(task_dir),
            "manifest": manifest,
            "state": state,
            "events": events,
            "handoffs": handoffs,
            "artifacts": artifacts,
            "counts": {
                "events": len(events),
                "handoffs": len(handoffs),
                "artifacts": len(artifacts),
            },
            "sourceRefs": [
                f"traces/{resolved_task_id}/manifest.yaml",
                f"traces/{resolved_task_id}/state.yaml",
                f"traces/{resolved_task_id}/events.yaml",
                f"traces/{resolved_task_id}/handoffs/",
                f"traces/{resolved_task_id}/artifacts/",
            ],
        },
        "policy": {
            "decisions": decisions,
            "candidates": [
                decision for decision in decisions if decision.get("decision") in {"activate", "defer"}
            ],
            "convergence": convergence,
        },
        "learning": {
            "indexes": [
                summarize_learning_index(ROOT_DIR / ref, errors) for ref in LEARNING_INDEX_REFS
            ]
        },
        "errors": errors,
    }


def list_tasks() -> dict[str, Any]:
    errors: list[SnapshotError] = []
    tasks: list[dict[str, Any]] = []
    for task_dir in list_task_dirs():
        manifest = read_yaml(task_dir / "manifest.yaml", errors)
        state = read_yaml(task_dir / "state.yaml", errors)
        if not isinstance(manifest, dict):
            manifest = {}
        if not isinstance(state, dict):
            state = {}
        tasks.append(
            {
                "taskId": task_dir.name,
                "summary": manifest.get("task_summary"),
                "status": state.get("task_status") or manifest.get("outcome"),
                "timestampStart": manifest.get("timestamp_start"),
                "timestampEnd": manifest.get("timestamp_end"),
                "entryNodes": manifest.get("entry_nodes", []),
                "terminalNodes": manifest.get("terminal_nodes", []),
                "artifactCount": len(manifest.get("artifact_index", []))
                if isinstance(manifest.get("artifact_index"), list)
                else 0,
                "handoffCount": len(manifest.get("handoff_trail", []))
                if isinstance(manifest.get("handoff_trail"), list)
                else 0,
                "sourceRef": rel_ref(task_dir),
            }
        )
    tasks.sort(key=lambda task: (task.get("timestampStart") or "", task["taskId"]), reverse=True)
    return {
        "schema": "silicon_org.visualizer.tasks.v1",
        "generatedAt": utc_now(),
        "tasks": tasks,
        "errors": errors,
    }


class OrgVizHandler(BaseHTTPRequestHandler):
    server_version = "SiliconOrgViz/0.1"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/health":
            self.send_json({"ok": True, "generatedAt": utc_now()})
            return
        if path == "/api/org":
            errors: list[SnapshotError] = []
            self.send_json(
                {
                    "schema": "silicon_org.visualizer.org.v1",
                    "generatedAt": utc_now(),
                    "graph": normalize_graph(errors),
                    "errors": errors,
                }
            )
            return
        if path == "/api/tasks":
            self.send_json(list_tasks())
            return
        if path == "/api/runs":
            self.send_json(list_tasks())
            return
        if path == "/api/snapshot":
            task_id = query.get("task_id", [self.server.default_task_id])[0]  # type: ignore[attr-defined]
            self.send_snapshot(task_id)
            return

        parts = [part for part in path.split("/") if part]
        if len(parts) >= 3 and parts[0] == "api" and parts[1] == "runs":
            task_id = urllib.parse.unquote(parts[2])
            if len(parts) == 4 and parts[3] == "snapshot":
                self.send_snapshot(task_id)
                return
            if len(parts) == 4 and parts[3] == "events":
                snapshot = self.valid_snapshot(task_id)
                if snapshot:
                    self.send_json({"schema": "silicon_org.visualizer.events.v1", "events": snapshot["trace"]["events"]})
                return
            if len(parts) == 4 and parts[3] == "policy":
                snapshot = self.valid_snapshot(task_id)
                if snapshot:
                    self.send_json({"schema": "silicon_org.visualizer.policy.v1", "policy": snapshot["policy"]})
                return
            if len(parts) == 5 and parts[3] == "handoffs":
                snapshot = self.valid_snapshot(task_id)
                if snapshot:
                    handoff_id = urllib.parse.unquote(parts[4])
                    handoff = self.find_by_id_or_ref(snapshot["trace"]["handoffs"], handoff_id)
                    if handoff:
                        self.send_json({"schema": "silicon_org.visualizer.handoff.v1", "handoff": handoff})
                    else:
                        self.send_error_json(HTTPStatus.NOT_FOUND, "HANDOFF_NOT_FOUND", "handoff not found")
                return
            if len(parts) == 5 and parts[3] == "artifacts":
                snapshot = self.valid_snapshot(task_id)
                if snapshot:
                    artifact_id = urllib.parse.unquote(parts[4])
                    artifact = self.find_by_id_or_ref(snapshot["trace"]["artifacts"], artifact_id)
                    if artifact:
                        self.send_json({"schema": "silicon_org.visualizer.artifact.v1", "artifact": artifact})
                    else:
                        self.send_error_json(HTTPStatus.NOT_FOUND, "ARTIFACT_NOT_FOUND", "artifact not found")
                return
        if path == "/api/learning":
            errors: list[SnapshotError] = []
            self.send_json(
                {
                    "schema": "silicon_org.visualizer.learning.v1",
                    "generatedAt": utc_now(),
                    "learning": {
                        "indexes": [
                            summarize_learning_index(ROOT_DIR / ref, errors) for ref in LEARNING_INDEX_REFS
                        ]
                    },
                    "errors": errors,
                }
            )
            return

        self.serve_static(path)

    def do_HEAD(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
            self.send_common_headers()
            self.end_headers()
            return
        self.serve_static(parsed.path, head_only=True)

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))

    def send_common_headers(self) -> None:
        for key, value in SECURITY_HEADERS.items():
            self.send_header(key, value)

    def send_error_json(self, status: HTTPStatus, code: str, message: str) -> None:
        self.send_json({"ok": False, "error": {"code": code, "message": message}}, status)

    def validate_task_request(self, task_id: str) -> bool:
        if task_id == "latest":
            return True
        if not is_valid_task_id(task_id):
            self.send_error_json(HTTPStatus.BAD_REQUEST, "INVALID_TASK_ID", "task_id is not a valid trace id")
            return False
        if not task_dir_for_id(task_id):
            self.send_error_json(HTTPStatus.NOT_FOUND, "TRACE_NOT_FOUND", "trace not found")
            return False
        return True

    def valid_snapshot(self, task_id: str) -> dict[str, Any] | None:
        if not self.validate_task_request(task_id):
            return None
        snapshot = build_snapshot(task_id)
        if not snapshot.get("taskId"):
            self.send_error_json(HTTPStatus.NOT_FOUND, "TRACE_NOT_FOUND", "trace not found")
            return None
        return snapshot

    def send_snapshot(self, task_id: str) -> None:
        snapshot = self.valid_snapshot(task_id)
        if snapshot:
            self.send_json(snapshot)

    def find_by_id_or_ref(self, items: list[dict[str, Any]], wanted: str) -> dict[str, Any] | None:
        for item in items:
            values = {
                str(item.get("id") or ""),
                str(item.get("artifact_id") or ""),
                str(item.get("artifactId") or ""),
                str(item.get("ref") or ""),
                str(item.get("sourceRef") or ""),
            }
            if wanted in values or any(value.endswith(f"/{wanted}") for value in values):
                return item
        return None

    def send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_common_headers()
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, path: str, head_only: bool = False) -> None:
        if path in ("", "/"):
            target = VISUALIZER_DIR / "index.html"
        else:
            relative = posixpath.normpath(urllib.parse.unquote(path).lstrip("/"))
            if relative.startswith("../"):
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            target = VISUALIZER_DIR / relative

        try:
            resolved = target.resolve()
            resolved.relative_to(VISUALIZER_DIR.resolve())
        except (OSError, ValueError):
            self.send_error(HTTPStatus.FORBIDDEN)
            return

        if not resolved.exists() or not resolved.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
        try:
            body = resolved.read_bytes()
        except OSError as exc:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, explain=str(exc))
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_common_headers()
        self.end_headers()
        if not head_only:
            self.wfile.write(body)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve Silicon Org visualizer snapshots.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--task-id", default="latest")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    os.chdir(ROOT_DIR)
    server = ThreadingHTTPServer((args.host, args.port), OrgVizHandler)
    server.default_task_id = args.task_id  # type: ignore[attr-defined]
    print(f"Serving Silicon Org visualizer at http://{args.host}:{args.port}")
    print(f"Default task_id: {args.task_id}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
