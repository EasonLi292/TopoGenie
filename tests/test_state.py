"""Tests for the :mod:`topozero.core.state` module."""

from topozero.core.state import State


def test_state_clone() -> None:
    """State.clone should return a new State instance."""
    s = State(data=123)
    clone = s.clone()
    assert isinstance(clone, State)
    assert clone.data == 123
