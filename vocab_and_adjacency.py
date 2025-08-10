# =======================================
# File: topozero/vocab_and_adjacency.py
# =======================================
"""
Defines the AnalogGenie-matching token vocabulary and a minimal adjacency/scaffold
for Euler-trail generation. Families & counts are chosen to mirror your retrain.py:

- 'pmos4': 1..34  (PM1..PM34, pins _D,_G,_S,_B)
- 'nmos4': 1..34  (NM1..NM34, pins _D,_G,_S,_B)
- 'npn'  : 1..26  (NPN1..NPN26, pins _C,_B,_E)
- 'pnp'  : 1..26  (PNP1..PNP26, pins _C,_B,_E)
- 'resistor'      1..27  (R1..R27, pins _P,_N)
- 'capacitor'     1..15  (C1..C15, pins _P,_N)
- 'inductor'      1..23  (L1..L23, pins _P,_N)
- 'diode'         1..7   (DIO1..DIO7, pins _P,_N)
- 'XOR'           1      (XOR1, pins _A,_B,_VDD,_VSS,_Y)
- 'PFD'           1      (PFD1, pins _A,_B,_QA,_QB,_VDD,_VSS)
- 'INVERTER'      1..10  (INVERTER1..10, pins _A,_Q,_VDD,_VSS)
- 'TRANSMISSION_GATE' 1..12 (.., pins _A,_B,_C,_VDD,_VSS)

Special tokens: VDD, VSS, END
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Set, DefaultDict
from collections import defaultdict

SPECIAL_TOKENS = ["VDD", "VSS", "END"]  # END is the termination token for MCTS

def _append_family(devs: List[str], prefix: str, count: int, pins: List[str]) -> None:
    for i in range(1, count + 1):
        base = f"{prefix}{i}"
        devs.append(base)
        for p in pins:
            devs.append(f"{base}_{p}")

def build_tokens() -> Tuple[List[str], Dict[str, int], Dict[int, str]]:
    tokens: List[str] = []

    # MOSFETs
    _append_family(tokens, "PM", 34, ["D", "G", "S", "B"])
    _append_family(tokens, "NM", 34, ["D", "G", "S", "B"])

    # BJTs
    _append_family(tokens, "NPN", 26, ["C", "B", "E"])
    _append_family(tokens, "PNP", 26, ["C", "B", "E"])

    # Passives
    _append_family(tokens, "R", 27, ["P", "N"])
    _append_family(tokens, "C", 15, ["P", "N"])
    _append_family(tokens, "L", 23, ["P", "N"])
    _append_family(tokens, "DIO", 7, ["P", "N"])

    # Logic blocks
    _append_family(tokens, "XOR", 1, ["A", "B", "VDD", "VSS", "Y"])
    _append_family(tokens, "PFD", 1, ["A", "B", "QA", "QB", "VDD", "VSS"])
    _append_family(tokens, "INVERTER", 10, ["A", "Q", "VDD", "VSS"])
    _append_family(tokens, "TRANSMISSION_GATE", 12, ["A", "B", "C", "VDD", "VSS"])

    # Supplies & END
    tokens.extend(SPECIAL_TOKENS)

    stoi = {t: i for i, t in enumerate(tokens)}
    itos = {i: t for t, i in stoi.items()}
    return tokens, stoi, itos

TOKENS, STOI, ITOS = build_tokens()
VOCAB_SIZE = len(TOKENS)

def device_root(pin: str) -> str:
    """Map 'NM3_G' -> 'NM3'; 'R4_P' -> 'R4'; 'VDD' -> 'VDD'."""
    if "_" in pin:
        return pin.split("_", 1)[0]
    return pin

def is_pin_token(tok: str) -> bool:
    return "_" in tok and tok not in ("VDD", "VSS", "END")

def initial_adjacency() -> Dict[str, List[str]]:
    """
    Start with a minimal graph containing only supplies.
    We treat supplies as nodes that can connect to any device pin during generation.
    """
    return {"VDD": [], "VSS": []}

def add_edge(adj: Dict[str, List[str]], a: str, b: str) -> None:
    if a not in adj: adj[a] = []
    if b not in adj: adj[b] = []
    if b not in adj[a]: adj[a].append(b)
    if a not in adj[b]: adj[b].append(a)

def all_candidate_new_pins(used_devices: Set[str]) -> List[str]:
    """
    Return a modest set of candidate pins to attach next.
    To keep branching tame for a demo, we offer first instances of each family
    plus any devices already started (to continue wiring them).
    You can broaden this later.
    """
    candidates: List[str] = []
    # Always allow first few MOSFET pins; expand library as needed.
    for base in ["NM1", "PM1", "R1", "C1", "INVERTER1"]:
        for p in TOKENS:
            if p.startswith(base + "_"):
                candidates.append(p)
    # If any device roots already used, expose their remaining pins
    for root in sorted(used_devices):
        for p in TOKENS:
            if p.startswith(root + "_") and p not in candidates:
                candidates.append(p)
    # Also allow connecting to VDD/VSS directly
    candidates.extend(["VDD", "VSS"])
    # Remove END if present
    return [c for c in candidates if c != "END"]