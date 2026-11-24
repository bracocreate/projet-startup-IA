# Installation détaillée

Le parcours rapide est dans le [README](../README.md). Ce document détaille chaque étape.

## 1. Récupérer le projet
Décompressez l'archive `hunter-ai.zip` dans un dossier de travail (ex. `~/Projets/hunter-ai`).
Le dépôt Git est déjà initialisé avec un premier commit : `git log` pour le voir.

## 2. Configurer `.env`
```bash
cd ~/Projets/hunter-ai
cp .env.example .env
```
Variables :

| Variable | Défaut | Description |
|---|---|---|
| `APP_ENV` | `development` | `production` impose `API_ACCESS_TOKEN` pour toute modification |
| `LOG_LEVEL` | `INFO` | `DEBUG` pour plus de détails |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `hunter` / *à changer* / `hunter` | Identifiants de la base |
| `POSTGRES_HOST` | `db` | `db` dans Docker, `localhost` sans Docker |
| `CORS_ORIGINS` | `http://localhost:3000` | Origines autorisées |
| `API_ACCESS_TOKEN` | *(vide)* | Jeton Bearer des routes de modification |
| `STALE_AFTER_HOURS` | `24` | Seuil « données périmées » |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | *(vide)* | Phase 8 |

## 3. Démarrer
```bash
make up        # ou : docker compose up -d --build
make ps        # les 3 services doivent être « running » / « healthy »
```
Ouvrez <http://localhost:3000>. La page d'accueil indique « Aucune donnée collectée pour
l'instant » : c'est le comportement attendu en Phase 1.

## 4. Vérifier
- <http://localhost:3000/sante> : Base de données **OK**, Migrations **OK**.
- <http://localhost:8000/api/v1/health> : `{"status":"ok", ...}`.
