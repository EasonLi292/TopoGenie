from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
import json

"""
Minimal state-space initializer per the user's pseudocode.
- No inventory rules
- No pin-order constraints
- No next-move constraints
- No connectivity/nets
Just enumerate ALL tokens (device-level and pin-level) plus externals and specials.
"""

# ------------------------------
# Catalogs exactly as listed
# ------------------------------
RANGES: Dict[str, int] = {
    # Devices with indices
    "NM": 34,
    "PM": 34,
    "NPN": 26,
    "PNP": 26,
    "R": 27,
    "C": 15,
    "L": 23,
    "DIO": 7,
    "INVERTER": 10,
    "TRANSMISSION_GATE": 12,
}

# Pin roles per family (where applicable)
PIN_ROLES: Dict[str, Tuple[str, ...]] = {
    "NM": ("D", "G", "S", "B"),
    "PM": ("D", "G", "S", "B"),
    "NPN": ("C", "B", "E"),
    "PNP": ("C", "B", "E"),
    "R": ("P", "N"),
    "C": ("P", "N"),
    "L": ("P", "N"),
    "DIO": ("P", "N"),
    "INVERTER": ("A", "Q", "VDD", "VSS"),
    "TRANSMISSION_GATE": ("A", "B", "C", "VDD", "VSS"),
}

# Singleton macros
SINGLETONS: Dict[str, Tuple[str, ...]] = {
    "XOR1": ("A", "B", "VDD", "VSS", "Y"),
    "PFD1": ("A", "B", "QA", "QB", "VDD", "VSS"),
}

# Externals with ranges
EXTERNALS: Dict[str, int] = {
    "VIN": 10, "IIN": 2, "VOUT": 6, "IOUT": 4,
    "VB": 10, "IB": 6, "VCONT": 20, "VCLK": 8,
    "VCM": 2, "VREF": 2, "IREF": 2, "VRF": 2,
    "VLO": 4, "VIF": 2, "VBB": 4,
    "LOGICA": 2, "LOGICB": 2, "LOGICD": 2, "LOGICF": 2, "LOGICG": 2,
    "LOGICQ": 2, "VLATCH": 2, "VTRACK": 2,
}
SINGLE_EXTERNALS = ("LOGICQA1", "LOGICQB1", "VHOLD1",)

SPECIAL = ("VDD", "VSS", "EoS")


# ------------------------------
# State space container
# ------------------------------
@dataclass
class StateSpace:
    tokens: List[str]
    tok2id: Dict[str, int]
    id2tok: List[str]
    groups: Dict[str, List[str]]  # keys: devices, pins, externals, single_externals, special
    by_family: Dict[str, Dict[str, List[str]]]  # family -> {"devices": [...], "pins": [...]}


# ------------------------------
# Generation
# ------------------------------

def generate_state_space() -> StateSpace:
    tokens: List[str] = []
    groups = {"devices": [], "pins": [], "externals": [], "single_externals": [], "special": []}
    by_family: Dict[str, Dict[str, List[str]]] = {}

    # Families with indices
    for fam, nmax in RANGES.items():
        fam_devices: List[str] = []
        fam_pins: List[str] = []
        roles = PIN_ROLES.get(fam, tuple())
        for i in range(1, nmax + 1):
            dev = f"{fam}{i}"
            tokens.append(dev)
            fam_devices.append(dev)
            groups["devices"].append(dev)
            if roles:
                for r in roles:
                    pin_tok = f"{dev}_{r}"
                    tokens.append(pin_tok)
                    fam_pins.append(pin_tok)
                    groups["pins"].append(pin_tok)
        by_family[fam] = {"devices": fam_devices, "pins": fam_pins}

    # Singletons
    for name, roles in SINGLETONS.items():
        tokens.append(name)
        groups["devices"].append(name)
        pin_list: List[str] = []
        for r in roles:
            pr = f"{name}_{r}"
            tokens.append(pr)
            groups["pins"].append(pr)
            pin_list.append(pr)
        by_family[name] = {"devices": [name], "pins": pin_list}

    # Externals
    for base, count in EXTERNALS.items():
        for i in range(1, count + 1):
            label = f"{base}{i}"
            tokens.append(label)
            groups["externals"].append(label)
    for s in SINGLE_EXTERNALS:
        tokens.append(s)
        groups["single_externals"].append(s)

    # Specials
    for s in SPECIAL:
        tokens.append(s)
        groups["special"].append(s)

    # Build id maps
    # Preserve insertion order; also provide a deterministic sort if needed.
    tok2id = {t: idx for idx, t in enumerate(tokens)}
    id2tok = list(tokens)

    return StateSpace(tokens=tokens, tok2id=tok2id, id2tok=id2tok, groups=groups, by_family=by_family)


# ------------------------------
# Utilities
# ------------------------------

def save_state_space_json(path: str, ss: StateSpace):
    with open(path, "w") as f:
        json.dump({
            "tokens": ss.tokens,
            "tok2id": ss.tok2id,
            "id2tok": ss.id2tok,
            "groups": ss.groups,
            "by_family": ss.by_family,
        }, f, indent=2)


def summary(ss: StateSpace) -> str:
    return (
        f"total_tokens={len(ss.tokens)} | "
        f"devices={len(ss.groups['devices'])} | pins={len(ss.groups['pins'])} | "
        f"externals={len(ss.groups['externals']) + len(ss.groups['single_externals'])} | "
        f"special={len(ss.groups['special'])}"
    )


# ------------------------------
# Demo
# ------------------------------
if __name__ == "__main__":
    ss = generate_state_space()
    print(summary(ss))
    # Example: persist to JSON for your MCTS/Euler pipeline
    # save_state_space_json("state_space.json", ss)
