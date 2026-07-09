"""domain/standards/mechanism_groups.py never fabricates a limit (TODO stub)."""

from app.domain.standards.mechanism_groups import check_mechanism_group_limit


def test_no_group_provided_is_not_available():
    result = check_mechanism_group_limit(None, starts_per_hour=40.91)
    assert result.status == "not_available"
    assert result.mechanism_group is None
    assert result.starts_per_hour_limit is None


def test_group_provided_but_dataset_not_populated_is_not_available():
    """Even with a declared group, the limit dataset isn't sourced yet — the
    check must not invent a threshold, per CLAUDE.md."""
    result = check_mechanism_group_limit("M5", starts_per_hour=40.91)
    assert result.status == "not_available"
    assert result.mechanism_group == "M5"
    assert result.starts_per_hour_limit is None
    assert "TODO" in result.note
