#!/bin/bash
# FlowPoster — deploy script
# Usage: bash deploy.sh
# Run from /opt/flowposter on the server after git pull

set -e

APP_DIR="/opt/flowposter"
cd "$APP_DIR"

echo "==> Pulling latest code..."
git pull origin main

echo "==> Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt --quiet

echo "==> Running database migrations..."
alembic upgrade head

echo "==> Building frontend..."
cd frontend
npm install --silent
npm run build
cd ..

echo "==> Restarting services..."
systemctl restart flowposter-api
systemctl restart flowposter-worker

echo ""
echo "Done. Status:"
systemctl is-active flowposter-api
systemctl is-active flowposter-worker
