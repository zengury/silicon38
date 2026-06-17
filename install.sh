#!/usr/bin/env bash
# Silicon Org — Verify skills are present (all pre-packaged, no install needed)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/.agents/skills"

echo "Silicon Org — Checking pre-packaged skills..."
echo ""

missing=0
total=0

for skill_dir in "$SKILLS_DIR"/*/; do
  skill=$(basename "$skill_dir")
  total=$((total + 1))
  if [ -f "$skill_dir/SKILL.md" ]; then
    echo "  ✅ $skill"
  else
    echo "  ❌ $skill — SKILL.md missing"
    missing=$((missing + 1))
  fi
done

echo ""
echo "$total skills checked, $missing missing."

if [ $missing -gt 0 ]; then
  echo "Run: git pull origin main to restore missing skills."
  exit 1
fi

echo "All skills present. No installation required."
echo "Start your coding agent in this directory to begin."
