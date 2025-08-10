"""Minimal PUCT-based Monte Carlo Tree Search implementation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import math
import random

from ..core.state import END_TOKEN, EulerState
from ..core.actions import available_actions
from . import reward as reward_module


@dataclass
class Node:
    state: EulerState
    parent: Optional[Node] = None
    prior: float = 1.0
    children: Dict[str, Node] = field(default_factory=dict)
    visit_count: int = 0
    total_value: float = 0.0

    # ------------------------------------------------------------------
    def is_expanded(self) -> bool:
        return bool(self.children)

    # ------------------------------------------------------------------
    def q_value(self) -> float:
        if self.visit_count == 0:
            return 0.0
        return self.total_value / self.visit_count

    # ------------------------------------------------------------------
    def expand(self) -> None:
        actions = available_actions(self.state)
        if not actions:
            return
        prob = 1.0 / len(actions)
        for action in actions:
            next_state = self.state.clone()
            next_state.apply_action(action)
            self.children[action] = Node(state=next_state, parent=self, prior=prob)

    # ------------------------------------------------------------------
    def select_child(self, c_puct: float) -> Node:
        """Select a child with maximum PUCT value."""
        best_score = -float("inf")
        best_action = None
        for action, child in self.children.items():
            u = c_puct * child.prior * math.sqrt(self.visit_count) / (1 + child.visit_count)
            q = child.q_value()
            score = q + u
            if score > best_score or (score == best_score and (best_action is None or action < best_action)):
                best_score = score
                best_action = action
        return self.children[best_action]

    # ------------------------------------------------------------------
    def best_child(self) -> Node:
        return max(self.children.values(), key=lambda n: n.visit_count)


class PUCT:
    """PUCT searcher with simple rollouts and reward function."""

    def __init__(self, c_puct: float = 1.0, n_simulations: int = 50, seed: int | None = 0):
        self.c_puct = c_puct
        self.n_simulations = n_simulations
        self.rng = random.Random(seed)

    # ------------------------------------------------------------------
    def _rollout(self, state: EulerState) -> float:
        """Run a random rollout until ``END_TOKEN`` and return reward."""
        sim_state = state.clone()
        while True:
            actions = available_actions(sim_state)
            if not actions:
                break
            action = self.rng.choice(actions)
            sim_state.apply_action(action)
            if action == END_TOKEN:
                break
        return reward_module.evaluate(sim_state)

    # ------------------------------------------------------------------
    def search(self, root_state: EulerState) -> EulerState:
        root = Node(state=root_state.clone())

        for _ in range(self.n_simulations):
            node = root
            # Selection
            while node.is_expanded() and node.state.legal_actions() and not node.state.is_complete():
                node = node.select_child(self.c_puct)
            # Expansion
            if not node.state.is_complete():
                node.expand()
                if node.children:
                    node = node.select_child(self.c_puct)
            # Simulation
            value = self._rollout(node.state)
            # Backup
            while node is not None:
                node.visit_count += 1
                node.total_value += value
                node = node.parent

        # Choose the most visited child to produce final sequence
        if not root.children:
            return root.state
        node = root.best_child()
        while not node.state.is_complete():
            if not node.children:
                node.expand()
            if not node.children:
                break
            node = node.best_child()
        # Append END if needed
        if END_TOKEN not in node.state.path:
            if node.state.is_complete():
                node.state.apply_action(END_TOKEN)
        return node.state

__all__ = ["PUCT"]
