"""Action utilities for manipulating :class:`EulerState` objects."""
from __future__ import annotations

from typing import List

from .state import EulerState


def available_actions(state: EulerState) -> List[str]:
    """Return the list of legal actions from ``state``.

    This is a thin wrapper around :meth:`EulerState.legal_actions` so the
    function mirrors the interface used in the placeholder project.
    """

    return state.legal_actions()


__all__ = ["available_actions"]
