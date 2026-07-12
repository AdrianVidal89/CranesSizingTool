"""Requirement-stage use case: hoist torque and speed requirement.

Orchestrates the MECH.HOIST domain formulas (app/domain/calc/mechanics/hoist.py).
Holds no physics of its own — see CLAUDE.md business flow, stage 1
("Requirement"): computed independently of any candidate motor.

Both hoisting directions are reported: lifting sizes the motor (friction
works against it), lowering is the brake/regeneration case (friction helps
hold the load) — see FORMULA_INVENTORY.md 2.1.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.calculate_travel_requirement import FormulaOutput
from app.domain.calc.mechanics.hoist import (
    HoistLoadDynamicTorqueInput,
    HoistRotorDynamicTorqueInput,
    HoistSpeedInput,
    HoistStaticTorqueInput,
    load_dynamic_torque,
    required_motor_speed,
    rotor_dynamic_torque,
    static_hoisting_torque,
    total_acceleration_torque,
)


@dataclass(frozen=True)
class HoistRequirementRequest:
    mass_load_kg: float
    mass_tool_kg: float
    velocity_ms: float
    accel_time_s: float
    drum_diameter_m: float
    reeving_factor: float
    gear_ratio: float
    efficiency: float
    motor_inertia_kgm2: float
    brake_inertia_kgm2: float


@dataclass(frozen=True)
class HoistRequirementResult:
    required_torque_nm: float
    required_speed_rpm: float
    static_lifting_torque_nm: float
    static_lowering_torque_nm: float
    rotor_dynamic_torque_nm: float
    load_dynamic_torque_nm: float
    components: tuple[FormulaOutput, ...]


class CalculateHoistRequirement:
    """Compute the torque/speed requirement for a hoist movement."""

    def execute(self, request: HoistRequirementRequest) -> HoistRequirementResult:
        hook_load_mass_kg = request.mass_load_kg + request.mass_tool_kg

        speed = required_motor_speed(
            HoistSpeedInput(
                velocity_ms=request.velocity_ms,
                drum_diameter_m=request.drum_diameter_m,
                reeving_factor=request.reeving_factor,
                gear_ratio=request.gear_ratio,
            )
        )
        static_lifting = static_hoisting_torque(
            HoistStaticTorqueInput(
                hook_load_mass_kg=hook_load_mass_kg,
                drum_diameter_m=request.drum_diameter_m,
                reeving_factor=request.reeving_factor,
                gear_ratio=request.gear_ratio,
                efficiency=request.efficiency,
                direction="lifting",
            )
        )
        static_lowering = static_hoisting_torque(
            HoistStaticTorqueInput(
                hook_load_mass_kg=hook_load_mass_kg,
                drum_diameter_m=request.drum_diameter_m,
                reeving_factor=request.reeving_factor,
                gear_ratio=request.gear_ratio,
                efficiency=request.efficiency,
                direction="lowering",
            )
        )
        rotor_dynamic = rotor_dynamic_torque(
            HoistRotorDynamicTorqueInput(
                motor_inertia_kgm2=request.motor_inertia_kgm2,
                brake_inertia_kgm2=request.brake_inertia_kgm2,
                motor_speed_rpm=speed.value_rpm,
                accel_time_s=request.accel_time_s,
            )
        )
        load_dynamic = load_dynamic_torque(
            HoistLoadDynamicTorqueInput(
                hook_load_mass_kg=hook_load_mass_kg,
                drum_diameter_m=request.drum_diameter_m,
                reeving_factor=request.reeving_factor,
                gear_ratio=request.gear_ratio,
                motor_speed_rpm=speed.value_rpm,
                accel_time_s=request.accel_time_s,
            )
        )
        acceleration = total_acceleration_torque(static_lifting, rotor_dynamic, load_dynamic)

        components = (
            FormulaOutput(
                label="Required motor speed",
                value=speed.value_rpm,
                unit="rpm",
                formula_id=speed.formula_id,
                assumptions=speed.assumptions,
                standard_refs=speed.standard_refs,
            ),
            FormulaOutput(
                label="Static hoisting torque (lifting)",
                value=static_lifting.value_nm,
                unit="N*m",
                formula_id=static_lifting.formula_id,
                assumptions=static_lifting.assumptions,
                standard_refs=static_lifting.standard_refs,
            ),
            FormulaOutput(
                label="Static torque (lowering)",
                value=static_lowering.value_nm,
                unit="N*m",
                formula_id=static_lowering.formula_id,
                assumptions=static_lowering.assumptions,
                standard_refs=static_lowering.standard_refs,
            ),
            FormulaOutput(
                label="Rotor dynamic torque (motor + brake)",
                value=rotor_dynamic.value_nm,
                unit="N*m",
                formula_id=rotor_dynamic.formula_id,
                assumptions=rotor_dynamic.assumptions,
                standard_refs=rotor_dynamic.standard_refs,
            ),
            FormulaOutput(
                label="Load dynamic torque",
                value=load_dynamic.value_nm,
                unit="N*m",
                formula_id=load_dynamic.formula_id,
                assumptions=load_dynamic.assumptions,
                standard_refs=load_dynamic.standard_refs,
            ),
            FormulaOutput(
                label="Total acceleration torque (lifting)",
                value=acceleration.value_nm,
                unit="N*m",
                formula_id=acceleration.formula_id,
                assumptions=acceleration.assumptions,
                standard_refs=acceleration.standard_refs,
            ),
        )

        return HoistRequirementResult(
            required_torque_nm=acceleration.value_nm,
            required_speed_rpm=speed.value_rpm,
            static_lifting_torque_nm=static_lifting.value_nm,
            static_lowering_torque_nm=static_lowering.value_nm,
            rotor_dynamic_torque_nm=rotor_dynamic.value_nm,
            load_dynamic_torque_nm=load_dynamic.value_nm,
            components=components,
        )
