"""CYCLE.ENERGY — energy consumption per cycle / per hour.

Reference: docs/DUTY_CYCLE_MODEL.md, section 6.4. Efficiency is applied in
the denominator for motoring phases and in the numerator for regenerative
phases (same criterion as hoisting direction). Each phase's energy keeps its
sign, so summing phases nets out recovered regenerative energy automatically
— no abs() anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.registry import register_formula

_CYCLE_STANDARD_REFS = ("ISO 4301-1",)


@dataclass(frozen=True)
class EnergyCycleInput:
    accel_torque_nm: float
    accel_time_s: float
    steady_torque_nm: float
    const_time_s: float
    decel_torque_nm: float
    """May be negative: indicates a regenerative deceleration phase."""
    decel_time_s: float
    nominal_angular_velocity_rad_s: float
    """omega = 2*pi*N_c/60, from the mechanics requirement stage."""
    efficiency: float
    starts_per_hour: float

    def __post_init__(self) -> None:
        if self.efficiency <= 0:
            raise ValueError("efficiency must be > 0")
        if self.nominal_angular_velocity_rad_s <= 0:
            raise ValueError("nominal_angular_velocity_rad_s must be > 0")
        if self.starts_per_hour <= 0:
            raise ValueError("starts_per_hour must be > 0")
        if self.accel_time_s < 0 or self.const_time_s < 0 or self.decel_time_s < 0:
            raise ValueError("phase times must be >= 0")


@dataclass(frozen=True)
class PhaseEnergy:
    label: str
    energy_j: float
    is_regenerative: bool


@dataclass(frozen=True)
class EnergyCycleResult:
    energy_per_cycle_j: float
    energy_per_hour_j: float
    phases: tuple[PhaseEnergy, ...]
    has_regenerative_phase: bool
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


def _phase_electrical_power_w(torque_nm: float, omega_rad_s: float, efficiency: float) -> float:
    mechanical_power_w = torque_nm * omega_rad_s
    if torque_nm >= 0:
        return mechanical_power_w / efficiency
    return mechanical_power_w * efficiency


@register_formula(
    "CYCLE.ENERGY.v1",
    standard_refs=_CYCLE_STANDARD_REFS,
    description="Net energy per cycle/hour, preserving sign for regenerative phases.",
)
def energy_per_cycle(inp: EnergyCycleInput) -> EnergyCycleResult:
    """CYCLE.ENERGY.v1 — Net energy per cycle/hour, motoring and regenerative.

    Ramp phases (accel/decel) use half the nominal angular velocity as their
    average (linear velocity ramp assumption); the constant-speed phase uses
    the nominal angular velocity. Efficiency is applied in the denominator
    for motoring phases (torque >= 0) and in the numerator for regenerative
    phases (torque < 0). Each phase's signed energy is summed directly (no
    abs()): the net cycle energy already accounts for recovered regenerative
    energy, matching DUTY_CYCLE_MODEL.md section 6.4.
    """
    ramp_omega = inp.nominal_angular_velocity_rad_s / 2

    accel_power = _phase_electrical_power_w(inp.accel_torque_nm, ramp_omega, inp.efficiency)
    steady_power = _phase_electrical_power_w(
        inp.steady_torque_nm, inp.nominal_angular_velocity_rad_s, inp.efficiency
    )
    decel_power = _phase_electrical_power_w(inp.decel_torque_nm, ramp_omega, inp.efficiency)

    phases = (
        PhaseEnergy(
            "Acceleration",
            round(accel_power * inp.accel_time_s, 2),
            inp.accel_torque_nm < 0,
        ),
        PhaseEnergy(
            "Constant speed",
            round(steady_power * inp.const_time_s, 2),
            inp.steady_torque_nm < 0,
        ),
        PhaseEnergy(
            "Deceleration",
            round(decel_power * inp.decel_time_s, 2),
            inp.decel_torque_nm < 0,
        ),
    )
    energy_per_cycle_j = sum(p.energy_j for p in phases)
    energy_per_hour_j = energy_per_cycle_j * inp.starts_per_hour

    return EnergyCycleResult(
        energy_per_cycle_j=round(energy_per_cycle_j, 2),
        energy_per_hour_j=round(energy_per_hour_j, 2),
        phases=phases,
        has_regenerative_phase=any(p.is_regenerative for p in phases),
        formula_id="CYCLE.ENERGY.v1",
        assumptions=(
            "Ramp phases use half the nominal angular velocity as their average",
            "Efficiency applied in the denominator when motoring (T>=0), in the "
            "numerator when regenerative (T<0)",
            "Rest phase (t_off) contributes no energy",
        ),
        standard_refs=_CYCLE_STANDARD_REFS,
    )
