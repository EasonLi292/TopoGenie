"""Run Monte Carlo Tree Search to generate analog topologies."""
from __future__ import annotations

from pprint import pprint
import sys
from pathlib import Path

# Ensure the src/ directory is importable when running from a source checkout
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from topozero.core.state import EulerState
from topozero.mcts.puct import PUCT
from topozero.mcts import reward

# A tiny example adjacency graph forming an Eulerian circuit.
ADJACENCY = {
    "NM1_D": ["R1_P", "NM1_S"],
    "R1_P": ["NM1_D", "R1_N"],
    "R1_N": ["R1_P", "NM1_S"],
    "NM1_S": ["R1_N", "NM1_D"],
}


def main() -> None:
    state = EulerState(start_pin="NM1_D", adjacency=ADJACENCY)
    searcher = PUCT(n_simulations=100, seed=0)
    final_state = searcher.search(state)
    pprint(final_state.path)
    print("reward:", reward.evaluate(final_state))


if __name__ == "__main__":
    main()
