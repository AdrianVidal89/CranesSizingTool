"""PDF content test: the rendered report must actually contain calc_version
(formula_ids) and standard references, not just exist as a valid file."""

import io

from pypdf import PdfReader

from tests.conftest import SAVE_CALCULATION_RUN_PAYLOAD, register_and_login


def _full_pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() for page in reader.pages)


def test_pdf_contains_calc_version_and_standard_refs(make_client):
    client = make_client()
    csrf_token = register_and_login(client, "pdf-content@example.com")

    saved = client.post(
        "/api/calculation-runs",
        json=SAVE_CALCULATION_RUN_PAYLOAD,
        headers={"X-CSRF-Token": csrf_token},
    ).json()

    report = client.post(
        "/api/reports",
        json={"calculation_run_id": saved["id"]},
        headers={"X-CSRF-Token": csrf_token},
    ).json()

    pdf_response = client.get(f"/api/reports/{report['id']}/pdf")
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"

    text = _full_pdf_text(pdf_response.content)

    # calc_version: every formula_id used must appear verbatim.
    for formula_id in saved["formula_ids"]:
        assert formula_id in text, f"{formula_id} missing from PDF"

    # Standard references must be visible, not just embedded as raw data.
    for standard in ("ISO 4301-1", "FEM 9.511", "IEC 60034-1", "IEC 61800"):
        assert standard in text, f"{standard} missing from PDF"

    # Key requirement numbers and the pass/fail verdict must be present.
    assert "10.68" in text  # required torque
    assert "606.3" in text  # required speed
    assert "PASS" in text

    # No manufacturer branding anywhere in the report.
    for manufacturer in ("Schneider", "ABB", "Siemens", "Rockwell", "SEW", "Danfoss"):
        assert manufacturer not in text


def test_pdf_reflects_a_failing_candidate():
    """A candidate that fails validation must show FAIL, not just PASS
    boilerplate — content varies with the actual result, it isn't a
    static template."""
    from app.application.dto import CalculationRunDTO
    from app.application.validate_candidate import ValidateCandidate, ValidateCandidateRequest
    from app.application.calculate_duty_cycle import CalculateDutyCycleRequest
    from app.application.calculate_travel_requirement import TravelRequirementRequest
    from app.application.save_calculation_run import extract_formula_ids
    from app.domain.calc.motor.candidate import MotorCandidate
    from app.infrastructure.reports.pdf_generator import generate_report_pdf
    from app.interfaces.api.calc import validate_candidate_response_from_result
    import uuid
    from datetime import datetime, timezone

    travel = TravelRequirementRequest(
        mass_dead_kg=800.0,
        mass_load_kg=5000.0,
        mass_tool_kg=200.0,
        velocity_ms=0.5,
        accel_time_s=2.0,
        wheel_diameter_m=0.315,
        gear_ratio=20.0,
        efficiency=0.9,
        motors_count=2,
        rolling_coeff=0.016,
    )
    duty_cycle = CalculateDutyCycleRequest(
        travel=travel,
        distance_m=10.0,
        decel_time_s=None,
        duty_factor_pct=25.0,
        starts_per_hour=None,
        cooling_factor=0.5,
        mechanism_group=None,
    )
    # Invented, deliberately undersized breakdown torque -> fails validation.
    motor = MotorCandidate(
        rated_power_kw=2.2,
        rated_speed_rpm=750.0,
        rated_voltage_v=400.0,
        power_factor=0.85,
        efficiency=0.87,
        nameplate_frequency_hz=50.0,
        breakdown_torque_pu=0.4,
        max_mechanical_torque_pu=3.0,
    )
    result = ValidateCandidate().execute(
        ValidateCandidateRequest(
            duty_cycle=duty_cycle, motor=motor, motor_target_frequency_hz=50.0, drive=None
        )
    )
    result_dict = validate_candidate_response_from_result(result).model_dump(mode="json")
    formula_ids = extract_formula_ids(result_dict)

    run = CalculationRunDTO(
        id=uuid.uuid4(),
        movement_id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        input_snapshot={},
        result_snapshot=result_dict,
        formula_ids=formula_ids,
        created_at=datetime.now(timezone.utc),
    )

    pdf_bytes = generate_report_pdf(run)
    text = _full_pdf_text(pdf_bytes)
    assert "FAIL" in text
    assert "MOTOR.VALIDATE.BreakdownTorque.v1" in text
