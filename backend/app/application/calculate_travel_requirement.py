"""Requirement-stage use case: travel torque and speed requirement.

Orchestrates the MECH.TRAVEL domain formulas (app/domain/calc/mechanics/travel.py).
Holds no physics of its own — see CLAUDE.md business flow, stage 1
("Requirement"): computed independently of any candidate motor.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.calc.mechanics.travel import (
    RollingResistanceInput,
    TravelDynamicTorqueInput,
    TravelSpeedInput,
    TravelTorqueInput,
    dynamic_torque,
    required_motor_speed,
    rolling_resistance_force,
    steady_state_torque,
    total_acceleration_torque,
)


@dataclass(frozen=True)
class TravelRequirementRequest:
    mass_dead_kg: float
    mass_load_kg: float
    mass_tool_kg: float
    velocity_ms: float
    accel_time_s: float
    wheel_diameter_m: float
    gear_ratio: float
    efficiency: float
    motors_count: int
    rolling_coeff: float


@dataclass(frozen=True)
class FormulaOutput:
    label: str
    value: float
    unit: str
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@dataclass(frozen=True)
class TravelRequirementResult:
    required_torque_nm: float
    required_speed_rpm: float
    components: tuple[FormulaOutput, ...]


class CalculateTravelRequirement:
    """Compute the torque/speed requirement for a travel movement."""

    def execute(self, request: TravelRequirementRequest) -> TravelRequirementResult:
        mass_total_kg = (
            request.mass_dead_kg + request.mass_load_kg + request.mass_tool_kg
        )

        rolling_resistance = rolling_resistance_force(
            RollingResistanceInput(
                mass_total_kg=mass_total_kg,
                rolling_coeff=request.rolling_coeff,
            )
        )
        speed = required_motor_speed(
            TravelSpeedInput(
                velocity_ms=request.velocity_ms,
                wheel_diameter_m=request.wheel_diameter_m,
                gear_ratio=request.gear_ratio,
            )
        )
        steady = steady_state_torque(
            TravelTorqueInput(
                mass_total_kg=mass_total_kg,
                wheel_diameter_m=request.wheel_diameter_m,
                gear_ratio=request.gear_ratio,
                efficiency=request.efficiency,
                motors_count=request.motors_count,
                rolling_coeff=request.rolling_coeff,
            )
        )
        dynamic = dynamic_torque(
            TravelDynamicTorqueInput(
                mass_total_kg=mass_total_kg,
                velocity_ms=request.velocity_ms,
                accel_time_s=request.accel_time_s,
                wheel_diameter_m=request.wheel_diameter_m,
                gear_ratio=request.gear_ratio,
                efficiency=request.efficiency,
                motors_count=request.motors_count,
            )
        )
        acceleration = total_acceleration_torque(steady, dynamic)

        components = (
            FormulaOutput(
                label="Rolling resistance force",
                value=rolling_resistance.value_n,
                unit="N",
                formula_id=rolling_resistance.formula_id,
                assumptions=rolling_resistance.assumptions,
                standard_refs=rolling_resistance.standard_refs,
            ),
            FormulaOutput(
                label="Required motor speed",
                value=speed.value_rpm,
                unit="rpm",
                formula_id=speed.formula_id,
                assumptions=speed.assumptions,
                standard_refs=speed.standard_refs,
            ),
            FormulaOutput(
                label="Steady-state torque",
                value=steady.value_nm,
                unit="N*m",
                formula_id=steady.formula_id,
                assumptions=steady.assumptions,
                standard_refs=steady.standard_refs,
            ),
            FormulaOutput(
                label="Dynamic torque",
                value=dynamic.value_nm,
                unit="N*m",
                formula_id=dynamic.formula_id,
                assumptions=dynamic.assumptions,
                standard_refs=dynamic.standard_refs,
            ),
            FormulaOutput(
                label="Total acceleration torque",
                value=acceleration.value_nm,
                unit="N*m",
                formula_id=acceleration.formula_id,
                assumptions=acceleration.assumptions,
                standard_refs=acceleration.standard_refs,
            ),
        )

        return TravelRequirementResult(
            required_torque_nm=acceleration.value_nm,
            required_speed_rpm=speed.value_rpm,
            components=components,
        )
