# CLAUDE.md — règles de travail HUNTER AI

Référence complète : `docs/cahier-des-charges.md` (à relire avant tout changement important).

## Le produit en une phrase
Plateforme personnelle (francophone, EUR, `Europe/Paris`) de veille commerciale qui transforme des
données commerciales **vérifiables** en opportunités d'achat‑revente documentées, classées et explicables.

## Règles impératives (non négociables)
1. Ne jamais prétendre qu'une fonctionnalité marche si elle n'est pas implémentée **et testée**.
2. Ne jamais fabriquer prix, stocks, ventes, tendances, fournisseurs, liens ou résultats.
   Toute donnée de démonstration est marquée `DEMO` (champ `is_demo=true` + badge visuel).
3. Ne pas inventer d'API/paramètre/connecteur : vérifier la doc officielle, consigner les limites dans `docs/connectors.md`.
4. Respecter CGU, quotas, robots, lois. Aucun contournement de CAPTCHA, auth, paywall, anti‑bot, géo‑restriction.
5. **Vinted : aucun scraping, aucune automatisation de compte.** Saisie manuelle ou fournisseur licencié uniquement.
6. Aucun achat, paiement, commande ou message vendeur automatique. Le bouton « Acheter » ouvre seulement le site marchand.
7. Aucun secret dans le code, Git, les logs ou le frontend. Secrets → `.env` local (ignoré par Git).
8. Toute action externe : explicitement autorisée, journalisée (`audit_logs`), réversible si possible.
9. Étapes verticales : chaque étape exécutable et testée avant la suivante.
10. Avant opération destructive, migration risquée, dépense payante ou activation d'un connecteur externe : expliquer l'impact et demander confirmation.
11. Ne jamais demander de coller un secret dans le chat.
12. Information manquante → valeur par défaut prudente, documentée, configurable.

## Règles métier clés
- Distinguer Produit / Variante / Offre / Marchand / Source / Observation de prix / Signal / Comparable / Opportunité / Lot / Décision.
- Pas de fusion de produits sur simple ressemblance de titre (GTIN/EAN/réf. fabricant + confiance).
- Traçabilité : source, URL, date UTC de collecte, pays, devise, méthode d'obtention, dernière vérification, confiance.
- Pas de fausse précision : inconnu → « non déterminé » ou fourchette. Jamais de valeur inventée pour compléter un calcul.
- Prix affiché ≠ prix payé ≠ prix de vente observé ≠ prix réalisé ; bénéfice estimé ≠ bénéfice réel.
- Scores séparés et déterministes (`deal_score`, `trend_score`, `source_trust_score`, `data_confidence_score`,
  `risk_score`, `resale_liquidity_score`). Un LLM n'invente jamais un score ni un calcul financier.
- Risques conformité/contrefaçon/sécurité/fraude = filtres bloquants ou pénalités explicites, jamais compensés par la marge.
- Un connecteur n'est `active` qu'après un test réel autorisé et documenté.
- « Prix inhabituellement bas à vérifier », jamais « erreur de prix » sans preuve.

## Stack
- Backend : Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL 16, psycopg 3, pytest, Ruff, mypy.
- Frontend : Next.js (App Router), React, TypeScript, Tailwind CSS, Vitest + Testing Library.
- Infra : Docker Compose, Makefile, scripts de sauvegarde.
- Monolithe modulaire. Pas de Redis/Celery tant que le besoin n'est pas démontré.

## Conventions
- Code et identifiants en anglais ; interface, messages utilisateur et docs en français.
- UUID comme identifiants publics, timestamps `timestamptz` en UTC.
- API versionnée `/api/v1`, schémas Pydantic, erreurs JSON `{"detail": ...}`.
- Toute route qui modifie un état écrit une entrée `audit_logs`.
- Toute modification de schéma passe par une migration Alembic revue (jamais `create_all` en prod).

## À chaque session
1. Lire ce fichier, le README et les docs concernées.
2. `git status` : vérifier les changements non commités.
3. Annoncer brièvement le plan ; travail cohérent et limité.
4. Lancer : `make lint`, `make test` (backend + frontend).
5. Résumer : fichiers modifiés, commandes lancées, résultats, limites restantes.

## Commandes
Voir `README.md` (section « Commandes ») et `Makefile`.

## État d'avancement
Voir `docs/roadmap.md`. Phase courante : **Phase 1 — socle fonctionnel**.
