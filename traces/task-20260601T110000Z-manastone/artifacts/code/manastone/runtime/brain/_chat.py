"""
manastone LLM client — internal module (not user-facing)

Supports: anthropic, openai, ollama

Config priority:
  1. ~/.manastone/config.yaml  (manastone config)
  2. ~/.manastone/engine settings  (legacy engine bridge)
  3. Environment variables (ANTHROPIC_API_KEY / OPENAI_API_KEY / MANASTONE_API_KEY)
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any


# ═══════════════════════════════════════════════════════════
# Config: read from engine settings
# ═══════════════════════════════════════════════════════════

def _load_engine_settings() -> dict[str, Any]:
    """Load engine bridge settings from config paths."""
    # Primary: ~/.manastone/config.yaml
    manastone_config = Path.home() / ".manastone" / "config.yaml"
    if manastone_config.exists():
        try:
            import yaml
            data = yaml.safe_load(manastone_config.read_text()) or {}
            engine = data.get("engine", {})
            if engine.get("api_key") or engine.get("provider"):
                return engine
        except Exception:
            pass
    # Fallback: legacy engine bridge settings (~/.pi/agent/settings.json)
    settings_path = Path.home() / ".pi" / "agent" / "settings.json"
    if settings_path.exists():
        try:
            return json.loads(settings_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def get_config() -> dict[str, Any]:
    """Get the active LLM configuration.
    
    Returns dict with: provider, api_key, model, api_base (optional)
    """
    settings = _load_engine_settings()
    
    # Check manastone API key (primary)
    manastone_api_key = os.environ.get("MANASTONE_API_KEY", "")
    if manastone_api_key:
        api_base = os.environ.get("MANASTONE_API_BASE", settings.get("api_base", ""))
        return {
            "provider": settings.get("provider", "anthropic"),
            "api_key": manastone_api_key,
            "model": settings.get("model", "claude-sonnet-4-20250514"),
            "api_base": api_base or None,
        }
    
    # Check legacy PI_API_KEY (silent fallback)
    pi_api_key = os.environ.get("PI_API_KEY", settings.get("apiKey", ""))
    if pi_api_key:
        return {
            "provider": "anthropic",
            "api_key": pi_api_key,
            "model": settings.get("model", "claude-sonnet-4-20250514"),
            "api_base": os.environ.get("PI_API_BASE", None),
        }
    
    # Check provider-specific keys
    for provider, env_key in [
        ("anthropic", "ANTHROPIC_API_KEY"),
        ("openai", "OPENAI_API_KEY"),
    ]:
        api_key = os.environ.get(env_key, "")
        if api_key:
            model = settings.get("model", "")
            return {
                "provider": provider,
                "api_key": api_key,
                "model": model or _default_model(provider),
            }
    
    # Check ollama (no key needed)
    if _ollama_available():
        return {
            "provider": "ollama",
            "api_key": "",
            "model": settings.get("model", "llama3"),
        }
    
    return {"provider": "", "api_key": "", "model": ""}


def _default_model(provider: str) -> str:
    if provider == "anthropic":
        return "claude-sonnet-4-20250514"
    if provider == "openai":
        return "gpt-4o"
    return ""


def _ollama_available() -> bool:
    try:
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        urllib.request.urlopen(f"{host}/api/tags", timeout=2)
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════
# Chat API
# ═══════════════════════════════════════════════════════════

async def chat(
    message: str,
    *,
    provider: str = "",
    model: str = "",
    context: dict[str, Any] | None = None,
    history: list[dict[str, str]] | None = None,
    system: str = "",
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> dict[str, Any]:
    """Send a chat message. Provider auto-detected from config if not specified."""
    if not provider:
        config = get_config()
        provider = config["provider"]
        model = model or config["model"]

    if provider == "anthropic":
        return await _chat_anthropic(message, model, context, history, system, max_tokens, temperature)
    elif provider == "openai":
        return await _chat_openai(message, model, context, history, system, max_tokens, temperature)
    elif provider == "ollama":
        return await _chat_ollama(message, model, context, history, system, max_tokens, temperature)
    else:
        return {"reply": "", "error": f"Unknown provider: {provider}. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."}


# ═══════════════════════════════════════════════════════════
# Subscription API (Anthropic-compatible, internal)
# ═══════════════════════════════════════════════════════════

async def _chat_subscription(
    message: str, model: str, context: dict | None,
    history: list[dict] | None, system: str,
    max_tokens: int, temperature: float,
    api_key: str, api_base: str | None = None,
) -> dict[str, Any]:
    if not api_key:
        return {"reply": "", "error": "API key not set. Set MANASTONE_API_KEY or ANTHROPIC_API_KEY environment variable."}
    
    model = model or "claude-sonnet-4-20250514"
    messages = _build_messages(message, context, history, system)
    api_base = api_base or "https://api.anthropic.com"
    
    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }).encode()
    
    req = urllib.request.Request(
        f"{api_base}/v1/messages",
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())
        reply = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                reply += block.get("text", "")
        return {"reply": reply, "model": data.get("model", model), "usage": data.get("usage")}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode(errors="replace")[:500]
        return {"reply": "", "error": f"API error ({e.code}): {err_body}"}
    except Exception as e:
        return {"reply": "", "error": str(e)}


# ═══════════════════════════════════════════════════════════
# Anthropic
# ═══════════════════════════════════════════════════════════

async def _chat_anthropic(
    message: str, model: str, context: dict | None,
    history: list[dict] | None, system: str,
    max_tokens: int, temperature: float,
) -> dict[str, Any]:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"reply": "", "error": "ANTHROPIC_API_KEY not set"}

    model = model or "claude-sonnet-4-20250514"
    messages = _build_messages(message, context, history, system)

    body = json.dumps({
        "model": model, "max_tokens": max_tokens,
        "temperature": temperature, "messages": messages,
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
    )

    try:
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())
        reply = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        return {"reply": reply, "model": data.get("model", model), "usage": data.get("usage")}
    except urllib.error.HTTPError as e:
        return {"reply": "", "error": f"Anthropic API error ({e.code}): {e.read().decode(errors='replace')[:500]}"}
    except Exception as e:
        return {"reply": "", "error": str(e)}


# ═══════════════════════════════════════════════════════════
# OpenAI
# ═══════════════════════════════════════════════════════════

async def _chat_openai(
    message: str, model: str, context: dict | None,
    history: list[dict] | None, system: str,
    max_tokens: int, temperature: float,
) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return {"reply": "", "error": "OPENAI_API_KEY not set"}

    model = model or "gpt-4o"
    messages = _build_messages(message, context, history, system)

    body = json.dumps({
        "model": model, "max_tokens": max_tokens,
        "temperature": temperature, "messages": messages,
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )

    try:
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())
        choice = data.get("choices", [{}])[0]
        reply = choice.get("message", {}).get("content", "")
        return {"reply": reply, "model": data.get("model", model), "usage": data.get("usage")}
    except urllib.error.HTTPError as e:
        return {"reply": "", "error": f"OpenAI API error ({e.code}): {e.read().decode(errors='replace')[:500]}"}
    except Exception as e:
        return {"reply": "", "error": str(e)}


# ═══════════════════════════════════════════════════════════
# Ollama
# ═══════════════════════════════════════════════════════════

async def _chat_ollama(
    message: str, model: str, context: dict | None,
    history: list[dict] | None, system: str,
    max_tokens: int, temperature: float,
) -> dict[str, Any]:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model = model or "llama3"

    messages = _build_messages(message, context, history, system)

    body = json.dumps({
        "model": model, "messages": messages, "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }).encode()

    req = urllib.request.Request(f"{host}/api/chat", data=body, headers={"Content-Type": "application/json"})

    try:
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read())
        reply = data.get("message", {}).get("content", "")
        return {
            "reply": reply, "model": data.get("model", model),
            "usage": {"prompt_tokens": data.get("prompt_eval_count", 0), "completion_tokens": data.get("eval_count", 0)},
        }
    except urllib.error.HTTPError as e:
        return {"reply": "", "error": f"Ollama API error ({e.code}): {e.read().decode(errors='replace')[:500]}"}
    except Exception as e:
        return {"reply": "", "error": str(e)}


# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════

def _build_messages(
    message: str, context: dict[str, Any] | None,
    history: list[dict[str, str]] | None, system: str,
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    system_parts = []
    if system:
        system_parts.append(system)
    if context:
        system_parts.append(f"Context:\n{json.dumps(context, ensure_ascii=False, indent=2)}")
    if system_parts:
        messages.append({"role": "system", "content": "\n\n".join(system_parts)})
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})
    return messages
