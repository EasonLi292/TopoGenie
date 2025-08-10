"""Utilities for exporting token sequences to SPICE netlists.

For the purposes of the unit tests this module simply joins the token sequence
into a string representing the netlist.  It acts as a placeholder for a more
complete exporter that would understand component connectivity.
"""
from __future__ import annotations

from typing import Iterable


def tokens_to_netlist(tokens: Iterable[str]) -> str:
    """Convert an iterable of tokens to a mock netlist string."""
    return "\n".join(tokens)


__all__ = ["tokens_to_netlist"]
