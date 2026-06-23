"""manastone doctor — post-install system verification.

Checks the health of a Manastone installation across all components:
conversation engine, Python runtime, configuration, robot detection, and connectivity.

Usage:
    manastone doctor               # Run all checks
    manastone doctor --json        # Machine-readable output
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ...constants import BRAND, ENGINE_DIR, ENGINE_BIN


@dataclass
class DoctorCheck:
    name: str
    ok: bool
    detail: str = ""
    fix: str = ""


@dataclass
class DoctorReport:
    checks: list[DoctorCheck] = field(default_factory=list)

    @property
    def all_ok(self) -> bool:
        return all(c.ok for c in self.checks)

    @property
    def ok_count(self) -> int:
        return sum(1 for c in self.checks if c.ok)

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if not c.ok)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.all_ok,
            "summary": f"{self.ok_count}/{len(self.checks)} checks passed",
            "checks": [
                {"name": c.name, "ok": c.ok, "detail": c.detail, "fix": c.fix}
                for c in self.checks
            ],
        }

    def render_text(self) -> str:
        lines = ["Manastone Doctor — System Verification", "=" * 42, ""]
        for c in self.checks:
            icon = "✓" if c.ok else "✗"
            lines.append(f"  [{icon}] {c.name}")
            if c.detail:
                lines.append(f"      {c.detail}")
            if not c.ok and c.fix:
                lines.append(f"      Fix: {c.fix}")
        lines.append("")
        lines.append(f"Result: {self.ok_count}/{len(self.checks)} checks passed")
        if not self.all_ok:
            lines.append(f"  {self.fail_count} issue(s) found. See details above.")
        return "\n".join(lines)


def run_doctor() -> DoctorReport:
    """Run all verification checks and return a report."""
    report = DoctorReport()

    # ── 1. Conversation engine ──
    if ENGINE_BIN.exists() and os.access(str(ENGINE_BIN), os.X_OK):
        try:
            result = subprocess.run(
                [str(ENGINE_BIN), "--version"],
                capture_output=True, text=True, timeout=5,
            )
            version = result.stdout.strip() or result.stderr.strip() or "unknown version"
            report.checks.append(DoctorCheck(
                name="Conversation engine",
                ok=True,
                detail=f"Installed: {version}",
            ))
        except Exception:
            report.checks.append(DoctorCheck(
                name="Conversation engine",
                ok=True,
                detail=f"Found at: {ENGINE_BIN}",
            ))
    else:
        report.checks.append(DoctorCheck(
            name="Conversation engine",
            ok=False,
            detail="Conversation engine not found",
            fix="Re-run bootstrap/install.sh to install the engine",
        ))

    # ── 2. Engine directory ──
    if ENGINE_DIR.exists():
        report.checks.append(DoctorCheck(
            name="Engine directory",
            ok=True,
            detail=str(ENGINE_DIR),
        ))
    else:
        report.checks.append(DoctorCheck(
            name="Engine directory",
            ok=False,
            detail=f"{ENGINE_DIR} does not exist",
            fix="Re-run bootstrap/install.sh",
        ))

    # ── 3. Node.js ──
    node_path = shutil.which("node")
    if node_path:
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
            report.checks.append(DoctorCheck(
                name="Node.js",
                ok=True,
                detail=result.stdout.strip(),
            ))
        except Exception:
            report.checks.append(DoctorCheck(
                name="Node.js",
                ok=True,
                detail=f"Found at: {node_path}",
            ))
    else:
        report.checks.append(DoctorCheck(
            name="Node.js",
            ok=False,
            detail="Node.js not found",
            fix="Install from https://nodejs.org/",
        ))

    # ── 3. Python runtime ──
    try:
        import manastone  # noqa: F401
        report.checks.append(DoctorCheck(
            name="Python runtime",
            ok=True,
            detail="manastone package importable",
        ))
    except ImportError:
        report.checks.append(DoctorCheck(
            name="Python runtime",
            ok=False,
            detail="manastone package not importable",
            fix="pip install -e . (from manastone directory)",
        ))

    # ── 4. Configuration ──
    config_path = Path.home() / ".manastone" / "config.yaml"
    if config_path.exists():
        try:
            import yaml
            data = yaml.safe_load(config_path.read_text()) or {}
            robot = (data.get("robot") or {}).get("model", "unknown")
            report.checks.append(DoctorCheck(
                name="Configuration",
                ok=True,
                detail=f"~/.manastone/config.yaml (robot: {robot})",
            ))
        except Exception:
            report.checks.append(DoctorCheck(
                name="Configuration",
                ok=True,
                detail="~/.manastone/config.yaml exists",
            ))
    else:
        report.checks.append(DoctorCheck(
            name="Configuration",
            ok=False,
            detail="~/.manastone/config.yaml not found",
            fix="Run: manastone init  (or re-run bootstrap/install.sh)",
        ))

    # ── 5. Launcher scripts ──
    launcher = Path.home() / ".local" / "bin" / "manastone-launcher"
    if launcher.exists() and os.access(str(launcher), os.X_OK):
        report.checks.append(DoctorCheck(
            name="Launcher script",
            ok=True,
            detail=str(launcher),
        ))
    else:
        report.checks.append(DoctorCheck(
            name="Launcher script",
            ok=False,
            detail="~/.local/bin/manastone-launcher not found or not executable",
            fix="Re-run bootstrap/install.sh",
        ))

    # ── 6. Python version ──
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        report.checks.append(DoctorCheck(
            name="Python version",
            ok=True,
            detail=py_ver,
        ))
    else:
        report.checks.append(DoctorCheck(
            name="Python version",
            ok=False,
            detail=f"{py_ver} — need 3.10+",
            fix="Install Python 3.10+: https://www.python.org/downloads/",
        ))

    # ── 7. Config directory ──
    manastone_dir = Path.home() / ".manastone"
    if manastone_dir.exists():
        report.checks.append(DoctorCheck(
            name="Config directory",
            ok=True,
            detail=str(manastone_dir),
        ))
    else:
        report.checks.append(DoctorCheck(
            name="Config directory",
            ok=False,
            detail="~/.manastone/ does not exist",
            fix="mkdir -p ~/.manastone",
        ))

    # ── 8. Robot tools extension ──
    # Check if pilot/coding-agent exists and has expected structure
    runtime_dir = _find_runtime_dir()
    ext_dir = runtime_dir / "pilot" / "coding-agent"
    if ext_dir.exists():
        pkg_json = ext_dir / "package.json"
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text())
                name = pkg.get("name", "unknown")
                report.checks.append(DoctorCheck(
                    name="Robot tools",
                    ok=True,
                    detail=f"{name} v{pkg.get('version', '?')}",
                ))
            except Exception:
                report.checks.append(DoctorCheck(
                    name="Robot tools",
                    ok=True,
                    detail="pilot/coding-agent/ exists",
                ))
        else:
            report.checks.append(DoctorCheck(
                name="Robot tools",
                ok=True,
                detail="pilot/coding-agent/ exists",
            ))
    else:
        report.checks.append(DoctorCheck(
            name="Robot tools",
            ok=False,
            detail="pilot/coding-agent/ not found",
            fix="Ensure you are in the manastone repository directory",
        ))

    # ── 9. pip ──
    pip_path = shutil.which("pip3") or shutil.which("pip")
    if pip_path:
        report.checks.append(DoctorCheck(
            name="pip",
            ok=True,
            detail=str(pip_path),
        ))
    else:
        report.checks.append(DoctorCheck(
            name="pip",
            ok=False,
            detail="pip not found",
            fix="python3 -m ensurepip --upgrade",
        ))

    # ── 10. Engine npm package ──
    engine_pkg_json = ENGINE_DIR / "node_modules" / "@mariozechner" / "pi-coding-agent" / "package.json"
    npm_path = shutil.which("npm")
    if engine_pkg_json.exists():
        try:
            pkg = json.loads(engine_pkg_json.read_text())
            report.checks.append(DoctorCheck(
                name="Engine package",
                ok=True,
                detail=f"v{pkg.get('version', '?')}",
            ))
        except Exception:
            report.checks.append(DoctorCheck(
                name="Engine package",
                ok=True,
                detail="Engine package found",
            ))
    elif npm_path:
        report.checks.append(DoctorCheck(
            name="Engine package",
            ok=False,
            detail="Engine npm package not found in local install",
            fix="Re-run bootstrap/install.sh",
        ))
    else:
        report.checks.append(DoctorCheck(
            name="Engine package",
            ok=False,
            detail="Cannot verify engine — npm not found",
            fix="Install Node.js from https://nodejs.org/ then re-run bootstrap/install.sh",
        ))

    return report


def _find_runtime_dir() -> Path:
    """Locate the manastone runtime directory."""
    # Try to find from import
    try:
        import manastone
        pkg_dir = Path(manastone.__file__).parent
        if (pkg_dir / "pyproject.toml").exists():
            return pkg_dir
        # We are in the installed package; walk up to the repo root
        for parent in pkg_dir.parents:
            if (parent / "pyproject.toml").exists():
                return parent
    except ImportError:
        pass

    # Fall back to current directory
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    return cwd
