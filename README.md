# Cranes Sizing Platform

A manufacturer-neutral engineering platform to size and validate industrial
crane drive systems. See [`CLAUDE.md`](./CLAUDE.md) for the non-negotiable
project rules, [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) for the
architecture, [`docs/DUTY_CYCLE_MODEL.md`](./docs/DUTY_CYCLE_MODEL.md) for
the duty cycle model, and
[`docs/formulas/FORMULA_INVENTORY.md`](./docs/formulas/FORMULA_INVENTORY.md)
for the full formula inventory.

## Status: Phase 4 — persistence, basic auth, and PDF reports

The full two-stage flow is implemented end to end: **requirement**
(mechanics + duty cycle, Phases 1-2) → **candidate validation** (motor +
drive, Phase 3) → **save + PDF report** (Phase 4). Basic login only (no
roles/permissions); no production deployment tuning yet (see
`docs/ARCHITECTURE.md` section 9 for the full build order).

## Run the preview with Docker Compose

```bash
docker compose up --build
```

Open **http://localhost:8080**. Nginx serves the built frontend and
reverse-proxies `/api/*` and `/health` to the backend, which runs
`alembic upgrade head` on startup against the bundled Postgres container.
This is the same setup you'd deploy on a small VPS. The Postgres
credentials and `FIELD_ENCRYPTION_SECRET` in `docker-compose.yml` are
clearly-labeled dev-only placeholders — override both for any real
deployment.

## Run without Docker (local development)

**Postgres** (a local instance, or point `DATABASE_URL` at any reachable one):

```bash
createuser cranes --pwprompt   # set password to match DATABASE_URL below
createdb cranes_sizing --owner=cranes
createdb cranes_sizing_test --owner=cranes   # used by the test suite
```

**Backend** (Python 3.11+):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL="postgresql+psycopg://cranes:<password>@localhost:5432/cranes_sizing"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

In another terminal, with the same `DATABASE_URL` (or let it default to
`cranes_sizing_test` — see `backend/tests/conftest.py`):

```bash
pytest   # domain/application/interfaces/infrastructure test suite
```

**Frontend** (Node 20+), in a third terminal:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The frontend defaults to calling the backend
directly at `http://localhost:8000` (see `frontend/src/api.ts`); no Nginx is
involved in this mode. Cookie-based auth needs `SESSION_COOKIE_SECURE=false`
in the backend's environment when testing over plain HTTP locally (the
Docker Compose setup already sets this).

## Environment variables (backend)

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | local Postgres, dev credentials | SQLAlchemy URL, `postgresql+psycopg://...` |
| `FIELD_ENCRYPTION_SECRET` | insecure dev placeholder | Derives the Fernet key for column-level encryption at rest — **must** be overridden outside local dev |
| `SESSION_COOKIE_SECURE` | `true` | Set `false` only for local HTTP development |
| `SESSION_TTL_HOURS` | `168` (7 days) | Session cookie lifetime |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated |

## API endpoints

**Calculation (stateless, no auth required):**
- `GET /health` — liveness check.
- `POST /api/calc/travel` — requirement stage: torque/speed for a travel movement.
- `POST /api/calc/duty-cycle` — adds the duty-cycle phase profile, %ED/starts-per-hour, thermal RMS torque, and energy.
- `POST /api/calc/validate-candidate` — adds motor (and optional drive) candidate validation against the requirement; the system validates, it never selects equipment.

**Auth:**
- `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me` — basic email/password auth, HttpOnly session cookie + CSRF double-submit cookie. Every mutating endpoint below requires the `X-CSRF-Token` header to match the `csrf_token` cookie.

**Persistence (all require login, all isolated per user):**
- `POST /api/projects`, `GET /api/projects`.
- `POST /api/calculation-runs` — runs `/api/calc/validate-candidate` once and persists the exact input and result as an immutable snapshot, plus the `calc_version` (the sorted list of every `formula_id` used).
- `GET /api/calculation-runs`, `GET /api/calculation-runs/{id}`.
- `POST /api/reports` — renders a PDF from an already-saved calculation run (never runs a calculation itself).
- `GET /api/reports/{id}/pdf` — downloads it.

## Try the full flow

1. Open the app, fill in the travel requirement form, calculate.
2. Fill in the duty cycle section, calculate.
3. Fill in a motor (and optionally drive) candidate, validate.
4. Register/log in, then save the calculation as a project.
5. Download the PDF report for the saved calculation run.

## What's implemented vs. what's next

Implemented: full mechanics (Modules 1-2), duty cycle (Module 4), motor and
drive candidate validation (Modules 5-6), persistence with per-user
isolation and encryption at rest, basic auth, and local PDF report
generation — see `docs/formulas/FORMULA_INVENTORY.md` for the formula-level
detail and corrections applied.

Not yet implemented: advanced auth (roles/permissions, password reset),
production deployment tuning (e.g. for Hetzner).
