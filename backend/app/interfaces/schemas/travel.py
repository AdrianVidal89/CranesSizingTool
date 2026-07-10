"""Pydantic schemas for the travel calculation endpoint."""

from __future__ import annotations

from pydantic import BaseModel

from app.interfaces.schemas.mechanics import MechanicsRequestFieldsSchema


class TravelRequirementRequestSchema(MechanicsRequestFieldsSchema):
    pass


class FormulaOutputSchema(BaseModel):
    label: str
    value: float
    unit: str
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


class TravelRequirementResponseSchema(BaseModel):
    required_torque_nm: float
    required_speed_rpm: float
    steady_torque_nm: float
    dynamic_torque_nm: float
    components: tuple[FormulaOutputSchema, ...]
