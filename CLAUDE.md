# CLAUDE.md

You are building an **engineering platform to size and validate industrial crane drive systems**, independent of any manufacturer. These rules are non-negotiable and override any other technical convenience.

All work, code, documentation, and communication in this project is in **English**.

## Master decision rule
When several valid solutions exist, choose the one that maximizes, **in this exact order**:
**1) Privacy · 2) Manufacturer neutrality · 3) Security · 4) Simplicity · 5) Maintainability · 6) Low operating cost.**

## Manufacturer neutrality (non-negotiable)
- Never hardcode or optimize for Schneider, ABB, Siemens, Rockwell, SEW, Danfoss, Beckhoff, Konecranes, Demag, or any other manufacturer.
- The core only uses generic parameters: rated power, rated current, voltage, service factor, torque curve, efficiency, inertia, protection rating.
- Manufacturer catalogs = **optional, importable** datasets, outside the core, with no influence on the architecture.

## Privacy first
- No telemetry by default, no tracking, no fingerprinting, no advertising.
- Project/calculation data never leaves to external services without explicit user approval.
- Analytics, if any: self-hosted, disabled by default, aggregated metrics only.

## AI (future features)
- Allowed: report drafting, documentation help, search, natural language.
- Forbidden: sending calculation/customer data to external AI by default, training on customer reports, letting AI modify calculations or decide autonomously.

## Calculation engine (the central asset)
- Every formula is a **typed pure function**: no `global`, no side effects, no hidden state.
- Every formula carries a versioned id (`DOMAIN.SUBSYSTEM.QUANTITY.vN`), its assumptions, and its normative reference.
- A published version = immutable. Physics changes ⇒ new version, never edit an existing one.
- The `domain/` package imports nothing from FastAPI, SQLAlchemy, PDF, or the frontend. It is pure Python.
- Standards (FEM/ISO/IEC/EN/CMAA) live as data in `domain/standards/`, never as scattered constants.

## Business flow (two stages — do not change it)
1. **Requirement:** from the real characteristics of the crane, calculate the required torque/speed/current + RMS. Agnostic of any specific motor.
2. **Validation (Candidate check):** the user provides nameplate data of a candidate motor/drive; the system validates it against stage 1 (OK / NOT OK with margins).

The system **never chooses** a catalog motor on its own. The user proposes, the system validates.

## Security by default
HTTPS always, secure cookies, CSRF/XSS protection, rate limiting, strict input validation, Argon2 (bcrypt acceptable) for passwords, never plain text, never log secrets/tokens.

## Logs — must never contain
Customer names, documents, drawings, reports, calculation data, credentials, tokens. Only technical diagnostics, error traces, system health.

## Data
Strict minimization. Encryption at rest for accounts, customer data, project data, and reports. Full isolation per user/organization. Explicit retention and easy export. No profiling.

## Stack
Backend: Python + FastAPI · DB: PostgreSQL + SQLAlchemy · Frontend: React + TypeScript · Docker + Docker Compose · Nginx · Celery/RQ only if strictly necessary.

## Architecture
**Modular monolith + DDD + Clean Architecture.** No microservices without proven business need. Layers, with dependencies always pointing toward the domain:
```
interfaces (FastAPI, schemas, auth)
application (use cases)
domain (calculation engine, entities, standards)   ★ core, no external dependencies
infrastructure (DB, PDF, files)
```

## Definition of Done
A change is "done" when: it introduces no telemetry/tracking/manufacturer dependency; if it touches calculation, the formula is versioned, tested with a documented expected result, and exposes assumptions + standard; it meets security and logging requirements; it is the simplest option that satisfies the above.

## Reference documents in `/docs`
- `ARCHITECTURE.md` — folder structure and pure-formula pattern.
- `DUTY_CYCLE_MODEL.md` — duty cycle model (trapezoidal profile, %ED, starts/hour).
- `formulas/Inventario_Formulas_CraneSizing.md` — every core formula, with its physics correction where applicable.

**Never sacrifice privacy for convenience. Never sacrifice correctness for development speed.**
