"""State representation for Eulerian traversal of a circuit graph.

The :class:`EulerState` keeps track of the current pin in the traversal,
which edges have already been used, and provides helpers for generating legal
moves.  Edges are considered undirected; once an edge between two pins has been
visited it cannot be traversed again.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

END_TOKEN = "END"


@dataclass
class EulerState:
    """State of an Eulerian trail over a pin-level graph."""

    start_pin: str
    adjacency: Dict[str, List[str]]
    current_pin: str | None = None
    visited_edges: Set[Tuple[str, str]] = field(default_factory=set)
    path: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.current_pin is None:
            self.current_pin = self.start_pin
        if not self.path:
            self.path.append(self.current_pin)
        # Pre-compute the set of all edges in the undirected graph.
        self._all_edges: Set[Tuple[str, str]] = set()
        for a, neighbours in self.adjacency.items():
            for b in neighbours:
                edge = self._canonical_edge(a, b)
                self._all_edges.add(edge)

    # ------------------------------------------------------------------
    @staticmethod
    def _canonical_edge(a: str, b: str) -> Tuple[str, str]:
        """Return a canonical representation for an undirected edge."""
        return (a, b) if a <= b else (b, a)

    # ------------------------------------------------------------------
    def clone(self) -> "EulerState":
        """Return a deep copy of the state."""
        return EulerState(
            start_pin=self.start_pin,
            adjacency=self.adjacency,
            current_pin=self.current_pin,
            visited_edges=set(self.visited_edges),
            path=list(self.path),
        )

    # ------------------------------------------------------------------
    def legal_actions(self) -> List[str]:
        """Return the list of legal next pins or [END_TOKEN]."""
        if self.is_complete():
            return [END_TOKEN]
        actions: List[str] = []
        for nxt in self.adjacency.get(self.current_pin, []):
            edge = self._canonical_edge(self.current_pin, nxt)
            if edge not in self.visited_edges:
                actions.append(nxt)
        return actions

    # ------------------------------------------------------------------
    def apply_action(self, action: str) -> None:
        """Advance the state by taking ``action``.

        Parameters
        ----------
        action:
            Either a neighbour pin to traverse or ``END_TOKEN`` when all edges
            have been visited.
        """
        if action == END_TOKEN:
            # Terminal action: record the token but keep the current pin so
            # :meth:`is_complete` remains ``True`` after applying END.
            self.path.append(END_TOKEN)
            return

        edge = self._canonical_edge(self.current_pin, action)
        if edge in self.visited_edges:
            raise ValueError(f"Edge {edge} has already been visited")
        self.visited_edges.add(edge)
        self.current_pin = action
        self.path.append(action)

    # ------------------------------------------------------------------
    def is_complete(self) -> bool:
        """Return ``True`` if all edges have been visited and we are back at the start."""
        return len(self.visited_edges) == len(self._all_edges) and self.current_pin == self.start_pin

    # ------------------------------------------------------------------
    @property
    def total_edges(self) -> int:
        return len(self._all_edges)


__all__ = ["EulerState", "END_TOKEN"]
