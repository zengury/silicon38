"""Shared runtime constants — single source of truth.

按 ARCHITECTURE 分层: runtime/ 是最底应用层 (只依赖 roboonto)，
runtime/ 与 pilot/apps/ 都可引用这里的常量。
pilot/orchestrator/ 设计上独立部署，保留自己的默认值。
"""
from __future__ import annotations

import os
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# Brand identity — single source for all user-facing strings
# ═══════════════════════════════════════════════════════════
BRAND = "Manastone"

# Engine directory — the conversation engine is installed here
# as a hidden dependency. Users never interact with this directly.
ENGINE_DIR = Path.home() / ".manastone" / "engine"
ENGINE_BIN = ENGINE_DIR / "node_modules" / ".bin" / "pi"

# manastone runtime daemon 的 Unix socket 默认路径。
# 可用 MANASTONE_SOCKET 环境变量覆盖。
DEFAULT_SOCKET = os.environ.get("MANASTONE_SOCKET", "/tmp/manastone.sock")
