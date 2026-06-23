"""
Structured logging — thin wrapper around loguru with PII masking and
machine-parseable context.

Usage::

    from infrastructure.observability.logging import structured_log

    structured_log("INFO", "User created", entity="User", user_id="abc123")

PII Protection (two layers, applied by default):
  1. Sensitive-key redaction: any key matching password/token/secret etc.
     pattern has its value replaced with [REDACTED].
  2. Value-pattern detection: emails, Chinese phone numbers, JWT tokens
     are auto-masked.

Correlation IDs:
  Call configure_correlation_logging() once at startup to enable
  automatic correlation_id injection into every log record.
"""

import re
from typing import Any, Dict, Optional

from loguru import logger

# ── PII detection patterns ────────────────────────────────────────────

# Keys whose values are always redacted
_SENSITIVE_KEY_PATTERNS = re.compile(
    r"(password|passwd|pwd|secret|token|api_key|apikey|"
    r"access_token|refresh_token|csrf_token|sender_password|"
    r"jwt_secret|private_key|credential|auth_key)$",
    re.IGNORECASE,
)

# Value patterns that indicate PII
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_CN_PHONE_RE = re.compile(r"1[3-9]\d{9}")
_JWT_RE = re.compile(r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+")

# Maximum value length to scan for PII patterns (performance guard)
_MAX_PII_SCAN_LENGTH = 500


def mask_pii_value(value: Any) -> str:
    """Return a PII-safe string representation of *value*.

    Args:
        value: Any value (str, int, float, etc.).

    Returns:
        A string with emails → ``***@***``, Chinese phones → ``138****1234``,
        JWT tokens → ``[JWT-REDACTED]``.  Non-string values are converted
        via ``str()`` without masking.
    """
    if not isinstance(value, str):
        return str(value)

    if len(value) > _MAX_PII_SCAN_LENGTH:
        return f"{value[:_MAX_PII_SCAN_LENGTH]}...[TRUNCATED-{len(value)}]"

    value = _EMAIL_RE.sub("***@***", value)
    value = _CN_PHONE_RE.sub(
        lambda m: f"{m.group()[:3]}****{m.group()[-4:]}", value
    )
    value = _JWT_RE.sub("[JWT-REDACTED]", value)
    return value


def _is_sensitive_key(key: str) -> bool:
    """Check whether *key* matches a known sensitive-key pattern."""
    return bool(_SENSITIVE_KEY_PATTERNS.search(key))


def _sanitize_context(context: Dict[str, Any], pii_safe: bool) -> str:
    """Build a key=value string from *context* with optional PII masking."""
    if not context:
        return ""

    parts: list[str] = []
    for k, v in sorted(context.items()):
        if pii_safe and _is_sensitive_key(k):
            parts.append(f"{k}=[REDACTED]")
        elif pii_safe:
            parts.append(f"{k}={mask_pii_value(v)}")
        else:
            parts.append(f"{k}={v}")
    return " ".join(parts)


def structured_log(
    level: str,
    message: str,
    *,
    pii_safe: bool = True,
    **context: Any,
) -> None:
    """Emit a structured log line with extra key=value context.

    Args:
        level: Log level — one of ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``.
        message: Human-readable log message (no string interpolation).
        pii_safe: If ``True`` (default), apply PII masking to context values.
        **context: Key-value pairs appended as ``key=value`` after the message.

    Example::

        structured_log(
            "ERROR", "Dify API call failed",
            http_status=401, dify_agent_id="app-xxx",
        )
        # → ERROR | Dify API call failed http_status=401 dify_agent_id=app-xxx

        structured_log(
            "INFO", "Login succeeded",
            user_email="alice@example.com",
        )
        # With pii_safe=True → user_email=***@***
    """
    ctx_str = _sanitize_context(context, pii_safe=pii_safe)
    if ctx_str:
        line = f"{message} | {ctx_str}"
    else:
        line = message
    logger.opt(depth=1).log(level, line)


def configure_correlation_logging() -> None:
    """Configure loguru to inject ``correlation_id`` into every log record.

    Call once at application startup.  After calling this, any ``logger.bind()``
    or ``logger.contextualize()`` with ``correlation_id`` will include it in
    the formatted output.

    The middleware in ``middleware.py`` uses ``logger.contextualize()`` to
    set the correlation ID per-request.
    """
    # Leave loguru's default format alone — correlation_id is picked up
    # via logger.bind() / logger.contextualize() in the middleware.
    # The configure() here is a no-op because we use per-record binding.
    logger.configure(
        extra={"correlation_id": ""},
        patcher=lambda record: record["extra"].setdefault("correlation_id", ""),
    )
