# Feuille de route

| Phase | Contenu | État |
|---|---|---|
| 0 | Audit, architecture, `CLAUDE.md`, conventions | ✅ Fait |
| 1 | Socle : FastAPI, Next.js, PostgreSQL, Docker Compose, migrations, health checks, configuration, logs, tests | ✅ Fait et vérifié (natif + Docker) |
| 2 | Dashboard complet : listes, fiches, filtres persistants, données DEMO identifiées | ⏳ Partiel (navigation, accueil état vide, paramètres, santé) |
| 3 | Modèle produit/offre, contrat de connecteur, connecteur DEMO, premier connecteur réel (eBay Browse API recommandé), normalisation, déduplication, historique | À faire |
| 4 | Price Radar | À faire |
| 5 | Profit Engine (coût rendu, lots, ROI/marge, scénarios) | À faire |
| 6 | Market Intelligence (première source de tendances autorisée) | À faire |
| 7 | Discovery AI (propositions validées par l'utilisateur) | À faire |
| 8 | Planification 06:00–08:00, quotas, Telegram, rapport de session | À faire |
| 9 | Renforcement, saisie achats/reventes réels, calibration des scores | À faire |
| 10 | Déploiement VPS (HTTPS, pare‑feu, authentification, sauvegardes auto) | À faire |

## Vérification de la Phase 1 (24/11/2026)
Vérifié en natif **et** via Docker Compose (PostgreSQL 16, Python 3.13, Node 22) :
- `make lint` : Ruff, format, mypy, tsc — OK ; `make test` : 17 tests backend + 8 frontend — OK ;
- `docker compose up -d --build` : `db`, `backend` (healthy) et `frontend` démarrent ;
- migrations appliquées au démarrage (révision `0001`), `/api/v1/health` et `/api/v1/system/status` OK ;
- le frontend relaie l'API (`/api/v1/dashboard/summary` via le port 3000), état vide explicite affiché ;
- modification des paramètres journalisée dans `audit_logs` ; `auto_purchase_allowed` refusé par l'API ;
- `scripts/backup.sh` puis `scripts/restore.sh` (confirmation « RESTAURER ») : données restaurées ;
- interface sans erreur console, pas de défilement horizontal en largeur mobile (390 px).

Note : dans l'environnement cloud de développement, la construction des images a nécessité un
fichier d'override local (non versionné) pour faire confiance au certificat du proxy réseau.
Sur une machine personnelle, `make up` fonctionne sans cet ajustement.

## Prochaine étape proposée
Phase 3 : créer les tables `products`, `product_variants`, `merchants`, `offers`,
`offer_observations`, le contrat `SourceConnector`, un connecteur DEMO, puis demander votre feu
vert avant d'activer eBay Browse API (création d'un compte développeur eBay gratuit).
