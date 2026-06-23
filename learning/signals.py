"""Structured learning signals for Silicon Org traces."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


OUTCOME_PRIORS = {
    "success": 1.0,
    "partial": 0.5,
    "failed": 0.0,
    "unknown": 0.0,
}

RELATION_MULTIPLIERS = {
    "triggers": 1.0,
    "may_trigger": 0.9,
    "evaluates": 0.85,
    "supports": 0.45,
    "constrains": 0.55,
    "complements": 0.40,
    "augments": 0.35,
}


@dataclass(frozen=True)
class LearningSignal:
    """A normalized signal with explanation for auditability."""

    value: float
    confidence: float
    source: str
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def outcome_status(manifest: dict[str, Any]) -> str:
    outcome = manifest.get("outcome") or {}
    return outcome.get("status") or "unknown"


def decoder_quality(manifest: dict[str, Any]) -> float | None:
    outcome = manifest.get("outcome") or {}
    quality = outcome.get("quality_signal") or {}
    value = quality.get("value")
    if isinstance(value, (int, float)):
        return clamp(float(value))
    return None


def base_outcome_signal(manifest: dict[str, Any]) -> LearningSignal:
    status = outcome_status(manifest)
    prior = OUTCOME_PRIORS.get(status, 0.0)
    quality = decoder_quality(manifest)
    if quality is None:
        value = prior
        detail = f"outcome={status}; no decoder quality override"
    else:
        value = (prior * 0.7) + (quality * 0.3)
        detail = f"outcome={status}; decoder_quality={quality:.2f}"
    return LearningSignal(
        value=clamp(value),
        confidence=0.50 if status == "unknown" else 0.65,
        source="manifest.outcome",
        detail=detail,
    )


def role_signal(manifest: dict[str, Any], role: str) -> LearningSignal:
    base = base_outcome_signal(manifest)
    terminal_nodes = set(manifest.get("terminal_nodes") or [])
    if role in terminal_nodes:
        confidence = min(1.0, base.confidence + 0.10)
        detail = f"{base.detail}; terminal_role=true"
    else:
        confidence = max(0.10, base.confidence - 0.10)
        detail = f"{base.detail}; terminal_role=false"
    return LearningSignal(
        value=base.value,
        confidence=confidence,
        source="role_credit_assignment.v0",
        detail=detail,
    )


def relation_signal(manifest: dict[str, Any], handoff: dict[str, Any]) -> LearningSignal:
    base = base_outcome_signal(manifest)
    rel_type = handoff.get("relation_type") or "unknown"
    multiplier = RELATION_MULTIPLIERS.get(rel_type, 0.25)
    value = clamp(base.value * multiplier)
    return LearningSignal(
        value=value,
        confidence=max(0.10, base.confidence * multiplier),
        source="relation_credit_assignment.v0",
        detail=(
            f"{base.detail}; relation_type={rel_type}; "
            f"multiplier={multiplier:.2f}"
        ),
    )
