"""Motor candidate — nameplate data proposed by the user for validation.

The system never selects a motor; the user proposes a candidate (nameplate
data) and the system validates it against the calculated requirement
(CLAUDE.md business flow, stage 2: "Validation"). Reference:
docs/formulas/FORMULA_INVENTORY.md, Module 5.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MotorCandidate:
    rated_power_kw: float
    rated_speed_rpm: float
    rated_voltage_v: float
    power_factor: float
    """cos(phi) at rated load."""
    efficiency: float
    nameplate_frequency_hz: float
    """Frequency the nameplate data (power, speed) is characterized at."""

    breakdown_torque_pu: float | None = None
    """Breakdown (stall) torque as a multiple of rated torque. Exactly one
    of breakdown_torque_pu / breakdown_torque_nm must be given — replaces
    the original code's fragile ">=7 => absolute value" heuristic with
    separate typed fields."""
    breakdown_torque_nm: float | None = None

    max_mechanical_torque_pu: float | None = None
    """Maximum mechanical torque as a multiple of rated torque. Exactly one
    of max_mechanical_torque_pu / max_mechanical_torque_nm must be given."""
    max_mechanical_torque_nm: float | None = None

    no_load_current_a: float | None = None
    """I_0, nameplate no-load (magnetizing) current. Optional: when absent,
    it is estimated from power_factor via sin(phi) (see domain/calc/drive/sizing.py)."""

    rotor_inertia_kgm2: float = 0.0

    def __post_init__(self) -> None:
        if self.rated_power_kw <= 0:
            raise ValueError("rated_power_kw must be > 0")
        if self.rated_speed_rpm <= 0:
            raise ValueError("rated_speed_rpm must be > 0")
        if self.rated_voltage_v <= 0:
            raise ValueError("rated_voltage_v must be > 0")
        if not 0 < self.power_factor <= 1:
            raise ValueError("power_factor (cos phi) must be in (0, 1]")
        if not 0 < self.efficiency <= 1:
            raise ValueError("efficiency must be in (0, 1]")
        if self.nameplate_frequency_hz <= 0:
            raise ValueError("nameplate_frequency_hz must be > 0")
        _require_exactly_one(
            "breakdown_torque", self.breakdown_torque_pu, self.breakdown_torque_nm
        )
        _require_exactly_one(
            "max_mechanical_torque",
            self.max_mechanical_torque_pu,
            self.max_mechanical_torque_nm,
        )
        if self.no_load_current_a is not None and self.no_load_current_a < 0:
            raise ValueError("no_load_current_a must be >= 0")
        if self.rotor_inertia_kgm2 < 0:
            raise ValueError("rotor_inertia_kgm2 must be >= 0")


def _require_exactly_one(name: str, pu: float | None, absolute: float | None) -> None:
    provided = (pu is not None, absolute is not None)
    if sum(provided) != 1:
        raise ValueError(f"Exactly one of {name}_pu or {name}_nm must be provided")


def resolve_absolute_torque_nm(
    pu: float | None, absolute_nm: float | None, rated_torque_nm: float
) -> float:
    """Resolve a pu-or-absolute torque field to an absolute N*m value.

    Exactly one of pu/absolute_nm is expected to be set (enforced by
    MotorCandidate.__post_init__ for the fields this is used with).
    """
    if pu is not None:
        return pu * rated_torque_nm
    if absolute_nm is not None:
        return absolute_nm
    raise ValueError("Exactly one of pu or absolute_nm must be provided")
