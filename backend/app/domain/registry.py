"""Central registry of versioned calculation formulas.

Every formula exposed by the calculation engine must be registered here with
its identifier, standard references, and a short description. This is the
single source of truth the report layer queries to attach provenance to a
result (see docs/ARCHITECTURE.md, section 5.3). No calculation is run without
being registered.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)


@dataclass(frozen=True)
class FormulaRecord:
    formula_id: str
    standard_refs: tuple[str, ...]
    description: str


_REGISTRY: dict[str, FormulaRecord] = {}


def register_formula(
    formula_id: str, standard_refs: tuple[str, ...], description: str
) -> Callable[[F], F]:
    """Class/function decorator registering a formula under a versioned id.

    Raises if the same formula_id is registered twice: published versions are
    immutable, a physics change must introduce a new id (vN -> vN+1).
    """
    if formula_id in _REGISTRY:
        raise ValueError(f"formula_id already registered: {formula_id}")

    def decorator(func: F) -> F:
        _REGISTRY[formula_id] = FormulaRecord(
            formula_id=formula_id,
            standard_refs=standard_refs,
            description=description,
        )
        return func

    return decorator


def get_formula_record(formula_id: str) -> FormulaRecord:
    return _REGISTRY[formula_id]


def list_formula_ids() -> tuple[str, ...]:
    return tuple(_REGISTRY.keys())
