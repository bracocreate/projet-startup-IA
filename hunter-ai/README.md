# HUNTER AI

Plateforme personnelle de **veille commerciale, sourcing mondial et intelligence de marché**.
Elle transforme des données commerciales vérifiables en opportunités d'achat‑revente documentées,
classées et explicables. **Elle n'achète jamais rien à votre place.**

> **État actuel : Phase 1 — socle technique.** L'application démarre, la base de données, l'API,
> l'interface, les paramètres et la page « Santé du système » fonctionnent. **Aucune donnée
> commerciale n'est encore collectée** : le tableau de bord affiche un état vide explicite.
> Voir [`docs/roadmap.md`](docs/roadmap.md).

---

## 1. Prérequis

| Outil | Version testée | Rôle |
|---|---|---|
| Docker Desktop (ou Docker Engine + Compose v2) | 29.x / Compose 5.x | Lance tout le projet |
| Git | 2.4x | Historique du code |
| *(optionnel, sans Docker)* Python | 3.13 | Backend |
| *(optionnel, sans Docker)* Node.js | 22 LTS | Frontend |
| *(optionnel, sans Docker)* PostgreSQL | 16 | Base de données |

Installer Docker Desktop : <https://docs.docker.com/get-docker/>

## 2. Installation (première fois)

Ouvrez un **terminal** (macOS : app « Terminal » ; Windows : « PowerShell » avec WSL recommandé),
placez‑vous dans le dossier du projet, puis :

```bash
cd hunter-ai
make env          # crée le fichier .env à partir de .env.example
```

Ouvrez ensuite `.env` dans un éditeur de texte et remplacez `POSTGRES_PASSWORD=change_me_local_only`
par un mot de passe de votre choix (par exemple généré avec `openssl rand -hex 24`).
**Ne partagez jamais ce fichier et ne collez jamais son contenu dans un chat.**

> Pas de `make` (Windows) ? Remplacez `make env` par `cp .env.example .env`, et `make up`
> par `docker compose up -d --build`. Toutes les commandes sont listées dans le `Makefile`.

## 3. Commandes

| Action | Commande |
|---|---|
| Démarrer | `make up` |
| Ouvrir l'application | <http://localhost:3000> |
| Documentation de l'API | <http://localhost:8000/api/docs> |
| Voir l'état des services | `make ps` |
| Voir les journaux | `make logs` |
| Arrêter (données conservées) | `make down` |
| Appliquer les migrations | `make migrate` *(fait automatiquement au démarrage)* |
| Sauvegarder la base | `make backup` → fichier dans `data/backups/` |
| Restaurer une sauvegarde | `make restore FILE=data/backups/hunter_AAAAMMJJ_HHMMSS.dump` |
| Lancer les tests | `make test` *(nécessite l'installation locale, voir §4)* |
| Lint + typage | `make lint` |
| Liste de toutes les commandes | `make help` |

Le premier `make up` télécharge les images et compile l'application : comptez quelques minutes.

## 4. Développement sans Docker (optionnel)

Avec PostgreSQL 16 installé localement, une base `hunter` et une base `hunter_test` appartenant
à l'utilisateur `hunter` :

```bash
make install                 # dépendances Python (backend/.venv) et Node (frontend/node_modules)
# dans .env : POSTGRES_HOST=localhost
make dev-backend             # terminal 1 → API sur http://localhost:8000
make dev-frontend            # terminal 2 → interface sur http://localhost:3000
make test                    # tests backend (sur la base hunter_test) + frontend
```

Les tests backend utilisent **exclusivement** la base `<POSTGRES_DB>_test` ; ils refusent de
s'exécuter sur une base dont le nom ne finit pas par `_test`.

## 5. Dépannage

| Symptôme | Cause probable | Solution |
|---|---|---|
| `POSTGRES_PASSWORD manquant dans .env` | `.env` absent | `make env`, puis éditez `.env` |
| `port is already allocated` (5432, 8000 ou 3000) | Un autre programme utilise le port | Arrêtez‑le, ou changez le port à gauche dans `docker-compose.yml` (ex. `"127.0.0.1:5433:5432"`) |
| Bandeau rouge « serveur injoignable » dans l'interface | Backend arrêté ou en erreur | `make ps` puis `make logs` |
| « Migrations : Attention » dans *Santé du système* | Base non à jour | `make migrate` |
| `password authentication failed` après changement du mot de passe | Le volume garde l'ancien mot de passe | Remettez l'ancien mot de passe, ou (⚠ efface les données) `docker compose down -v` puis `make up` |

## 6. Sécurité en bref

- Les secrets ne vivent que dans `.env` (ignoré par Git). `.env.example` n'en contient aucun.
- PostgreSQL, l'API et l'interface n'écoutent que sur `127.0.0.1` (pas d'accès depuis le réseau).
- Les journaux sont au format JSON et masquent mots de passe, jetons et clés.
- Toute modification d'état (ex. paramètres) est inscrite dans la table `audit_logs`.
- En production, les modifications exigent `API_ACCESS_TOKEN` (refus par défaut sinon).
- L'achat automatique est interdit, jusque dans la base (contrainte SQL).

## 7. Documentation

- [`CLAUDE.md`](CLAUDE.md) — règles de travail pour Claude Code
- [`docs/cahier-des-charges.md`](docs/cahier-des-charges.md) — spécification complète de référence
- [`docs/architecture.md`](docs/architecture.md) · [`docs/setup.md`](docs/setup.md) ·
  [`docs/connectors.md`](docs/connectors.md) · [`docs/data-policy.md`](docs/data-policy.md) ·
  [`docs/scoring.md`](docs/scoring.md) · [`docs/operations.md`](docs/operations.md) ·
  [`docs/roadmap.md`](docs/roadmap.md)
