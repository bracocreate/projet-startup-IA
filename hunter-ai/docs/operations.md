# Exploitation

## Sauvegarde
`make backup` crée `data/backups/hunter_AAAAMMJJ_HHMMSS.dump` (format `pg_dump --format=custom`).
Copiez régulièrement ces fichiers hors de la machine, idéalement sur un support chiffré.

## Restauration
`make restore FILE=data/backups/....dump`. Le script demande de taper `RESTAURER`, fait d'abord une
sauvegarde de sécurité de l'état actuel, arrête le backend, restaure, puis le redémarre.
Le couple `pg_dump`/`pg_restore --clean --if-exists` a été vérifié (aller‑retour d'une modification).

## Journaux
`make logs`. Format JSON une ligne par événement : `ts`, `level`, `logger`, `msg`, `request_id`,
`method`, `path`, `status`, `duration_ms`. Les secrets sont masqués (`***`).

## Santé
- `GET /api/v1/health` (utilisé par le healthcheck Docker) : 200 si la base répond, sinon 503.
- Page **Santé du système** dans l'interface : base, migrations, connecteurs, planificateur, Telegram.

## Migrations
Appliquées automatiquement au démarrage du conteneur backend (`alembic upgrade head`).
Créer une migration : `cd backend && .venv/bin/alembic revision --autogenerate -m "message"`,
**relire le fichier généré** (types ENUM, contraintes, données) puis tester l'aller‑retour.

## Ports
Tous liés à `127.0.0.1` : 3000 (interface), 8000 (API), 5432 (PostgreSQL). Ne jamais exposer
PostgreSQL à Internet ; le déploiement VPS (Phase 10) passera par un reverse proxy HTTPS.
