# HUNTER AI — commandes usuelles. Lancer depuis le dossier racine du projet.
# Les cibles « docker » utilisent Docker Compose ; les cibles « dev-* » tournent sans Docker.

COMPOSE := docker compose
BACKEND := backend
FRONTEND := frontend
PY := $(BACKEND)/.venv/bin

.PHONY: help env up down restart ps logs migrate backup restore \
        install install-backend install-frontend test test-backend test-frontend \
        lint lint-backend lint-frontend dev-backend dev-frontend

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

env: ## Crée .env à partir de .env.example (sans écraser)
	@test -f .env && echo ".env existe déjà (non modifié)" || (cp .env.example .env && echo ".env créé : modifiez POSTGRES_PASSWORD")

# --- Docker ---
up: ## Construit et démarre base + backend + frontend
	$(COMPOSE) up -d --build

down: ## Arrête les services (les données sont conservées)
	$(COMPOSE) down

restart: down up ## Redémarre

ps: ## État des services
	$(COMPOSE) ps

logs: ## Journaux en continu (Ctrl+C pour quitter)
	$(COMPOSE) logs -f --tail=100

migrate: ## Applique les migrations dans le conteneur backend
	$(COMPOSE) exec backend alembic upgrade head

backup: ## Sauvegarde la base dans data/backups/
	./scripts/backup.sh

restore: ## Restaure une sauvegarde : make restore FILE=data/backups/xxx.dump
	./scripts/restore.sh "$(FILE)"

# --- Développement local sans Docker ---
install: install-backend install-frontend ## Installe les dépendances

install-backend:
	cd $(BACKEND) && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

install-frontend:
	cd $(FRONTEND) && npm ci

dev-backend: ## Lance l'API en local (port 8000)
	cd $(BACKEND) && .venv/bin/alembic upgrade head && .venv/bin/uvicorn app.main:app --reload --port 8000

dev-frontend: ## Lance l'interface en local (port 3000)
	cd $(FRONTEND) && BACKEND_URL=http://localhost:8000 npm run dev

test: test-backend test-frontend ## Lance tous les tests

test-backend:
	cd $(BACKEND) && .venv/bin/pytest

test-frontend:
	cd $(FRONTEND) && npm test

lint: lint-backend lint-frontend ## Lint + typage

lint-backend:
	cd $(BACKEND) && .venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy app

lint-frontend:
	cd $(FRONTEND) && npm run lint
