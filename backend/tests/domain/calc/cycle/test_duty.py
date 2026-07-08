"""Physics tests for CYCLE.ED.v1 — %ED and starts/hour as equivalent inputs."""

import pytest

from app.domain.calc.cycle.duty import DutyRegimeInput, duty_regime


def test_duty_regime_from_duty_factor_pct():
    """on_time=22s (from the trapezoidal profile test), target %ED=25."""
    result = duty_regime(DutyRegimeInput(on_time_s=22.0, duty_factor_pct=25.0))
    assert result.off_time_s == 66.0
    assert result.cycle_time_s == 88.0
    assert result.duty_factor_pct == 25.0
    assert result.starts_per_hour == 40.91
    assert result.formula_id == "CYCLE.ED.v1"


def test_duty_regime_from_starts_per_hour():
    """Same on_time=22s, but the input is starts/hour instead of %ED."""
    result = duty_regime(DutyRegimeInput(on_time_s=22.0, starts_per_hour=30.0))
    assert result.cycle_time_s == 120.0
    assert result.off_time_s == 98.0
    assert result.duty_factor_pct == 18.33
    assert result.starts_per_hour == 30.0


def test_rejects_both_duty_inputs():
    with pytest.raises(ValueError, match="Exactly one of"):
        DutyRegimeInput(on_time_s=22.0, duty_factor_pct=25.0, starts_per_hour=30.0)


def test_rejects_neither_duty_input():
    with pytest.raises(ValueError, match="Exactly one of"):
        DutyRegimeInput(on_time_s=22.0)


def test_rejects_starts_per_hour_too_high_for_on_time():
    """starts_per_hour=1000 implies cycle_time=3.6s, shorter than on_time=22s."""
    with pytest.raises(ValueError):
        duty_regime(DutyRegimeInput(on_time_s=22.0, starts_per_hour=1000.0))


@pytest.mark.parametrize("duty_factor_pct", [0, -1, 100.1])
def test_rejects_out_of_range_duty_factor_pct(duty_factor_pct):
    with pytest.raises(ValueError):
        DutyRegimeInput(on_time_s=22.0, duty_factor_pct=duty_factor_pct)
