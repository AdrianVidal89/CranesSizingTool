"""PDF report generation from an already-persisted CalculationRun.

This module never runs a calculation — it only formats results that have
already been computed and stored (CLAUDE.md: "El generador de PDF no
ejecuta cálculos, sólo formatea resultados ya obtenidos"). No manufacturer
branding, no external services: everything renders locally with reportlab.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.application.dto import CalculationRunDTO

_STYLES = getSampleStyleSheet()
_TITLE_STYLE = _STYLES["Title"]
_HEADING_STYLE = _STYLES["Heading2"]
_SUBHEADING_STYLE = _STYLES["Heading3"]
_BODY_STYLE = _STYLES["BodyText"]
_SMALL_STYLE = ParagraphStyle("Small", parent=_BODY_STYLE, fontSize=8, leading=10)

_TABLE_HEADER_BG = colors.HexColor("#e5e4e7")
_PASS_COLOR = colors.HexColor("#166534")
_FAIL_COLOR = colors.HexColor("#991b1b")


def generate_report_pdf(run: CalculationRunDTO) -> bytes:
    """Render a CalculationRun snapshot to a PDF byte string."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
    )

    result = run.result_snapshot
    inputs = run.input_snapshot
    requirement = result["requirement"]

    story: list = []
    story.extend(_executive_summary(run, result))
    story.extend(_inputs_section(inputs))
    story.extend(_requirement_section(requirement))
    story.extend(_candidate_section(result))
    story.extend(_formula_registry_section(run))

    doc.build(story)
    return buffer.getvalue()


def _executive_summary(run: CalculationRunDTO, result: dict) -> list:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    motor_passed = result["motor_passed"]
    drive_passed = result.get("drive_passed")
    overall_pass = motor_passed and (drive_passed is None or drive_passed)

    verdict_text = "PASS — candidate meets all validated conditions" if overall_pass else (
        "FAIL — candidate does not meet all validated conditions"
    )
    verdict_color = _PASS_COLOR if overall_pass else _FAIL_COLOR

    requirement = result["requirement"]
    return [
        Paragraph("Crane Drive Sizing Report", _TITLE_STYLE),
        Paragraph(f"Generated: {generated_at}", _BODY_STYLE),
        Paragraph(f"Calculation run ID: {run.id}", _SMALL_STYLE),
        Spacer(1, 6 * mm),
        Paragraph("Executive summary", _HEADING_STYLE),
        Paragraph(
            f"Required torque: {requirement['required_torque_nm']} N*m &nbsp;|&nbsp; "
            f"Required speed: {requirement['required_speed_rpm']} rpm &nbsp;|&nbsp; "
            f"Thermal RMS torque: {requirement['rms_torque']['value']} N*m",
            _BODY_STYLE,
        ),
        Paragraph(
            f'<font color="{verdict_color.hexval()}"><b>{verdict_text}</b></font>', _BODY_STYLE
        ),
        Paragraph(
            "This report validates the specific motor/drive candidate the user proposed. "
            "The system does not select or recommend equipment from any catalog.",
            _SMALL_STYLE,
        ),
        Spacer(1, 6 * mm),
    ]


def _kv_table(rows: list[tuple[str, object]]) -> Table:
    data = [["Field", "Value"]] + [[k, "" if v is None else str(v)] for k, v in rows]
    table = Table(data, colWidths=[70 * mm, 90 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _TABLE_HEADER_BG),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def _inputs_section(inputs: dict) -> list:
    story: list = [Paragraph("Inputs", _HEADING_STYLE)]

    mechanics_rows = [
        ("Dead mass (kg)", inputs.get("mass_dead_kg")),
        ("Load mass / SWL (kg)", inputs.get("mass_load_kg")),
        ("Tool / spreader mass (kg)", inputs.get("mass_tool_kg")),
        ("Travel velocity (m/s)", inputs.get("velocity_ms")),
        ("Acceleration ramp time (s)", inputs.get("accel_time_s")),
        ("Wheel diameter (m)", inputs.get("wheel_diameter_m")),
        ("Gear ratio", inputs.get("gear_ratio")),
        ("Mechanical efficiency", inputs.get("efficiency")),
        ("Number of motors", inputs.get("motors_count")),
        ("Rolling resistance coefficient", inputs.get("rolling_coeff")),
    ]
    story.append(Paragraph("Mechanics", _SUBHEADING_STYLE))
    story.append(_kv_table(mechanics_rows))
    story.append(Spacer(1, 3 * mm))

    cycle_rows = [
        ("Distance (m)", inputs.get("distance_m")),
        ("Deceleration ramp time (s)", inputs.get("decel_time_s")),
        ("Target %ED", inputs.get("duty_factor_pct")),
        ("Starts per hour", inputs.get("starts_per_hour")),
        ("Standstill cooling factor k_f", inputs.get("cooling_factor")),
        ("Mechanism group", inputs.get("mechanism_group")),
    ]
    story.append(Paragraph("Duty cycle", _SUBHEADING_STYLE))
    story.append(_kv_table(cycle_rows))
    story.append(Spacer(1, 3 * mm))

    motor = inputs.get("motor", {}) or {}
    motor_rows = [
        ("Rated power (kW)", motor.get("rated_power_kw")),
        ("Rated speed (rpm)", motor.get("rated_speed_rpm")),
        ("Rated voltage (V)", motor.get("rated_voltage_v")),
        ("Power factor cos(phi)", motor.get("power_factor")),
        ("Efficiency", motor.get("efficiency")),
        ("Nameplate frequency (Hz)", motor.get("nameplate_frequency_hz")),
        ("Target mains frequency (Hz)", inputs.get("motor_target_frequency_hz")),
        ("Breakdown torque (pu)", motor.get("breakdown_torque_pu")),
        ("Breakdown torque (N*m)", motor.get("breakdown_torque_nm")),
        ("Max mechanical torque (pu)", motor.get("max_mechanical_torque_pu")),
        ("Max mechanical torque (N*m)", motor.get("max_mechanical_torque_nm")),
        ("No-load current I_0 (A)", motor.get("no_load_current_a")),
    ]
    story.append(Paragraph("Motor candidate (nameplate)", _SUBHEADING_STYLE))
    story.append(_kv_table(motor_rows))
    story.append(Spacer(1, 3 * mm))

    drive = inputs.get("drive")
    if drive:
        drive_rows = [
            ("Rated current (A)", drive.get("rated_current_a")),
            ("Overload factor", drive.get("overload_factor")),
            ("Overload duration (s)", drive.get("overload_duration_s")),
            ("Rated voltage (V)", drive.get("rated_voltage_v")),
        ]
        story.append(Paragraph("Drive candidate", _SUBHEADING_STYLE))
        story.append(_kv_table(drive_rows))
        story.append(Spacer(1, 3 * mm))

    return story


def _formula_result_paragraph(label: str, value_text: str, node: dict) -> list:
    assumptions = "; ".join(node.get("assumptions", []))
    standards = ", ".join(node.get("standard_refs", []))
    return [
        Paragraph(f"<b>{label}:</b> {value_text}", _BODY_STYLE),
        Paragraph(
            f"formula_id: <font face='Courier'>{node.get('formula_id', '')}</font> "
            f"&nbsp;|&nbsp; standard(s): {standards}",
            _SMALL_STYLE,
        ),
        Paragraph(f"Assumptions: {assumptions}", _SMALL_STYLE),
        Spacer(1, 2 * mm),
    ]


def _requirement_section(requirement: dict) -> list:
    story: list = [Paragraph("Requirement (mechanics + duty cycle)", _HEADING_STYLE)]

    story.append(
        Paragraph(
            f"Required torque: {requirement['required_torque_nm']} N*m &nbsp;|&nbsp; "
            f"Required speed: {requirement['required_speed_rpm']} rpm &nbsp;|&nbsp; "
            f"Steady torque: {requirement['steady_torque_nm']} N*m &nbsp;|&nbsp; "
            f"Dynamic torque: {requirement['dynamic_torque_nm']} N*m",
            _BODY_STYLE,
        )
    )
    story.append(Spacer(1, 2 * mm))

    profile = requirement["profile"]
    profile_text = (
        f"{'Triangular' if profile['is_triangular'] else 'Trapezoidal'} profile — "
        f"accel {profile['accel_time_s']} s, const {profile['const_time_s']} s, "
        f"decel {profile['decel_time_s']} s"
    )
    story.extend(_formula_result_paragraph("Motion profile", profile_text, profile))

    regime = requirement["regime"]
    regime_text = f"{regime['duty_factor_pct']}% ED, {regime['starts_per_hour']} starts/hour"
    story.extend(_formula_result_paragraph("Duty regime", regime_text, regime))

    decel = requirement["decel_torque"]
    decel_text = f"{decel['value_nm']} N*m" + (
        " (regenerative)" if decel["is_regenerative"] else ""
    )
    story.extend(_formula_result_paragraph("Deceleration torque", decel_text, decel))

    rms = requirement["rms_torque"]
    story.extend(_formula_result_paragraph("Thermal RMS torque", f"{rms['value']} N*m", rms))

    energy = requirement["energy"]
    energy_text = f"{energy['energy_per_cycle_j']} J/cycle, {energy['energy_per_hour_j']} J/hour"
    if energy["has_regenerative_phase"]:
        energy_text += " (includes a regenerative phase)"
    story.extend(_formula_result_paragraph("Energy consumption", energy_text, energy))

    mech_group = requirement["mechanism_group_check"]
    if mech_group.get("mechanism_group"):
        story.append(
            Paragraph(
                f"Mechanism group {mech_group['mechanism_group']}: {mech_group['note']}",
                _SMALL_STYLE,
            )
        )
        story.append(Spacer(1, 2 * mm))

    story.append(Spacer(1, 4 * mm))
    return story


def _conditions_table(conditions: list[dict]) -> Table:
    header = ["Condition", "Required", "Available", "Margin", "Verdict", "Formula ID", "Standard(s)"]
    rows = [header]
    for c in conditions:
        rows.append(
            [
                c["label"],
                str(c["required_value"]),
                str(c["available_value"]),
                f"{c['margin'] * 100:.1f}%",
                c["verdict"].upper(),
                c["formula_id"],
                ", ".join(c.get("standard_refs", [])),
            ]
        )

    table = Table(
        rows, colWidths=[32 * mm, 18 * mm, 18 * mm, 15 * mm, 15 * mm, 38 * mm, 24 * mm]
    )
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), _TABLE_HEADER_BG),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for i, c in enumerate(conditions, start=1):
        color = _PASS_COLOR if c["verdict"] == "pass" else _FAIL_COLOR
        style.append(("TEXTCOLOR", (4, i), (4, i), color))
    table.setStyle(TableStyle(style))
    return table


def _candidate_section(result: dict) -> list:
    story: list = [Paragraph("Candidate evaluated & validation verdict", _HEADING_STYLE)]

    motor = result["resolved_motor"]
    motor_summary_rows = [
        ("Rated torque (N*m)", motor["rated_torque_nm"]),
        ("Rated speed (rpm)", motor["rated_speed_rpm"]),
        ("Rated current (A)", motor["rated_current_a"]),
        ("Breakdown torque, resolved (N*m)", motor["breakdown_torque_nm"]),
        ("Max mechanical torque, resolved (N*m)", motor["max_mechanical_torque_nm"]),
    ]
    story.append(Paragraph("Motor — resolved nameplate values", _SUBHEADING_STYLE))
    story.append(_kv_table(motor_summary_rows))
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("Motor conditions (Module 5.5)", _SUBHEADING_STYLE))
    story.append(_conditions_table(result["motor_conditions"]))
    story.append(Spacer(1, 4 * mm))

    if result.get("drive_conditions"):
        if result.get("rms_current_a") is not None:
            story.append(Paragraph(f"RMS current: {result['rms_current_a']} A", _BODY_STYLE))
        story.append(Paragraph("Drive conditions (Module 6.4)", _SUBHEADING_STYLE))
        story.append(_conditions_table(result["drive_conditions"]))
        story.append(Spacer(1, 4 * mm))

    return story


def _formula_registry_section(run: CalculationRunDTO) -> list:
    story: list = [Paragraph("Formula versions used (calc_version)", _HEADING_STYLE)]
    formula_ids = ", ".join(run.formula_ids)
    story.append(Paragraph(formula_ids, _SMALL_STYLE))
    story.append(Spacer(1, 4 * mm))
    story.append(
        Paragraph(
            "Every formula_id above is versioned and immutable once published — this report "
            "reproduces bit-for-bit from the stored input, independent of later calculation "
            "engine changes.",
            _SMALL_STYLE,
        )
    )
    return story
