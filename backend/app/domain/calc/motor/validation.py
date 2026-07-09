"""MOTOR validation — Module 5.5: 4 conditions comparing a candidate motor
against the calculated requirement.

The system validates a user-proposed candidate; it never selects a motor on
its own (CLAUDE.md business flow, stage 2). Margins are injected via
MotorSizingPolicy, never hardcoded in these formulas.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.calc.condition_result import ConditionResult, relative_margin
from app.domain.registry import register_formula
from app.domain.standards.motor_sizing_policy import MotorSizingPolicy

_MOTOR_MECH_STANDARD_REFS = ("FEM 1.001", "IEC 60034-1")


@dataclass(frozen=True)
class MechTorqueCheckInput:
    required_torque_nm: float
    """T_acc, from the mechanics + duty cycle requirement."""
    max_mechanical_torque_nm: float
    """T_mech,max, resolved from the candidate's pu-or-absolute field."""

    def __post_init__(self) -> None:
        if self.required_torque_nm < 0:
            raise ValueError("required_torque_nm must be >= 0")
        if self.max_mechanical_torque_nm <= 0:
            raise ValueError("max_mechanical_torque_nm must be > 0")


@register_formula(
    "MOTOR.VALIDATE.MechTorque.v1",
    standard_refs=_MOTOR_MECH_STANDARD_REFS,
    description="Candidate's max mechanical torque must exceed the required acceleration torque.",
)
def check_mechanical_torque(inp: MechTorqueCheckInput) -> ConditionResult:
    """MOTOR.VALIDATE.MechTorque.v1 — T_mech,max > T_acc."""
    verdict = "pass" if inp.max_mechanical_torque_nm > inp.required_torque_nm else "fail"
    return ConditionResult(
        label="Mechanical torque",
        verdict=verdict,
        required_value=round(inp.required_torque_nm, 3),
        available_value=round(inp.max_mechanical_torque_nm, 3),
        margin=round(
            relative_margin(inp.max_mechanical_torque_nm, inp.required_torque_nm), 4
        ),
        formula_id="MOTOR.VALIDATE.MechTorque.v1",
        assumptions=("T_mech,max > T_acc",),
        standard_refs=_MOTOR_MECH_STANDARD_REFS,
    )


@dataclass(frozen=True)
class BreakdownTorqueCheckInput:
    required_torque_nm: float
    """T_acc."""
    breakdown_torque_nm: float
    """T_st, resolved from the candidate's pu-or-absolute field."""
    policy: MotorSizingPolicy

    def __post_init__(self) -> None:
        if self.required_torque_nm < 0:
            raise ValueError("required_torque_nm must be >= 0")
        if self.breakdown_torque_nm <= 0:
            raise ValueError("breakdown_torque_nm must be > 0")


@register_formula(
    "MOTOR.VALIDATE.BreakdownTorque.v1",
    standard_refs=_MOTOR_MECH_STANDARD_REFS,
    description="Candidate's breakdown torque, derated by the policy margin, must exceed T_acc.",
)
def check_breakdown_torque(inp: BreakdownTorqueCheckInput) -> ConditionResult:
    """MOTOR.VALIDATE.BreakdownTorque.v1 — T_st / margin > T_acc."""
    effective = inp.breakdown_torque_nm / inp.policy.breakdown_torque_margin
    verdict = "pass" if effective > inp.required_torque_nm else "fail"
    return ConditionResult(
        label="Breakdown torque (with margin)",
        verdict=verdict,
        required_value=round(inp.required_torque_nm, 3),
        available_value=round(effective, 3),
        margin=round(relative_margin(effective, inp.required_torque_nm), 4),
        formula_id="MOTOR.VALIDATE.BreakdownTorque.v1",
        assumptions=(f"T_st / {inp.policy.breakdown_torque_margin} > T_acc",),
        standard_refs=inp.policy.standard_refs,
    )


@dataclass(frozen=True)
class SpeedBandCheckInput:
    required_speed_rpm: float
    """N_c."""
    rated_speed_rpm: float
    """N_r."""
    policy: MotorSizingPolicy

    def __post_init__(self) -> None:
        if self.required_speed_rpm <= 0:
            raise ValueError("required_speed_rpm must be > 0")
        if self.rated_speed_rpm <= 0:
            raise ValueError("rated_speed_rpm must be > 0")


@register_formula(
    "MOTOR.VALIDATE.Speed.v1",
    standard_refs=_MOTOR_MECH_STANDARD_REFS,
    description="Required speed must sit within the candidate's speed band (below rated, above the policy's minimum ratio).",
)
def check_speed_band(inp: SpeedBandCheckInput) -> ConditionResult:
    """MOTOR.VALIDATE.Speed.v1 — N_r > N_c and N_c > min_speed_ratio * N_r."""
    min_speed = inp.policy.min_speed_ratio * inp.rated_speed_rpm
    verdict = (
        "pass"
        if (inp.rated_speed_rpm > inp.required_speed_rpm and inp.required_speed_rpm > min_speed)
        else "fail"
    )
    return ConditionResult(
        label="Speed band",
        verdict=verdict,
        required_value=round(inp.required_speed_rpm, 2),
        available_value=round(inp.rated_speed_rpm, 2),
        margin=round(relative_margin(inp.rated_speed_rpm, inp.required_speed_rpm), 4),
        formula_id="MOTOR.VALIDATE.Speed.v1",
        assumptions=(
            f"N_r > N_c and N_c > {inp.policy.min_speed_ratio} * N_r",
            "margin reflects the upper-bound check only (N_r vs N_c); the "
            "lower-bound check is reflected in the pass/fail verdict",
        ),
        standard_refs=inp.policy.standard_refs,
    )


@dataclass(frozen=True)
class ThermalTorqueCheckInput:
    required_rms_torque_nm: float
    """T_rms."""
    rated_torque_nm: float
    """T_r."""
    policy: MotorSizingPolicy

    def __post_init__(self) -> None:
        if self.required_rms_torque_nm < 0:
            raise ValueError("required_rms_torque_nm must be >= 0")
        if self.rated_torque_nm <= 0:
            raise ValueError("rated_torque_nm must be > 0")


@register_formula(
    "MOTOR.VALIDATE.Thermal.v1",
    standard_refs=_MOTOR_MECH_STANDARD_REFS,
    description="Candidate's rated torque, derated by the policy margin, must exceed T_rms.",
)
def check_thermal_torque(inp: ThermalTorqueCheckInput) -> ConditionResult:
    """MOTOR.VALIDATE.Thermal.v1 — T_r > thermal_margin * T_rms."""
    required_effective = inp.policy.thermal_margin * inp.required_rms_torque_nm
    verdict = "pass" if inp.rated_torque_nm > required_effective else "fail"
    return ConditionResult(
        label="Thermal RMS torque",
        verdict=verdict,
        required_value=round(required_effective, 3),
        available_value=round(inp.rated_torque_nm, 3),
        margin=round(relative_margin(inp.rated_torque_nm, required_effective), 4),
        formula_id="MOTOR.VALIDATE.Thermal.v1",
        assumptions=(f"T_r > {inp.policy.thermal_margin} * T_rms",),
        standard_refs=inp.policy.standard_refs,
    )


@dataclass(frozen=True)
class MotorValidationInput:
    required_torque_nm: float
    required_speed_rpm: float
    required_rms_torque_nm: float
    rated_torque_nm: float
    rated_speed_rpm: float
    max_mechanical_torque_nm: float
    breakdown_torque_nm: float
    policy: MotorSizingPolicy


@dataclass(frozen=True)
class MotorValidationResult:
    conditions: tuple[ConditionResult, ...]
    passed: bool


def validate_motor_candidate(inp: MotorValidationInput) -> MotorValidationResult:
    """Run all 4 Module 5.5 conditions and aggregate a pass/fail verdict.

    Not itself a registered formula (it aggregates 4 distinct formula_ids,
    it isn't a new physical quantity) — see the 4 check_* functions above.
    """
    conditions = (
        check_mechanical_torque(
            MechTorqueCheckInput(
                required_torque_nm=inp.required_torque_nm,
                max_mechanical_torque_nm=inp.max_mechanical_torque_nm,
            )
        ),
        check_breakdown_torque(
            BreakdownTorqueCheckInput(
                required_torque_nm=inp.required_torque_nm,
                breakdown_torque_nm=inp.breakdown_torque_nm,
                policy=inp.policy,
            )
        ),
        check_speed_band(
            SpeedBandCheckInput(
                required_speed_rpm=inp.required_speed_rpm,
                rated_speed_rpm=inp.rated_speed_rpm,
                policy=inp.policy,
            )
        ),
        check_thermal_torque(
            ThermalTorqueCheckInput(
                required_rms_torque_nm=inp.required_rms_torque_nm,
                rated_torque_nm=inp.rated_torque_nm,
                policy=inp.policy,
            )
        ),
    )
    return MotorValidationResult(
        conditions=conditions, passed=all(c.verdict == "pass" for c in conditions)
    )
