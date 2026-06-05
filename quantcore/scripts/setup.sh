#!/usr/bin/env bash
set -euo pipefail

echo "=== QuantCore AI — Setup ==="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker required but not found"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3.11+ required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js 20+ required"; exit 1; }

cd "$(dirname "$0")/.."

# Backend environment
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  echo "✓ Created backend/.env — Fill in your API keys before starting live trading"
fi

# Start infrastructure
echo "==> Starting Docker services…"
docker compose up -d postgres redis

echo "==> Waiting for PostgreSQL…"
until docker compose exec postgres pg_isready -U quantcore 2>/dev/null; do sleep 1; done

# Run migrations
echo "==> Running database migrations…"
cd backend
pip install alembic >/dev/null 2>&1 || true
alembic upgrade head 2>/dev/null || echo "  (alembic not configured yet — run: cd backend && alembic init migrations)"
cd ..

# Frontend deps
echo "==> Installing frontend dependencies…"
cd frontend
npm install >/dev/null 2>&1
cd ..

echo ""
echo "=== Setup complete ==="
echo ""
echo "Start the full stack:"
echo "  docker compose up"
echo ""
echo "Or start services individually:"
echo "  Backend:  cd backend && uvicorn app.main:socket_app --reload --loop uvloop"
echo "  Frontend: cd frontend && npm run dev"
echo "  Celery:   cd backend && celery -A app.tasks.celery_app worker -l info"
echo ""
echo "Default URLs:"
echo "  API:       http://localhost:8000"
echo "  Dashboard: http://localhost:5173"
echo "  API docs:  http://localhost:8000/docs"
echo "  Grafana:   http://localhost:3001 (admin / quantcore)"
echo ""
echo "⚠️  IMPORTANT: Paper trade all strategies for ≥30 days before going live."
echo "⚠️  Run ≥1,000 Monte Carlo simulations before activating any strategy live."
