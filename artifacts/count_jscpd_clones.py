#!/usr/bin/env python3
"""
Count jscpd clones from a JSON report file.

Usage:
    python3 scripts/count_jscpd_clones.py jscpd-report-backend/jscpd-report.json
    # Prints: <clone_count>

Exit codes:
    0 — success (prints clone count, may be 0)
    1 — file not found
    2 — JSON parse error
"""
import json
import sys

if len(sys.argv) < 2:
    print("Usage: count_jscpd_clones.py <jscpd-report.json>", file=sys.stderr)
    sys.exit(1)

try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
except FileNotFoundError:
    print("0")
    sys.exit(1)
except json.JSONDecodeError:
    print("0")
    sys.exit(2)

clones = data.get("statistics", {}).get("total", {}).get("clonesCount", 0)
print(clones)
