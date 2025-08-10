"""Device pin vocabulary for topology generation.

This module defines the mapping between token strings and integer ids used by
search and learning components.  The vocabulary is intentionally small for the
unit tests but mirrors what a larger system would contain.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Vocabulary:
    """Bidirectional mapping between tokens and integer ids."""

    tokens: List[str]

    def __post_init__(self) -> None:  # Build lookup tables.
        self._token_to_id: Dict[str, int] = {tok: i for i, tok in enumerate(self.tokens)}
        self._id_to_token: Dict[int, str] = {i: tok for tok, i in self._token_to_id.items()}

    def token_to_id(self, token: str) -> int:
        return self._token_to_id[token]

    def id_to_token(self, idx: int) -> str:
        return self._id_to_token[idx]


# A tiny default vocabulary used in tests.  Real systems would enumerate all
# device pins and special tokens.
DEFAULT_TOKENS: List[str] = [
    "NM1_D",
    "NM1_G",
    "NM1_S",
    "PM1_D",
    "PM1_G",
    "PM1_S",
    "R1_P",
    "R1_N",
    "C1_P",
    "C1_N",
    "VDD",
    "VSS",
    # Special token signalling that the Euler trail has covered all edges.
    "END",
]

DEFAULT_VOCAB = Vocabulary(DEFAULT_TOKENS)

__all__ = ["Vocabulary", "DEFAULT_TOKENS", "DEFAULT_VOCAB"]
