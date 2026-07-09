"""Drive (VFD) candidate — nameplate/capability data proposed by the user.

Overload capability (factor + duration) is drive-specific hardware data; it
varies by manufacturer and product class, so it lives on the candidate, not
as a core constant (FORMULA_INVENTORY.md Module 6.3 flags hardcoding this as
a manufacturer-neutrality risk).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DriveCandidate:
    rated_current_a: float
    """I_h, continuous current rating."""
    overload_factor: float
    """Short-duration overload capability as a multiple of rated_current_a
    (e.g. 1.6 for 160%). Candidate/dataset data, never a core constant."""
    overload_duration_s: float
    """How long the overload can be sustained, informational (not used in
    the Module 6.4 conditions, which only compare instantaneous currents)."""
    rated_voltage_v: float

    def __post_init__(self) -> None:
        if self.rated_current_a <= 0:
            raise ValueError("rated_current_a must be > 0")
        if self.overload_factor < 1:
            raise ValueError("overload_factor must be >= 1")
        if self.overload_duration_s <= 0:
            raise ValueError("overload_duration_s must be > 0")
        if self.rated_voltage_v <= 0:
            raise ValueError("rated_voltage_v must be > 0")
