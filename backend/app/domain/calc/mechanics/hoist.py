"""MECH.HOIST — hoisting mechanics formulas.

Pure, typed functions for the hoist mechanism. Reference:
docs/formulas/FORMULA_INVENTORY.md, Module 2.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from app.domain.constants import GRAVITY_M_S2
from app.domain.registry import register_formula

_HOIST_STANDARD_REFS = ("FEM 1.001", "ISO 4301-1")

HoistDirection = Literal["lifting", "lowering"]


@dataclass(frozen=True)
class HoistStaticTorqueInput:
    hook_load_mass_kg: float
    drum_diameter_m: float
    reeving_factor: float
    gear_ratio: float
    efficiency: float
    direction: HoistDirection
    gravity: float = GRAVITY_M_S2


@dataclass(frozen=True)
class HoistStaticTorqueResult:
    value_nm: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "MECH.HOIST.Tss.v1",
    standard_refs=_HOIST_STANDARD_REFS,
    description="Static hoisting torque, with direction-dependent efficiency.",
)
def static_hoisting_torque(inp: HoistStaticTorqueInput) -> HoistStaticTorqueResult:
    """MECH.HOIST.Tss.v1 — Static torque to hold/move the hook load.

    Efficiency direction correction (FORMULA_INVENTORY.md 2.1): when lifting,
    the motor must overcome friction (eta in the denominator); when lowering,
    friction helps hold the load (eta in the numerator). The original code
    only modeled lifting.
    """
    radius = inp.drum_diameter_m / 2
    weight = inp.hook_load_mass_kg * inp.gravity
    if inp.direction == "lifting":
        tss = (weight * radius) / (inp.reeving_factor * inp.gear_ratio * inp.efficiency)
    else:
        tss = (weight * radius * inp.efficiency) / (inp.reeving_factor * inp.gear_ratio)
    return HoistStaticTorqueResult(
        value_nm=round(tss, 2),
        formula_id="MECH.HOIST.Tss.v1",
        assumptions=(
            f"Direction: {inp.direction}",
            "Rope tension = hook load weight / reeving factor",
        ),
        standard_refs=_HOIST_STANDARD_REFS,
    )


@dataclass(frozen=True)
class HoistSpeedInput:
    velocity_ms: float
    drum_diameter_m: float
    reeving_factor: float
    gear_ratio: float


@dataclass(frozen=True)
class HoistSpeedResult:
    value_rpm: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "MECH.HOIST.Nc.v1",
    standard_refs=_HOIST_STANDARD_REFS,
    description="Required motor shaft speed for a hoist mechanism.",
)
def required_motor_speed(inp: HoistSpeedInput) -> HoistSpeedResult:
    """MECH.HOIST.Nc.v1 — Required motor speed from hook speed and reeving."""
    nc = (
        (inp.velocity_ms * inp.reeving_factor) / (math.pi * inp.drum_diameter_m)
    ) * inp.gear_ratio * 60
    return HoistSpeedResult(
        value_rpm=round(nc, 2),
        formula_id="MECH.HOIST.Nc.v1",
        assumptions=("Rope does not slip on the drum",),
        standard_refs=_HOIST_STANDARD_REFS,
    )


@dataclass(frozen=True)
class HoistRotorDynamicTorqueInput:
    motor_inertia_kgm2: float
    brake_inertia_kgm2: float
    motor_speed_rpm: float
    accel_time_s: float


@dataclass(frozen=True)
class HoistRotorDynamicTorqueResult:
    value_nm: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "MECH.HOIST.Tdyn_rotor.v1",
    standard_refs=_HOIST_STANDARD_REFS,
    description="Dynamic torque to accelerate the motor+brake rotor inertia.",
)
def rotor_dynamic_torque(
    inp: HoistRotorDynamicTorqueInput,
) -> HoistRotorDynamicTorqueResult:
    """MECH.HOIST.Tdyn_rotor.v1 — Dynamic torque of the motor+brake assembly."""
    omega = inp.motor_speed_rpm * 2 * math.pi / 60
    alpha = omega / inp.accel_time_s
    tdyn = (inp.motor_inertia_kgm2 + inp.brake_inertia_kgm2) * alpha
    return HoistRotorDynamicTorqueResult(
        value_nm=round(tdyn, 4),
        formula_id="MECH.HOIST.Tdyn_rotor.v1",
        assumptions=("Constant angular acceleration alpha=omega/t_r",),
        standard_refs=_HOIST_STANDARD_REFS,
    )


@dataclass(frozen=True)
class HoistLoadDynamicTorqueInput:
    hook_load_mass_kg: float
    drum_diameter_m: float
    reeving_factor: float
    gear_ratio: float
    motor_speed_rpm: float
    accel_time_s: float


@dataclass(frozen=True)
class HoistLoadDynamicTorqueResult:
    value_nm: float
    reflected_inertia_kgm2: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "MECH.HOIST.Tdyn_load.v1",
    standard_refs=_HOIST_STANDARD_REFS,
    description=(
        "Dynamic torque to accelerate the hoisted load, reflected to the motor shaft "
        "(corrected inertia formula)."
    ),
)
def load_dynamic_torque(
    inp: HoistLoadDynamicTorqueInput,
) -> HoistLoadDynamicTorqueResult:
    """MECH.HOIST.Tdyn_load.v1 — Dynamic torque of the hoisted load (corrected).

    Physics correction (FORMULA_INVENTORY.md 2.4): the hoisted load is a
    translating mass, not a spinning cylinder. Its inertia reflected to the
    motor shaft is J = m*(D/2)^2 / (s^2*i^2) — NOT the original
    (1/4)*(1/2)*m*(D/2)^2/i^2, which was missing the reeving factor s^2 and
    used the wrong (solid-cylinder) inertia shape, underestimating the
    dynamic torque by a factor of about 2/s^2.
    """
    radius = inp.drum_diameter_m / 2
    j_load = (inp.hook_load_mass_kg * radius**2) / (
        inp.reeving_factor**2 * inp.gear_ratio**2
    )
    omega = inp.motor_speed_rpm * 2 * math.pi / 60
    alpha = omega / inp.accel_time_s
    tdyn = j_load * alpha
    return HoistLoadDynamicTorqueResult(
        value_nm=round(tdyn, 4),
        reflected_inertia_kgm2=round(j_load, 6),
        formula_id="MECH.HOIST.Tdyn_load.v1",
        assumptions=(
            "Hoisted load modeled as a translating mass reflected to the motor shaft",
            "J = m*(D/2)^2 / (s^2*i^2)",
        ),
        standard_refs=_HOIST_STANDARD_REFS,
    )


@dataclass(frozen=True)
class HoistAccelerationTorqueResult:
    value_nm: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "MECH.HOIST.Tacc.v1",
    standard_refs=_HOIST_STANDARD_REFS,
    description="Total sizing torque during acceleration for a hoist mechanism.",
)
def total_acceleration_torque(
    static: HoistStaticTorqueResult,
    rotor_dynamic: HoistRotorDynamicTorqueResult,
    load_dynamic: HoistLoadDynamicTorqueResult,
) -> HoistAccelerationTorqueResult:
    """MECH.HOIST.Tacc.v1 — Total torque = static + rotor dynamic + load dynamic."""
    tacc = static.value_nm + rotor_dynamic.value_nm + load_dynamic.value_nm
    return HoistAccelerationTorqueResult(
        value_nm=round(tacc, 2),
        formula_id="MECH.HOIST.Tacc.v1",
        assumptions=("Sizing torque = static + rotor dynamic + load dynamic torque",),
        standard_refs=_HOIST_STANDARD_REFS,
    )
