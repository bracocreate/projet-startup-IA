# Connecteurs et sources de données

**Aucun connecteur n'est actif.** Ce document recense les pistes vérifiées le 24/11/2026 dans la
documentation officielle. Rien ici n'autorise une collecte : chaque source doit encore passer par
la validation des conditions, des coûts et un test réel (statut `active` uniquement après ce test).

## Pistes prioritaires (accès officiel)

| Source | Méthode | Ce que ça apporte | Limites / points à vérifier | Coût |
|---|---|---|---|---|
| **eBay Browse API** (`/buy/browse/v1/item_summary/search`) | API officielle (OAuth app) | Offres actives : recherche par mots‑clés, GTIN, catégorie, filtres prix/vendeur | 10 000 résultats max par recherche ; `limit` ≤ 200 ; quotas par application ; CGU eBay Developers | Gratuit (compte développeur) |
| **eBay Marketplace Insights API** | API *Limited Release* | Historique des **ventes conclues** (idéal pour les comparables de revente) | Réservée aux partenaires validés par eBay : ne pas compter dessus | Sur demande |
| **Amazon Creators API** | API officielle (programme Partenaires) | Catalogue, offres, prix Amazon | **PA‑API 5 est dépréciée** et renvoie 403 ; utiliser uniquement Creators API. Nécessite un compte Partenaires actif et respecte des conditions d'usage strictes | Gratuit sous conditions d'affiliation |
| **Keepa API** | Fournisseur sous licence | Historiques de prix Amazon complets, deals, best‑sellers ; serveur MCP officiel | Abonnement mensuel à jetons ; vérifier le droit de stockage des données | **Payant** |
| **Awin** (flux produits éditeur) | Flux d'affiliation autorisé | Catalogues complets de marchands affiliés (ex. programme adidas FR) | Inscription éditeur + acceptation par chaque annonceur ; clé de flux à garder dans `.env` | Gratuit (commission sur ventes) |
| **Google Trends API (alpha)** | API officielle | Volumes de recherche normalisés, séries temporelles, géographie | Accès alpha sur candidature, délais de réponse longs signalés | Gratuit (si accepté) |
| **Telegram Bot API** | API officielle | Notifications (Phase 8) | Jeton de bot dans `.env` uniquement | Gratuit |

## Bloquées par principe

| Source | Statut | Raison |
|---|---|---|
| Vinted | `blocked_by_terms` | Interdiction de scraping et d'automatisation de compte (règle 5). Saisie manuelle de comparables uniquement. |
| Google Search (scraping) | `blocked_by_terms` | Interdit par les CGU ; utiliser une API de recherche autorisée. |

## Outils évalués pendant la recherche

- **Firecrawl (connecté à votre compte Claude)** : utile pour la *recherche documentaire* (trouver
  et lire la doc officielle d'une API, Discovery AI en Phase 7). Son catalogue « Alexandria »
  propose aussi des extracteurs de pages marchandes (ex. offres Amazon.com.br, paliers de prix
  Alibaba). **Ces extracteurs lisent des pages publiques : ils ne valent pas autorisation.** Ils ne
  pourront être utilisés pour une source qu'après vérification de ses CGU, et seront alors
  déclarés `permitted_automation` avec la justification dans `terms_notes`.
- **Connecteur Amazon Selling Partner** (disponible dans l'annuaire Claude, connexion incomplète
  sur votre compte) : réservé aux **vendeurs** Amazon (votre propre compte vendeur). Pertinent plus
  tard pour la revente sur Amazon, pas pour le sourcing.
- **Keepa MCP** : alternative à une intégration directe si vous prenez un abonnement Keepa.

## Contrat de connecteur (Phase 3)

Le contrat `SourceConnector` (`health_check`, `search`, `fetch_offer`, `get_capabilities`) sera
implémenté dans `backend/app/connectors/` avec un connecteur de démonstration marqué `DEMO`, puis
un premier connecteur réel (recommandation : **eBay Browse API**, gratuit et documenté).
