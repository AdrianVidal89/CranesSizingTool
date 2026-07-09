"""Shared result type for candidate validation conditions.

Used by both domain/calc/motor/validation.py and domain/calc/drive/validation.py
so the two stay structurally consistent without merging their sizing
policies (CLAUDE.md: keep motor/drive margins traceable to separate
normative sources). Not itself a registered formula — it's the common
output shape a condition check returns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ConditionVerdict = Literal["pass", "fail"]


@dataclass(frozen=True)
class ConditionResult:
    label: str
    verdict: ConditionVerdict
    required_value: float
    available_value: float
    margin: float
    """(available/required - 1), as a fraction; negative = shortfall."""
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


def relative_margin(available: float, required: float) -> float:
    """(available/required - 1); +inf when required == 0 (any capacity clears it)."""
    if required == 0:
        return float("inf")
    return available / required - 1.0
