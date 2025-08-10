"""Tests for the EulerState class."""
from topozero.core.state import END_TOKEN, EulerState

ADJACENCY = {
    "NM1_D": ["R1_P", "NM1_S"],
    "R1_P": ["NM1_D", "R1_N"],
    "R1_N": ["R1_P", "NM1_S"],
    "NM1_S": ["R1_N", "NM1_D"],
}


def test_state_clone_and_traversal() -> None:
    state = EulerState(start_pin="NM1_D", adjacency=ADJACENCY)
    clone = state.clone()
    clone.apply_action("R1_P")
    # Original state should remain unchanged
    assert state.current_pin == "NM1_D"
    assert set(state.legal_actions()) == {"R1_P", "NM1_S"}

    # Traverse an entire Euler circuit
    state.apply_action("R1_P")
    state.apply_action("R1_N")
    state.apply_action("NM1_S")
    state.apply_action("NM1_D")
    assert state.is_complete()
    assert state.legal_actions() == [END_TOKEN]
