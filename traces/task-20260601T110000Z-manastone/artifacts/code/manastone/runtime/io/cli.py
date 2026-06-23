from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import sys
import time

from .daemon import Daemon, UnixSocketClient, daemon_running
from .formatter import Formatter
from .manifest import render_manifest
from ..adapters import Ros2ActionExecutor
from ..adapters import format_probe_text, run_hardware_probe
from pilot.apps.env_check.engine import run_env_check
from ..brain import Pilot
from ..data import DeviceMemory
from ..brain import PILOT_SYSTEM_PROMPT
from ..adapters import X2Ros2Bridge, probe_ros2
from ..composer import Bootstrap
from ..config import load_config
from .tui import RUNTIME_ICON, render_runtime_icon
from pilot.apps.builder.engine import add_builder_subparser, handle_builder
from pilot.apps.diag.engine import add_diag_subparser, handle_diag
from pilot.apps.vla.recorder import add_vla_subparser, handle_vla
from pilot.apps.diag.log_watcher import LogWatcher
from .connect import (
    connect_mode_label,
    init_g1_dds,
    read_robot_id,
    resolve_connect_mode,
)
try:
    from roboonto.importers.doc_ingestor import ingest_document
    _HAS_DOC_INGEST = True
except ImportError:
    _HAS_DOC_INGEST = False
    def ingest_document(*args, **kwargs):
        raise RuntimeError("doc-ingest is only available in the engineer edition. Install with: pip install -e '.[engineer]'")

from ..constants import DEFAULT_SOCKET


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="manastone")
    parser.add_argument("--ontology", default=None,
                        help="RoboOnto ontology directory (default: from ~/.manastone/config.yaml; "
                             "falls back to roboonto/robots/<robot>)")
    parser.add_argument("--robot", default=None,
                        help="Robot model id (e.g. agibot_x2). Used to resolve ontology when --ontology not set. "
                             "Overrides ~/.manastone/config.yaml robot.model")
    parser.add_argument("--memory", default=".manastone", help="Persistent identity/memory directory")
    parser.add_argument("--skills", default="pilot/skills", help="Directory containing */SKILL.md")
    parser.add_argument("--socket", default=DEFAULT_SOCKET, help="Runtime daemon Unix socket")
    parser.add_argument("--format", default="json", choices=["json", "text"], help="Output format")
    parser.add_argument("--no-daemon", action="store_true", help="Do not use an already-running daemon")
    sub = parser.add_subparsers(dest="cmd", required=True)

    resources = sub.add_parser("resources")
    resources.add_argument("--pattern")
    resources.add_argument("--kind")

    get = sub.add_parser("get")
    get.add_argument("resource_id")

    sub.add_parser("manifest")

    icon = sub.add_parser("icon")
    icon.add_argument("--ascii", action="store_true", help="Render an ASCII fallback icon")
    icon.add_argument("--label", action="store_true", help="Include the runtime label")
    icon.add_argument("--spec", action="store_true", help="Emit the icon metadata as JSON")

    status = sub.add_parser("status")
    status.add_argument("--pattern")

    intent = sub.add_parser("intent")
    intent.add_argument("action")
    intent.add_argument("--params", default="{}")
    intent.add_argument("--source", default="agent")
    intent.add_argument("--execute-ros2", action="store_true", help="Execute accepted ROS2 action on the real robot")
    intent.add_argument("--duration", type=float, default=0.0, help="Stream duration in seconds (0=one-shot). Use for velocity topics.")
    intent.add_argument("--rate", type=int, default=10, help="Stream publish rate in Hz (default: 10)")

    # ── validate + execute (new) ──
    validate = sub.add_parser("validate", help="Check if an action is safe (preconditions + safety gate)")
    validate.add_argument("action")
    validate.add_argument("--params", default="{}")
    validate.add_argument("--source", default="agent")

    execute = sub.add_parser("execute", help="Execute an action on the robot (auto-validates first)")
    execute.add_argument("action")
    execute.add_argument("--params", default="{}")
    execute.add_argument("--source", default="agent")
    execute.add_argument("--duration", type=float, default=0.0, help="Stream duration in seconds (0=one-shot)")
    execute.add_argument("--rate", type=int, default=10, help="Stream publish rate in Hz (default: 10)")

    # ── query ──
    query = sub.add_parser("query", help="Query the robot ontology")
    query_sub = query.add_subparsers(dest="query_cmd", required=True)
    q_actions = query_sub.add_parser("actions", help="List available actions")
    q_actions.add_argument("--filter", default="")
    q_explain = query_sub.add_parser("explain", help="Explain an entity")
    q_explain.add_argument("target")
    q_related = query_sub.add_parser("related", help="Find related entities")
    q_related.add_argument("target")
    query_sub.add_parser("topics", help="List ROS2 topics in ontology")

    # ── record ──
    record = sub.add_parser("record", help="Record observations to robot memory")
    record_sub = record.add_subparsers(dest="record_cmd", required=True)
    rec_log = record_sub.add_parser("log", help="Ingest a log line into Pilot experience stream")
    rec_log.add_argument("--text")
    rec_log.add_argument("--file")
    rec_log.add_argument("--source", default="log")
    rec_log.add_argument("--level", default="info")
    rec_ingest = record_sub.add_parser("ingest", help="Inject a value into a semantic resource")
    rec_ingest.add_argument("resource_id")
    rec_ingest.add_argument("json_value")
    rec_ingest.add_argument("--source", default="cli")

    # ── recall ──
    recall = sub.add_parser("recall", help="Query robot memory and history")
    recall_sub = recall.add_subparsers(dest="recall_cmd", required=True)
    rec_history = recall_sub.add_parser("history", help="Time-series data for a resource")
    rec_history.add_argument("resource_id")
    rec_history.add_argument("--hours", type=float, default=1)
    rec_history.add_argument("--limit", type=int, default=200)
    rec_events = recall_sub.add_parser("events", help="Recent runtime events")
    rec_events.add_argument("--limit", type=int, default=20)
    rec_anomalies = recall_sub.add_parser("anomalies", help="Detected anomalies")
    rec_anomalies.add_argument("--hours", type=float, default=24)
    recall_sub.add_parser("dark", help="Accumulated dark knowledge")

    # ── probe (alias for hardware-probe) ──
    probe = sub.add_parser("probe", help="4-layer hardware diagnostic")
    probe.add_argument("--deep", action="store_true")
    probe.add_argument("--duration", type=float, default=None)

    ingest = sub.add_parser("ingest")
    ingest.add_argument("resource_id")
    ingest.add_argument("json_value")
    ingest.add_argument("--source", default="cli")

    events = sub.add_parser("events")
    events.add_argument("--limit", type=int, default=20)

    context = sub.add_parser("context")
    context_sub = context.add_subparsers(dest="context_cmd", required=True)
    external = context_sub.add_parser("external-agent")
    external.add_argument("--limit", type=int, default=20)

    log = sub.add_parser("log")
    log_sub = log.add_subparsers(dest="log_cmd", required=True)
    log_ingest = log_sub.add_parser("ingest")
    log_ingest.add_argument("--text")
    log_ingest.add_argument("--file")
    log_ingest.add_argument("--source", default="log")
    log_ingest.add_argument("--level", default="info")
    log_records = log_sub.add_parser("records")
    log_records.add_argument("--limit", type=int, default=20)

    sub.add_parser("ros2-probe")

    if _HAS_DOC_INGEST:
        doc = sub.add_parser("doc-ingest", help="Ingest product/maintenance docs into structured knowledge")
        doc.add_argument("path", help="Path to document (.md / .txt / .pdf)")
        doc.add_argument("--type", default="manual", choices=["manual", "sdk", "maintenance", "spec"], help="Document type")
        doc.add_argument("--output-dir", default="skills", help="Output directory for generated skill drafts")
        doc.add_argument("--no-generate-skills", action="store_true", help="Skip SKILL.md generation")
        doc.add_argument("-v", "--verbose", action="store_true")

    plan = sub.add_parser("plan", help="Generate a validated action plan from natural language instruction")
    plan.add_argument("instruction", help="Natural language instruction to plan")
    plan.add_argument("--json", action="store_true", help="Output plan as JSON only")
    plan.add_argument("--execute", action="store_true", help="Execute the plan after validation")

    hw = sub.add_parser("hardware-probe")
    hw.add_argument("--deep", action="store_true", help="Deep probe with extended sampling duration")
    hw.add_argument("--duration", type=float, default=None, help="Custom probe duration in seconds")

    env_check = sub.add_parser("env-check")
    env_check.add_argument("-v", "--verbose", action="store_true", help="Show all check details")

    doctor = sub.add_parser("doctor", help="Post-install system verification — checks all components")
    doctor.add_argument("--json", action="store_true", help="Machine-readable JSON output")

    daemon = sub.add_parser("daemon")
    daemon_sub = daemon.add_subparsers(dest="daemon_cmd", required=True)
    daemon_start = daemon_sub.add_parser("start")
    daemon_start.add_argument(
        "--ros2",
        action="store_true",
        help="Force AgiBot X2 ROS2 bridge (default for agibot_x2 ontology)",
    )
    daemon_start.add_argument(
        "--g1",
        action="store_true",
        help="Force Unitree G1 Cyclone DDS bridge via SDK2 (default for unitree_g1 ontology)",
    )
    daemon_start.add_argument(
        "--no-connect",
        action="store_true",
        help="Offline: no ROS2/DDS bridge (ontology + ledger only)",
    )
    daemon_sub.add_parser("status")
    daemon_sub.add_parser("stop")
    bench = daemon_sub.add_parser("bench")
    bench.add_argument("--count", type=int, default=1000)

    wizard = sub.add_parser("wizard")
    wizard.add_argument("--port", type=int, default=8765, help="Web server port (default: 8765)")

    tui = sub.add_parser("start")
    tui.add_argument("--no-pi", action="store_true", help="Start without conversation engine")

    serve = sub.add_parser("serve")
    serve.add_argument("--mcp", action="store_true", help="Serve as MCP stdio instead of HTTP")
    serve.add_argument("--port", type=int, default=8765, help="Tool server port (default: 8765)")
    serve.add_argument("--ros2", action="store_true", help="Force AgiBot X2 ROS2 bridge")
    serve.add_argument("--g1", action="store_true", help="Force Unitree G1 Cyclone DDS bridge")
    serve.add_argument("--no-connect", action="store_true", help="Offline: no hardware bridge")
    serve.add_argument("--seconds", type=float, default=0.0, help="Run duration; 0 means forever")

    add_diag_subparser(sub)
    add_vla_subparser(sub)
    add_builder_subparser(sub)
    return parser


def make_runtime(args) -> Bootstrap:
    return Bootstrap(args.ontology, memory_dir=args.memory, skill_dir=args.skills)


def main(argv: list[str] | None = None) -> int:
    try:
        return _main_impl(argv)
    except FileNotFoundError as e:
        sys.stderr.write(f"Error: File not found — {e}\n")
        sys.stderr.write("Check that the ontology directory exists and is readable.\n")
        return 2
    except ModuleNotFoundError as e:
        sys.stderr.write(f"Error: Missing dependency — {e}\n")
        sys.stderr.write("Run: pip install -e . --break-system-packages\n")
        sys.stderr.write("Or run: manastone env-check to diagnose.\n")
        return 2
    except KeyError as e:
        sys.stderr.write(f"Error: Environment variable not set — {e}\n")
        sys.stderr.write("Required: ROBOONTO_ONTOLOGY_DIR (path to ontology directory)\n")
        sys.stderr.write("Check docs/LAUNCH_CHECKLIST.md for setup instructions.\n")
        return 2
    except Exception as e:
        if "rclpy" in str(e).lower() or "ros2" in str(e).lower():
            sys.stderr.write(f"Error: ROS2 not available — {e}\n")
            sys.stderr.write("Run: source /opt/ros/humble/setup.bash\n")
            sys.stderr.write("Then: source <sdk_path>/install/setup.bash\n")
        else:
            sys.stderr.write(f"Error: {type(e).__name__}: {e}\n")
            sys.stderr.write("Run: manastone env-check to diagnose.\n")
        return 2


def _resolve_ontology_dir(args) -> str:
    """Resolve ontology dir from CLI / config / env / hardcoded fallback.

    Precedence (highest first):
      1. --ontology CLI arg
      2. --robot CLI arg → roboonto/robots/<robot>
      3. ~/.manastone/config.yaml robot.ontology_dir
      4. ~/.manastone/config.yaml robot.model → roboonto/robots/<model>
      5. ROBOONTO_ONTOLOGY_DIR env var
      6. roboonto/robots/agibot_x2 (hardcoded default)
    """
    if args.ontology:
        return args.ontology
    if args.robot:
        return f"roboonto/robots/{args.robot}"
    cfg = load_config()
    if cfg.robot.ontology_dir:
        return os.path.expanduser(cfg.robot.ontology_dir)
    if cfg.robot.model:
        return f"roboonto/robots/{cfg.robot.model}"
    env_dir = os.environ.get("ROBOONTO_ONTOLOGY_DIR")
    if env_dir:
        return env_dir
    return "roboonto/robots/agibot_x2"


def _main_impl(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.ontology is None:
        args.ontology = _resolve_ontology_dir(args)
    fmt = Formatter(args.format)

    if args.cmd == "doc-ingest":
        result = ingest_document(
            args.path,
            doc_type=args.type,
            output_dir=args.output_dir,
            generate_skills=not args.no_generate_skills,
            verbose=args.verbose,
        )
        if not result.ok:
            sys.stderr.write(f"Error: {result.error}\n")
            return 2
        fmt.emit({
            "ok": True,
            "source": result.source_path,
            "sections": result.sections,
            "discoveries": len(result.discoveries),
            "dark_knowledge": len(result.dark_knowledge),
            "skill_candidates": len(result.skill_candidates),
            "ontology_hints": len(result.ontology_hints),
            "elapsed_s": round(result.elapsed_s, 2),
        })
        if args.verbose:
            sys.stdout.write("\n=== Ontology Hints ===\n")
            for h in result.ontology_hints[:10]:
                sys.stdout.write(f"  - {h}\n")
        return 0

    if args.cmd in ("ros2-probe", "probe", "hardware-probe"):
        # probe and hardware-probe are the same 4-layer diagnostic
        if args.cmd == "ros2-probe":
            result = probe_ros2()
            fmt.emit(result.__dict__)
            return 0 if result.available else 2
        report, exit_code = run_hardware_probe(
            args.ontology,
            deep=getattr(args, 'deep', False),
            duration=getattr(args, 'duration', None),
            format=args.format,
        )
        if args.format == "text":
            sys.stdout.write(format_probe_text(report) + "\n")
        else:
            fmt.emit(report)
        _feed_probe_to_pilot(report, args)
        return exit_code

    if args.cmd == "doctor":
        from .cli_handlers.doctor import run_doctor
        report = run_doctor()
        if getattr(args, 'json', False) or args.format == "json":
            fmt.emit(report.to_dict())
        else:
            sys.stdout.write(report.render_text() + "\n")
        return 0 if report.all_ok else 1

    if args.cmd == "env-check":
        results, all_ok = run_env_check(verbose=args.verbose)
        if args.format == "json":
            fmt.emit([{"item": r.item, "ok": r.ok, "detail": r.detail, "fix": r.fix} for r in results])
        # Feed probe results to Pilot as confirmed pattern discoveries
        if not args.no_daemon:
            client = _maybe_daemon_client(args)
        else:
            client = None
        if client:
            discoveries = [
                {"key": f"deploy.{r.item}", "summary": r.detail, "domain": "deploy",
                 "constraint": r.detail, "workaround": r.fix, "discovered_by": "env_check"}
                for r in results if not r.ok
            ]
            if discoveries:
                try:
                    client.call("pilot.confirmed_patterns", discoveries=discoveries)
                except Exception:
                    pass  # daemon may not support this yet
                finally:
                    client.close()
        return 0 if all_ok else 1

    runtime = make_runtime(args)

    if args.cmd == "manifest":
        sys.stdout.write(render_manifest(runtime.ontology))
        return 0

    if args.cmd == "icon":
        if args.spec:
            fmt.emit(RUNTIME_ICON.__dict__)
        else:
            sys.stdout.write(render_runtime_icon(ascii_only=args.ascii, with_label=args.label) + "\n")
        return 0

    if args.cmd == "start":
        from pilot.apps.console.engine import start_manastone
        if args.no_pi:
            os.environ["MANASTONE_NO_PI"] = "1"
        if not os.environ.get("ROBOONTO_ONTOLOGY_DIR"):
            os.environ["ROBOONTO_ONTOLOGY_DIR"] = args.ontology
        start_manastone()
        return 0

    if args.cmd == "daemon":
        return _daemon(runtime, args, fmt)

    daemon_client = _maybe_daemon_client(args)

    if args.cmd == "resources":
        result = _call_or_local(daemon_client, runtime, "resources", pattern=args.pattern, kind=args.kind)
        fmt.emit(result)
        return 0

    if args.cmd == "get":
        result = _call_or_local(daemon_client, runtime, "get", resource_id=args.resource_id)
        fmt.emit(result)
        return 0 if result else 1

    if args.cmd == "status":
        result = _call_or_local(daemon_client, runtime, "status", pattern=args.pattern)
        fmt.emit(result)
        return 0

    if args.cmd == "intent":
        params = json.loads(args.params)
        payload = {"action": args.action, "params": params, "source": args.source}
        is_stream = args.duration > 0
        if is_stream:
            payload["duration_sec"] = args.duration
            payload["rate_hz"] = args.rate
        if args.execute_ros2 and daemon_client is not None:
            cmd = "stream_intent" if is_stream else "execute_intent"
            exec_result = daemon_client.call(cmd, **payload)
            daemon_client.close()
            result = exec_result
            obs_ok = exec_result.get("observation", {}).get("ok", False)
            exec_ok = exec_result.get("execution", {}).get("ok", False)
            exit_code = 0 if (obs_ok and exec_ok) else 1
        else:
            obs_dict = _call_or_local(daemon_client, runtime, "intent", **payload)
            result = {"observation": obs_dict}
            exit_code = 0 if obs_dict.get("ok") else 1
            if args.execute_ros2 and obs_dict.get("ok"):
                obs = runtime.submit_intent(payload)
                execution = Ros2ActionExecutor(runtime).execute_observation(
                    obs,
                    duration_sec=args.duration,
                    rate_hz=args.rate,
                    intent_source=args.source,
                )
                result["execution"] = execution.__dict__
                exit_code = 0 if execution.ok else 1
        fmt.emit(result)
        return exit_code

    # ── validate (new) ──
    if args.cmd == "validate":
        params = json.loads(args.params)
        payload = {"action": args.action, "params": params, "source": args.source}
        result = _call_or_local(daemon_client, runtime, "intent", **payload)
        fmt.emit(result)
        return 0 if result.get("ok") else 1

    # ── execute (new) ──
    if args.cmd == "execute":
        params = json.loads(args.params)
        payload = {"action": args.action, "params": params, "source": args.source}
        is_stream = args.duration > 0
        if is_stream:
            payload["duration_sec"] = args.duration
            payload["rate_hz"] = args.rate
        if daemon_client is not None:
            cmd = "stream_intent" if is_stream else "execute_intent"
            exec_result = daemon_client.call(cmd, **payload)
            daemon_client.close()
            fmt.emit(exec_result)
            obs_ok = exec_result.get("observation", {}).get("ok", False)
            exec_ok = exec_result.get("execution", {}).get("ok", False)
            return 0 if (obs_ok and exec_ok) else 1
        else:
            obs = runtime.submit_intent(payload)
            result = {"observation": obs.to_dict()}
            if obs.ok and obs.type == "intent.accepted":
                execution = Ros2ActionExecutor(runtime).execute_observation(
                    obs,
                    duration_sec=args.duration,
                    rate_hz=args.rate,
                    intent_source=args.source,
                )
                result["execution"] = execution.__dict__
            fmt.emit(result)
            return 0 if obs.ok else 1

    # ── query ──
    if args.cmd == "query":
        from .cli_handlers import query as h_query
        return h_query.handle(args, runtime, daemon_client, fmt)

    # ── record ──
    if args.cmd == "record":
        from .cli_handlers import record as h_record
        return h_record.handle(args, runtime, daemon_client, fmt)

    # ── recall ──
    if args.cmd == "recall":
        from .cli_handlers import recall as h_recall
        return h_recall.handle(args, runtime, daemon_client, fmt)

    # ── backward compat: old command names ──
    if args.cmd == "ingest":
        value = json.loads(args.json_value)
        result = _call_or_local(daemon_client, runtime, "ingest", resource_id=args.resource_id, value=value, source=args.source)
        fmt.emit(result)
        return 0

    if args.cmd == "events":
        result = _call_or_local(daemon_client, runtime, "events", limit=args.limit)
        fmt.emit(result)
        return 0

    if args.cmd == "context":
        if getattr(args, 'context_cmd', '') == "external-agent":
            result = _call_or_local(daemon_client, runtime, "context.external_agent", limit=getattr(args, 'limit', 20))
            fmt.emit(result)
            return 0

    if args.cmd == "plan":
        instruction = getattr(args, 'instruction', '')
        if not instruction:
            sys.stderr.write("plan requires an instruction\n")
            return 2
        result = _call_or_local(daemon_client, runtime, "plan", instruction=instruction)
        if getattr(args, 'json', False):
            json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
        else:
            fmt.emit(result)
        # Optional: execute plan steps sequentially
        if getattr(args, 'execute', False) and result.get("valid"):
            for step in result.get("plan", []):
                action = step.get("action")
                params = step.get("params", {})
                if not action:
                    continue
                payload = {"action": action, "params": params, "source": "planner"}
                exec_result = _call_or_local(daemon_client, runtime, "execute_intent", **payload)
                fmt.emit({"step": step, "result": exec_result})
        return 0

    if args.cmd == "log":
        if getattr(args, 'log_cmd', '') == "ingest":
            text = getattr(args, 'text', None)
            if getattr(args, 'file', None):
                with open(args.file, encoding="utf-8") as f:
                    text = f.read()
            if not text:
                sys.stderr.write("log ingest requires --text or --file\n")
                return 2
            result = _call_or_local(daemon_client, runtime, "log.ingest", text=text, source=getattr(args, 'source', 'log'), level=getattr(args, 'level', 'info'))
            fmt.emit(result)
            return 0
        if getattr(args, 'log_cmd', '') == "records":
            result = _call_or_local(daemon_client, runtime, "log.records", limit=getattr(args, 'limit', 20))
            fmt.emit(result)
            return 0

    if args.cmd == "serve":
        if getattr(args, 'mcp', False):
            from .mcp import serve_mcp
            serve_mcp()
            return 0
        return _serve(runtime, args)

    if args.cmd == "diag":
        return handle_diag(args)

    if args.cmd == "vla-record":
        return handle_vla(args, runtime=runtime)

    if args.cmd == "builder":
        return handle_builder(args)

    return 1


# ═══════════════════════════════════════════════════════════
# New command handlers: query, record, recall
# ═══════════════════════════════════════════════════════════

def _maybe_daemon_client(args) -> UnixSocketClient | None:
    if args.no_daemon or not daemon_running(args.socket):
        return None
    client = UnixSocketClient(args.socket)
    client.connect()
    return client


def _call_or_local(client: UnixSocketClient | None, runtime: Bootstrap, cmd: str, **args):
    if client is not None:
        try:
            return client.call(cmd, **args)
        finally:
            client.close()
    from .daemon import dispatch_runtime

    return dispatch_runtime(runtime, cmd, args)


def _daemon_health_gate(runtime: Bootstrap, fmt: Formatter, bridge=None, *, timeout: float = 10.0) -> None:
    """Quick pre-flight check at daemon startup.
    
    Checks critical safety conditions. Warns on issues but does NOT block.
    Run `manastone probe --deep` for detailed diagnostics.
    """
    import time as _time
    start = _time.time()
    items: list[tuple[str, bool, str]] = []

    # Wait up to timeout for initial sensor data, spinning ROS2 to receive PMU
    while _time.time() - start < timeout:
        if bridge:
            bridge.spin_once(0.05)
        _time.sleep(0.5)
        # Check if we have any real sensor data (not just defaults)
        batt = runtime.registry.get("system.battery_pct")
        if batt and batt.source != "registry":
            break  # Got real data

    def _v(key, default=None):
        rv = runtime.registry.get(key)
        return default if rv is None else rv.value

    # ── Check 1: Battery ──
    battery = _v("system.battery_pct")
    if battery is None or battery < 0:
        items.append(("Battery", False, "unknown (waiting for PMU sensor)"))
    elif battery < 5:
        items.append(("Battery", False, f"{battery}% < 5%. Charge first."))
    else:
        items.append(("Battery", True, f"{battery}%"))

    # ── Check 2: Robot bus (ROS2 or G1 DDS) ──
    bus_label = "Robot bus"
    if getattr(runtime.ontology, "robot_id", "") == "unitree_g1":
        bus_label = "DDS (G1)"
    bus_status = _v("runtime.ros2.status", "unknown")
    if str(bus_status).lower() == "connected":
        items.append((bus_label, True, "connected"))
    else:
        items.append((bus_label, False, f"{bus_status} — check hardware bridge"))

    # ── Check 3: Body tilt (not already falling) ──
    tilt = _v("body.tilt_angle_deg")
    if tilt is not None and abs(float(tilt)) > 30:
        items.append(("Body tilt", False, f"{tilt:.1f}° — robot may be fallen"))
    else:
        items.append(("Body tilt", True, f"{tilt:.1f}°" if tilt is not None else "unknown"))

    # ── Check 4: EtherCAT wkc (X2 only) ──
    if getattr(runtime.ontology, "robot_id", "") != "unitree_g1":
        wkc = _v("ethercat.wkc")
        wkc_exp = _v("ethercat.wkc_expected", 9)
        if wkc is not None and int(wkc) < int(wkc_exp):
            items.append(("EtherCAT", False, f"wkc={wkc} (expected {wkc_exp}) — bus unstable"))
        else:
            items.append(("EtherCAT", True, f"wkc={wkc}" if wkc is not None else "not monitored"))

    # ── Report ──
    all_ok = all(ok for _, ok, _ in items)
    fmt.emit({
        "health_gate": {
            "passed": all_ok,
            "checks": [{"item": name, "ok": ok, "detail": detail} for name, ok, detail in items],
        }
    })

    if not all_ok:
        failures = [f"  ⚠️ {n}: {d}" for n, ok, d in items if not ok]
        sys.stderr.write("\n".join(["[health] Startup checks:"] + failures) + "\n")
        sys.stderr.write("[health] Daemon starting anyway. Run: manastone probe --deep for detailed diagnostics.\n")
        sys.stderr.flush()


def _daemon(runtime: Bootstrap, args, fmt: Formatter) -> int:
    if args.daemon_cmd == "start":
        if daemon_running(args.socket):
            sys.stderr.write(f"daemon already running at {args.socket}\n")
            return 1

        robot_id = runtime.ontology.robot_id or read_robot_id(args.ontology)
        connect_mode = resolve_connect_mode(
            robot_id,
            no_connect=getattr(args, "no_connect", False),
            force_ros2=getattr(args, "ros2", False),
            force_g1=getattr(args, "g1", False),
        )
        if getattr(args, "ros2", False) and getattr(args, "g1", False):
            sys.stderr.write("error: --ros2 and --g1 are mutually exclusive\n")
            return 2

        sys.stderr.write(
            f"[daemon] robot={robot_id} connect={connect_mode} "
            f"({connect_mode_label(connect_mode)})\n"
        )
        sys.stderr.flush()

        bridge = None
        g1_adapter = None
        g1_executor = None

        if connect_mode == "ros2":
            bridge = X2Ros2Bridge(runtime)
            bridge.start()
            runtime.ros2_bridge = bridge
            for _ in range(10):
                bridge.spin_once(0.05)
                time.sleep(0.1)
            runtime.registry.update(
                "runtime.ros2.status",
                "connected" if bridge.is_healthy() else "disconnected",
                source="ros2_bridge",
            )
            _daemon_health_gate(runtime, fmt, bridge)

        elif connect_mode == "g1":
            try:
                init_g1_dds()
            except ImportError as exc:
                sys.stderr.write(
                    f"error: G1 DDS requires unitree_sdk2py — {exc}\n"
                    f"  pip install unitree_sdk2py\n"
                    f"  export MANASTONE_DDS_INTERFACE=eth0  # robot LAN NIC\n"
                )
                return 2
            from ..g1 import G1Adapter, G1Executor

            g1_adapter = G1Adapter(runtime)
            g1_executor = G1Executor(runtime)
            g1_adapter.start()
            g1_executor.start()
            runtime.g1_adapter = g1_adapter
            time.sleep(0.5)
            _daemon_health_gate(runtime, fmt, bridge=None)

        # Open time-series DB for persistent event logging
        runtime.ledger.open()
        log_watcher = LogWatcher(runtime)
        log_watcher.start()

        tick_count = [0]

        def tick_with_health():
            if bridge:
                bridge.spin_once(0.05)
            tick_count[0] += 1
            if tick_count[0] % 30 == 0 and (bridge or g1_adapter):
                if bridge:
                    healthy = bridge.is_healthy()
                    source = "ros2_bridge"
                else:
                    healthy = g1_adapter.is_healthy()
                    source = "g1_dds"
                runtime.registry.update(
                    "runtime.ros2.status",
                    "connected" if healthy else "disconnected",
                    source=source,
                )
                if not healthy:
                    sys.stderr.write("[daemon] Robot bus disconnected\n")
                    sys.stderr.flush()
            if tick_count[0] % 200 == 0:
                runtime.registry.update(
                    "runtime.heartbeat", {"running": True}, source="runtime"
                )
                try:
                    runtime.ledger.snapshot_resources(runtime.registry)
                except Exception:
                    pass
            runtime.condition_monitor.tick()

        if connect_mode == "ros2":
            executor = Ros2ActionExecutor(runtime, owns_rclpy=False)
        elif connect_mode == "g1":
            executor = g1_executor
        else:
            executor = None

        daemon = Daemon(
            runtime,
            args.socket,
            on_tick=tick_with_health if connect_mode != "none" else None,
            executor=executor,
        )
        signal.signal(signal.SIGINT, lambda *_: daemon.stop())
        signal.signal(signal.SIGTERM, lambda *_: daemon.stop())
        try:
            daemon.serve_forever()
        finally:
            log_watcher.stop()
            if bridge:
                bridge.shutdown()
            if g1_adapter:
                g1_adapter.shutdown()
        return 0

    if args.daemon_cmd == "status":
        if not daemon_running(args.socket):
            fmt.emit({"running": False, "socket": args.socket})
            return 1
        client = UnixSocketClient(args.socket)
        client.connect()
        try:
            info = client.call("ping")
        finally:
            client.close()
        fmt.emit({"running": True, "socket": args.socket, **info})
        return 0

    if args.daemon_cmd == "stop":
        if not daemon_running(args.socket):
            fmt.emit({"running": False, "socket": args.socket})
            return 1
        client = UnixSocketClient(args.socket)
        client.connect()
        try:
            result = client.call("stop")
        finally:
            client.close()
        fmt.emit({"socket": args.socket, **result})
        return 0

    if args.daemon_cmd == "bench":
        if not daemon_running(args.socket):
            sys.stderr.write("daemon not running\n")
            return 1
        client = UnixSocketClient(args.socket)
        client.connect()
        try:
            for _ in range(20):
                client.call("ping")
            samples = []
            for _ in range(args.count):
                start = time.perf_counter_ns()
                client.call("ping")
                samples.append((time.perf_counter_ns() - start) / 1000.0)
        finally:
            client.close()
        samples.sort()
        fmt.emit(
            {
                "rtt_us": {
                    "n": args.count,
                    "p50": round(samples[int(len(samples) * 0.50)], 1),
                    "p99": round(samples[int(len(samples) * 0.99)], 1),
                }
            }
        )
        return 0

    return 1


def _serve(runtime: Bootstrap, args) -> int:
    bridge = X2Ros2Bridge(runtime) if args.ros2 else None
    if bridge:
        bridge.start()

    async def run():
        await runtime.start()
        start = time.time()
        try:
            while args.seconds <= 0 or time.time() - start < args.seconds:
                if bridge:
                    bridge.spin_once(0.05)
                await asyncio.sleep(0.05)
        finally:
            if bridge:
                bridge.shutdown()
            await runtime.stop()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"manastone serve failed: {exc}", file=sys.stderr)
        return 1
    return 0


def _feed_probe_to_pilot(report: dict, args) -> None:
    """B5: 把 Hardware Probe 的发现喂给 Cerebellum 暗知识积累。"""
    discoveries = []

    # Orphan topics (真机有但 ontology 没有)
    orphans = report.get("graph", {}).get("topics", {}).get("orphan", [])
    for topic in orphans[:20]:
        if "aima" in topic:
            discoveries.append({
                "key": f"topic.orphan.{topic}",
                "summary": f"Orphan topic observed: {topic}",
                "domain": "naming",
                "constraint": f"Topic {topic} exists on robot but not in ontology",
                "workaround": "Add to ontology interfaces.yaml",
                "discovered_by": "hardware_probe",
            })

    # QoS mismatches
    sensors = report.get("sensors", {})
    for sensor_id, info in sensors.items():
        if info.get("qos_actual") == "no_data" and info.get("qos_expected"):
            discoveries.append({
                "key": f"qos.mismatch.{sensor_id}",
                "summary": f"QoS mismatch: {sensor_id} got no data with expected QoS {info['qos_expected']}",
                "domain": "qos",
                "constraint": f"Sensor {sensor_id} QoS: expected={info['qos_expected']}, actual=no_data",
                "workaround": "Try different QoS (TRANSIENT_LOCAL / RELIABLE)",
                "discovered_by": "hardware_probe",
            })

    if not discoveries:
        return

    # Feed via daemon if available, otherwise create local stream
    client = _maybe_daemon_client(args)
    if client:
        try:
            client.call("pilot.confirmed_patterns", discoveries=discoveries)
        except Exception:
            pass
        finally:
            client.close()
    else:
        # Fallback: local memory
        try:
            from ..kernel import SemanticResourceRegistry
            registry = SemanticResourceRegistry()
            memory = DeviceMemory(args.memory)
            stream = Pilot(
                registry, memory, model_client=None,
                system_prompt=PILOT_SYSTEM_PROMPT,
            )
            stream.bind()
            stream.accumulate_patterns(discoveries)
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
