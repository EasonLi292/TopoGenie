"""Placeholder reward function for circuit evaluation.

The real project would export the generated circuit to a SPICE netlist and run
PySpice simulations.  For unit tests we simply return ``1.0`` when the Euler
trail is complete and ``0.0`` otherwise.
"""
from __future__ import annotations

from ..core.state import EulerState


def evaluate(state: EulerState) -> float:
    """Return a heuristic reward for ``state``."""
    return 1.0 if state.is_complete() else 0.0


__all__ = ["evaluate"]
