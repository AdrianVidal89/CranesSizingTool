# Cranes Sizing Platform — Architecture and Engineering Context

> **Role of this document.** This is the **root context** of the project. Claude Code must read it at the start of every session and treat its rules as non-negotiable. If a task conflicts with these rules, the rule wins — never convenience. Section 1 is written so it can be copied verbatim into `CLAUDE.md`.

---

## 0. What this platform is

A professional engineering application to **size and validate industrial crane drive systems**, independent of any manufacturer. It covers: motor sizing, VFD sizing, duty cycle calculations, mechanical loads, electrical calculations, start/stop analysis, thermal analysis, energy consumption estimation, report and technical documentation generation, and traceable calculation records.

The **calculation engine is the central asset** of the platform. Everything else (API, persistence, frontend, reports) exists to serve it with guarantees of privacy, security, and traceability.

---

## 1. Non-negotiable guardrails (for `CLAUDE.md`)

These rules translate the project principles into **concrete code decisions**. They are not aspirations; they are acceptance criteria.

### 1.1 Master decision rule
When several valid technical solutions exist, always choose the one that maximizes, **in this exact order**:
**1) Privacy · 2) Manufacturer neutrality · 3) Security · 4) Simplicity · 5) Maintainability · 6) Low operating cost.**
This order overrides any other implementation preference.

### 1.2 Privacy first
- No telemetry by default. No fingerprinting. No advertising. No third-party trackers.
- Do not collect personal information that is not strictly necessary.
- Project data and calculations **never** leave to external services except with **explicit** user approval, per operation.
- Analytics (if ever needed): self-hosted only, disabled by default, aggregated technical metrics only.

### 1.3 Manufacturer neutrality
- The core depends **exclusively** on generic engineering parameters (rated power, rated current, voltage, service factor, torque curve, efficiency, inertia, protection rating…).
- It is forbidden to design around, optimize for, or depend on any specific manufacturer (Schneider, ABB, Siemens, Rockwell, SEW, Danfoss, Beckhoff, Konecranes, Demag, …).
- Manufacturer catalogs are **optional importable datasets** that live outside the calculation domain and **never** influence the core architecture.

### 1.4 AI (for future features)
- Allowed: report drafting, documentation help, knowledge search, natural language interaction.
- Forbidden: sending calculation or customer data to external AI providers by default; using customer reports for training; letting AI modify calculations or make engineering decisions autonomously.
- Prefer self-hosted models over cloud models whenever economically viable. Every AI feature is optional and privacy-preserving.

### 1.5 Calculation engine
Every calculation must be **deterministic, transparent, auditable, reproducible, and versioned**. No hidden calculations are allowed. Every result is traceable back to its formula, version, assumptions, and standard.

### 1.6 Security by default
HTTPS everywhere. Secure cookies. CSRF and XSS protection. Rate limiting. Strict input validation. Passwords with Argon2 (bcrypt acceptable). Never store passwords in plain text. Never log secrets or tokens.

### 1.7 Logging policy
Logs **never** contain: customer names, documents, drawings, reports, calculation data, credentials, or tokens. Only: technical diagnostics, error traces, and system health.

### 1.8 Data
Data minimization. Encryption of sensitive information (accounts, customer data, project data, reports). Strict isolation: each user accesses only their own authorized content. Explicit retention and easy export. No profiling or shadow collection.

### 1.9 Standards
FEM, ISO, IEC, EN, CMAA, and future standards must be **abstracted** away from business logic. Never embed standard-derived constants scattered through the code.

---

## 2. Stack and deployment profile

| Layer | Technology |
|---|---|
| Backend | Python + FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Frontend | React + TypeScript |
| Packaging | Docker + Docker Compose |
| Reverse proxy | Nginx |
| Background jobs | Celery or RQ **only if strictly necessary** |

**Target profile:** 2 vCPU · 4 GB RAM · Linux. The application must run fast and reliably on cheap hosting. Avoid unnecessary infrastructure complexity: **modular monolith**, not microservices (unless there is a clear, demonstrated business need).

---

## 3. Architecture: modular monolith + DDD + Clean Architecture

Four layers, with **dependencies always pointing toward the domain** (the domain knows nothing about FastAPI, SQLAlchemy, PDF, or React):

```
┌─────────────────────────────────────────────────────────┐
│  Interfaces (FastAPI routers, Pydantic schemas, auth)    │  ← HTTP, input validation
├─────────────────────────────────────────────────────────┤
│  Application (use cases, orchestration, DTOs)            │  ← "create project", "run calculation", "generate report"
├─────────────────────────────────────────────────────────┤
│  Domain (calculation engine, entities, standards) ★CORE★ │  ← pure physics, no external dependencies
├─────────────────────────────────────────────────────────┤
│  Infrastructure (PostgreSQL/SQLAlchemy, PDF, files)      │  ← implements ports defined by the domain
└─────────────────────────────────────────────────────────┘
```

**Golden rule:** the `domain/` package imports nothing from the upper layers or from infrastructure. It is pure Python (dataclasses/pydantic-core, numpy if needed). This is what guarantees the calculation is testable, deterministic, and portable.

---

## 4. Folder structure (initial proposal)

```
crane-sizing/
├── docker-compose.yml
├── CLAUDE.md                      # section 1 of this document
├── docs/
│   ├── ARCHITECTURE.md            # this document
│   ├── DUTY_CYCLE_MODEL.md        # duty cycle model
│   └── formulas/                  # formula inventory (one sheet per formula)
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── domain/                # ★ CORE — no external dependencies
│   │   │   ├── calc/
│   │   │   │   ├── mechanics/     # travel, hoisting, incline
│   │   │   │   ├── motor/         # motor sizing and validation
│   │   │   │   ├── drive/         # VFD sizing and validation
│   │   │   │   ├── cycle/         # duty cycle and RMS (see DUTY_CYCLE_MODEL.md)
│   │   │   │   ├── thermal/       # thermal analysis
│   │   │   │   └── energy/        # energy consumption
│   │   │   ├── standards/         # abstraction of FEM/ISO/IEC/EN/CMAA
│   │   │   ├── models/            # domain entities (Project, Movement, Result…)
│   │   │   └── registry.py        # registry of versioned formulas
│   │   ├── application/           # use cases / services
│   │   ├── infrastructure/        # persistence, PDF, storage
│   │   ├── interfaces/            # FastAPI routers, schemas, auth
│   │   └── config.py
│   └── tests/                     # domain tests = source of truth for the physics
├── frontend/                      # React + TypeScript
└── nginx/
```

---

## 5. The calculation engine as first-class data

This is the part that makes the platform unique. Every calculation is treated as a **versioned, auditable artifact**, not a loose function.

### 5.1 Pure, typed formulas
Every formula is a **pure function**: it receives a typed input object, returns a typed output object, **with no global state, no side effects, no `print`**. (The original code used massive `global` variables; that is now forbidden.)

```python
# domain/calc/mechanics/travel.py
from dataclasses import dataclass

@dataclass(frozen=True)
class TravelTorqueInput:
    mass_total_kg: float
    wheel_diameter_m: float
    gear_ratio: float
    efficiency: float
    motors_count: int
    rolling_coeff: float
    gravity: float = 9.80665

@dataclass(frozen=True)
class SteadyTorqueResult:
    value_nm: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]

def steady_state_torque(inp: TravelTorqueInput) -> SteadyTorqueResult:
    """MECH.TRAVEL.Tss — Steady-state torque, horizontal track."""
    fr = inp.rolling_coeff * inp.mass_total_kg * inp.gravity
    tss = (fr * inp.wheel_diameter_m) / (
        2 * inp.motors_count * inp.gear_ratio * inp.efficiency
    )
    return SteadyTorqueResult(
        value_nm=round(tss, 2),
        formula_id="MECH.TRAVEL.Tss.v1",
        assumptions=("Horizontal track", "Simplified rolling resistance F=μ·m·g"),
        standard_refs=("FEM 9.511", "ISO 4301-1"),
    )
```

### 5.2 Calculation identifier and version
Every formula carries a hierarchical id and version: `DOMAIN.SUBSYSTEM.QUANTITY.vN`
(e.g. `MECH.HOIST.Tdyn.v1`, `DRIVE.Irms.v1`). A change in the physics ⇒ new version (`v2`); a published version is **never** modified. This way an old report can always be reproduced bit for bit.

### 5.3 Formula registry (`registry.py`)
A central registry maps `formula_id → {function, formula reference, standard, changelog}`. The report queries the registry to attach provenance to every result. No calculation runs without being registered.

### 5.4 Standards abstraction
Standards live in `domain/standards/` as data (service factors, margins, mechanism groups), not as scattered `if` statements. A formula receives the *sizing policy* (the set of factors derived from the selected standard) as an input. Switching from FEM to CMAA = switching the policy dataset, not the formula code.

### 5.5 Determinism and reproducibility
- Physical constants declared in a single place (`g = 9.80665`), never scattered literals.
- No randomness, no clock dependency inside a calculation (timestamps are added at the report layer).
- All rounding is explicit and part of the formula specification.
- Domain tests are the **source of truth for the physics**: every formula has cases with a documented expected result (ideally against a worked example from a standard or textbook).

### 5.6 Corrections already identified (incorporate from v1)
From the previous formula inventory, incorporate these corrections from the start:
- **Load inertia in the hoist:** `J = m·(D/2)² / (s²·i²)` (the original underestimated the dynamic torque).
- **No-load current:** `i₀ ≈ sinφ = √(1−cos²φ)`, or better, nameplate input `I₀` (the original used `√(1−cosφ)`, which is not physical).
- **Efficiency depending on travel direction** in hoisting (lifting: η in the denominator; lowering: η in the numerator).
- **Sign of the incline force** preserved (distinguishes motoring from regenerative operation).
- **Criterion constants** (margins 1.2 / 0.75 / 0.9, drive overloads 1.6 / 1.5, cycle fraction 0.1) externalized as sizing policy / equipment dataset.

---

## 6. Data model and privacy

- **Minimization:** store only what is needed to reproduce a calculation and issue its report.
- **Isolation per user/organization:** every query filters by owner; no exception.
- **Encryption at rest** for project data, customer data, and reports.
- **Explicit retention and export:** the user can export and delete their data easily.
- Core entities: `User`, `Project`, `CraneConfiguration`, `Movement` (gantry/trolley/hoist), `CalculationRun` (with `calc_version`, inputs, assumptions, timestamp), `Report`.
- `CalculationRun` stores the complete input snapshot + formula version ⇒ reproducibility guaranteed even as the engine evolves.

---

## 7. Security by default (implementation checklist)

- FastAPI behind Nginx with mandatory TLS; HSTS.
- Authentication with Argon2 hashing; sessions/tokens with `Secure`, `HttpOnly`, `SameSite` cookies.
- CSRF on stateful operations; security headers (CSP, X-Content-Type-Options…).
- Rate limiting on auth and calculation endpoints.
- Input validation at the edge (Pydantic) **and** domain invariants in the core.
- Secrets via environment variables / secret manager; never in the repo or in logs.

---

## 8. Report generation

Professional, printable reports, exportable to PDF, traceable and auditable. Every report includes: executive summary, inputs, assumptions, calculation results, equipment recommendations, **formula references** and **standard references**, calculation version, and generation timestamp. PDF generation lives in `infrastructure/`, consuming results already calculated by the domain (the domain does not know what a PDF is).

---

## 9. Build order (phases)

Build from the inside out, so the central asset is solid before dressing it up:

1. **Skeleton + engine domain.** Folder structure, `registry.py`, physical constants, and the **mechanics** formulas (travel, hoisting, incline) as typed pure functions, **with the corrections already applied** and their physics tests. No DB or API yet.
2. **Duty cycle and RMS.** Implement `domain/calc/cycle/` per `DUTY_CYCLE_MODEL.md` (trapezoidal profile, %ED, starts/hour), which feeds thermal and energy.
3. **Motor and drive.** Sizing and validation (Modules 5 and 6 of the inventory), consuming outputs from mechanics and cycle.
4. **Thermal and energy.** On top of the cycle: thermal RMS with duty factor, and consumption estimation with regeneration.
5. **Persistence.** PostgreSQL + SQLAlchemy, entities, `CalculationRun` with reproducible snapshot, per-user isolation and encryption.
6. **API.** FastAPI: use cases, secure auth, validation, rate limiting.
7. **Reports.** Traceable PDF in `infrastructure/`.
8. **Frontend.** React + TypeScript.
9. **Packaging and deployment.** Docker Compose + Nginx, tuned to the 2 vCPU / 4 GB profile.

Each phase delivers something testable and does not break the guarantees of the previous ones.

---

## 10. Definition of Done (for every change)

Quality priority, in order: **1) Privacy · 2) Security · 3) Correctness · 4) Maintainability · 5) Simplicity · 6) Performance · 7) Feature richness.**

A change is "done" when:
- It introduces no telemetry, tracking, or data leaks to third parties.
- It embeds no manufacturer dependency in the core.
- If it touches calculation: the formula is registered, versioned, has a test with a documented expected result, and exposes assumptions + standard references.
- It meets the security defaults and the logging policy.
- It is the simplest option that satisfies the above.

---

*Never sacrifice privacy for convenience. Never sacrifice correctness for development speed.*
