"""Silicon Org learning kernel.

Learning converts task traces into conservative role and relation signals.
Current code writes indices; it does not mutate graph weights automatically.
"""

from .proposals import trace_learning_proposals
from .signals import LearningSignal, relation_signal, role_signal

__all__ = [
    "LearningSignal",
    "relation_signal",
    "role_signal",
    "trace_learning_proposals",
]
