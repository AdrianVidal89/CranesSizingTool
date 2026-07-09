"""DRIVE sizing — Module 6.1-6.2: motor current as a function of torque.

Reference: docs/formulas/FORMULA_INVENTORY.md, Module 6.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.domain.registry import register_formula

_DRIVE_STANDARD_REFS = ("IEC 60034-1", "IEC 61800")


@dataclass(frozen=True)
class NoLoadCurrentRatioInput:
    rated_current_a: float
    power_factor: float
    """cos(phi)."""
    no_load_current_a: float | None = None
    """I_0, nameplate value if available."""

    def __post_init__(self) -> None:
        if self.rated_current_a <= 0:
            raise ValueError("rated_current_a must be > 0")
        if not 0 < self.power_factor <= 1:
            raise ValueError("power_factor (cos phi) must be in (0, 1]")
        if self.no_load_current_a is not None and self.no_load_current_a < 0:
            raise ValueError("no_load_current_a must be >= 0")


@dataclass(frozen=True)
class NoLoadCurrentRatioResult:
    value: float
    """i_o = I_0 / I_r."""
    source: str
    """"nameplate" or "estimated_sinphi"."""
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "DRIVE.NoLoadRatio.v1",
    standard_refs=_DRIVE_STANDARD_REFS,
    description="No-load (magnetizing) current ratio i_o, from nameplate I_0 or estimated via sin(phi).",
)
def no_load_current_ratio(inp: NoLoadCurrentRatioInput) -> NoLoadCurrentRatioResult:
    """DRIVE.NoLoadRatio.v1 — i_o = I_0/I_r.

    Physics correction (FORMULA_INVENTORY.md 6.1): the magnetizing current is
    the reactive component of the rated current, so the correct estimator is
    sin(phi) = sqrt(1 - cos(phi)^2) — not the non-physical sqrt(1 - cos(phi))
    used by the original code, which mixes dimensions. A nameplate I_0 is
    always preferred when available.
    """
    if inp.no_load_current_a is not None:
        i_o = inp.no_load_current_a / inp.rated_current_a
        source = "nameplate"
        assumptions = ("i_o = I_0 / I_r, from nameplate I_0",)
    else:
        i_o = math.sqrt(1 - inp.power_factor**2)
        source = "estimated_sinphi"
        assumptions = (
            "No nameplate I_0 given: i_o estimated as sin(phi) = "
            "sqrt(1 - cos(phi)^2)",
        )
    return NoLoadCurrentRatioResult(
        value=round(i_o, 4),
        source=source,
        formula_id="DRIVE.NoLoadRatio.v1",
        assumptions=assumptions,
        standard_refs=_DRIVE_STANDARD_REFS,
    )


@dataclass(frozen=True)
class CurrentOfTorqueInput:
    rated_current_a: float
    rated_torque_nm: float
    torque_nm: float
    no_load_ratio: float
    """i_o, from DRIVE.NoLoadRatio.v1."""

    def __post_init__(self) -> None:
        if self.rated_current_a <= 0:
            raise ValueError("rated_current_a must be > 0")
        if self.rated_torque_nm <= 0:
            raise ValueError("rated_torque_nm must be > 0")
        if not 0 <= self.no_load_ratio <= 1:
            raise ValueError("no_load_ratio (i_o) must be in [0, 1]")


@dataclass(frozen=True)
class CurrentOfTorqueResult:
    value_a: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "DRIVE.I_of_T.v1",
    standard_refs=_DRIVE_STANDARD_REFS,
    description="Motor current as a function of torque: quadrature sum of magnetizing and load current.",
)
def current_of_torque(inp: CurrentOfTorqueInput) -> CurrentOfTorqueResult:
    """DRIVE.I_of_T.v1 — I(T) = I_r * sqrt(i_o^2 + (T/T_r)^2 * (1 - i_o^2)).

    Verifies I(0) = I_r*i_o = I_0 and I(T_r) = I_r. torque_nm may be
    negative (a regenerative phase); the ratio is squared, so the current
    magnitude is correctly the same either direction.
    """
    ratio = inp.torque_nm / inp.rated_torque_nm
    i = inp.rated_current_a * math.sqrt(
        inp.no_load_ratio**2 + ratio**2 * (1 - inp.no_load_ratio**2)
    )
    return CurrentOfTorqueResult(
        value_a=round(i, 3),
        formula_id="DRIVE.I_of_T.v1",
        assumptions=(
            "Quadrature sum of a constant magnetizing current and a load "
            "current proportional to torque",
        ),
        standard_refs=_DRIVE_STANDARD_REFS,
    )


@dataclass(frozen=True)
class PhaseCurrentsInput:
    rated_current_a: float
    rated_torque_nm: float
    no_load_ratio: float
    steady_torque_nm: float
    accel_torque_nm: float
    motors_count: int

    def __post_init__(self) -> None:
        if self.motors_count <= 0:
            raise ValueError("motors_count must be > 0")


@dataclass(frozen=True)
class PhaseCurrentsResult:
    steady_current_a: float
    """I_ss, summed across motors_count parallel motors."""
    accel_current_a: float
    """I_acc, summed across motors_count parallel motors."""
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "DRIVE.PhaseCurrents.v1",
    standard_refs=_DRIVE_STANDARD_REFS,
    description="Steady-state and acceleration drive currents, summed across parallel motors.",
)
def phase_currents(inp: PhaseCurrentsInput) -> PhaseCurrentsResult:
    """DRIVE.PhaseCurrents.v1 — I_ss = I(T_ss), I_acc = I(T_acc), times motors_count."""
    i_ss = current_of_torque(
        CurrentOfTorqueInput(
            rated_current_a=inp.rated_current_a,
            rated_torque_nm=inp.rated_torque_nm,
            torque_nm=inp.steady_torque_nm,
            no_load_ratio=inp.no_load_ratio,
        )
    ).value_a
    i_acc = current_of_torque(
        CurrentOfTorqueInput(
            rated_current_a=inp.rated_current_a,
            rated_torque_nm=inp.rated_torque_nm,
            torque_nm=inp.accel_torque_nm,
            no_load_ratio=inp.no_load_ratio,
        )
    ).value_a
    return PhaseCurrentsResult(
        steady_current_a=round(i_ss * inp.motors_count, 3),
        accel_current_a=round(i_acc * inp.motors_count, 3),
        formula_id="DRIVE.PhaseCurrents.v1",
        assumptions=("Parallel motor currents sum linearly across motors_count",),
        standard_refs=_DRIVE_STANDARD_REFS,
    )
