#!/bin/sh
# Update-in-place deploy for a NAS checkout that was installed without git
# (see docs/NAS_DEPLOYMENT.md) — pulls the latest commit on a branch via
# GitHub's REST API + tarball download (no git needed on the NAS),
# verifies the download, applies pending Alembic migrations as an
# explicit pre-flight step (so a bad migration never reaches the running
# app), then rebuilds and restarts docker-compose.nas.yml. Keeps exactly
# one previous release for `--rollback`.
#
# Usage:
#   scripts/deploy-nas.sh              deploy the latest commit (no-op if already up to date)
#   scripts/deploy-nas.sh --force      redeploy even if already on the latest commit
#   scripts/deploy-nas.sh --dry-run    download + verify + preview, touch nothing running
#   scripts/deploy-nas.sh --rollback   swap back to the previous release and restart
set -eu

# Re-exec from a temp copy of this script before doing anything else: a
# long-running shell script that gets overwritten mid-run (which this one
# does, to itself, since it lives inside the checkout it updates) can read
# garbled/mixed old+new content from disk partway through. Running from a
# copy makes that safe regardless of what happens to the original file.
if [ -z "${DEPLOY_NAS_REPO_DIR:-}" ]; then
    DEPLOY_NAS_REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
    export DEPLOY_NAS_REPO_DIR
    TMP_SELF="$(mktemp)"
    cp "$0" "$TMP_SELF"
    chmod +x "$TMP_SELF"
    exec "$TMP_SELF" "$@"
fi

REPO_DIR="$DEPLOY_NAS_REPO_DIR"
REPO_SLUG="AdrianVidal89/CranesSizingTool"
BRANCH="${DEPLOY_BRANCH:-main}"
ENV_FILE="${DEPLOY_ENV_FILE:-.env.nas}"
COMPOSE_FILE="${DEPLOY_COMPOSE_FILE:-docker-compose.nas.yml}"
PREVIOUS_DIR="${REPO_DIR}.previous"
SHA_FILE="${REPO_DIR}/.deployed_sha"

log() { echo "[deploy] $*"; }
fail() { echo "[deploy] ERROR: $*" >&2; exit 1; }

compose() {
    if docker compose version >/dev/null 2>&1; then
        docker compose "$@"
    elif command -v docker-compose >/dev/null 2>&1; then
        docker-compose "$@"
    elif [ -x "$HOME/bin/docker-compose" ]; then
        # Falls back here even if $HOME/bin isn't on PATH in whatever
        # shell/context invoked this script (a common gap right after a
        # manual `curl`-installed docker-compose, since `export PATH=...`
        # only lasts the session it was run in).
        "$HOME/bin/docker-compose" "$@"
    else
        fail "Neither 'docker compose' nor 'docker-compose' was found (checked PATH and \$HOME/bin/docker-compose)."
    fi
}

cd "$REPO_DIR"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"; rm -f "$0"' EXIT

ACTION=""
DRY_RUN=""
for arg in "$@"; do
    case "$arg" in
        --rollback) ACTION="rollback" ;;
        --force) ACTION="force" ;;
        --dry-run) DRY_RUN="1" ;;
        *) fail "Unknown argument: $arg" ;;
    esac
done

if [ "$ACTION" = "rollback" ]; then
    [ -d "$PREVIOUS_DIR" ] || fail "No previous release to roll back to ($PREVIOUS_DIR not found)."
    log "Rolling back to the previous release..."
    SWAP_TMP="${REPO_DIR}.rollback-tmp"
    rm -rf "$SWAP_TMP"
    mv "$REPO_DIR" "$SWAP_TMP"
    mv "$PREVIOUS_DIR" "$REPO_DIR"
    mv "$SWAP_TMP" "$PREVIOUS_DIR"
    cd "$REPO_DIR"
    log "Rebuilding and restarting with the previous release's code..."
    compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --build
    log "Rolled back. This restarts the PREVIOUS CODE against the CURRENT database schema —"
    log "if the deploy you're rolling back from ran a migration, this does NOT undo it."
    log "Run this again to swap back if needed."
    exit 0
fi

[ -f "$ENV_FILE" ] || fail "$ENV_FILE not found in $REPO_DIR — copy ${ENV_FILE}.example to $ENV_FILE and fill it in first."

log "Checking the latest commit on branch '$BRANCH'..."
API_RESPONSE="$(curl -fsSL "https://api.github.com/repos/${REPO_SLUG}/commits/${BRANCH}")" \
    || fail "Could not reach the GitHub API to check the latest commit."
LATEST_SHA="$(printf '%s\n' "$API_RESPONSE" | grep '"sha"' | head -n1 | sed -E 's/.*"sha": *"([0-9a-f]+)".*/\1/')"
[ -n "$LATEST_SHA" ] || fail "Could not parse a commit SHA out of the GitHub API response."

if [ "$ACTION" != "force" ] && [ -f "$SHA_FILE" ] && [ "$(cat "$SHA_FILE")" = "$LATEST_SHA" ]; then
    log "Already running the latest commit ($LATEST_SHA). Nothing to do (pass --force to redeploy anyway)."
    exit 0
fi

log "Downloading commit ${LATEST_SHA}..."
TARBALL="$WORKDIR/source.tar.gz"
curl -fsSL -o "$TARBALL" "https://github.com/${REPO_SLUG}/archive/${LATEST_SHA}.tar.gz" \
    || fail "Download failed."

log "Verifying archive integrity..."
[ -s "$TARBALL" ] || fail "Downloaded archive is empty."
tar tzf "$TARBALL" >/dev/null 2>&1 || fail "Downloaded archive is not a valid tar.gz — aborting, nothing was touched."

log "Extracting..."
tar xzf "$TARBALL" -C "$WORKDIR"
EXTRACTED_DIR="$(find "$WORKDIR" -mindepth 1 -maxdepth 1 -type d -name "CranesSizingTool-*")"
[ -n "$EXTRACTED_DIR" ] && [ -d "$EXTRACTED_DIR" ] || fail "Could not find the extracted source directory."
[ -f "$EXTRACTED_DIR/$COMPOSE_FILE" ] || fail "Extracted source looks incomplete ($COMPOSE_FILE missing) — aborting."

if [ -n "$DRY_RUN" ]; then
    log "Dry run: downloaded and verified commit ${LATEST_SHA} successfully. Nothing else was touched."
    log "Currently deployed: $([ -f "$SHA_FILE" ] && cat "$SHA_FILE" || echo "unknown")"
    exit 0
fi

log "Backing up the current release to $(basename "$PREVIOUS_DIR")..."
rm -rf "$PREVIOUS_DIR"
cp -a "$REPO_DIR" "$PREVIOUS_DIR"

log "Syncing the new source into place (keeping $ENV_FILE, backups/, .deployed_sha)..."
if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
        --exclude ".env" --exclude ".env.nas" --exclude ".env.local" \
        --exclude "backups/" --exclude ".deployed_sha" \
        "$EXTRACTED_DIR"/ "$REPO_DIR"/
else
    log "rsync not found — falling back to cp (files removed upstream may linger; install rsync to avoid this)."
    find "$REPO_DIR" -mindepth 1 -maxdepth 1 \
        ! -name ".env" ! -name ".env.nas" ! -name ".env.local" \
        ! -name "backups" ! -name ".deployed_sha" \
        -exec rm -rf {} +
    cp -a "$EXTRACTED_DIR"/. "$REPO_DIR"/
fi

cd "$REPO_DIR"

if [ ! -f "$REPO_DIR/scripts/deploy-nas.sh" ]; then
    log "WARNING: scripts/deploy-nas.sh is missing after syncing — the branch"
    log "you're deploying from doesn't include this script yet. This run will"
    log "still finish (it's already running from a safe temp copy), but the"
    log "NEXT invocation of 'scripts/deploy-nas.sh' will fail with"
    log "'No such file or directory' until you restore it."
fi

log "Building the backend image..."
compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build backend

log "Applying pending database migrations..."
if ! compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" run --rm backend alembic upgrade head; then
    log "Migration failed — the running application was NOT touched."
    log "Fix the migration (or restore from $(basename "$PREVIOUS_DIR") if it's a code problem) and re-run."
    exit 1
fi

log "Deploying the new version..."
compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --build

# `up -d` does not recreate nginx when only the content of its
# bind-mounted config changed, and a non-restarted nginx keeps proxying
# to the previous backend container's now-dead IP -> 502 on every /api
# call (see the resolver note in nginx/nas/default.conf). Restarting it
# here makes every deploy pick up config changes and re-resolve the
# backend, whichever nginx config version is currently mounted.
log "Restarting nginx so it reloads its config and re-resolves the backend..."
compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" restart nginx

log "Waiting for the app to report healthy..."
PORT="$(grep -E '^NAS_HTTP_PORT=' "$ENV_FILE" | cut -d= -f2)"
PORT="${PORT:-8090}"
i=0
until curl -fsS "http://localhost:${PORT}/health" >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -ge 20 ]; then
        log "Health check did not pass after 60s."
        log "Run 'scripts/deploy-nas.sh --rollback' to revert to the previous release."
        fail "Deploy finished but the health check failed — investigate before trusting this deploy."
    fi
    sleep 3
done

echo "$LATEST_SHA" > "$SHA_FILE"
log "Deployed successfully: commit ${LATEST_SHA}"
