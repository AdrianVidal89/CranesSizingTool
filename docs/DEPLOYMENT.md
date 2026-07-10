# Deployment

Production bring-up on a single small VPS. Target profile: **2 vCPU · 4 GB
RAM**, per `docs/ARCHITECTURE.md` section 2. No paid third-party service
(TLS, backups, monitoring) is used anywhere in this stack.

Stack: `db` (Postgres) · `backend` (FastAPI/Uvicorn) · `frontend`
(build-only, static assets) · `nginx` (TLS termination + reverse proxy +
rate limiting) · `certbot` (Let's Encrypt renewal) · `backup` (scheduled
`pg_dump`). Defined in `docker-compose.prod.yml`, distinct from the plain-
HTTP `docker-compose.yml` used for local development.

## 1. Environment variables

Copy `.env.example` to `.env` next to `docker-compose.prod.yml` and fill
in every value — `docker compose` reads `.env` automatically to resolve
the `${VAR}` references in the compose file. Never commit the real
`.env` (already gitignored).

| Variable | Used by | Notes |
|---|---|---|
| `POSTGRES_USER` | `db`, `backend`, `backup` | Any non-default name is fine. |
| `POSTGRES_PASSWORD` | `db`, `backend`, `backup` | High-entropy; not exposed outside the compose network (Postgres has no published host port). |
| `POSTGRES_DB` | `db`, `backend`, `backup` | Database name. |
| `DOMAIN` | `nginx`, `init-letsencrypt.sh` | Public DNS name, e.g. `cranes.example.com`. Must already resolve to the VPS's IP before TLS bootstrap. |
| `LETSENCRYPT_EMAIL` | `init-letsencrypt.sh` | Only used for Let's Encrypt expiry-notice registration. |
| `FIELD_ENCRYPTION_SECRET` | `backend` | Derives the column-level encryption-at-rest key (`backend/app/infrastructure/db/encrypted_types.py`). Generate with `openssl rand -base64 32`. Losing this makes existing encrypted data unrecoverable — back it up somewhere other than the VPS itself. |
| `BACKUP_RETENTION_DAYS` | `backup` | Optional, defaults to 14. |
| `BACKUP_INTERVAL_SECONDS` | `backup` | Optional, defaults to 86400 (daily). |

A few settings are deliberately **not** environment variables — they are
fixed to their secure value directly in `docker-compose.prod.yml`'s
`backend.environment` block so a misconfigured `.env` can't accidentally
weaken them: `SESSION_COOKIE_SECURE=true`, `SESSION_COOKIE_SAMESITE=strict`,
`ENVIRONMENT=production` (disables `/docs`, `/redoc`, `/openapi.json`).

## 2. First-time bring-up on the VPS

1. Point `DOMAIN`'s DNS `A`/`AAAA` record at the VPS before continuing —
   Let's Encrypt's http-01 challenge needs it resolvable.
2. Install Docker + the Compose plugin on the VPS.
3. Clone this repository, `cd` into it, copy `.env.example` to `.env` and
   fill in every `CHANGE_ME`.
4. Run the one-time TLS bootstrap: `./scripts/init-letsencrypt.sh`. This
   starts `nginx` with a throwaway self-signed certificate just long
   enough to pass the Let's Encrypt http-01 challenge, then reloads
   `nginx` with the real certificate. See the script's header comment for
   why this two-step dance is necessary. After this, the `certbot`
   service in the compose file keeps the certificate renewed
   automatically — this script is not run again.
5. Bring up the full stack: `docker compose -f docker-compose.prod.yml up -d`.
6. Verify: `curl -I https://$DOMAIN/health` should return `200`, and
   `curl -I http://$DOMAIN/` should `301` to `https://`.

## 3. Local smoke test (simulating production without a real domain)

Since there's no real DNS/TLS in a local/dev environment, run the stack
with `DOMAIN=localhost` and skip the Let's Encrypt bootstrap — generate a
throwaway self-signed certificate in its place:

```sh
cp .env.example .env
# fill in POSTGRES_*, FIELD_ENCRYPTION_SECRET; set DOMAIN=localhost

mkdir -p /tmp/letsencrypt-local/live/localhost
openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout /tmp/letsencrypt-local/live/localhost/privkey.pem \
    -out /tmp/letsencrypt-local/live/localhost/fullchain.pem \
    -subj "/CN=localhost"
docker volume create cranessizingtool_certbot_conf
docker run --rm -v cranessizingtool_certbot_conf:/dst -v /tmp/letsencrypt-local:/src alpine \
    cp -r /src/live /dst/

docker compose -f docker-compose.prod.yml up -d db backend frontend nginx
curl -Ik https://localhost/health   # -k: self-signed cert
```

Then exercise the calculation flow (register, run a travel/duty-cycle
calculation, save it, download the PDF report) against `https://localhost/`
exactly as in the dev preview, and confirm the response headers include
`Strict-Transport-Security`, `Content-Security-Policy`,
`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`.

## 4. Backups

`scripts/backup.sh` runs inside the `backup` service: `pg_dump -Fc` on a
fixed interval (default daily) to `./backups/` on the VPS host, deleting
dumps older than `BACKUP_RETENTION_DAYS`. Copy `./backups/` off the VPS
periodically (`rsync`/`scp` to wherever you keep offsite backups) — this
project does not do that for you, to avoid assuming a specific offsite
target or paid service.

**Restore:**

```sh
docker compose -f docker-compose.prod.yml cp ./backups/<file>.dump db:/tmp/restore.dump
docker compose -f docker-compose.prod.yml exec db \
    pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists /tmp/restore.dump
```

## 5. Resource sizing (2 vCPU / 4 GB)

Per-container limits in `docker-compose.prod.yml`, steady state (the
`frontend` container only runs during the initial build, not counted
here):

| Container | CPU limit | Memory limit |
|---|---|---|
| `db` | 0.75 | 768 MB |
| `backend` (2 Uvicorn workers) | 1.0 | 1024 MB |
| `nginx` | 0.25 | 128 MB |
| `certbot` | 0.1 | 64 MB |
| `backup` | 0.1 | 64 MB |
| **Total** | **2.2** | **~2 GB** |

Memory fits comfortably: ~2 GB of the 4 GB box, leaving headroom for the
host OS, Postgres's own disk cache, and the brief `frontend` build step.

CPU is the one figure worth calling out honestly: the limits sum to 2.2
vCPU on a 2 vCPU box. `deploy.resources.limits` are hard per-container
*ceilings*, not reservations, so this only matters if multiple containers
hit their ceiling at the same moment — `backup` and `certbot` are idle
almost all the time, so in practice `db` and `backend` (1.75 vCPU
combined) are what matters under real load, which does fit. If sustained
concurrent load ever saturates both `db` and `backend` at once, that's a
signal to move to a bigger VPS rather than to shave these limits further.

## 6. What could not be verified in this project's dev sandbox

- Live Let's Encrypt issuance (`scripts/init-letsencrypt.sh`) — requires a
  real domain with DNS already pointed at a real VPS.
- Live Nginx request/response behavior (redirects, rate-limit counters,
  response headers) — the sandbox's network namespace does not expose
  loopback TCP listeners to `curl`, even though `nginx -t` validates the
  config and the process binds successfully. Config syntax and the
  `${DOMAIN}` templating were validated for real with a local Nginx
  install.
- `docker compose -f docker-compose.prod.yml up` end-to-end — the Docker
  daemon is unavailable in this sandbox (a limitation disclosed in every
  phase of this project so far). The compose file itself was validated
  with `docker compose -f docker-compose.prod.yml config`, which resolves
  cleanly with no errors.
