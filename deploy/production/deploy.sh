#!/bin/bash
# =============================================================================
# BDD Property Tracker — Update / Deploy
#
# Usage, on 10.100.100.88 as `aidev`:
#
#     /opt/bdd-git/deploy.sh
#     /opt/bdd-git/deploy.sh --check     # preflight only, changes nothing
#
# No sudo. aidev owns /opt/bdd-git and /opt/bdd-data and is in the docker group.
#
# Source code is baked into the images at build time, so `git pull` alone
# changes files that nothing reads — the images must be rebuilt and the
# containers recreated for a pull to have any effect. That is the whole reason
# this script exists rather than a bare `git pull`.
#
# Unlike the AI Infra and TMS boxes this deployment spans TWO repositories
# (frontend and backend) with the compose file, both .env files, nginx/ and
# certbot/ living beside them, untracked. Every one of those is a thing a
# careless pull could break, so the preflight checks all of them.
#
# Every run is logged to ~/deploy-logs/.
# =============================================================================
set -euo pipefail

PROJECT_DIR="/opt/bdd-git"
OLD_TREE="/opt/bdd"                     # July's stack. Never touched. The way back.
UPLOADS_HOST="/opt/bdd-data/uploads"
DB_CONTAINER="bdd-db-local"
BACKEND_CONTAINER="bdd-backend-local"
FRONTEND_CONTAINER="bdd-frontend-local"
DB_USER="postgres"
DB_NAME="bdd_production_db"
FRONTEND_IMAGE="bdd-local-frontend"
BACKEND_IMAGE="bdd-local-backend"
PGDATA_VOLUME="bdd-local_pgdata"
JULY_TAG="july-2026"
HEALTH_URL="https://127.0.0.1/"
BACKUP_DIR="$HOME/cutover-backup"
LOG_DIR="$HOME/deploy-logs"

# Resolved absolutely so the re-exec below survives a relative invocation.
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"

red()    { printf '\033[31m%s\033[0m\n' "$*"; }
green()  { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }

# --- logging -----------------------------------------------------------------
# Re-execs once through `tee` rather than `exec > >(tee ...)`: process
# substitution lets the script exit before tee has flushed, losing the tail of
# the log exactly when the SSH session drops. Piping keeps the real exit status
# via PIPESTATUS.
if [ -z "${DEPLOY_LOG_ACTIVE:-}" ]; then
    mkdir -p "$LOG_DIR"
    export DEPLOY_LOG_ACTIVE=1
    export DEPLOY_LOG_FILE="$LOG_DIR/bdd-$(date +%Y-%m-%d_%H%M%S).log"
    find "$LOG_DIR" -maxdepth 1 -name 'bdd-*.log' -type f -mtime +90 -delete 2>/dev/null || true
    bash "$SCRIPT_PATH" "$@" 2>&1 | tee -a "$DEPLOY_LOG_FILE"
    exit "${PIPESTATUS[0]}"
fi
LOG_FILE="$DEPLOY_LOG_FILE"

cd "$PROJECT_DIR"

echo ""
echo "================================================================"
echo "  BDD Deploy  —  $(date '+%Y-%m-%d %H:%M:%S')"
echo "  log: $LOG_FILE"
echo "================================================================"

# --- step 1: preflight -------------------------------------------------------
# Runs before the backup so a run that was never going to proceed does not leave
# a junk dump behind.
echo ""
echo "[1/7] Preflight..."

if [ "$(id -un)" = "root" ]; then
    red "  Run as aidev, not root. A root run leaves the checkouts owned by root"
    echo "  and the deploy keys unreadable on the next run."
    exit 1
fi

# The compose project name derives BOTH the image names and the database volume
# name. There is no `image:` line to fall back on — the services only have
# `build:` — so if this line is lost the stack silently builds new images and
# attaches a brand-new empty database.
if ! grep -q '^name: bdd-local' "$PROJECT_DIR/docker-compose.yml"; then
    red "  docker-compose.yml is missing 'name: bdd-local'. Refusing to deploy."
    echo "  Without it Compose picks a project name from the directory, which"
    echo "  detaches $PGDATA_VOLUME and starts with an EMPTY database."
    exit 1
fi

# The uploads bind must stay absolute. As a relative path it resolves against
# whatever directory the compose file sits in, and Docker helpfully creates an
# empty one — the stack comes up, every check passes, and all the photos 404.
if ! grep -q "^\s*-\s*${UPLOADS_HOST}:/app/uploads" "$PROJECT_DIR/docker-compose.yml"; then
    red "  The uploads bind is not $UPLOADS_HOST. Refusing to deploy."
    grep -n 'uploads' "$PROJECT_DIR/docker-compose.yml" | sed 's/^/    /'
    exit 1
fi

# Both .env files. The top-level one is easy to forget and fails confusingly:
# Compose substitutes an empty ${PG_PASSWORD} and nothing can reach the database.
for f in "$PROJECT_DIR/.env" "$PROJECT_DIR/backend/.env"; do
    if [ ! -f "$f" ]; then
        red "  Missing $f. Refusing to deploy."
        exit 1
    fi
done

# The July images are the standing answer to "can we go back". A build
# overwrites :latest, so if these are gone there is no floor under a rollback.
MISSING_PIN=0
for img in "$FRONTEND_IMAGE" "$BACKEND_IMAGE"; do
    docker image inspect "$img:$JULY_TAG" >/dev/null 2>&1 || MISSING_PIN=1
done
if [ "$MISSING_PIN" -eq 1 ]; then
    if [ "${ALLOW_MISSING_JULY_PIN:-0}" = "1" ]; then
        yellow "  July pin missing — continuing because ALLOW_MISSING_JULY_PIN=1."
    else
        red "  The $JULY_TAG images are missing. Refusing to deploy."
        echo "  They are the guaranteed rollback point for this deployment."
        echo "  Restore them:"
        echo "    gunzip -c ~/july-images/frontend-$JULY_TAG.tar.gz | docker load"
        echo "    gunzip -c ~/july-images/backend-$JULY_TAG.tar.gz  | docker load"
        echo "  Or, if they are deliberately retired: ALLOW_MISSING_JULY_PIN=1 $0"
        exit 1
    fi
fi

# Checked before the diff below, which would otherwise report "tracked files
# modified" when the real problem is that there is no repository at all —
# `git diff --quiet` exits non-zero either way. Misleading at exactly the moment
# you need an accurate message.
for repo in frontend backend; do
    if [ ! -e "$PROJECT_DIR/$repo/.git" ]; then
        case "$repo" in
            frontend) slug="client" ;;
            backend)  slug="server" ;;
        esac
        red "  $PROJECT_DIR/$repo is not a git checkout. Refusing to deploy."
        echo "  This script deploys from git. If the tree was replaced by hand,"
        echo "  re-clone it before deploying:"
        echo "    git clone git@github.com-bdd-$slug:Global-Comfort-Group/bdd_$slug.git $PROJECT_DIR/$repo"
        exit 1
    fi
done

# Tracked files edited directly on the VM. Pulling over them would either fail
# or silently discard the change; refusing is safer than either.
for repo in frontend backend; do
    if ! git -C "$PROJECT_DIR/$repo" diff --quiet || ! git -C "$PROJECT_DIR/$repo" diff --cached --quiet; then
        red "  Tracked files modified in $repo. Refusing to deploy."
        git -C "$PROJECT_DIR/$repo" status --short | sed 's/^/    /'
        echo ""
        echo "  Commit them upstream, or discard: git -C $PROJECT_DIR/$repo checkout -- ."
        exit 1
    fi
done

# Checked explicitly rather than relying on set -e: a failed fetch would make
# every comparison below compare against stale refs and wrongly report success.
for repo in frontend backend; do
    if ! git -C "$PROJECT_DIR/$repo" fetch --quiet origin main; then
        red "  Cannot reach GitHub from $repo (git fetch failed). Refusing to deploy."
        echo "  Without a successful fetch the checks below would compare against"
        echo "  stale refs and report that everything is fine."
        exit 1
    fi
done

# Untracked files colliding with incoming paths. `git diff --quiet` cannot see
# these, and this box has real candidates: backend/.env sits inside the backend
# checkout and is untracked. The day anything like it lands upstream, `git pull`
# aborts and under `set -e` that kills the script before the rebuild.
for repo in frontend backend; do
    COLLISIONS=$(comm -12 \
        <(git -C "$PROJECT_DIR/$repo" diff --name-only HEAD origin/main | sort) \
        <(git -C "$PROJECT_DIR/$repo" ls-files --others --exclude-standard | sort) || true)
    if [ -n "$COLLISIONS" ]; then
        red "  Untracked files in $repo collide with incoming changes. Refusing."
        echo ""
        while IFS= read -r f; do
            [ -z "$f" ] && continue
            if git -C "$PROJECT_DIR/$repo" show "origin/main:$f" 2>/dev/null \
                 | diff -q - "$PROJECT_DIR/$repo/$f" >/dev/null 2>&1; then
                echo "    $f  — identical to incoming, safe to remove"
            else
                yellow "    $f  — DIFFERS from incoming, review before removing"
            fi
        done <<< "$COLLISIONS"
        echo ""
        echo "  Remove the ones marked identical, then re-run."
        exit 1
    fi
done

green "  Preflight OK (project name, uploads bind, both .env, July pin, clean trees)"

for repo in frontend backend; do
    echo "  $repo: $(git -C "$PROJECT_DIR/$repo" rev-parse --short HEAD)" \
         "-> origin/main $(git -C "$PROJECT_DIR/$repo" rev-parse --short origin/main)" \
         "($(git -C "$PROJECT_DIR/$repo" rev-list --count HEAD..origin/main) commit(s) behind)"
done

# --check exists so the preflight can be exercised on a real box without
# touching anything — including on the day something is actually wrong, when
# you want to know what without starting a deploy to find out.
if [ "${1:-}" = "--check" ]; then
    echo ""
    green "Preflight only (--check). Nothing was changed."
    echo "Log: $LOG_FILE"
    exit 0
fi

# --- step 2: backup ----------------------------------------------------------
# Taken before the pull so the dump reflects the state you would roll back to.
# A dump that cannot be read is worse than no dump, because you would trust it.
echo ""
echo "[2/7] Backing up..."
mkdir -p "$BACKUP_DIR"
STAMP=$(date +%F_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db-$STAMP.dump"

docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc --no-owner --no-acl > "$BACKUP_FILE"

if ! docker exec -i "$DB_CONTAINER" pg_restore --list < "$BACKUP_FILE" >/dev/null 2>&1; then
    red "  Backup verification failed — pg_restore cannot read the dump. Aborting."
    echo "  Bad dump left for inspection: $BACKUP_FILE"
    exit 1
fi
green "  Backup verified: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

# Recorded so the post-deploy check compares against reality rather than a
# hardcoded number that drifts. Note the quoting: the users table is named
# "user", a reserved word — unquoted, Postgres returns the session username
# instead of erroring, so the check would silently pass on nonsense.
read -r BEFORE_PROPERTIES BEFORE_USERS BEFORE_ATTACHMENTS <<< "$(
  docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -A -F' ' -c \
    'SELECT (SELECT count(*) FROM properties), (SELECT count(*) FROM "user"), (SELECT count(*) FROM property_attachments);' \
  | tr -d '\r')"
BEFORE_UPLOADS=$(find "$UPLOADS_HOST" -type f | wc -l)
echo "  Baseline: $BEFORE_PROPERTIES properties, $BEFORE_USERS users, $BEFORE_ATTACHMENTS attachments, $BEFORE_UPLOADS upload files"

if [ "${BEFORE_PROPERTIES:-0}" -lt 1 ] || [ "${BEFORE_UPLOADS:-0}" -lt 1 ]; then
    red "  Baseline looks wrong (properties=$BEFORE_PROPERTIES uploads=$BEFORE_UPLOADS). Aborting."
    echo "  Something is already broken; deploying on top of it would hide the cause."
    exit 1
fi

# --- step 3: pull ------------------------------------------------------------
echo ""
echo "[3/7] Pulling..."
CHANGED=0
declare -A BEFORE_SHA
for repo in frontend backend; do
    BEFORE_SHA[$repo]=$(git -C "$PROJECT_DIR/$repo" rev-parse --short HEAD)
    # --ff-only refuses anything needing a merge commit, rather than baking a
    # half-merged tree into an image.
    git -C "$PROJECT_DIR/$repo" pull --ff-only origin main
    AFTER=$(git -C "$PROJECT_DIR/$repo" rev-parse --short HEAD)
    if [ "${BEFORE_SHA[$repo]}" = "$AFTER" ]; then
        echo "  $repo: already at $AFTER"
    else
        echo "  $repo: ${BEFORE_SHA[$repo]} -> $AFTER"
        git -C "$PROJECT_DIR/$repo" log --oneline "${BEFORE_SHA[$repo]}..$AFTER" | head -20 | sed 's/^/      /'
        CHANGED=1
    fi
done

if [ "$CHANGED" -eq 0 ]; then
    echo "  Nothing new in either repo. Rebuilding anyway in case images are stale."
    echo "  Ctrl-C within 5s to abort."
    sleep 5
fi

# --- step 4: build -----------------------------------------------------------
# Deliberately before any teardown: a failed build leaves the running containers
# completely untouched and the service stays up.
#
# :latest is retagged :previous first. The build overwrites :latest in place, so
# without this the last known-good images are lost and rolling back would mean
# rebuilding from an older commit. :july-2026 is never touched — it is the
# permanent floor, where :previous is the rolling one.
echo ""
echo "[4/7] Building..."
ROLLBACK_AVAILABLE=true
for img in "$FRONTEND_IMAGE" "$BACKEND_IMAGE"; do
    if docker image inspect "$img:latest" >/dev/null 2>&1; then
        docker tag "$img:latest" "$img:previous"
    else
        yellow "  $img:latest not present — no rolling rollback point for it."
        ROLLBACK_AVAILABLE=false
    fi
done

docker compose build
green "  Images built"

# --- step 5: migrate ---------------------------------------------------------
# Run explicitly, before the swap, so a failure stops the deploy with the old
# containers still serving. The backend image runs uvicorn directly and never
# executes start.sh, so nothing migrates on its own — this is the only thing
# that ever touches the schema.
#
# --no-deps stops Compose starting a second database alongside the running one.
# --name sidesteps the fixed container_name, which a plain `run` would clash on.
echo ""
echo "[5/7] Migrations..."
docker rm -f bdd-alembic-oneshot >/dev/null 2>&1 || true
BEFORE_REV=$(docker compose run --rm -T --no-deps --name bdd-alembic-oneshot \
    --entrypoint alembic backend current 2>/dev/null < /dev/null | tail -1 || echo "unknown")
docker compose run --rm -T --no-deps --name bdd-alembic-oneshot \
    --entrypoint alembic backend upgrade head < /dev/null
AFTER_REV=$(docker compose run --rm -T --no-deps --name bdd-alembic-oneshot \
    --entrypoint alembic backend current 2>/dev/null < /dev/null | tail -1 || echo "unknown")
echo "  $BEFORE_REV  ->  $AFTER_REV"

# --- step 6: swap ------------------------------------------------------------
echo ""
echo "[6/7] Recreating containers..."
if ! docker volume ls --format '{{.Name}}' | grep -qx "$PGDATA_VOLUME"; then
    red "  $PGDATA_VOLUME not found before down. Aborting to protect the database."
    exit 1
fi

docker compose down          # NEVER -v. The -v deletes the database volume.

if ! docker volume ls --format '{{.Name}}' | grep -qx "$PGDATA_VOLUME"; then
    red "  $PGDATA_VOLUME disappeared during down. STOP — do not run up."
    echo "  Restore from $BACKUP_FILE before anything else touches this box."
    exit 1
fi
echo "  Volume intact"

docker compose up -d

# --- step 7: verify ----------------------------------------------------------
# Only nginx publishes ports (80/443). The backend's 8000 and frontend's 3000
# are container-internal, so curling them from the host returns 000 even when
# everything is healthy. Check through nginx, which is the path users take.
#
# Both are polled together. The frontend answers through nginx in a couple of
# seconds while the backend takes appreciably longer to boot, so checking the
# backend once after the site goes green reads it before it is up and rolls back
# a perfectly good deploy.
#
# curl prints 000 itself on a connection failure, so no `|| echo 000` — that
# would concatenate with curl's own output and produce "000000". `|| true` is
# still needed: under `set -e` a failing curl in a command substitution would
# otherwise kill the script.
http_code() {
    curl -sk -o /dev/null -w '%{http_code}' --max-time 5 "$1" 2>/dev/null || true
}
backend_health_code() {
    docker exec "$BACKEND_CONTAINER" curl -s -o /dev/null -w '%{http_code}' --max-time 5 \
        http://localhost:8000/health 2>/dev/null || true
}

echo ""
echo -n "[7/7] Waiting for health"
HEALTHY=false
SITE_CODE=000
BACKEND_CODE=000
for _ in $(seq 1 40); do
    SITE_CODE=$(http_code "$HEALTH_URL")
    BACKEND_CODE=$(backend_health_code)
    if [ "$SITE_CODE" = "200" ] && [ "$BACKEND_CODE" = "200" ]; then
        echo ""
        green "  Site and backend responding"
        HEALTHY=true
        break
    fi
    echo -n "."
    sleep 3
done
[ "$HEALTHY" = true ] || echo " (last seen: site=$SITE_CODE backend=$BACKEND_CODE)"

FAILED=""
if [ "$HEALTHY" = true ]; then
    # Liveness is not enough. An empty database or an unmounted uploads
    # directory both serve a perfectly healthy-looking 200.
    read -r AFTER_PROPERTIES AFTER_USERS AFTER_ATTACHMENTS <<< "$(
      docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -A -F' ' -c \
        'SELECT (SELECT count(*) FROM properties), (SELECT count(*) FROM "user"), (SELECT count(*) FROM property_attachments);' \
      | tr -d '\r')"
    AFTER_UPLOADS=$(docker exec "$BACKEND_CONTAINER" sh -c 'find /app/uploads -type f | wc -l' | tr -d '\r')

    echo "  properties  $BEFORE_PROPERTIES -> $AFTER_PROPERTIES"
    echo "  users       $BEFORE_USERS -> $AFTER_USERS"
    echo "  attachments $BEFORE_ATTACHMENTS -> $AFTER_ATTACHMENTS"
    echo "  uploads     $BEFORE_UPLOADS (host) -> $AFTER_UPLOADS (in container)"

    echo "  backend /health = $BACKEND_CODE   site = $SITE_CODE"

    [ "${AFTER_PROPERTIES:-0}" -ge "$BEFORE_PROPERTIES" ] || FAILED="$FAILED properties($BEFORE_PROPERTIES->$AFTER_PROPERTIES)"
    [ "${AFTER_USERS:-0}" -ge "$BEFORE_USERS" ]           || FAILED="$FAILED users($BEFORE_USERS->$AFTER_USERS)"
    [ "${AFTER_UPLOADS:-0}" -eq "$BEFORE_UPLOADS" ]       || FAILED="$FAILED uploads($BEFORE_UPLOADS->$AFTER_UPLOADS)"
fi

if [ "$HEALTHY" = true ] && [ -z "$FAILED" ]; then
    echo ""
    echo "  --- containers ---"
    docker ps --format '  {{.Names}}  {{.Status}}'
    echo ""
    echo "================================================================"
    green "  DEPLOY COMPLETE"
    for repo in frontend backend; do
        echo "  $repo: $(git -C "$PROJECT_DIR/$repo" rev-parse --short HEAD)"
    done
    echo "  schema: $AFTER_REV"
    echo "  backup: $BACKUP_FILE"
    echo "  log:    $LOG_FILE"
    echo "================================================================"
    exit 0
fi

# --- failure -----------------------------------------------------------------
echo ""
if [ "$HEALTHY" != true ]; then
    red "Did not become healthy within 120s."
else
    red "Came up, but verification failed:$FAILED"
fi

echo ""
echo "--- last 40 log lines, captured BEFORE rollback ---"
docker logs --tail 40 "$BACKEND_CONTAINER"  2>&1 | sed 's/^/  [backend]  /' || true
docker logs --tail 40 "$FRONTEND_CONTAINER" 2>&1 | sed 's/^/  [frontend] /' || true
echo ""

if [ "$ROLLBACK_AVAILABLE" = true ]; then
    yellow "Rolling images back to :previous..."
    docker tag "$FRONTEND_IMAGE:previous" "$FRONTEND_IMAGE:latest"
    docker tag "$BACKEND_IMAGE:previous"  "$BACKEND_IMAGE:latest"
    # --force-recreate is required. Retagging moves the image ID but leaves the
    # reference unchanged, so Compose considers the running containers current
    # and silently does nothing — a rollback that looks like it ran and did not.
    docker compose up -d --force-recreate
    echo -n "Verifying rollback"
    ROLLED_BACK_OK=false
    for _ in $(seq 1 20); do
        if [ "$(http_code "$HEALTH_URL")" = "200" ] && [ "$(backend_health_code)" = "200" ]; then
            echo ""; green "Service restored on the previous images."
            ROLLED_BACK_OK=true
            break
        fi
        echo -n "."
        sleep 3
    done
    if [ "$ROLLED_BACK_OK" != true ]; then
        echo ""
        red "The rollback did NOT come back healthy. The site is down."
        echo "  site=$(http_code "$HEALTH_URL")  backend=$(backend_health_code)"
        echo "  Go to the July images — see below."
    fi
    echo ""
    yellow "The checkouts are still at the new commits. To match them to the images:"
    for repo in frontend backend; do
        echo "  git -C $PROJECT_DIR/$repo reset --hard ${BEFORE_SHA[$repo]}"
    done
else
    red "No :previous images to roll back to."
fi

echo ""
yellow "If :previous is also bad, the July build is the floor:"
echo "  docker tag $FRONTEND_IMAGE:$JULY_TAG $FRONTEND_IMAGE:latest"
echo "  docker tag $BACKEND_IMAGE:$JULY_TAG  $BACKEND_IMAGE:latest"
echo "  cd $OLD_TREE && docker compose up -d --force-recreate"
echo ""
yellow "NOTE: none of the above undoes a migration that already ran."
echo "To restore the database from the backup taken at the start of this run:"
echo "  docker exec -i $DB_CONTAINER pg_restore -U $DB_USER -d $DB_NAME --clean --if-exists < $BACKUP_FILE"
echo ""
echo "Log: $LOG_FILE"
exit 1
