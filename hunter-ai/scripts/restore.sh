#!/usr/bin/env bash
# Restaure une sauvegarde créée par backup.sh. OPÉRATION DESTRUCTIVE : remplace les données actuelles.
# Usage : ./scripts/restore.sh data/backups/hunter_YYYYMMDD_HHMMSS.dump
set -euo pipefail
cd "$(dirname "$0")/.."

file="${1:-}"
if [ -z "$file" ] || [ ! -f "$file" ]; then
  echo "Fichier de sauvegarde introuvable : '${file}'" >&2
  echo "Usage : make restore FILE=data/backups/hunter_....dump" >&2
  exit 1
fi

# shellcheck disable=SC1091
set -a; [ -f .env ] && . ./.env; set +a
: "${POSTGRES_USER:?POSTGRES_USER manquant (.env)}"
: "${POSTGRES_DB:=hunter}"

echo "ATTENTION : les données actuelles de la base '$POSTGRES_DB' vont être remplacées par $file."
read -r -p "Tapez RESTAURER pour confirmer : " answer
[ "$answer" = "RESTAURER" ] || { echo "Annulé."; exit 1; }

echo "Sauvegarde de sécurité de l'état actuel…"
./scripts/backup.sh

docker compose stop backend
docker compose exec -T db pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner < "$file"
docker compose start backend
echo "Restauration terminée. Vérifiez : http://localhost:3000/sante"
