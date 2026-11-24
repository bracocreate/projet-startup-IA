#!/usr/bin/env bash
# Sauvegarde la base PostgreSQL (format custom pg_dump) dans data/backups/.
# Usage : ./scripts/backup.sh
set -euo pipefail
cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
set -a; [ -f .env ] && . ./.env; set +a
: "${POSTGRES_USER:?POSTGRES_USER manquant (.env)}"
: "${POSTGRES_DB:=hunter}"

mkdir -p data/backups
out="data/backups/hunter_$(date +%Y%m%d_%H%M%S).dump"

docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner > "$out"
size=$(du -h "$out" | cut -f1)
echo "Sauvegarde créée : $out ($size)"
echo "Conseil : copiez ce fichier hors de l'ordinateur (disque externe, stockage chiffré)."
