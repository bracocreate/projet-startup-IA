# Architecture

## Choix structurants

| Décision | Choix | Raison |
|---|---|---|
| Forme | Monolithe modulaire | Un seul utilisateur, une équipe réduite ; découpage par moteurs (`app/engines/*`) prêt à être extrait si besoin. |
| Backend | FastAPI + Pydantic v2 | Validation stricte, OpenAPI auto (`/api/docs`). |
| Accès BDD | SQLAlchemy 2 **synchrone** + psycopg 3 | Plus simple à tester et déboguer ; FastAPI exécute les routes synchrones dans un pool de threads. Les connecteurs (I/O réseau) seront asynchrones (HTTPX) en Phase 3. |
| Migrations | Alembic, revues à la main | Jamais de `create_all` ; migration réversible testée (`test_migrations_downgrade_and_upgrade_roundtrip`). |
| Frontend | Next.js (App Router) + Tailwind | Le navigateur n'appelle que `/api/v1/*` sur le même domaine ; Next relaie vers le backend (*rewrites*) → pas de secret ni d'URL interne exposés, CORS non sollicité. |
| Files d'attente | **Aucune** pour l'instant | Redis/Celery seulement si la Phase 8 démontre le besoin (APScheduler + verrou PostgreSQL d'abord). |
| Authentification | Jeton `API_ACCESS_TOKEN` sur les routes de modification ; refus par défaut en production | Suffisant en local ; une vraie authentification (reverse proxy + session) est prévue en Phase 10. |

Écart à la structure indicative du cahier des charges : `frontend/app` (routes Next), `frontend/features`
(écrans), `frontend/components` (UI partagée), `frontend/lib` (client API, formats, navigation).
`backend/app/repositories` est créé mais vide : en Phase 1 les requêtes sont triviales et restent
dans les services ; il sera utilisé quand les requêtes métier (offres, historiques) apparaîtront.

## Flux d'une requête

```
Navigateur ──/api/v1/*──▶ Next.js (3000) ──rewrite──▶ FastAPI (8000) ──▶ PostgreSQL (5432)
                                                     │
                                                     └─ middleware : request_id + log JSON
```

## Modèle de données (Phase 1)

| Table | Rôle |
|---|---|
| `users` | Utilisateur unique `local` (créé à la première demande). |
| `user_settings` | Paramètres métier §2 (budget 100 €, 06:00 + 120 min, marques, marchés…). Contrainte `auto_purchase_allowed = false`. |
| `sources` | Registre des sources avec statuts `planned … blocked_by_terms`, méthode d'accès, `is_demo`. |
| `audit_logs` | Journal des actions modifiant un état (acteur, action, entité, détails JSON masqués). |

Les autres entités du §13 (produits, variantes, offres, observations, opportunités, lots…) seront
ajoutées par migrations successives à partir de la Phase 3.

## Endpoints disponibles

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/v1/health` | Santé (503 si la base est injoignable) |
| GET | `/api/v1/system/status` | Composants, révision de migration, éléments non implémentés |
| GET | `/api/v1/dashboard/summary` | Résumé du tableau de bord (état vide / DEMO / réel, fraîcheur, 3 classements) |
| GET | `/api/v1/settings` | Paramètres |
| PATCH | `/api/v1/settings` | Modification validée + journalisée |
| GET | `/api/v1/sources` | Liste des sources |
