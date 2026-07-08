"""CYCLE.PROFILE — trapezoidal / triangular motion profile.

Pure, typed functions for the phase timing of one elementary movement
(a travel or a hoisting move of a given distance). Reference:
docs/DUTY_CYCLE_MODEL.md, section 4. Replaces the original hardcoded 0.1
fraction with an explicit model derived from distance, speed, and ramp time.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.domain.registry import register_formula

_CYCLE_STANDARD_REFS = ("ISO 4301-1", "FEM 9.511")


@dataclass(frozen=True)
class MotionProfileInput:
    distance_m: float
    velocity_ms: float
    accel_time_s: float
    decel_time_s: float | None = None
    """Deceleration ramp time; defaults to accel_time_s (symmetric ramps)."""

    def __post_init__(self) -> None:
        if self.distance_m <= 0:
            raise ValueError("distance_m must be > 0")
        if self.velocity_ms <= 0:
            raise ValueError("velocity_ms must be > 0")
        if self.accel_time_s <= 0:
            raise ValueError("accel_time_s must be > 0")
        if self.decel_time_s is not None and self.decel_time_s <= 0:
            raise ValueError("decel_time_s must be > 0")


@dataclass(frozen=True)
class MotionProfileResult:
    accel_time_s: float
    const_time_s: float
    decel_time_s: float
    accel_distance_m: float
    const_distance_m: float
    decel_distance_m: float
    peak_velocity_ms: float
    is_triangular: bool
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "CYCLE.PROFILE.v1",
    standard_refs=_CYCLE_STANDARD_REFS,
    description="Trapezoidal motion profile, auto-degenerating to triangular.",
)
def motion_profile(inp: MotionProfileInput) -> MotionProfileResult:
    """CYCLE.PROFILE.v1 — Phase times/distances for one elementary movement.

    Detects when the travel distance is too short to reach the nominal
    velocity and switches automatically to a triangular profile
    (DUTY_CYCLE_MODEL.md section 4.4): v_peak = sqrt(a*d), t_a = t_d =
    sqrt(d/a), t_c = 0. The acceleration used for this check and for the
    triangular case is a = velocity_ms / accel_time_s (the primary ramp).
    """
    t_a_nominal = inp.accel_time_s
    t_d_nominal = inp.decel_time_s if inp.decel_time_s is not None else inp.accel_time_s

    a = inp.velocity_ms / t_a_nominal
    d_a_nominal = 0.5 * inp.velocity_ms * t_a_nominal
    d_d_nominal = 0.5 * inp.velocity_ms * t_d_nominal

    if inp.distance_m < d_a_nominal + d_d_nominal:
        t_tri = math.sqrt(inp.distance_m / a)
        peak_v = math.sqrt(a * inp.distance_m)
        return MotionProfileResult(
            accel_time_s=round(t_tri, 4),
            const_time_s=0.0,
            decel_time_s=round(t_tri, 4),
            accel_distance_m=round(inp.distance_m / 2, 4),
            const_distance_m=0.0,
            decel_distance_m=round(inp.distance_m / 2, 4),
            peak_velocity_ms=round(peak_v, 4),
            is_triangular=True,
            formula_id="CYCLE.PROFILE.v1",
            assumptions=(
                "Distance too short to reach nominal velocity: degenerated to a "
                "symmetric triangular profile",
                "Acceleration a=velocity_ms/accel_time_s reused for both ramps",
            ),
            standard_refs=_CYCLE_STANDARD_REFS,
        )

    d_c = inp.distance_m - d_a_nominal - d_d_nominal
    t_c = d_c / inp.velocity_ms

    return MotionProfileResult(
        accel_time_s=round(t_a_nominal, 4),
        const_time_s=round(t_c, 4),
        decel_time_s=round(t_d_nominal, 4),
        accel_distance_m=round(d_a_nominal, 4),
        const_distance_m=round(d_c, 4),
        decel_distance_m=round(d_d_nominal, 4),
        peak_velocity_ms=round(inp.velocity_ms, 4),
        is_triangular=False,
        formula_id="CYCLE.PROFILE.v1",
        assumptions=("Trapezoidal profile: acceleration -> constant speed -> deceleration",),
        standard_refs=_CYCLE_STANDARD_REFS,
    )
