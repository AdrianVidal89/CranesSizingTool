"""MOTOR sizing — Module 5.1, 5.2, 5.4: frequency conversion, rated current,
field weakening.

Reference: docs/formulas/FORMULA_INVENTORY.md, Module 5.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.domain.registry import register_formula

_MOTOR_STANDARD_REFS = ("IEC 60034-1",)


@dataclass(frozen=True)
class FrequencyConversionInput:
    rated_power_kw: float
    rated_speed_rpm: float
    nameplate_frequency_hz: float
    target_frequency_hz: float

    def __post_init__(self) -> None:
        if self.rated_power_kw <= 0:
            raise ValueError("rated_power_kw must be > 0")
        if self.rated_speed_rpm <= 0:
            raise ValueError("rated_speed_rpm must be > 0")
        if self.nameplate_frequency_hz <= 0:
            raise ValueError("nameplate_frequency_hz must be > 0")
        if self.target_frequency_hz <= 0:
            raise ValueError("target_frequency_hz must be > 0")


@dataclass(frozen=True)
class FrequencyConversionResult:
    rated_power_kw: float
    rated_speed_rpm: float
    rated_torque_nm: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "MOTOR.FREQ_CONVERT.v1",
    standard_refs=_MOTOR_STANDARD_REFS,
    description="Scales nameplate power/speed to a target mains frequency and derives rated torque.",
)
def convert_frequency(inp: FrequencyConversionInput) -> FrequencyConversionResult:
    """MOTOR.FREQ_CONVERT.v1 — Scale power/speed by frequency ratio; T_r from P_r/N_r.

    When nameplate_frequency_hz == target_frequency_hz the ratio is 1 and
    this reduces to a plain rated-torque calculation with no scaling — this
    formula is always the single entry point for T_r, not just the 50/60 Hz
    case. This is an engineering estimate (constant torque, proportional
    voltage assumed); nameplate data at the target frequency is preferred
    when available.
    """
    ratio = inp.target_frequency_hz / inp.nameplate_frequency_hz
    speed = inp.rated_speed_rpm * ratio
    power = inp.rated_power_kw * ratio
    torque = (power * 1000) / (2 * math.pi * speed / 60)
    return FrequencyConversionResult(
        rated_power_kw=round(power, 4),
        rated_speed_rpm=round(speed, 2),
        rated_torque_nm=round(torque, 3),
        formula_id="MOTOR.FREQ_CONVERT.v1",
        assumptions=(
            "Constant torque, power and speed scale linearly with the "
            "frequency ratio (proportional voltage assumed)",
            "Estimate only when target_frequency_hz != nameplate_frequency_hz; "
            "prefer nameplate data characterized at the target frequency",
        ),
        standard_refs=_MOTOR_STANDARD_REFS,
    )


@dataclass(frozen=True)
class RatedCurrentInput:
    rated_power_kw: float
    rated_voltage_v: float
    efficiency: float
    power_factor: float

    def __post_init__(self) -> None:
        if self.rated_power_kw <= 0:
            raise ValueError("rated_power_kw must be > 0")
        if self.rated_voltage_v <= 0:
            raise ValueError("rated_voltage_v must be > 0")
        if not 0 < self.efficiency <= 1:
            raise ValueError("efficiency must be in (0, 1]")
        if not 0 < self.power_factor <= 1:
            raise ValueError("power_factor (cos phi) must be in (0, 1]")


@dataclass(frozen=True)
class RatedCurrentResult:
    value_a: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "MOTOR.Ir.v1",
    standard_refs=_MOTOR_STANDARD_REFS,
    description="Rated current from three-phase power balance.",
)
def rated_current(inp: RatedCurrentInput) -> RatedCurrentResult:
    """MOTOR.Ir.v1 — I_r = P_r*1000 / (sqrt(3) * V_r * eta * cos(phi))."""
    ir = (inp.rated_power_kw * 1000) / (
        math.sqrt(3) * inp.rated_voltage_v * inp.efficiency * inp.power_factor
    )
    return RatedCurrentResult(
        value_a=round(ir, 3),
        formula_id="MOTOR.Ir.v1",
        assumptions=("Three-phase power balance P = sqrt(3)*V*I*cos(phi)*eta",),
        standard_refs=_MOTOR_STANDARD_REFS,
    )


@dataclass(frozen=True)
class FieldWeakeningInput:
    breakdown_torque_nm: float
    """T_st at rated (base) speed."""
    rated_speed_rpm: float
    operating_speed_rpm: float
    """Must be >= rated_speed_rpm: this formula only covers the constant-power region."""

    def __post_init__(self) -> None:
        if self.breakdown_torque_nm <= 0:
            raise ValueError("breakdown_torque_nm must be > 0")
        if self.rated_speed_rpm <= 0:
            raise ValueError("rated_speed_rpm must be > 0")
        if self.operating_speed_rpm < self.rated_speed_rpm:
            raise ValueError(
                "operating_speed_rpm must be >= rated_speed_rpm "
                "(field weakening only applies above base speed)"
            )


@dataclass(frozen=True)
class FieldWeakeningResult:
    value_nm: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "MOTOR.FIELD_WEAKENING.v1",
    standard_refs=_MOTOR_STANDARD_REFS,
    description="Breakdown torque available above base speed (constant-power region).",
)
def field_weakening_torque(inp: FieldWeakeningInput) -> FieldWeakeningResult:
    """MOTOR.FIELD_WEAKENING.v1 — T_st(N) = T_st * (N_r/N)^2, for N >= N_r.

    Standard approximation for an induction motor above base speed at
    constant voltage: flux falls off and available torque decreases
    approximately with 1/N^2. Not yet wired into MOTOR.VALIDATE.v1 in this
    phase (the speed-band condition already requires N_c < N_r for a pass,
    so the validated cases stay at/below base speed); available standalone
    for above-base-speed analysis.
    """
    value = inp.breakdown_torque_nm * (inp.rated_speed_rpm / inp.operating_speed_rpm) ** 2
    return FieldWeakeningResult(
        value_nm=round(value, 3),
        formula_id="MOTOR.FIELD_WEAKENING.v1",
        assumptions=(
            "Constant-voltage operation above base speed",
            "Breakdown torque decreases approximately with 1/N^2 (induction "
            "motor approximation; actual behavior depends on motor reactance)",
        ),
        standard_refs=_MOTOR_STANDARD_REFS,
    )
