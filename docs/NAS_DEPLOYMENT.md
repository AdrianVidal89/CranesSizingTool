# NAS deployment (QNAP / LAN-only)

A quick-start for running this on a home/office NAS with Docker support
(QNAP Container Station and similar) — reachable on your local network
only, no public domain or TLS required. If you instead want an
internet-facing deployment with automatic HTTPS, see `docs/DEPLOYMENT.md`
and `docker-compose.prod.yml`.

Uses `docker-compose.nas.yml`, a variant of the production compose file
with Let's Encrypt/Certbot removed and a single plain-HTTP port
published. Everything else — Argon2 password hashing, CSRF, per-owner
data isolation, encryption at rest, rate limiting, security headers — is
unchanged. No paid service of any kind is used.

## 1. Get the repository onto the NAS

Container Station builds the `backend` and `frontend` images from this
repo's own `Dockerfile`s (there is no pre-built image on a registry), so
you need the full repository on the NAS, not just the compose file.

**Via SSH** (QNAP: enable SSH under Control Panel → Network & File
Services → Telnet/SSH):

```sh
ssh admin@<nas-ip>
git clone https://github.com/<your-fork-or-org>/CranesSizingTool.git
cd CranesSizingTool
```

**Without SSH**: download the repository as a zip from GitHub and
extract it into a shared folder via File Station, then use Container
Station's file browser to locate it.

## 2. Configure

```sh
cp .env.nas.example .env.nas
# edit .env.nas: POSTGRES_USER/PASSWORD/DB, FIELD_ENCRYPTION_SECRET
# (openssl rand -base64 32), LAN_ORIGIN (http://<nas-ip>:<port>),
# NAS_HTTP_PORT (default 8090 — QNAP's own admin UI often already
# uses 8080)
```

## 3. Bring it up

**Via SSH / CLI** (recommended — works identically to any Linux host
with Docker installed):

```sh
docker compose --env-file .env.nas -f docker-compose.nas.yml up -d --build
```

Then open `http://<nas-ip>:<NAS_HTTP_PORT>/` (default port 8090) from
any device on your LAN.

**Via the Container Station GUI**: "Create" → "Create Application" →
paste the contents of `docker-compose.nas.yml`. The GUI's own env
substitution only reads a file literally named `.env` in the project
folder, not `--env-file .env.nas` — so for the GUI path, copy
`.env.nas.example` to plain `.env` instead of `.env.nas` (only do this
if you are not also running the internet-facing `docker-compose.prod.yml`
on the same checkout, since that one also reads `.env`).

## 4. Managing the stack

```sh
docker compose --env-file .env.nas -f docker-compose.nas.yml ps
docker compose --env-file .env.nas -f docker-compose.nas.yml logs -f backend
docker compose --env-file .env.nas -f docker-compose.nas.yml down
```

**Updating**: most QNAP firmware doesn't ship `git`, so use
`scripts/deploy-nas.sh` instead — it fetches the latest commit on `main`
straight from GitHub (REST API + tarball, no `git` needed), verifies the
download, keeps your `.env.nas` and `backups/` untouched, applies
pending database migrations as an explicit step *before* touching the
running app (so a bad migration never reaches it), then rebuilds and
restarts. It also keeps exactly one previous release for instant
rollback.

```sh
cd ~/CranesSizingTool
scripts/deploy-nas.sh --dry-run    # preview what would change, touches nothing
scripts/deploy-nas.sh              # deploy the latest commit
scripts/deploy-nas.sh --rollback   # revert to the previous release if something's wrong
```

(If you did install `git` via Entware, `git pull && docker compose ... up -d --build` works just as well — `scripts/deploy-nas.sh` exists for the more common case of not having `git` on the NAS at all.)

## 5. Backups

Same mechanism as the production stack (`scripts/backup.sh`, see
`docs/DEPLOYMENT.md` section 4 for the restore procedure) — dumps land
in `./backups/` on the NAS's filesystem. Most NAS platforms already have
their own snapshot/backup tooling (e.g. QNAP's Hybrid Backup Sync) —
point it at this repo's `./backups/` folder, or at the whole checkout,
to get it included in your existing NAS backup routine for free.

## 6. Adding TLS yourself (optional)

This compose file deliberately does not manage TLS — on a home/office
LAN, that is usually handled by the NAS itself if you want it at all
(e.g. QNAP's built-in Reverse Proxy under myQNAPcloud, or your own
reverse proxy container). To add it:

1. Point your reverse proxy of choice at `http://<nas-ip>:<NAS_HTTP_PORT>`.
2. Set `SESSION_COOKIE_SECURE: "true"` in `docker-compose.nas.yml`'s
   `backend.environment` block (cookies can only carry the `Secure` flag
   once the browser is actually talking to your app over HTTPS — even if
   that HTTPS is terminated by the reverse proxy in front of this stack,
   not by this stack itself).

## 7. Resource sizing

`docker-compose.nas.yml` ships with the same per-container
`deploy.resources.limits` as the internet-facing stack (see
`docs/DEPLOYMENT.md` section 5) as a reasonable starting point. NAS
hardware varies far more than a cloud VPS SKU — some QNAP models are
low-power ARM boards with 2 GB RAM. If yours is one of those: lower
`backend`'s `--workers 2` to `--workers 1` in the compose file's
`command:`, and reduce the `memory:` limits accordingly. This project's
dev sandbox has no QNAP hardware to test against, so these defaults are
a starting point to tune, not a guarantee — watch `docker stats` after
first bring-up and adjust.
