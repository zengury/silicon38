"""Conservative formulas for human-reviewed graph weight proposals."""

from __future__ import annotations


def ema(previous: float, signal: float, alpha: float = 0.05) -> float:
    """Exponential moving average for bounded graph weights."""

    previous = max(0.0, min(1.0, previous))
    signal = max(0.0, min(1.0, signal))
    return (previous * (1 - alpha)) + (signal * alpha)


def confidence_from_samples(samples: int) -> float:
    """Map sample count to a slow confidence ramp."""

    return max(0.0, min(1.0, samples / 100))
