"""
Tiny entrypoint to run a few MCTS simulations and print a candidate sequence + reward.
"""

from __future__ import annotations
from typing import Optional
from .euler_mcts import EulerState, MCTS
from .vocab_and_adjacency import initial_adjacency

def main(num_simulations: int = 200) -> None:
    # Start at VSS with only supplies in the graph
    st = EulerState(current_pin="VSS", start_pin="VSS", adjacency=initial_adjacency())
    mcts = MCTS(num_simulations=num_simulations, c_puct=1.5)

    root = mcts.run(st)
    # Roll out a single greedy trajectory using best actions
    seq = []
    state = st
    for _ in range(128):
        root = mcts.run(state)  # re-run from current state for a better policy-improvement feel
        action = mcts.best_action(root, temperature=0.0)
        seq.append(action)
        state = state.apply(action)
        if action == "END":
            break

    # Score the final state
    from .netlist_io import score_circuit
    reward = score_circuit(state)

    print("Actions:")
    for i, a in enumerate(seq):
        print(f"{i:02d}: {a}")
    print(f"Reward: {reward:.4f}")

if __name__ == "__main__":
    main()