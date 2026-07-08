"""Duty-cycle use case: phase profile, %ED/starts-per-hour, thermal RMS, and
energy for a travel movement.

Orchestrates the Phase 1 mechanics use case (CalculateTravelRequirement) with
the CYCLE.* domain formulas (app/domain/calc/cycle/). Holds no physics of its
own — see docs/DUTY_CYCLE_MODEL.md section 10 for how these pieces fit
together.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.application.calculate_travel_requirement import (
    CalculateTravelRequirement,
    TravelRequirementRequest,
)
from app.domain.calc.cycle.duty import DutyRegimeInput, DutyRegimeResult, duty_regime
from app.domain.calc.cycle.energy import (
    EnergyCycleInput,
    EnergyCycleResult,
    energy_per_cycle,
)
from app.domain.calc.cycle.profile import (
    MotionProfileInput,
    MotionProfileResult,
    motion_profile,
)
from app.domain.calc.cycle.thermal import ThermalRmsInput, ThermalRmsResult, rms_torque
from app.domain.calc.mechanics.travel import (
    TravelDecelTorqueInput,
    TravelDecelTorqueResult,
    decel_torque,
)
from app.domain.standards.mechanism_groups import (
    MechanismGroupCheckResult,
    check_mechanism_group_limit,
)


@dataclass(frozen=True)
class CalculateDutyCycleRequest:
    travel: TravelRequirementRequest
    distance_m: float
    decel_time_s: float | None
    duty_factor_pct: float | None
    starts_per_hour: float | None
    cooling_factor: float
    mechanism_group: str | None


@dataclass(frozen=True)
class DutyCycleCalculationResult:
    required_torque_nm: float
    required_speed_rpm: float
    steady_torque_nm: float
    dynamic_torque_nm: float
    profile: MotionProfileResult
    regime: DutyRegimeResult
    decel_torque: TravelDecelTorqueResult
    rms_torque: ThermalRmsResult
    energy: EnergyCycleResult
    mechanism_group_check: MechanismGroupCheckResult


class CalculateDutyCycle:
    """Compute the duty-cycle profile, service regime, thermal RMS torque,
    and energy for a travel movement, given its mechanics requirement."""

    def execute(self, request: CalculateDutyCycleRequest) -> DutyCycleCalculationResult:
        mechanics = CalculateTravelRequirement().execute(request.travel)

        profile = motion_profile(
            MotionProfileInput(
                distance_m=request.distance_m,
                velocity_ms=request.travel.velocity_ms,
                accel_time_s=request.travel.accel_time_s,
                decel_time_s=request.decel_time_s,
            )
        )

        on_time_s = profile.accel_time_s + profile.const_time_s + profile.decel_time_s
        regime = duty_regime(
            DutyRegimeInput(
                on_time_s=on_time_s,
                duty_factor_pct=request.duty_factor_pct,
                starts_per_hour=request.starts_per_hour,
            )
        )

        decel = decel_torque(
            TravelDecelTorqueInput(
                steady_torque_nm=mechanics.steady_torque_nm,
                dynamic_torque_nm=mechanics.dynamic_torque_nm,
            )
        )

        trms = rms_torque(
            ThermalRmsInput(
                accel_value=mechanics.required_torque_nm,
                steady_value=mechanics.steady_torque_nm,
                decel_value=decel.value_nm,
                accel_time_s=profile.accel_time_s,
                const_time_s=profile.const_time_s,
                decel_time_s=profile.decel_time_s,
                off_time_s=regime.off_time_s,
                cooling_factor=request.cooling_factor,
            )
        )

        nominal_omega = mechanics.required_speed_rpm * 2 * math.pi / 60
        energy = energy_per_cycle(
            EnergyCycleInput(
                accel_torque_nm=mechanics.required_torque_nm,
                accel_time_s=profile.accel_time_s,
                steady_torque_nm=mechanics.steady_torque_nm,
                const_time_s=profile.const_time_s,
                decel_torque_nm=decel.value_nm,
                decel_time_s=profile.decel_time_s,
                nominal_angular_velocity_rad_s=nominal_omega,
                efficiency=request.travel.efficiency,
                starts_per_hour=regime.starts_per_hour,
            )
        )

        group_check = check_mechanism_group_limit(
            request.mechanism_group, regime.starts_per_hour
        )

        return DutyCycleCalculationResult(
            required_torque_nm=mechanics.required_torque_nm,
            required_speed_rpm=mechanics.required_speed_rpm,
            steady_torque_nm=mechanics.steady_torque_nm,
            dynamic_torque_nm=mechanics.dynamic_torque_nm,
            profile=profile,
            regime=regime,
            decel_torque=decel,
            rms_torque=trms,
            energy=energy,
            mechanism_group_check=group_check,
        )
