# Cranes Sizing Platform

A manufacturer-neutral engineering platform to size and validate industrial
crane drive systems. See [`CLAUDE.md`](./CLAUDE.md) for the non-negotiable
project rules, [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) for the
architecture, [`docs/DUTY_CYCLE_MODEL.md`](./docs/DUTY_CYCLE_MODEL.md) for
the duty cycle model, and
[`docs/formulas/FORMULA_INVENTORY.md`](./docs/formulas/FORMULA_INVENTORY.md)
for the full formula inventory.

## Status: Phase 1 — navigable skeleton

This is an early scaffold: minimal backend + frontend wired together, and
the travel/hoist mechanics domain implemented and tested. No database,
authentication, or report generation yet (see `docs/ARCHITECTURE.md` section
9 for the full build order).

## Run the preview with Docker Compose

```bash
docker compose up --build
```

Open **http://localhost:8080** — a form for the travel (gantry/trolley)
requirement calculation. Submitting it calls the backend and shows the
required torque and motor speed, with each intermediate quantity's
`formula_id`, standard references, and assumptions.

Nginx (port 8080) serves the built frontend and reverse-proxies `/api/*` and
`/health` to the backend. This is the same setup you'd deploy on a small VPS.

## Run without Docker (local development)

**Backend** (Python 3.11+):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
pytest   # run the domain/application/API test suite
```

**Frontend** (Node 20+), in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The frontend defaults to calling the backend
directly at `http://localhost:8000` (see `frontend/src/api.ts`); no Nginx is
involved in this mode.

## API endpoints (Phase 1)

- `GET /health` — liveness check.
- `POST /api/calc/travel` — requirement-stage calculation for a travel
  (gantry/trolley) movement: given the mechanism's mass, kinematics, and
  mechanical parameters, returns the required torque and motor speed,
  independent of any candidate motor (see `CLAUDE.md`, business flow stage 1).

## What's implemented vs. what's next

Implemented: `domain/calc/mechanics/travel.py` and `hoist.py` (Modules 1 and
2 of the formula inventory), with the two safety-critical corrections from
`docs/formulas/FORMULA_INVENTORY.md` already applied — corrected hoist load
inertia and direction-dependent hoist efficiency.

Not yet implemented (Phase 2 onward, per `docs/ARCHITECTURE.md` section 9):
duty cycle and RMS (`domain/calc/cycle/`), motor and drive sizing/validation,
thermal and energy analysis, persistence, authentication, and PDF reports.
