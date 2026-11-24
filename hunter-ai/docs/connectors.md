# Connecteurs et sources de données

**Aucun connecteur réel n'est actif.** Seul le connecteur DEMO (données fictives) est disponible. Ce document recense les pistes vérifiées le 24/11/2026 dans la
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

## Contrat de connecteur (implémenté en Phase 3)

`backend/app/connectors/base.py` définit le contrat `SourceConnector` :

| Méthode | Rôle |
|---|---|
| `health_check()` | La source répond-elle ? Une source en échec ne déclenche aucune recherche. |
| `get_capabilities()` | Méthode d'accès, recherche GTIN, résultats max., délai minimal entre appels, limites. |
| `search(SearchQuery)` | Renvoie des `RawOffer` (champs inconnus = `None`). |
| `fetch_offer(external_id)` | Relit une offre précise (revérification). |

Un connecteur **ne touche jamais à la base** : normalisation, déduplication et historique sont
communs (`collection_service`). Il est enregistré dans `connectors/registry.py`. Une source ne peut
collecter que si son statut est `active` (ou `degraded` / `error` pour une nouvelle tentative) :
`planned`, `needs_credentials`, `needs_approval`, `disabled` et `blocked_by_terms` sont refusés.

### Connecteur DEMO (`connectors/demo.py`)

- 6 offres **inventées** : marques fictives (« Alpha DEMO »…), titres préfixés `[DEMO]`, liens
  `example.com` (domaine réservé), GTIN de la plage GS1 « 2xx » (usage interne, jamais attribuée à
  un produit du commerce). Aucun accès réseau.
- Couvre volontairement les cas difficiles : même GTIN chez deux marchands, même référence avec
  une casse différente, devises USD/GBP sans taux (prix EUR « non déterminé »), livraison
  inconnue vs gratuite, rupture, disponibilité inconnue.
- Chargement / suppression : boutons de la vue d'ensemble, ou `POST /api/v1/demo/load` et
  `DELETE /api/v1/demo` (journalisés). La suppression retire tout ce qui est marqué `is_demo`.

### Connecteur eBay Browse API (implémenté, à activer avec vos clés)

Vérifié le 24/11/2026 dans la documentation officielle eBay :

| Point | Ce que dit eBay | Ce que fait HUNTER AI |
|---|---|---|
| Jeton | `POST /identity/v1/oauth2/token`, *client credentials*, portée `https://api.ebay.com/oauth/api_scope`, valable 7 200 s | Jeton mis en cache (marge de 2 min) |
| Recherche | `GET /buy/browse/v1/item_summary/search`, `sort=newlyListed`, `limit` ≤ 200, 10 000 résultats max | Annonces les plus récentes d'abord, prix fixe uniquement, livrables en France, place de marché `EBAY_FR` |
| Quota | 5 000 appels/jour par défaut (Browse) | Plafond configurable `EBAY_DAILY_CALL_BUDGET` (4 500), compté en base, refus au-delà |
| Accès production | « Buy APIs require an additional license » ; usage production « intended for eBay partners », candidature via eBay Partner Network, sans garantie | **Incertain tant que le test réel n'est pas fait.** Un refus 401/403 met la source en `needs_approval`, sans contournement |

Choix prudents : enchères exclues (prix non final) ; frais de livraison retenus seulement s'ils
sont fixes et dans la devise du prix, sinon « inconnus » ; disponibilité « à confirmer » (la
recherche ne donne pas le stock) ; **pseudonyme et notes du vendeur non enregistrés** ; lien public
de l'annonce, pas le lien d'affiliation.

**À relire avant usage intensif :** l'*eBay API License Agreement* (durée de conservation et
affichage des données eBay). HUNTER AI ne stocke que les champs nécessaires et revérifie les offres.

#### Mise en route (vous)
1. Créez un compte sur <https://developer.ebay.com> (gratuit), puis **Application Keys** →
   créez un *keyset* **Production**.
2. Ouvrez le fichier `.env` de HUNTER AI et renseignez `EBAY_CLIENT_ID` (App ID) et
   `EBAY_CLIENT_SECRET` (Cert ID). **Ne les collez jamais dans un chat.**
3. Redémarrez : `make restart`.
4. Dans **Sites et fournisseurs**, cliquez **Tester la connexion** :
   - « Test réel réussi » → la source passe `active`, le formulaire de collecte apparaît ;
   - « Accès … refusé par eBay » → statut `needs_approval` : il faut demander l'accès
     production aux Buy APIs via l'eBay Partner Network (gratuit, réponse sous ~10 jours ouvrés).
     En attendant, `EBAY_ENVIRONMENT=sandbox` permet de tester avec les données factices d'eBay.

#### Collecte automatique (n8n de votre homelab)
`POST /api/v1/sources/ebay/collect` avec l'en-tête `Authorization: Bearer <API_ACCESS_TOKEN>` et
un corps JSON `{"keywords": "polo ralph lauren", "max_price": 30, "limit": 50}`. Exemple de cadence :
10 recherches toutes les 5 minutes ≈ 2 900 appels/jour (sous le plafond de 4 500). Les alertes
ntfy sur les bonnes affaires arriveront avec le Price Radar (Phase 4).


### Connecteur AliExpress Affiliate API (implémenté, à activer avec vos clés)

Vérifié le 24/11/2026 (référence officielle de `aliexpress.affiliate.product.query` et règle de
signature, reproduite sur les deux exemples officiels — secret `helloworld` — dans les tests) :

| Point | Source officielle | HUNTER AI |
|---|---|---|
| Appel | `GET https://api-sg.aliexpress.com/sync?method=aliexpress.affiliate.product.query` | Idem |
| Signature | HMAC-SHA256 (clé = App Secret) des paramètres triés nom+valeur, hex majuscule ; horodatage en ms ; `sign_method=sha256` | Idem ; le secret n'est jamais envoyé |
| Paramètres | `keywords`, `page_size` 1–50, `target_currency`, `target_language`, `ship_to_country`, `tracking_id`… | EUR, FR, livraison France ; 50 max |
| Prix | `target_sale_price` (devise cible) ; « prix selon la politique fiscale du pays » | Prix EUR enregistré ; **TVA incluse probable mais à confirmer** dans le calculateur |
| Prix max. | `max_sale_price` documenté « unit cent » (ambigu) | **Non envoyé** : filtrage local |
| Livraison | `aliexpress.affiliate.product.shipping.get` (product_id, sku_id, ship_to_country, target_currency, target_sale_price, target_language, tax_rate → shipping_fee, délais, ship_from_country) | Frais réels pour les N premiers produits (`ALIEXPRESS_SHIPPING_LOOKUPS_PER_RUN`, 10 par défaut, 1 appel chacun) ; pays d'expédition enregistré ; échec → frais « inconnus » + avertissement, sans bloquer |
| Quota | Non publié | Plafond HUNTER AI `ALIEXPRESS_DAILY_CALL_BUDGET` (1 000/jour) ; chaque collecte réserve 1 + N appels avant de partir |

Liens : la fiche produit publique (`product_detail_url`), **jamais votre lien d'affiliation**
(acheter via son propre lien est en général interdit par les programmes d'affiliation).

**À relire :** l'accord du programme d'affiliation AliExpress, notamment l'usage des données de
l'API pour vos propres achats (l'API est conçue pour promouvoir des produits). Usage prévu ici :
lecture seule, faible volume, aucune republication.

#### Mise en route (vous)
1. Sur <https://openservice.aliexpress.com>, connectez-vous avec votre compte affilié, puis
   **App Management** → créez une application de type **Affiliate API** (validation par AliExpress
   possible).
2. Récupérez **App Key** et **App Secret**, et votre **Tracking ID** sur
   <https://portals.aliexpress.com> (facultatif pour la recherche).
3. Renseignez `ALIEXPRESS_APP_KEY`, `ALIEXPRESS_APP_SECRET` (et `ALIEXPRESS_TRACKING_ID`) dans
   `.env`, puis `make restart`. **Jamais dans un chat.**
4. **Sites et fournisseurs** → AliExpress → **Tester la connexion** (recherche « phone case »,
   3 produits). Succès → `active` ; « identifiants » → vérifier les clés ; « refusé » →
   l'application n'a pas encore l'autorisation Affiliate API.

**Hypothèse documentée :** `shipping_fee` n'indique pas sa devise ; il est demandé avec
`target_currency=EUR` et enregistré comme montant en euros.

**Écarté :** `sudheer-ranga/aliexpress-product-scraper` (navigateur automatisé avec module
« stealth » de contournement anti-robots et appel à une API interne `mtop`) — contraire à la
règle 4 du cahier des charges. Les mêmes informations (frais de port, détail, variantes) passent
par les méthodes officielles ci-dessus.
