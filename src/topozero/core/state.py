"""State representation for circuit topologies.

The :class:`State` object captures the current graph of components and
connections during the search process.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class State:
    """A minimal state placeholder."""

    data: Any = None

    def clone(self) -> "State":
        """Return a copy of the state."""
        return State(self.data)
