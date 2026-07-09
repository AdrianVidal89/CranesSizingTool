"""Drive (VFD) sizing policy: engineering margins for drive candidate
validation (FORMULA_INVENTORY.md Module 6.4).

Kept as a separate object from MotorSizingPolicy on purpose — motor and
drive margins are not guaranteed to share a normative source, and merging
them would obscure that (CLAUDE.md guidance for this phase).

TODO: same caveat as motor_sizing_policy.py — the default below is carried
over from the original tool's practice, not independently re-derived from
the primary IEC 61800 clause text.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DriveSizingPolicy:
    thermal_margin: float
    """I_r,drive > thermal_margin * I_rms. Original practice: 0.9 (same
    numeric criterion as the motor's thermal margin, but tracked separately
    since it applies to a different piece of equipment)."""
    standard_refs: tuple[str, ...]
    source_note: str


DEFAULT_DRIVE_SIZING_POLICY = DriveSizingPolicy(
    thermal_margin=0.9,
    standard_refs=("IEC 61800",),
    source_note=(
        "Carried over from the original tool's engineering practice "
        "(FORMULA_INVENTORY.md Module 6.4). TODO: verify against the "
        "primary IEC 61800 clause before treating as normative."
    ),
)
