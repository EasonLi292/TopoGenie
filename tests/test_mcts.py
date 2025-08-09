"""Tests for the :mod:`topozero.mcts.puct` module."""

from topozero.core.state import State
from topozero.mcts.puct import PUCT


def test_puct_search_runs() -> None:
    """PUCT.search should run without errors and return ``None`` for now."""
    state = State()
    searcher = PUCT()
    result = searcher.search(state)
    assert result is None
