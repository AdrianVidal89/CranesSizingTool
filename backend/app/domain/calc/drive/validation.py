"""DRIVE validation — Module 6.4: 3 conditions comparing a candidate drive
against the calculated requirement.

Overload/continuous conditions use the candidate's own capability data
(DriveCandidate); the thermal condition's margin is injected via
DriveSizingPolicy, never hardcoded.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.calc.condition_result import ConditionResult, relative_margin
from app.domain.registry import register_formula
from app.domain.standards.drive_sizing_policy import DriveSizingPolicy

_DRIVE_VALIDATION_STANDARD_REFS = ("IEC 61800",)


@dataclass(frozen=True)
class OverloadCheckInput:
    accel_current_a: float
    """I_acc."""
    rated_current_a: float
    """I_h, candidate's continuous current rating."""
    overload_factor: float
    """Candidate's own short-duration overload capability."""

    def __post_init__(self) -> None:
        if self.accel_current_a < 0:
            raise ValueError("accel_current_a must be >= 0")
        if self.rated_current_a <= 0:
            raise ValueError("rated_current_a must be > 0")
        if self.overload_factor < 1:
            raise ValueError("overload_factor must be >= 1")


@register_formula(
    "DRIVE.VALIDATE.Overload.v1",
    standard_refs=_DRIVE_VALIDATION_STANDARD_REFS,
    description="Candidate's overload current capacity must exceed the acceleration current.",
)
def check_overload(inp: OverloadCheckInput) -> ConditionResult:
    """DRIVE.VALIDATE.Overload.v1 — I_h * overload_factor > I_acc."""
    available = inp.rated_current_a * inp.overload_factor
    verdict = "pass" if available > inp.accel_current_a else "fail"
    return ConditionResult(
        label="Overload capacity",
        verdict=verdict,
        required_value=round(inp.accel_current_a, 3),
        available_value=round(available, 3),
        margin=round(relative_margin(available, inp.accel_current_a), 4),
        formula_id="DRIVE.VALIDATE.Overload.v1",
        assumptions=(f"I_h * overload_factor({inp.overload_factor}) > I_acc",),
        standard_refs=_DRIVE_VALIDATION_STANDARD_REFS,
    )


@dataclass(frozen=True)
class ContinuousCheckInput:
    steady_current_a: float
    """I_ss."""
    rated_current_a: float
    """I_h."""

    def __post_init__(self) -> None:
        if self.steady_current_a < 0:
            raise ValueError("steady_current_a must be >= 0")
        if self.rated_current_a <= 0:
            raise ValueError("rated_current_a must be > 0")


@register_formula(
    "DRIVE.VALIDATE.Continuous.v1",
    standard_refs=_DRIVE_VALIDATION_STANDARD_REFS,
    description="Candidate's continuous current rating must exceed the steady-state current.",
)
def check_continuous(inp: ContinuousCheckInput) -> ConditionResult:
    """DRIVE.VALIDATE.Continuous.v1 — I_h > I_ss."""
    verdict = "pass" if inp.rated_current_a > inp.steady_current_a else "fail"
    return ConditionResult(
        label="Continuous current",
        verdict=verdict,
        required_value=round(inp.steady_current_a, 3),
        available_value=round(inp.rated_current_a, 3),
        margin=round(relative_margin(inp.rated_current_a, inp.steady_current_a), 4),
        formula_id="DRIVE.VALIDATE.Continuous.v1",
        assumptions=("I_h > I_ss",),
        standard_refs=_DRIVE_VALIDATION_STANDARD_REFS,
    )


@dataclass(frozen=True)
class DriveThermalCheckInput:
    required_rms_current_a: float
    """I_rms."""
    rated_current_a: float
    """I_h."""
    policy: DriveSizingPolicy

    def __post_init__(self) -> None:
        if self.required_rms_current_a < 0:
            raise ValueError("required_rms_current_a must be >= 0")
        if self.rated_current_a <= 0:
            raise ValueError("rated_current_a must be > 0")


@register_formula(
    "DRIVE.VALIDATE.Thermal.v1",
    standard_refs=_DRIVE_VALIDATION_STANDARD_REFS,
    description="Candidate's rated current, derated by the policy margin, must exceed I_rms.",
)
def check_drive_thermal(inp: DriveThermalCheckInput) -> ConditionResult:
    """DRIVE.VALIDATE.Thermal.v1 — I_r,drive > thermal_margin * I_rms."""
    required_effective = inp.policy.thermal_margin * inp.required_rms_current_a
    verdict = "pass" if inp.rated_current_a > required_effective else "fail"
    return ConditionResult(
        label="Thermal RMS current",
        verdict=verdict,
        required_value=round(required_effective, 3),
        available_value=round(inp.rated_current_a, 3),
        margin=round(relative_margin(inp.rated_current_a, required_effective), 4),
        formula_id="DRIVE.VALIDATE.Thermal.v1",
        assumptions=(f"I_r,drive > {inp.policy.thermal_margin} * I_rms",),
        standard_refs=inp.policy.standard_refs,
    )


@dataclass(frozen=True)
class DriveValidationInput:
    accel_current_a: float
    steady_current_a: float
    required_rms_current_a: float
    rated_current_a: float
    overload_factor: float
    policy: DriveSizingPolicy


@dataclass(frozen=True)
class DriveValidationResult:
    conditions: tuple[ConditionResult, ...]
    passed: bool


def validate_drive_candidate(inp: DriveValidationInput) -> DriveValidationResult:
    """Run all 3 Module 6.4 conditions and aggregate a pass/fail verdict.

    Not itself a registered formula — see the 3 check_* functions above.
    """
    conditions = (
        check_overload(
            OverloadCheckInput(
                accel_current_a=inp.accel_current_a,
                rated_current_a=inp.rated_current_a,
                overload_factor=inp.overload_factor,
            )
        ),
        check_continuous(
            ContinuousCheckInput(
                steady_current_a=inp.steady_current_a,
                rated_current_a=inp.rated_current_a,
            )
        ),
        check_drive_thermal(
            DriveThermalCheckInput(
                required_rms_current_a=inp.required_rms_current_a,
                rated_current_a=inp.rated_current_a,
                policy=inp.policy,
            )
        ),
    )
    return DriveValidationResult(
        conditions=conditions, passed=all(c.verdict == "pass" for c in conditions)
    )
