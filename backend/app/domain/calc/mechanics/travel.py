"""MECH.TRAVEL — travel (gantry / trolley) mechanics formulas.

Pure, typed functions for horizontal movements on wheels and rail. Reference:
docs/formulas/FORMULA_INVENTORY.md, Module 1.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.domain.constants import GRAVITY_M_S2
from app.domain.registry import register_formula

_TRAVEL_STANDARD_REFS = ("FEM 9.511", "ISO 4301-1")


@dataclass(frozen=True)
class RollingResistanceInput:
    mass_total_kg: float
    rolling_coeff: float
    gravity: float = GRAVITY_M_S2


@dataclass(frozen=True)
class RollingResistanceResult:
    value_n: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "MECH.TRAVEL.Fr.v1",
    standard_refs=_TRAVEL_STANDARD_REFS,
    description="Rolling resistance force for a travel mechanism (level-1 simplified model).",
)
def rolling_resistance_force(inp: RollingResistanceInput) -> RollingResistanceResult:
    """MECH.TRAVEL.Fr.v1 — Rolling resistance force, F = mu * m * g."""
    fr = inp.rolling_coeff * inp.mass_total_kg * inp.gravity
    return RollingResistanceResult(
        value_n=round(fr, 2),
        formula_id="MECH.TRAVEL.Fr.v1",
        assumptions=(
            "Horizontal track",
            "Simplified rolling resistance F=mu*m*g (level 1; full FEM model with "
            "bearing friction and flange factor is a future level-2 option)",
        ),
        standard_refs=_TRAVEL_STANDARD_REFS,
    )


@dataclass(frozen=True)
class TravelSpeedInput:
    velocity_ms: float
    wheel_diameter_m: float
    gear_ratio: float


@dataclass(frozen=True)
class RequiredSpeedResult:
    value_rpm: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "MECH.TRAVEL.Nc.v1",
    standard_refs=_TRAVEL_STANDARD_REFS,
    description="Required motor shaft speed for a travel mechanism.",
)
def required_motor_speed(inp: TravelSpeedInput) -> RequiredSpeedResult:
    """MECH.TRAVEL.Nc.v1 — Required motor speed from linear travel speed."""
    nc = (inp.velocity_ms / (math.pi * inp.wheel_diameter_m)) * inp.gear_ratio * 60
    return RequiredSpeedResult(
        value_rpm=round(nc, 2),
        formula_id="MECH.TRAVEL.Nc.v1",
        assumptions=("Rigid wheel, no slip",),
        standard_refs=_TRAVEL_STANDARD_REFS,
    )


@dataclass(frozen=True)
class TravelTorqueInput:
    mass_total_kg: float
    wheel_diameter_m: float
    gear_ratio: float
    efficiency: float
    motors_count: int
    rolling_coeff: float
    gravity: float = GRAVITY_M_S2


@dataclass(frozen=True)
class SteadyTorqueResult:
    value_nm: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "MECH.TRAVEL.Tss.v1",
    standard_refs=_TRAVEL_STANDARD_REFS,
    description="Steady-state torque for a travel mechanism, horizontal track.",
)
def steady_state_torque(inp: TravelTorqueInput) -> SteadyTorqueResult:
    """MECH.TRAVEL.Tss.v1 — Steady-state torque, horizontal track."""
    fr = inp.rolling_coeff * inp.mass_total_kg * inp.gravity
    tss = (fr * inp.wheel_diameter_m) / (
        2 * inp.motors_count * inp.gear_ratio * inp.efficiency
    )
    return SteadyTorqueResult(
        value_nm=round(tss, 2),
        formula_id="MECH.TRAVEL.Tss.v1",
        assumptions=("Horizontal track", "Simplified rolling resistance F=mu*m*g"),
        standard_refs=_TRAVEL_STANDARD_REFS,
    )


@dataclass(frozen=True)
class TravelDynamicTorqueInput:
    mass_total_kg: float
    velocity_ms: float
    accel_time_s: float
    wheel_diameter_m: float
    gear_ratio: float
    efficiency: float
    motors_count: int


@dataclass(frozen=True)
class DynamicTorqueResult:
    value_nm: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "MECH.TRAVEL.Tdyn.v1",
    standard_refs=_TRAVEL_STANDARD_REFS,
    description="Dynamic (acceleration) torque for a travel mechanism.",
)
def dynamic_torque(inp: TravelDynamicTorqueInput) -> DynamicTorqueResult:
    """MECH.TRAVEL.Tdyn.v1 — Dynamic torque to accelerate the translated mass.

    Does not include motor/gearbox/wheel rotor inertia (see
    FORMULA_INVENTORY.md 1.4); acceptable for low-inertia travel mechanisms.
    """
    a = inp.velocity_ms / inp.accel_time_s
    tdyn = (inp.mass_total_kg * a * inp.wheel_diameter_m) / (
        2 * inp.motors_count * inp.gear_ratio * inp.efficiency
    )
    return DynamicTorqueResult(
        value_nm=round(tdyn, 2),
        formula_id="MECH.TRAVEL.Tdyn.v1",
        assumptions=(
            "Constant acceleration ramp a=v/t_r",
            "Rotor inertia of motor/gearbox/wheels not included (level 1)",
        ),
        standard_refs=_TRAVEL_STANDARD_REFS,
    )


@dataclass(frozen=True)
class AccelerationTorqueResult:
    value_nm: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "MECH.TRAVEL.Tacc.v1",
    standard_refs=_TRAVEL_STANDARD_REFS,
    description="Total sizing torque during acceleration for a travel mechanism.",
)
def total_acceleration_torque(
    steady: SteadyTorqueResult, dynamic: DynamicTorqueResult
) -> AccelerationTorqueResult:
    """MECH.TRAVEL.Tacc.v1 — Total torque during acceleration = Tss + Tdyn."""
    tacc = steady.value_nm + dynamic.value_nm
    return AccelerationTorqueResult(
        value_nm=round(tacc, 2),
        formula_id="MECH.TRAVEL.Tacc.v1",
        assumptions=("Sizing torque = steady-state + dynamic torque",),
        standard_refs=_TRAVEL_STANDARD_REFS,
    )


@dataclass(frozen=True)
class TravelDecelTorqueInput:
    steady_torque_nm: float
    dynamic_torque_nm: float


@dataclass(frozen=True)
class TravelDecelTorqueResult:
    value_nm: float
    is_regenerative: bool
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "MECH.TRAVEL.Tdec.v1",
    standard_refs=_TRAVEL_STANDARD_REFS,
    description="Deceleration torque for a travel mechanism; negative indicates regenerative braking.",
)
def decel_torque(inp: TravelDecelTorqueInput) -> TravelDecelTorqueResult:
    """MECH.TRAVEL.Tdec.v1 — Deceleration torque = Tdyn - Tss.

    May be negative: this indicates the mechanism returns energy while
    decelerating (regenerative braking), which sizes the braking resistor.
    The sign is preserved — never take abs() (DUTY_CYCLE_MODEL.md section 5).
    """
    tdec = inp.dynamic_torque_nm - inp.steady_torque_nm
    return TravelDecelTorqueResult(
        value_nm=round(tdec, 2),
        is_regenerative=tdec < 0,
        formula_id="MECH.TRAVEL.Tdec.v1",
        assumptions=(
            "Tdec = Tdyn - Tss",
            "Negative value indicates regenerative braking; sign preserved",
        ),
        standard_refs=_TRAVEL_STANDARD_REFS,
    )
