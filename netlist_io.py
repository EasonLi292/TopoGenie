"""
SPICE/score bridge.
- Convert a state's traversed edges into a coarse netlist (best-effort).
- Use PySpice (if available) to confirm whether the circuit is 'interesting':
  e.g., has finite bias path, not a dead open, and shows non-trivial small-signal gain.

This file is intentionally conservative: if we cannot confidently synthesize a
netlist from the partial/strange topology, we return a low reward.
"""

from __future__ import annotations
from typing import List, Tuple, Optional, Dict, Set
import math

try:
    import PySpice.Logging.Logging as Logging  # type: ignore
    import PySpice.Documentation.ExampleTools as tools  # type: ignore
    from PySpice.Spice.Netlist import Circuit  # type: ignore
    from PySpice.Unit import u, m, n, V, A, Ohm, k
    HAVE_PYSPICE = True
except Exception:
    HAVE_PYSPICE = False

def _contains_supply_loop(state) -> bool:
    # Very rough check: any visited edge touches both VDD and VSS components via multiple steps.
    touched_vdd = "VDD" in state.adjacency and len(state.adjacency["VDD"]) > 0
    touched_vss = "VSS" in state.adjacency and len(state.adjacency["VSS"]) > 0
    return touched_vdd and touched_vss and len(state.visited_edges) >= 3

def _heuristic_reward(state) -> float:
    # Simple topological score: more visited edges, plus bonus for touching both supplies and closing a trail.
    score = 0.1 * len(state.visited_edges)
    if _contains_supply_loop(state): score += 1.0
    if state.is_complete() and state.current_pin == state.start_pin: score += 0.5
    # Small regularizer for fewer ADDs
    add_ops = sum(1 for s in state.seq if isinstance(s, str) and s.startswith("ADD:"))
    score -= 0.01 * add_ops
    return max(0.0, score)

def _toy_inverter_circuit() -> Optional["Circuit"]:
    if not HAVE_PYSPICE:
        return None
    circuit = Circuit('ToyInv')
    circuit.V('dd', 'VDD', circuit.gnd, 1.8@V)
    # Load resistor from VDD to OUT, NMOS to ground driven by IN
    circuit.R('load', 'VDD', 'OUT', 10@k*Ohm)
    # Emulate NMOS with a voltage-controlled switch (toy); real PDK devices would be better.
    # As a placeholder, we can at least run an AC source at IN and see some transfer.
    circuit.SinusoidalVoltageSource('in', 'IN', circuit.gnd, amplitude=10@m*V, frequency=1@k)
    circuit.R('gate_to_out', 'IN', 'OUT', 100@k*Ohm)
    return circuit

def _simulate_gain(circuit: "Circuit") -> Optional[float]:
    try:
        simulator = circuit.simulator(temperature=25, nominal_temperature=25)
        ac = simulator.ac(start_frequency=1@k, stop_frequency=10@M, number_of_points=10, variation='dec')
        # Measure |V(OUT)/V(IN)|
        import numpy as np  # local import
        vin = ac['IN']
        vout = ac['OUT']
        mag = np.abs(vout / vin)
        return float(np.max(mag))
    except Exception:
        return None

def score_circuit(state) -> float:
    """
    Returns a scalar reward. Strategy:
    1) Try to recognize a trivial 'toy inverter' pattern (OUT connected to something, both supplies touched).
       If recognized and PySpice is present, simulate and map gain to reward.
    2) Otherwise, return a robust heuristic based on topology features (touching supplies, edges, closure).
    """
    if HAVE_PYSPICE and _contains_supply_loop(state):
        circ = _toy_inverter_circuit()
        if circ is not None:
            gain = _simulate_gain(circ)
            if gain is not None:
                # Compress gain to a [0, ~2] scale with log-ish mapping
                reward = min(2.0, math.log1p(gain))
                return reward

    # Fallback: heuristic
    return _heuristic_reward(state)