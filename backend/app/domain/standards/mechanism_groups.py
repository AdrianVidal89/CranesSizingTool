"""Mechanism group starts/hour and duty limits (ISO 4301-1 / FEM 9.511).

TODO(Phase 3+): this dataset is not populated yet. ISO 4301-1 / FEM 9.511
define per-group (M1-M8) maximum starts/hour and duty-factor limits, but
those numeric thresholds must be sourced from the actual standard text
before being declared here — CLAUDE.md forbids inventing normative values.
Until this dataset exists, `check_mechanism_group_limit` always returns a
"not_available" verdict rather than fabricating a threshold.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MechanismGroupCheckStatus = Literal["ok", "exceeded", "not_available"]


@dataclass(frozen=True)
class MechanismGroupCheckResult:
    status: MechanismGroupCheckStatus
    mechanism_group: str | None
    starts_per_hour_limit: float | None
    note: str


def check_mechanism_group_limit(
    mechanism_group: str | None, starts_per_hour: float
) -> MechanismGroupCheckResult:
    """Compare z_h against the declared mechanism group's starts/hour limit.

    Always returns status="not_available" until the ISO 4301-1 / FEM 9.511
    group-limit dataset is populated (see module TODO). This deliberately
    never guesses a threshold.
    """
    if mechanism_group is None:
        return MechanismGroupCheckResult(
            status="not_available",
            mechanism_group=None,
            starts_per_hour_limit=None,
            note="No mechanism_group was provided; nothing to check.",
        )
    return MechanismGroupCheckResult(
        status="not_available",
        mechanism_group=mechanism_group,
        starts_per_hour_limit=None,
        note=(
            "TODO: ISO 4301-1 / FEM 9.511 starts/hour limits per mechanism group "
            "are not yet populated in domain/standards/. z_h cannot be validated "
            "against a limit until this dataset is sourced from the standard."
        ),
    )
