"""Declarative base for all ORM models. Kept out of domain/ and
application/ — those layers never import SQLAlchemy directly."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
