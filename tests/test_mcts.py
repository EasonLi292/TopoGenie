"""Tests for the PUCT search implementation."""
from topozero.core.state import EulerState
from topozero.mcts.puct import PUCT
from topozero.mcts import reward

ADJACENCY = {
    "NM1_D": ["R1_P", "NM1_S"],
    "R1_P": ["NM1_D", "R1_N"],
    "R1_N": ["R1_P", "NM1_S"],
    "NM1_S": ["R1_N", "NM1_D"],
}


def test_puct_finds_complete_path() -> None:
    state = EulerState(start_pin="NM1_D", adjacency=ADJACENCY)
    searcher = PUCT(n_simulations=50, seed=0)
    final_state = searcher.search(state)
    assert final_state.is_complete()
    assert final_state.path[0] == "NM1_D"
    assert final_state.path[-1] == "END"
    assert reward.evaluate(final_state) == 1.0
    # start + number_of_edges + END
    assert len(final_state.path) == final_state.total_edges + 2
