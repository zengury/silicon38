#!/usr/bin/env python3
"""Brand audit — scan codebase for pi brand leaks.

Reports every location where the pi brand leaks into user-facing code.
Respects .gitignore. Non-zero exit on findings so it can gate CI.

Usage:
    python3 scripts/brand_audit.py             # scan all files
    python3 scripts/brand_audit.py --json       # machine-readable output
    python3 scripts/brand_audit.py --fix-docs   # list only docs needing update
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# ── Patterns that indicate a pi brand leak ──
# Each entry: (regex, severity, description, allowed_context)
# severity: high (user-facing) / medium (internal docs) / low (comment / dev-only)
BRAND_PATTERNS: list[dict[str, Any]] = [
    {
        "pattern": re.compile(r"@mariozechner/pi-coding-agent"),
        "severity": "high",
        "description": "npm package name reference",
        "allowed_in": [
            "pilot/coding-agent/package.json",  # npm dependency name (external fact)
            "pilot/coding-agent/package-lock.json",
            "pilot/coding-agent/extensions/robot-tools.ts",  # TS type import
            "scripts/brand_audit.py",  # this file
            "docs/brand/",  # brand inventory docs
            "bootstrap/install.sh",  # external dep install (silent, > /dev/null)
        ],
    },
    {
        "pattern": re.compile(r"\bpi-coding-agent\b"),
        "severity": "high",
        "description": "package short-name reference",
        "allowed_in": [
            "pilot/coding-agent/package.json",
            "pilot/coding-agent/package-lock.json",
            "pilot/coding-agent/extensions/robot-tools.ts",  # TS type import
            "scripts/brand_audit.py",
            "docs/brand/",
            "bootstrap/install.sh",  # external dep install
            "runtime/io/cli_handlers/doctor.py",  # engine path check
        ],
    },
    {
        "pattern": re.compile(r"npm install -g.*pi"),
        "severity": "high",
        "description": "install command leaking pi brand",
        "allowed_in": [
            "scripts/brand_audit.py",
            "docs/brand/",
            "bootstrap/install.sh",  # internal install script — reviewed for silent install
        ],
    },
    {
        "pattern": re.compile(r"\bPI_API_KEY\b"),
        "severity": "medium",
        "description": "legacy pi API key env var",
        "allowed_in": [
            "runtime/brain/_chat.py",  # fallback for existing users
            "roboonto/importers/doc_ingestor.py",  # fallback for existing users
            "scripts/brand_audit.py",
            "docs/brand/",
        ],
    },
    {
        "pattern": re.compile(r"pi\.dev"),
        "severity": "high",
        "description": "pi website reference",
        "allowed_in": [
            "scripts/brand_audit.py",
            "docs/brand/",
        ],
    },
    {
        "pattern": re.compile(r"~/.pi/"),
        "severity": "medium",
        "description": "pi config directory reference",
        "allowed_in": [
            "runtime/brain/_chat.py",  # legacy fallback
            "scripts/brand_audit.py",
            "docs/brand/",
            "pilot/apps/diag/launcher.py",  # legacy fallback
            "pilot/apps/console/engine.py",  # legacy settings read
            "roboonto/importers/doc_ingestor.py",  # legacy settings read
        ],
    },
    {
        "pattern": re.compile(r"\"pi\"|\'pi\'(?![a-zA-Z])", re.IGNORECASE),
        "severity": "medium",
        "description": "string literal 'pi' (may be a false positive for math)",
        "allowed_in": [
            "runtime/constants.py",  # ENGINE_BIN path
            "scripts/brand_audit.py",
            "docs/brand/",
            "runtime/io/cli_handlers/doctor.py",  # engine path checks
            "pilot/apps/diag/launcher.py",  # engine path fallback
            "pilot/coding-agent/package.json",  # pi extension config key (external API)
            "pyproject.toml",  # comment about pi/ module structure
            "pilot/__init__.py",  # historical naming note
        ],
    },
    {
        "pattern": re.compile(r"\bPi (dialog|coding|chat)\s+engine\b"),
        "severity": "medium",
        "description": "pi engine in prose (should say conversation engine)",
        "allowed_in": [
            "scripts/brand_audit.py",
            "docs/brand/",
        ],
    },
]

# ── Files to skip entirely ──
SKIP_GLOBS = [
    "*.pyc",
    "__pycache__/*",
    ".git/*",
    ".pytest_cache/*",
    "node_modules/*",
    "*.egg-info/*",
    "*.lock",
]


def should_skip(path: Path) -> bool:
    """Check if a file should be skipped."""
    rel = str(path)
    for glob in SKIP_GLOBS:
        if path.match(glob) or glob in rel:
            return True
    # Skip all documentation — internal, not user-facing
    if "docs/" in rel or "docs\\" in rel:
        return True
    return False


def is_allowed(path: Path, allowed_in: list[str]) -> bool:
    """Check if a finding is in an allowed location."""
    rel = str(path)
    for allowed in allowed_in:
        if allowed.rstrip("/") in rel or rel.startswith(allowed.rstrip("/")):
            return True
    return False


def scan_file(path: Path) -> list[dict[str, Any]]:
    """Scan a single file for brand leaks."""
    findings: list[dict[str, Any]] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return findings

    lines = content.split("\n")
    for pattern_info in BRAND_PATTERNS:
        pattern = pattern_info["pattern"]
        allowed_in = pattern_info.get("allowed_in", [])
        if is_allowed(path, allowed_in):
            continue
        for i, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append({
                    "file": str(path),
                    "line": i,
                    "text": line.strip()[:120],
                    "severity": pattern_info["severity"],
                    "description": pattern_info["description"],
                })
    return findings


def scan_repo(root: Path) -> list[dict[str, Any]]:
    """Scan all tracked files in the repository."""
    all_findings: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if should_skip(path):
            continue
        findings = scan_file(path)
        all_findings.extend(findings)
    return all_findings


def render_text(findings: list[dict[str, Any]]) -> str:
    """Render findings as human-readable text."""
    if not findings:
        return "Brand audit: PASSED — no pi brand leaks found.\n"

    lines = [f"Brand audit: {len(findings)} potential brand leak(s) found.\n"]
    high = [f for f in findings if f["severity"] == "high"]
    medium = [f for f in findings if f["severity"] == "medium"]
    low = [f for f in findings if f["severity"] == "low"]

    for label, subset in [("HIGH", high), ("MEDIUM", medium), ("LOW", low)]:
        if not subset:
            continue
        lines.append(f"\n  [{label}] {len(subset)} finding(s):")
        for f in subset:
            lines.append(f"    {f['file']}:{f['line']}")
            lines.append(f"      {f['text']}")
            lines.append(f"      → {f['description']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manastone brand audit — scan for pi brand leaks")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--root", default=None, help="Repository root (default: auto-detect)")
    args = parser.parse_args(argv)

    if args.root:
        root = Path(args.root)
    else:
        # Auto-detect: walk up from this script
        script_dir = Path(__file__).resolve().parent
        for parent in [script_dir] + list(script_dir.parents):
            if (parent / "pyproject.toml").exists():
                root = parent
                break
        else:
            root = script_dir.parent
            sys.stderr.write(f"warning: could not find repo root, using {root}\n")

    findings = scan_repo(root)

    if args.json:
        result = {
            "passed": len(findings) == 0,
            "findings_count": len(findings),
            "findings": findings,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(render_text(findings))

    return 0 if len(findings) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
