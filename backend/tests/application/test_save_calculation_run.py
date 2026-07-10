"""Unit tests for the extract_formula_ids helper (no DB required)."""

from app.application.save_calculation_run import extract_formula_ids


def test_extracts_and_sorts_nested_formula_ids():
    node = {
        "requirement": {
            "profile": {"formula_id": "CYCLE.PROFILE.v1"},
            "regime": {"formula_id": "CYCLE.ED.v1"},
        },
        "motor_conditions": [
            {"formula_id": "MOTOR.VALIDATE.Speed.v1"},
            {"formula_id": "MOTOR.VALIDATE.MechTorque.v1"},
        ],
        "drive_conditions": None,
    }
    assert extract_formula_ids(node) == [
        "CYCLE.ED.v1",
        "CYCLE.PROFILE.v1",
        "MOTOR.VALIDATE.MechTorque.v1",
        "MOTOR.VALIDATE.Speed.v1",
    ]


def test_deduplicates_repeated_formula_ids():
    node = {"a": {"formula_id": "X.v1"}, "b": {"formula_id": "X.v1"}}
    assert extract_formula_ids(node) == ["X.v1"]


def test_empty_structure_returns_empty_list():
    assert extract_formula_ids({}) == []
    assert extract_formula_ids([]) == []
