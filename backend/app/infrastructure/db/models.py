"""SQLAlchemy ORM models.

Ownership chain: User -> Project -> CraneConfiguration -> Movement ->
CalculationRun -> Report. owner_id is denormalized onto CalculationRun and
Report (in addition to the natural FK chain) so every isolation check is a
single equality filter, never a deep join a repository author could forget
(CLAUDE.md: "toda query filtra por propietario, sin excepción").

Sensitive text/JSON fields (project/config/movement names, calculation
input+result snapshots, report PDFs) use the Encrypted* column types from
encrypted_types.py. Password hashes and formula_id lists are not encrypted:
an Argon2 hash isn't reversible plaintext, and formula_ids are calculation
engine metadata, not customer/calculation data.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base
from app.infrastructure.db.encrypted_types import (
    EncryptedBytes,
    EncryptedJSON,
    EncryptedString,
)

_TZ_DATETIME = DateTime(timezone=True)
"""All timestamp columns are timezone-aware (TIMESTAMPTZ): comparisons
against datetime.now(timezone.utc) in application code must never mix
naive and aware datetimes."""


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(_TZ_DATETIME, default=_now)

    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class UserSession(Base):
    """Opaque server-side session for basic cookie auth. Only a hash of the
    session token is stored; the raw token is only ever held by the
    client's HttpOnly cookie (see interfaces/auth.py)."""

    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    csrf_token: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(_TZ_DATETIME, default=_now)
    expires_at: Mapped[datetime] = mapped_column(_TZ_DATETIME, nullable=False)

    user: Mapped["User"] = relationship(back_populates="sessions")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = _uuid_pk()
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    created_at: Mapped[datetime] = mapped_column(_TZ_DATETIME, default=_now)
    updated_at: Mapped[datetime] = mapped_column(_TZ_DATETIME, default=_now, onupdate=_now)

    owner: Mapped["User"] = relationship(back_populates="projects")
    crane_configurations: Mapped[list["CraneConfiguration"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class CraneConfiguration(Base):
    __tablename__ = "crane_configurations"

    id: Mapped[uuid.UUID] = _uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    created_at: Mapped[datetime] = mapped_column(_TZ_DATETIME, default=_now)

    project: Mapped["Project"] = relationship(back_populates="crane_configurations")
    movements: Mapped[list["Movement"]] = relationship(
        back_populates="crane_configuration", cascade="all, delete-orphan"
    )


class Movement(Base):
    __tablename__ = "movements"

    id: Mapped[uuid.UUID] = _uuid_pk()
    crane_configuration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crane_configurations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    """"travel" or "hoist" (see docs/formulas/FORMULA_INVENTORY.md Modules 1-2)."""
    name: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    created_at: Mapped[datetime] = mapped_column(_TZ_DATETIME, default=_now)

    crane_configuration: Mapped["CraneConfiguration"] = relationship(back_populates="movements")
    calculation_runs: Mapped[list["CalculationRun"]] = relationship(
        back_populates="movement", cascade="all, delete-orphan"
    )


class CalculationRun(Base):
    """An immutable, reproducible snapshot: the exact input that was sent
    and the exact result that was computed, plus the formula_ids used. Never
    recomputed from mutable references — a stored run must reproduce
    identically even after the calculation engine evolves (new formula
    versions get new formula_ids, never overwrite these)."""

    __tablename__ = "calculation_runs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    movement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    """Denormalized from movement -> crane_configuration -> project.owner_id
    so isolation checks never require a deep join."""

    input_snapshot: Mapped[dict] = mapped_column(EncryptedJSON, nullable=False)
    result_snapshot: Mapped[dict] = mapped_column(EncryptedJSON, nullable=False)
    formula_ids: Mapped[list] = mapped_column(JSONB, nullable=False)
    """Sorted list of every formula_id present in result_snapshot, for
    at-a-glance auditing without decrypting the full snapshot."""
    created_at: Mapped[datetime] = mapped_column(_TZ_DATETIME, default=_now)

    movement: Mapped["Movement"] = relationship(back_populates="calculation_runs")
    reports: Mapped[list["Report"]] = relationship(
        back_populates="calculation_run", cascade="all, delete-orphan"
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = _uuid_pk()
    calculation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calculation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    """Denormalized from calculation_run.owner_id."""

    pdf_data: Mapped[bytes] = mapped_column(EncryptedBytes, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(_TZ_DATETIME, default=_now)

    calculation_run: Mapped["CalculationRun"] = relationship(back_populates="reports")
