"""Motor sizing policy: engineering margins for motor candidate validation.

These are NOT core physics constants — they are risk/margin criteria applied
on top of the physics (FORMULA_INVENTORY.md Module 5.5). Declared as data
here, injected into the validation formulas as a parameter, so the core
formulas stay margin-agnostic and auditable (CLAUDE.md: "standards live as
data, never as scattered constants").

TODO: the default values below are carried over from the original tool's
documented engineering practice (FORMULA_INVENTORY.md Module 5.5), not
independently re-derived from the primary FEM 1.001 / ISO 4301 clause text.
Cite the specific clause before treating these as normative rather than
"practice carried over from the legacy tool".
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MotorSizingPolicy:
    breakdown_torque_margin: float
    """T_st / margin > T_acc. Original practice: 1.2."""
    min_speed_ratio: float
    """N_c > min_speed_ratio * N_r. Original practice: 0.75."""
    thermal_margin: float
    """T_r > thermal_margin * T_rms. Original practice: 0.9."""
    standard_refs: tuple[str, ...]
    source_note: str


DEFAULT_MOTOR_SIZING_POLICY = MotorSizingPolicy(
    breakdown_torque_margin=1.2,
    min_speed_ratio=0.75,
    thermal_margin=0.9,
    standard_refs=("FEM 1.001", "ISO 4301-1"),
    source_note=(
        "Carried over from the original tool's engineering practice "
        "(FORMULA_INVENTORY.md Module 5.5). TODO: verify against the "
        "primary FEM 1.001 / ISO 4301 clause before treating as normative."
    ),
)
