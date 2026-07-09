"""CYCLE.Trms / CYCLE.Irms — thermal RMS torque and current.

Reference: docs/DUTY_CYCLE_MODEL.md, section 6.1-6.2. Includes the
standstill cooling factor k_f in the denominator — an explicit improvement
over the original code, which ignored the rest phase entirely.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.domain.registry import register_formula

_CYCLE_STANDARD_REFS = ("ISO 4301-1", "IEC 60034-1")


@dataclass(frozen=True)
class ThermalRmsInput:
    accel_value: float
    """T_acc or I_acc (acceleration-phase torque/current)."""
    steady_value: float
    """T_ss or I_ss (constant-speed-phase torque/current)."""
    decel_value: float
    """T_dec or I_dec; may be negative (regenerative). Squaring in the RMS
    makes the sign irrelevant to the magnitude, so no abs() is used."""
    accel_time_s: float
    const_time_s: float
    decel_time_s: float
    off_time_s: float
    cooling_factor: float
    """k_f in [0, 1]: 1 = full cooling at standstill, <1 = self-ventilated."""

    def __post_init__(self) -> None:
        if not 0 <= self.cooling_factor <= 1:
            raise ValueError("cooling_factor (k_f) must be in [0, 1]")
        if self.accel_time_s < 0 or self.const_time_s < 0 or self.decel_time_s < 0:
            raise ValueError("phase times must be >= 0")
        if self.off_time_s < 0:
            raise ValueError("off_time_s must be >= 0")
        if self.accel_time_s + self.const_time_s + self.decel_time_s <= 0:
            raise ValueError("total on-time must be > 0")


@dataclass(frozen=True)
class ThermalRmsResult:
    value: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


def _phase_weighted_rms(inp: ThermalRmsInput) -> float:
    numerator = (
        inp.accel_value**2 * inp.accel_time_s
        + inp.steady_value**2 * inp.const_time_s
        + inp.decel_value**2 * inp.decel_time_s
    )
    denominator = (
        inp.accel_time_s
        + inp.const_time_s
        + inp.decel_time_s
        + inp.cooling_factor * inp.off_time_s
    )
    return math.sqrt(numerator / denominator)


@register_formula(
    "CYCLE.Trms.v1",
    standard_refs=_CYCLE_STANDARD_REFS,
    description="Thermal-equivalent RMS torque over the duty cycle, with standstill cooling.",
)
def rms_torque(inp: ThermalRmsInput) -> ThermalRmsResult:
    """CYCLE.Trms.v1 — RMS torque for motor thermal sizing."""
    value = _phase_weighted_rms(inp)
    return ThermalRmsResult(
        value=round(value, 4),
        formula_id="CYCLE.Trms.v1",
        assumptions=(
            f"Standstill cooling factor k_f={inp.cooling_factor}",
            "Deceleration torque squared, so its sign (regenerative or not) does "
            "not affect the RMS magnitude",
        ),
        standard_refs=_CYCLE_STANDARD_REFS,
    )


@register_formula(
    "CYCLE.Irms.v1",
    standard_refs=_CYCLE_STANDARD_REFS,
    description="Thermal-equivalent RMS current over the duty cycle, with standstill cooling.",
)
def rms_current(inp: ThermalRmsInput) -> ThermalRmsResult:
    """CYCLE.Irms.v1 — RMS current for drive thermal sizing.

    Takes the per-phase currents as inputs (from the Module 6 motor/drive
    current model, not implemented until Phase 3); this formula is generic
    over any already-computed phase values, torque or current.
    """
    value = _phase_weighted_rms(inp)
    return ThermalRmsResult(
        value=round(value, 4),
        formula_id="CYCLE.Irms.v1",
        assumptions=(f"Standstill cooling factor k_f={inp.cooling_factor}",),
        standard_refs=_CYCLE_STANDARD_REFS,
    )
