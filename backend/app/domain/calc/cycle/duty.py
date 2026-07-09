"""CYCLE.ED — cyclic duration factor (%ED) and starts/hour derivation.

Reference: docs/DUTY_CYCLE_MODEL.md, sections 3 and 4.5. Accepts exactly one
of the two equivalent duty-regime inputs and derives the rest — this
replaces the original hardcoded 0.1 fraction with an explicit, declared
service regime.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.registry import register_formula

_CYCLE_STANDARD_REFS = ("ISO 4301-1", "FEM 1.001")


@dataclass(frozen=True)
class DutyRegimeInput:
    on_time_s: float
    """t_on = t_a + t_c + t_d, from CYCLE.PROFILE.v1."""
    duty_factor_pct: float | None = None
    starts_per_hour: float | None = None

    def __post_init__(self) -> None:
        if self.on_time_s <= 0:
            raise ValueError("on_time_s must be > 0")
        provided = [self.duty_factor_pct is not None, self.starts_per_hour is not None]
        if sum(provided) != 1:
            raise ValueError(
                "Exactly one of duty_factor_pct or starts_per_hour must be provided"
            )
        if self.duty_factor_pct is not None and not (0 < self.duty_factor_pct <= 100):
            raise ValueError("duty_factor_pct must be in (0, 100]")
        if self.starts_per_hour is not None and self.starts_per_hour <= 0:
            raise ValueError("starts_per_hour must be > 0")


@dataclass(frozen=True)
class DutyRegimeResult:
    on_time_s: float
    off_time_s: float
    cycle_time_s: float
    duty_factor_pct: float
    starts_per_hour: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


@register_formula(
    "CYCLE.ED.v1",
    standard_refs=_CYCLE_STANDARD_REFS,
    description="Derives t_off, cyclic duration factor (%ED), and starts/hour.",
)
def duty_regime(inp: DutyRegimeInput) -> DutyRegimeResult:
    """CYCLE.ED.v1 — Derive t_off / %ED / starts-per-hour.

    From the target %ED: t_off = t_on*(100/%ED - 1).
    From starts/hour: t_cycle = 3600/z_h, t_off = t_cycle - t_on.
    """
    if inp.duty_factor_pct is not None:
        off_time_s = inp.on_time_s * (100.0 / inp.duty_factor_pct - 1.0)
        cycle_time_s = inp.on_time_s + off_time_s
        duty_factor_pct = inp.duty_factor_pct
        starts_per_hour = 3600.0 / cycle_time_s
        source = "duty_factor_pct"
    else:
        assert inp.starts_per_hour is not None
        cycle_time_s = 3600.0 / inp.starts_per_hour
        off_time_s = cycle_time_s - inp.on_time_s
        if off_time_s < 0:
            raise ValueError(
                "starts_per_hour is too high for this movement's on_time_s "
                "(implies negative rest time)"
            )
        duty_factor_pct = (inp.on_time_s / cycle_time_s) * 100.0
        starts_per_hour = inp.starts_per_hour
        source = "starts_per_hour"

    return DutyRegimeResult(
        on_time_s=round(inp.on_time_s, 4),
        off_time_s=round(off_time_s, 4),
        cycle_time_s=round(cycle_time_s, 4),
        duty_factor_pct=round(duty_factor_pct, 2),
        starts_per_hour=round(starts_per_hour, 2),
        formula_id="CYCLE.ED.v1",
        assumptions=(f"t_off derived from {source}",),
        standard_refs=_CYCLE_STANDARD_REFS,
    )
