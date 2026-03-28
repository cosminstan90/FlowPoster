#!/usr/bin/env bash
# deploy-pm2.sh — Deploy FlowPoster on CloudPanel VPS (PM2 + venv, no Docker)
#
# Usage:
#   ./deploy-pm2.sh              # deploy latest main branch
#   ./deploy-pm2.sh --skip-pull  # deploy from current working tree
#
# Requirements: Python 3.12, PM2, PostgreSQL running, Redis running, git
#
# NOTE: This replaces docker-compose. PostgreSQL and Redis run as system services.
#       FlowPoster API runs on port 8050, served via CloudPanel nginx reverse proxy.

set -euo pipefail

APP_DIR="/home/flowposter/app"
VENV="$APP_DIR/venv"
SKIP_PULL=false

for arg in "$@"; do
  case $arg in
    --skip-pull) SKIP_PULL=true ;;
    *) echo "Unknown argument: $arg"; exit 1 ;;
  esac
done

echo ""
echo "════════════════════════════════════════════"
echo "  FlowPoster — PM2 Deploy"
echo "  $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "════════════════════════════════════════════"
echo ""

cd "$APP_DIR"

# ── 1. Pull latest code ────────────────────────────────────────────────────────
if [ "$SKIP_PULL" = false ]; then
  echo "▶ Step 1/5 — Pulling latest code..."
  git pull --ff-only origin main
  echo "✓ Code updated: $(git log -1 --pretty='%h %s')"
else
  echo "▶ Step 1/5 — Skipping git pull (--skip-pull)"
fi
echo ""

# ── 2. Update Python dependencies ─────────────────────────────────────────────
echo "▶ Step 2/5 — Updating Python dependencies..."
source "$VENV/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
deactivate
echo "✓ Python dependencies updated"
echo ""

# ── 3. Run database migrations ────────────────────────────────────────────────
echo "▶ Step 3/5 — Running Alembic migrations..."
source "$VENV/bin/activate"
alembic upgrade head
deactivate
echo "✓ Database up to date"
echo ""

# ── 4. Rebuild frontend ────────────────────────────────────────────────────────
echo "▶ Step 4/5 — Building React frontend..."
cd "$APP_DIR/frontend"
npm ci --silent
npm run build
cd "$APP_DIR"
echo "✓ Frontend built → frontend/dist/"
echo ""

# ── 5. Reload PM2 processes ───────────────────────────────────────────────────
echo "▶ Step 5/5 — Reloading PM2 processes..."
pm2 reload flowposter-api --update-env
# Worker: restart (not reload) to ensure clean state after migrations
pm2 restart flowposter-worker --update-env
pm2 save
echo "✓ PM2 processes reloaded"
echo ""

# ── Health check ───────────────────────────────────────────────────────────────
echo "▶ Waiting for health check (up to 30s)..."
RETRIES=15
until curl -sf http://127.0.0.1:8050/health > /dev/null 2>&1; do
  RETRIES=$((RETRIES - 1))
  if [ $RETRIES -eq 0 ]; then
    echo "✗ Health check failed. Check: pm2 logs flowposter-api"
    exit 1
  fi
  sleep 2
done

echo ""
echo "════════════════════════════════════════════"
echo "  ✓ Deploy successful!"
echo "  Commit: $(git log -1 --pretty='%h %s')"
echo "  Time:   $(date '+%Y-%m-%d %H:%M:%S')"
echo "════════════════════════════════════════════"
echo ""
