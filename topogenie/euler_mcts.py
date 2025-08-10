"""
Core search:
- EulerState: bidirectional unused-edge tracking, adjacency that grows as we add edges,
  and a simple move system: either traverse an unused existing edge, or attach a new pin
  via an ADD edge from the current pin.
- MCTS with PUCT.
- reward() calls netlist_io.score_circuit(seq_edges) to confirm "interesting" circuits
  with PySpice when available.
"""

from __future__ import annotations
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
import math
import random
from .vocab import STOI, ITOS, TOKENS, VOCAB_SIZE, initial_adjacency, add_edge, all_candidate_new_pins

Edge = Tuple[str, str]  # undirected conceptual edge (ordered as (min,max) for hashing)

def _norm_edge(a: str, b: str) -> Edge:
    return (a, b) if a <= b else (b, a)

@dataclass
class EulerState:
    current_pin: str
    start_pin: str = "VSS"
    adjacency: Dict[str, List[str]] = field(default_factory=initial_adjacency)
    visited_edges: Set[Edge] = field(default_factory=set)
    used_device_roots: Set[str] = field(default_factory=set)
    seq: List[str] = field(default_factory=list)  # action history (pins or "ADD:<pin>" or "END")

    def legal_actions(self) -> List[str]:
        """Legal actions: move along an unused edge; or 'ADD:<pin>' to attach a new pin; or 'END'."""
        actions: List[str] = []
        # Move along unused existing edges
        for nb in self.adjacency.get(self.current_pin, []):
            e = _norm_edge(self.current_pin, nb)
            if e not in self.visited_edges:
                actions.append(nb)

        # If not complete, allow adding a new pin (connects via a new edge)
        if not self.is_complete():
            for pin in all_candidate_new_pins(self.used_device_roots):
                actions.append(f"ADD:{pin}")

        # End condition
        if self.is_complete() and self.current_pin == self.start_pin:
            actions.append("END")
        return actions

    def apply(self, action: str) -> "EulerState":
        ns = self.copy()
        if action == "END":
            ns.seq.append("END")
            return ns

        if action.startswith("ADD:"):
            pin = action.split("ADD:", 1)[1]
            add_edge(ns.adjacency, self.current_pin, pin)
            ns.seq.append(action)
            # mark device as used
            from .vocab import device_root
            root = device_root(pin)
            if "_" in pin:
                ns.used_device_roots.add(root)
            return ns

        # otherwise action is moving to an existing neighbor
        nb = action
        e = _norm_edge(self.current_pin, nb)
        ns.visited_edges.add(e)
        ns.seq.append(nb)
        ns.current_pin = nb
        # Track device usage if we land on a device pin
        from .vocab import device_root
        root = device_root(nb)
        if "_" in nb:
            ns.used_device_roots.add(root)
        return ns

    def is_complete(self) -> bool:
        # All edges in adjacency must be visited (undirected count)
        total_edges = 0
        for a, nbs in self.adjacency.items():
            total_edges += len(nbs)
        total_edges //= 2
        return len(self.visited_edges) >= total_edges and total_edges > 0

    def copy(self) -> "EulerState":
        return EulerState(
            current_pin=self.current_pin,
            start_pin=self.start_pin,
            adjacency={k: list(v) for k, v in self.adjacency.items()},
            visited_edges=set(self.visited_edges),
            used_device_roots=set(self.used_device_roots),
            seq=list(self.seq),
        )

    def hash_key(self) -> Tuple[str, Tuple[Edge, ...]]:
        return (self.current_pin, tuple(sorted(self.visited_edges)))

# ---- MCTS (PUCT) ----

@dataclass
class Node:
    state: EulerState
    prior: float = 0.0
    N: int = 0
    W: float = 0.0
    Q: float = 0.0
    children: Dict[str, "Node"] = field(default_factory=dict)

class MCTS:
    def __init__(self, c_puct: float = 1.5, num_simulations: int = 200, policy=None, rng: Optional[random.Random]=None):
        self.c_puct = c_puct
        self.num_simulations = num_simulations
        self.policy = policy  # optional callable: (state, actions)-> priors dict
        self.rng = rng or random.Random(0)
        self.table: Dict[Tuple[str, Tuple[Edge,...]], Node] = {}

    def run(self, root_state: EulerState) -> Node:
        root_key = root_state.hash_key()
        root = self.table.get(root_key)
        if root is None:
            root = Node(state=root_state, prior=1.0)
            self.table[root_key] = root

        for _ in range(self.num_simulations):
            path: List[Tuple[Node, str]] = []
            node = root
            # SELECTION
            while True:
                actions = node.state.legal_actions()
                if not actions:
                    break
                if not node.children:
                    break
                # pick child with max Q + U
                total_N = sum(ch.N for ch in node.children.values()) + 1
                best_a, best_child, best_score = None, None, -1e9
                for a, ch in node.children.items():
                    P = ch.prior if ch.prior is not None else 0.0
                    U = self.c_puct * P * math.sqrt(total_N) / (1 + ch.N)
                    score = ch.Q + U
                    if score > best_score:
                        best_a, best_child, best_score = a, ch, score
                path.append((node, best_a))
                node = best_child
                if node is None:
                    break
                if best_a == "END":
                    break

                # continue until expansion point
                if not node.children:
                    break

            # EXPANSION
            if node.children == {}:
                acts = node.state.legal_actions()
                if acts:
                    priors = self._priors(node.state, acts)
                    for a in acts:
                        next_state = node.state.apply(a)
                        ch = Node(state=next_state, prior=priors.get(a, 1.0 / max(1, len(acts))))
                        node.children[a] = ch
                        path.append((node, a))
                        node = ch
                        break  # expand only one child per sim

            # SIMULATION
            reward = self._rollout(node.state)

            # BACKUP
            # (single-player optimization problem → same reward for path)
            for n, _a in path:
                n.N += 1
                n.W += reward
                n.Q = n.W / n.N

        return root

    def best_action(self, root: Node, temperature: float = 1e-9) -> str:
        # pick child by visit count (or greedy Q if tie)
        if not root.children:
            return "END"
        if temperature <= 1e-8:
            return max(root.children.items(), key=lambda kv: kv[1].N)[0]
        # soft sample by N^1/T
        items = list(root.children.items())
        weights = [pow(ch.N + 1e-6, 1.0 / temperature) for _, ch in items]
        total = sum(weights)
        r = self.rng.random() * total
        acc = 0.0
        for (a, ch), w in zip(items, weights):
            acc += w
            if r <= acc:
                return a
        return items[-1][0]

    def _priors(self, state: EulerState, actions: List[str]) -> Dict[str, float]:
        if self.policy is None:
            # Uniform priors with a small bias to END when legal
            priors = {a: 1.0 for a in actions}
            if "END" in priors:
                priors["END"] = 2.0
            s = sum(priors.values())
            return {k: v / s for k, v in priors.items()}
        return self.policy(state, actions)

    def _rollout(self, state: EulerState, max_steps: int = 64) -> float:
        """Greedy-on-priors rollout until END or cap, then score with PySpice if possible."""
        s = state.copy()
        for _ in range(max_steps):
            acts = s.legal_actions()
            if not acts:
                break
            if "END" in acts and s.is_complete() and s.current_pin == s.start_pin:
                s = s.apply("END")
                break
            # simple heuristic: prefer moving over adding when possible
            move_acts = [a for a in acts if not a.startswith("ADD:") and a != "END"]
            a = move_acts[0] if move_acts else acts[0]
            s = s.apply(a)
        # Reward from SPICE confirmation (or heuristic fallback)
        from .netlist_io import score_circuit
        return score_circuit(s)

