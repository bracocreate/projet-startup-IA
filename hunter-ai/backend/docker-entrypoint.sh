#!/bin/sh
set -e
echo "[hunter] Application des migrations…"
alembic upgrade head
echo "[hunter] Démarrage de l'API sur :8000"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log
