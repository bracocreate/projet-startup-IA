# HUNTER AI --- Cahier des charges maître et prompt de développement

**Version : 1.0 --- 21 novembre 2026**\
**Langue de l'application : français**\
**Nom du produit : HUNTER AI**\
**Nature : plateforme de sourcing mondial, veille commerciale et
intelligence de marché**

------------------------------------------------------------------------

# Instructions à Claude Code

Tu interviens comme **architecte logiciel principal, ingénieur backend
et frontend, ingénieur data, spécialiste de l'automatisation et
responsable qualité** du projet HUNTER AI.

Ta mission est de construire une application réellement exploitable,
maintenable, sécurisée et évolutive. Ne produis pas une simple maquette,
un prototype visuel trompeur ou un ensemble de scripts jetables.

Ce document constitue le cahier des charges de référence. Lis-le
intégralement avant toute modification. Si un dépôt existe déjà,
inspecte-le avant de modifier quoi que ce soit. Préserve le travail
existant et propose les migrations nécessaires plutôt que de réécrire
arbitrairement le projet.

## Règles impératives de travail

1.  **Ne prétends jamais qu'une fonctionnalité fonctionne si elle n'a
    pas été implémentée et testée.**
2.  Ne fabrique jamais de prix, de disponibilité, de ventes, de
    tendances, de fournisseurs, de liens ou de résultats de recherche.
    Les données de démonstration doivent être explicitement marquées
    `DEMO`.
3.  N'invente pas d'API, de schéma, de paramètre, de connecteur ou de
    disponibilité commerciale. Vérifie la documentation officielle et
    consigne les limites.
4.  Respecte les conditions d'utilisation, les droits d'accès, les
    limites de débit, les règles robots applicables et les lois
    pertinentes. N'essaie pas de contourner CAPTCHA, authentification,
    paywalls, protections anti-bot, restrictions géographiques ou autres
    mesures d'accès.
5.  N'extrais pas les données d'une plateforme en violation de ses
    conditions. En particulier, ne réalise pas de scraping automatisé de
    Vinted et n'automatise pas les actions sur un compte Vinted. Utilise
    uniquement des données autorisées, des fournisseurs licenciés ou des
    saisies manuelles.
6.  Aucun achat, paiement, commande, message à un vendeur ou engagement
    commercial ne doit être exécuté automatiquement. L'application
    prépare les informations et ouvre le site marchand ; l'utilisateur
    prend la décision.
7.  Ne stocke jamais de mots de passe, cookies de session, clés API ou
    secrets dans le code, Git, les logs ou le frontend.
8.  Toute action externe doit être explicitement autorisée, journalisée
    et réversible lorsque cela est possible.
9.  Construis par étapes verticales fonctionnelles. Chaque étape doit
    être exécutable et testée avant la suivante.
10. Avant une opération destructive, une migration risquée, une dépense
    payante ou l'activation d'un connecteur externe, explique l'impact
    et demande confirmation.
11. Ne demande pas à l'utilisateur de coller des secrets dans le chat.
    Fais-les saisir dans un fichier `.env` local ou un gestionnaire de
    secrets.
12. Si une information manque, choisis une valeur par défaut prudente,
    documente-la et rends-la configurable. Pose une question uniquement
    si elle bloque réellement une décision technique.

À chaque session : - commence par lire `CLAUDE.md`, le README et les
documents pertinents ; - vérifie l'état Git et les changements non
commités ; - annonce brièvement le plan ; - effectue un travail cohérent
et limité ; - lance les tests, le lint et les vérifications pertinents
; - résume les fichiers modifiés, les commandes exécutées, les résultats
et les limites restantes.

------------------------------------------------------------------------

# 1. Vision et objectif produit

HUNTER AI est une plateforme personnelle de **veille commerciale et de
détection d'opportunités d'achat-revente à l'échelle internationale**.

L'application doit aider l'utilisateur à découvrir : - des produits
proposés à un prix inhabituellement bas ; - des promotions et
déstockages réellement intéressants ; - des écarts de prix entre
marchands ou marchés ; - des lots et opportunités de gros ; - des
produits sous-évalués même sans réduction affichée ; - des produits dont
la demande ou la popularité progresse ; - de nouvelles marques,
catégories, niches et tendances ; - de nouveaux marchands, fournisseurs
et sources de données à examiner.

Le logiciel n'est pas limité à Vinted. Vinted peut être un canal de
revente envisagé, mais HUNTER AI ne publie aucune annonce et
n'automatise aucune action sur Vinted. L'utilisateur peut aussi
envisager d'autres marketplaces, la revente locale, la vente en lots ou
d'autres canaux.

Le périmètre produit est volontairement large : toutes les catégories de
biens légaux et commercialisables, sans restriction de secteur. Les
produits réglementés, dangereux, contrefaits, interdits ou dont la
conformité ne peut pas être raisonnablement vérifiée doivent être
bloqués ou placés en revue renforcée.

## Objectif central

Transformer des informations commerciales dispersées en **opportunités
documentées, comparables, classées et vérifiables**, sans présenter une
estimation comme une certitude.

## Utilisateur cible et expérience

-   Un utilisateur principal, francophone, basé en France.
-   Devise d'affichage principale : EUR.
-   Fuseau horaire par défaut : `Europe/Paris`, configurable.
-   Interface responsive, utilisable sur ordinateur et mobile.
-   Utilisateur qui souhaite valider lui-même chaque achat.
-   Niveau technique de l'utilisateur potentiellement débutant :
    installation, sauvegardes et erreurs doivent être expliquées
    clairement.

------------------------------------------------------------------------

# 2. Paramètres métier initiaux

Ces valeurs doivent être modifiables dans les paramètres de
l'application.

  -----------------------------------------------------------------------
  Paramètre                           Valeur initiale
  ----------------------------------- -----------------------------------
  Nom                                 HUNTER AI

  Langue                              Français

  Devise de référence                 EUR

  Fuseau horaire                      Europe/Paris

  Budget maximal indicatif par        100 €
  article                             

  Budget maximal d'un lot             Non défini au départ, configurable

  Durée de collecte quotidienne       2 heures

  Horaire initial                     06:00--08:00, heure locale

  Marchés                             France, Europe, Chine/Asie,
                                      États-Unis, Royaume-Uni et autres
                                      pays pertinents

  Catégories                          Toutes catégories légales, sous
                                      réserve des filtres de risque

  Marques prioritaires initiales      Nike, Adidas, Ralph Lauren,
                                      Lacoste, The North Face, Tommy
                                      Hilfiger

  Modèle d'achat                      À l'unité et en lots

  Notifications                       Tableau de bord et Telegram
                                      optionnel

  Achat automatique                   Interdit

  Découverte de nouvelles sources     Propositions automatiques,
                                      activation après validation

  Actualisation à l'ouverture         Afficher immédiatement le cache,
                                      puis actualiser en arrière-plan
  -----------------------------------------------------------------------

Le budget de 100 € est une valeur initiale par article, pas une limite
universelle. Pour les lots, distinguer le budget global, le nombre
d'unités, le coût rendu par unité et le taux de produits invendables ou
défectueux.

------------------------------------------------------------------------

# 3. Principes fonctionnels fondamentaux

## 3.1 Distinguer les entités

Le modèle doit distinguer clairement : - **Produit** : identité
générique d'un article ou modèle. - **Variante** : taille, couleur,
capacité, version, conditionnement ou référence. - **Offre** :
proposition commerciale d'un marchand à un instant donné. - **Marchand**
: vendeur ou fournisseur. - **Source** : site, API, flux, newsletter ou
fournisseur de données. - **Observation de prix** : prix constaté à une
date et dans un contexte précis. - **Signal de tendance** : mesure de
popularité, recherche ou intérêt. - **Comparable de revente** : donnée
permettant d'estimer un prix de revente. - **Opportunité** : analyse
combinant une offre, un coût rendu, des comparables, des risques et un
score. - **Lot** : ensemble d'unités achetées ensemble, avec répartition
des coûts. - **Décision utilisateur** : favori, ignoré, à vérifier,
acheté, vendu ou clôturé.

Ne fusionne pas deux produits uniquement parce que leurs titres se
ressemblent. Utilise les GTIN/EAN/UPC, références fabricant, marque,
modèle, variantes et similarité textuelle comme indices avec niveau de
confiance.

## 3.2 Traçabilité des données

Chaque donnée externe doit conserver autant que possible : - la source
et l'identifiant du connecteur ; - l'URL de référence ; - la date et
l'heure de collecte UTC ; - le pays et la devise d'origine ; - la
méthode d'obtention (API, flux, saisie manuelle, fournisseur licencié,
etc.) ; - la date de dernière vérification ; - le statut de
disponibilité ; - le niveau de confiance ; - les conditions ou limites
d'utilisation pertinentes.

Ne présente jamais une information ancienne comme actuelle. Affiche la
fraîcheur de chaque offre.

## 3.3 Pas de fausse précision

Si le prix de revente, les frais, la TVA, les droits de douane ou la
disponibilité sont inconnus, affiche une fourchette ou « non déterminé
». N'invente pas de valeur pour compléter un calcul.

Sépare toujours : - prix affiché ; - prix réellement payé, s'il est
connu ; - prix de vente observé ; - prix de vente réalisé ; - bénéfice
estimé ; - bénéfice réel.

------------------------------------------------------------------------

# 4. Sources et collecte mondiale

## 4.1 Familles de sources à prévoir

Construire une architecture de connecteurs indépendante de chaque
fournisseur.

Familles : 1. Marketplaces généralistes. 2. Marketplaces B2B et
grossistes. 3. Boutiques officielles de marques. 4. Déstockage, outlets
et ventes privées. 5. Comparateurs de prix. 6. Flux de catalogues et
programmes d'affiliation autorisés. 7. API commerciales officielles. 8.
Newsletters et alertes auxquelles l'utilisateur s'est abonné. 9. Sources
de tendances et études de marché. 10. Fournisseurs de données tiers sous
licence. 11. Saisie manuelle et import CSV. 12. Sources locales ou
régionales pertinentes.

Exemples de sites à évaluer, sans supposer qu'un accès automatisé est
disponible : - Amazon ; - eBay ; - AliExpress ; - Alibaba ; - 1688 ; -
DHgate ; - Temu ; - Banggood ; - Nike ; - Adidas ; - Zalando ; - ABOUT
YOU ; - Veepee ; - Showroomprivé ; - Spartoo ; - Sarenza ; - La Redoute
; - Private Sport Shop ; - Cdiscount ; - boutiques outlet officielles
; - autres marchands découverts pendant la veille.

La présence d'un nom dans cette liste ne vaut pas autorisation de
collecte. Pour chaque source, vérifier les conditions, les API et les
flux disponibles.

## 4.2 Contrat de connecteur

Définir une interface Python commune, par exemple :

``` python
class SourceConnector(Protocol):
    source_id: str

    async def health_check(self) -> SourceHealth:
        ...

    async def search(self, query: SearchQuery) -> list[RawOffer]:
        ...

    async def fetch_offer(self, external_id: str) -> RawOffer | None:
        ...

    async def get_capabilities(self) -> SourceCapabilities:
        ...
```

Adapter précisément ce contrat à l'architecture retenue. Tous les
connecteurs doivent : - déclarer leurs capacités ; - déclarer leur
méthode d'accès et leurs limites ; - appliquer les quotas et délais ; -
gérer les erreurs et les réponses partielles ; - normaliser les devises
et dates ; - fournir les URLs sources ; - éviter les doublons ; -
pouvoir être désactivés sans casser l'application.

Prévoir les statuts : - `planned` ; - `needs_credentials` ; -
`needs_approval` ; - `active` ; - `degraded` ; - `disabled` ; -
`blocked_by_terms` ; - `error`.

Ne jamais marquer un connecteur `active` tant qu'un test réel n'a pas
confirmé son fonctionnement.

## 4.3 Politique de collecte

Priorité d'accès : 1. API officielle documentée. 2. Flux produit ou flux
d'affiliation autorisé. 3. Fournisseur de données sous contrat/licence.
4. Newsletter ou alertes reçues légalement. 5. Import manuel CSV/URL. 6.
Consultation automatisée uniquement si explicitement permise par les
conditions applicables.

Respecter : - conditions d'utilisation ; - limites de débit ; -
authentification autorisée ; - restrictions territoriales ; - droits de
propriété intellectuelle ; - RGPD et règles applicables ; - exigences
d'attribution et de conservation des données.

Ne pas : - contourner CAPTCHA ou anti-bot ; - simuler des comptes ou
sessions ; - utiliser des cookies privés non autorisés ; - contourner
des paywalls ; - multiplier les comptes pour éviter les limites ; -
collecter des données personnelles non nécessaires ; - scraper Google
Search ou des plateformes sociales en violation de leurs conditions.

------------------------------------------------------------------------

# 5. Moteur Global Scout

Le moteur Global Scout recherche des offres dans les sources activées.

Fonctions : - recherche par mots-clés ; - recherche par marque, modèle
et référence ; - recherche par catégorie ; - recherche par pays et
région ; - recherche par fourchette de prix ; - recherche de lots ; -
recherche de promotions ; - recherche de nouveaux produits ; -
surveillance de listes de suivi ; - détection des nouvelles offres ; -
comparaison entre vendeurs.

Prévoir des requêtes multilingues. Une recherche française peut générer
des variantes anglaises, allemandes, espagnoles, italiennes,
néerlandaises ou chinoises translittérées lorsque cela améliore la
couverture. Conserver la requête originale et les traductions utilisées.

Ne lance pas toutes les combinaisons de mots-clés sans limite. Utilise
des quotas, priorités et budgets de requêtes configurables.

## Découverte de fournisseurs et lots

Pour les offres B2B : - quantité minimale de commande ; - prix par
palier ; - frais d'échantillon ; - frais de transport ; - délai estimé
; - conditions de paiement ; - Incoterm si disponible ; - pays
d'expédition ; - identité du fournisseur et éléments de réputation ; -
documents de conformité disponibles ; - coût rendu estimé par unité.

Ne présume pas qu'un prix fournisseur est un prix final livré en France.

------------------------------------------------------------------------

# 6. Moteur Price Radar

Détecter plusieurs familles d'opportunités :

1.  Promotion réelle.
2.  Prix inhabituellement bas.
3.  Baisse récente.
4.  Écart entre marchands.
5.  Prix sous la médiane historique.
6.  Produit sous-évalué sans réduction.
7.  Liquidation ou déstockage.
8.  Lot intéressant.
9.  Prix d'appel ou offre conditionnelle.
10. Produit dont le prix varie fortement.

## Historique et référence

Pour chaque produit/variante, conserver les observations. Calculer,
lorsque l'historique est suffisant : - minimum observé ; - maximum
observé ; - médiane ; - moyenne, avec prudence ; - percentile ; -
variation sur 7, 30, 90 et 180 jours lorsque disponible ; - nombre
d'observations ; - ancienneté de l'historique.

Ne qualifie pas un prix d'« erreur de prix » sans preuve. Utilise plutôt
« prix inhabituellement bas à vérifier ».

Repérer les faux prix barrés et les réductions calculées à partir d'un
prix de référence non fiable. Une remise affichée ne doit jamais être la
seule base du score.

## Disponibilité

La disponibilité doit être datée. Si elle n'a pas été vérifiée
récemment, afficher « disponibilité à confirmer ».

------------------------------------------------------------------------

# 7. Market Intelligence --- analyse du marché et des tendances

Créer un moteur d'analyse de signaux, pas un générateur de prédictions
non vérifiées.

## 7.1 Sources possibles

Selon les API, licences et conditions disponibles : - Google Trends ou
autres interfaces officielles autorisées ; - API de recherche web ; -
données de marketplaces autorisées ; - Reddit API ; - Pinterest API ; -
YouTube Data API ; - API officielles de réseaux sociaux ; - rapports et
études de marché ; - newsletters et médias spécialisés ; - données de
catalogues et ventes sous licence.

L'accès aux API peut être payant, limité ou soumis à validation. Prévoir
un système de capacités et ne pas rendre l'application dépendante d'une
seule API.

## 7.2 Signaux à mesurer

-   évolution du volume de recherche, si la source le fournit ;
-   accélération de l'intérêt ;
-   mentions et engagement, en les distinguant des ventes ;
-   nombre de marchands proposant le produit ;
-   disponibilité des stocks ;
-   dispersion des prix ;
-   saisonnalité ;
-   intérêt géographique ;
-   apparition d'une nouvelle marque ou catégorie ;
-   évolution du nombre de sources indépendantes qui parlent du produit.

Chaque signal doit indiquer la période, la source, la méthodologie et
les limites.

## 7.3 Détection des tendances émergentes

Identifier les produits ou catégories dont plusieurs signaux convergent.
Éviter de déclencher une recommandation sur la base d'une seule vidéo
virale ou d'un pic isolé.

Créer un score de tendance séparé du score de rentabilité.

Exemple de fiche : - produit ou catégorie ; - résumé de la tendance ; -
pays concernés ; - période d'observation ; - sources ; - évolution
mesurée ; - niveau de confiance ; - produits associés ; - marchands où
le produit est disponible ; - prix d'achat constatés ; - recommandation
: surveiller, tester ou ignorer.

Les recommandations doivent être formulées comme des hypothèses à
tester, pas comme des garanties de demande future.

------------------------------------------------------------------------

# 8. Discovery AI --- découverte de nouveaux sites et produits

Le moteur doit proposer de nouvelles pistes à l'utilisateur.

## 8.1 Découverte de nouveaux sites

À partir des marques, produits et tendances identifiés : 1. rechercher
des marchands potentiels via des sources de recherche autorisées ; 2.
vérifier que le domaine existe et correspond bien au marchand ; 3.
identifier le pays, la catégorie et le type de vendeur ; 4. rechercher
des informations publiques de réputation ; 5. vérifier les conditions
d'accès aux données ; 6. identifier les API, flux ou autres méthodes
permises ; 7. évaluer les coûts, les frais de livraison et les risques ;
8. créer une proposition de connecteur.

Un domaine découvert ne doit jamais être automatiquement considéré comme
fiable.

## 8.2 Fiche de proposition

Chaque proposition contient : - nom du site ; - domaine ; - pays ; -
catégorie ; - raison de la découverte ; - produits pertinents ; -
réputation et sources consultées ; - méthode d'accès possible ; -
conditions d'utilisation à vérifier ; - coût éventuel ; - niveau de
confiance ; - statut de validation.

L'utilisateur peut : - approuver pour étude ; - refuser ; - mettre en
attente ; - demander une vérification complémentaire.

L'approbation pour étude ne donne pas automatiquement l'autorisation de
collecter des données. La méthode d'accès doit encore être validée.

## 8.3 Découverte de nouveaux produits

Proposer des mots-clés et produits à surveiller, expliquer pourquoi ils
ont été proposés, puis permettre de les ajouter à une liste de suivi.

Ne jamais modifier silencieusement les préférences de l'utilisateur.

------------------------------------------------------------------------

# 9. Profit Engine --- calcul du coût rendu et de la rentabilité

Le moteur doit calculer une rentabilité par produit et par scénario de
revente.

## 9.1 Coût total d'acquisition

Inclure selon le cas : - prix d'achat ; - transport intérieur ; -
transport international ; - assurance ; - droits de douane ; - TVA à
l'importation ; - frais de dédouanement ; - frais de paiement et de
change ; - inspection et échantillons ; - préparation et emballage ; -
frais de plateforme ; - provision pour défauts, retours et invendus.

Les taxes dépendent du pays, du type de produit, de la valeur, du régime
fiscal et de la situation de l'acheteur. Ne pas coder une règle fiscale
universelle. Créer un moteur de scénarios configurable et afficher « à
vérifier » si les données manquent.

Ne pas calculer automatiquement une TVA récupérable sans connaître le
régime applicable.

## 9.2 Lots

Pour les lots : - prix global ; - quantité ; - répartition des frais ; -
coût rendu par unité ; - taux de défaut ou de perte estimé, si renseigné
; - valeur de liquidation des invendus ; - marge globale ; - marge par
unité vendable.

Permettre plusieurs méthodes de répartition des coûts : par quantité,
poids, valeur ou saisie manuelle.

## 9.3 Prix de revente

Estimer le prix de revente à partir de données autorisées et documentées
: - ventes réellement réalisées lorsqu'elles sont accessibles ; -
comparables pertinents ; - prix affichés, clairement séparés des ventes
conclues ; - état et variante du produit ; - pays et canal de vente ; -
frais du canal ; - délai probable de vente si des données fiables
existent.

Ne pas scraper Vinted. Ne pas automatiser de connexion, d'extraction, de
favoris, de messages ou de publication sur Vinted. Permettre uniquement
la saisie manuelle ou l'intégration de fournisseurs de données disposant
des droits nécessaires.

Afficher une fourchette basse, centrale et haute si les données le
permettent, ainsi que le niveau de confiance et le nombre de
comparables.

## 9.4 Formules

Coût rendu = achat + transport + taxes + douane + frais + préparation +
provisions.

Bénéfice net estimé = prix de revente estimé - coût rendu - frais de
vente - autres coûts applicables.

ROI = bénéfice net estimé / coût total engagé × 100.

Marge sur vente = bénéfice net estimé / prix de revente estimé × 100.

Distinguer ROI et marge. Gérer les valeurs nulles et les données
manquantes sans division invalide.

Calculer également : - prix d'achat maximum pour atteindre un bénéfice
cible ; - prix de revente minimum pour atteindre un ROI cible ; - seuil
de rentabilité ; - scénarios pessimiste, central et optimiste.

------------------------------------------------------------------------

# 10. Scoring et classements

Ne pas fusionner toutes les dimensions dans un score opaque.

Créer au minimum :

1.  `deal_score` : qualité de l'offre immédiate.
2.  `trend_score` : dynamique de tendance.
3.  `source_trust_score` : fiabilité du marchand et de la source.
4.  `data_confidence_score` : qualité et fraîcheur des données.
5.  `risk_score` : risques commerciaux, conformité et logistique.
6.  `resale_liquidity_score` : facilité probable de revente, uniquement
    si les données le permettent.

## 10.1 Score d'opportunité initial

Proposition de pondération, à tester et ajuster : - rentabilité nette
potentielle : 30 % ; - demande et liquidité : 20 % ; - écart au prix
historique ou marché : 15 % ; - fiabilité du marchand : 10 % ; -
confiance des comparables : 10 % ; - fraîcheur et disponibilité : 10 %
; - adéquation aux préférences : 5 %.

Le score doit être pénalisé lorsque des informations critiques sont
inconnues. Les risques de conformité, contrefaçon, sécurité ou fraude
doivent agir comme des filtres bloquants ou des pénalités explicites,
pas être compensés par une marge élevée.

## 10.2 Trois classements sur le tableau de bord

A. **Meilleures affaires immédiates** : offres disponibles, récentes et
vérifiées.

B. **Tendances et opportunités émergentes** : produits dont l'intérêt
progresse.

C. **Nouveaux marchés à explorer** : sites, fournisseurs, marques et
catégories à étudier.

Chaque classement doit afficher son propre score, les raisons
principales, les incertitudes et les sources.

## 10.3 Explicabilité

Pour chaque score, montrer : - les facteurs positifs ; - les facteurs
négatifs ; - les données manquantes ; - les règles appliquées ; - la
date du calcul.

Ne pas utiliser un modèle de langage pour inventer le score. Les calculs
financiers et les pondérations doivent être déterministes et testables.
L'IA peut aider à classer, résumer et proposer des hypothèses, mais les
résultats doivent être vérifiables.

------------------------------------------------------------------------

# 11. Dashboard --- expérience utilisateur

Créer une application moderne, sobre, professionnelle et entièrement en
français.

## 11.1 Navigation

Menu latéral : 1. Vue d'ensemble. 2. Meilleures affaires. 3. Recherche
mondiale. 4. Market Intelligence. 5. Tendances. 6. Découvertes IA. 7.
Sites et fournisseurs. 8. Comparateur de prix. 9. Listes de
surveillance. 10. Lots et achats. 11. Résultats de revente. 12.
Historique. 13. Notifications. 14. Paramètres. 15. Santé du système.

## 11.2 Accueil

À l'ouverture : - afficher immédiatement les dernières données
enregistrées ; - indiquer l'heure de dernière actualisation ; - signaler
les données périmées ; - actualiser en arrière-plan ; - ne pas bloquer
l'interface pendant une collecte ; - présenter les meilleures offres et
les trois classements ; - afficher les sources en erreur ; - présenter
les nouvelles découvertes à valider.

Les données de démonstration doivent être visuellement identifiées comme
telles.

## 11.3 Fiche opportunité

Chaque fiche comprend : - image si une image autorisée est disponible
; - nom et description ; - marque, modèle, référence ; - catégorie et
variante ; - marchand et pays ; - prix d'origine et prix actuel ; -
devise d'origine et conversion EUR ; - date de collecte ; -
disponibilité et date de vérification ; - frais de livraison ; - coût
rendu estimé ; - prix de revente bas/central/haut ; - bénéfice et ROI
par scénario ; - scores et niveau de confiance ; - risques et
informations manquantes ; - liens vers les sources ; - historique de
prix.

Actions utilisateur : - ajouter aux favoris ; - ignorer ; - ajouter à
une liste de surveillance ; - marquer « à vérifier » ; - marquer « achat
effectué » avec saisie des coûts réels ; - ouvrir le site marchand ; -
exporter la fiche.

Le bouton « Acheter » doit uniquement ouvrir le site marchand. Il ne
doit pas déclencher de commande.

## 11.4 Filtres

Filtres : - catégorie ; - pays ; - marchand ; - marque ; - prix ; - coût
rendu ; - bénéfice estimé ; - ROI ; - score ; - date de collecte ; -
niveau de confiance ; - statut de disponibilité ; - achat unitaire ou
lot ; - type d'opportunité.

## 11.5 Accessibilité et qualité

-   interface responsive ;
-   navigation clavier ;
-   contrastes lisibles ;
-   états de chargement et d'erreur ;
-   pagination ou chargement progressif ;
-   filtres persistants ;
-   tri stable ;
-   affichage clair des devises et dates.

------------------------------------------------------------------------

# 12. Automatisation et planification

## 12.1 Recherche quotidienne

Durée initiale : deux heures, horaire par défaut 06:00--08:00
Europe/Paris.

La durée correspond à une fenêtre de travail planifiée, pas à une
promesse de couverture exhaustive du web.

Étapes : 1. vérifier l'état des connecteurs ; 2. charger les listes de
surveillance ; 3. sélectionner les requêtes prioritaires ; 4. collecter
les nouvelles offres ; 5. normaliser et dédupliquer ; 6. actualiser les
prix ; 7. calculer les coûts ; 8. actualiser les signaux de tendance
selon leur fréquence ; 9. calculer les scores ; 10. enregistrer les
résultats ; 11. envoyer les notifications pertinentes ; 12. produire un
rapport d'exécution.

Les quotas par source doivent être respectés. Une source indisponible ne
doit pas bloquer les autres.

## 12.2 À l'ouverture

-   servir rapidement le dernier état connu ;
-   lancer un contrôle de fraîcheur ;
-   planifier les actualisations nécessaires ;
-   mettre à jour les classements à mesure que les données arrivent ;
-   afficher clairement les offres non revérifiées.

## 12.3 Recherche manuelle

Ajouter un bouton « Lancer une recherche » avec : - choix des catégories
; - choix des régions ; - budget ; - sources ; - profondeur de recherche
; - estimation du temps et des quotas.

## 12.4 Notifications Telegram

Telegram est optionnel. Prévoir une configuration sécurisée.

Une alerte peut contenir : - produit ; - prix ; - coût rendu estimé ; -
bénéfice et ROI estimés ; - score ; - confiance ; - marchand ; - pays
; - date de vérification ; - lien source.

Permettre de régler le seuil d'alerte et d'éviter les notifications
répétées pour une même offre.

------------------------------------------------------------------------

# 13. Modèle de données et base PostgreSQL

Créer des modèles SQLAlchemy avec migrations Alembic.

Entités recommandées :

-   `users` ;
-   `user_settings` ;
-   `products` ;
-   `product_variants` ;
-   `categories` ;
-   `brands` ;
-   `merchants` ;
-   `sources` ;
-   `source_capabilities` ;
-   `offers` ;
-   `offer_observations` ;
-   `price_history` ;
-   `trend_signals` ;
-   `trend_topics` ;
-   `market_comparables` ;
-   `resale_scenarios` ;
-   `cost_scenarios` ;
-   `opportunities` ;
-   `opportunity_score_breakdowns` ;
-   `discovery_proposals` ;
-   `watchlists` ;
-   `watchlist_items` ;
-   `purchase_batches` ;
-   `purchase_items` ;
-   `resale_records` ;
-   `user_decisions` ;
-   `search_runs` ;
-   `connector_runs` ;
-   `notifications` ;
-   `audit_logs`.

Prévoir : - UUID comme identifiants publics ; - timestamps UTC ; -
contraintes d'intégrité ; - index sur les recherches fréquentes ; -
unicité des identifiants externes par source ; - archivage des offres
expirées ; - politique de rétention configurable ; - migrations testées
; - sauvegardes et restauration documentées.

Ne stocker que les données nécessaires et autorisées.

------------------------------------------------------------------------

# 14. Architecture logicielle et structure du dépôt

Commencer par un monolithe modulaire, pas par des microservices
prématurés.

Structure indicative :

``` text
hunter-ai/
├── CLAUDE.md
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Makefile
├── docs/
│   ├── architecture.md
│   ├── setup.md
│   ├── connectors.md
│   ├── data-policy.md
│   ├── scoring.md
│   ├── operations.md
│   └── roadmap.md
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── engines/
│   │   │   ├── global_scout/
│   │   │   ├── market_intelligence/
│   │   │   ├── price_radar/
│   │   │   ├── profit_engine/
│   │   │   ├── discovery_ai/
│   │   │   └── ranking/
│   │   ├── connectors/
│   │   ├── scheduler/
│   │   ├── notifications/
│   │   └── workers/
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── app/
│   ├── components/
│   ├── features/
│   ├── lib/
│   └── tests/
├── scripts/
├── infrastructure/
└── data/
    └── exports/
```

Adapte cette structure si nécessaire, mais documente les raisons.

## Dépendances recommandées

Backend : - Python version stable et supportée ; - FastAPI ; - Pydantic
; - SQLAlchemy ; - Alembic ; - PostgreSQL ; - HTTPX ; - APScheduler ; -
Redis/Celery si le besoin est confirmé ; - pytest ; - Ruff ; - mypy ou
pyright.

Frontend : - version LTS/compatible de Node.js ; - Next.js ; - React ; -
TypeScript ; - Tailwind CSS ; - bibliothèque de composants accessible
; - bibliothèque de graphiques maintenue.

Infrastructure : - Docker Compose ; - Git ; - scripts de sauvegarde ; -
health checks.

Évite d'ajouter des dépendances sans nécessité. Verrouille les versions
et documente les mises à jour.

------------------------------------------------------------------------

# 15. API backend

Créer une API versionnée, par exemple `/api/v1`.

Routes indicatives :

``` text
GET    /api/v1/health
GET    /api/v1/dashboard/summary
GET    /api/v1/opportunities
GET    /api/v1/opportunities/{id}
POST   /api/v1/opportunities/{id}/favorite
POST   /api/v1/opportunities/{id}/ignore
POST   /api/v1/opportunities/{id}/watch
GET    /api/v1/products
GET    /api/v1/products/{id}
GET    /api/v1/products/{id}/price-history
GET    /api/v1/sources
GET    /api/v1/sources/{id}
POST   /api/v1/sources/{id}/enable
POST   /api/v1/sources/{id}/disable
GET    /api/v1/trends
GET    /api/v1/discoveries
POST   /api/v1/discoveries/{id}/approve-for-review
POST   /api/v1/discoveries/{id}/reject
POST   /api/v1/search-runs
GET    /api/v1/search-runs
GET    /api/v1/settings
PATCH  /api/v1/settings
GET    /api/v1/system/status
```

Ces routes sont indicatives. Définir des schémas Pydantic, validation,
pagination, filtres, codes d'erreur et documentation OpenAPI.

Les routes de changement d'état doivent vérifier l'autorisation et
journaliser l'action.

------------------------------------------------------------------------

# 16. Sécurité, conformité et risques

## 16.1 Sécurité technique

-   secrets uniquement côté serveur ;
-   `.env` ignoré par Git ;
-   `.env.example` sans secret ;
-   validation des entrées ;
-   protection contre injection SQL ;
-   protection SSRF pour les URLs soumises par l'utilisateur ;
-   restrictions des domaines et protocoles ;
-   limites de taille et de débit ;
-   CORS restrictif ;
-   authentification si l'application est exposée au réseau ;
-   sauvegardes chiffrées si possible ;
-   logs sans secrets ni données sensibles ;
-   dépendances vérifiées ;
-   mises à jour de sécurité.

Même en usage local, ne suppose pas que toutes les entrées ou URLs sont
fiables.

## 16.2 Risques produits et commerciaux

Créer des filtres ou drapeaux de risque pour : - contrefaçon ou
suspicion de contrefaçon ; - produits rappelés ; - produits dangereux
; - conformité CE ou autres normes applicables ; - batteries et
transport réglementé ; - cosmétiques et produits de santé ; - jouets et
produits pour enfants ; - produits électriques ; - marques et propriété
intellectuelle ; - restrictions d'importation ; - fournisseurs non
vérifiés ; - frais cachés ; - fausses promotions ; - disponibilité non
confirmée.

Ne pas fournir de conseil juridique ou fiscal définitif. Afficher les
hypothèses et les points à vérifier. Les produits réglementés ou à haut
risque peuvent être exclus du sourcing par défaut.

## 16.3 Importation depuis la Chine et autres pays hors UE

Prévoir les champs nécessaires à l'estimation : - pays d'origine ; -
pays d'expédition ; - code douanier si connu ; - valeur en douane ; -
Incoterm ; - transport ; - assurance ; - TVA et droits éventuels ; -
frais de dossier ; - documents de conformité ; - responsabilité de
l'importateur.

Ne pas estimer les droits de douane sans données suffisantes. Prévoir
une mention « estimation indicative --- validation douanière nécessaire
».

------------------------------------------------------------------------

# 17. Tests et critères d'acceptation

Une fonctionnalité n'est terminée que lorsque ses tests passent.

## Tests backend

-   tests unitaires des calculs ;
-   tests de normalisation ;
-   tests de déduplication ;
-   tests des conversions monétaires ;
-   tests de frais et scénarios ;
-   tests des scores ;
-   tests de fraîcheur ;
-   tests API ;
-   tests de migrations ;
-   tests des erreurs de connecteurs.

## Tests frontend

-   affichage des états vides ;
-   chargement ;
-   erreurs API ;
-   filtres ;
-   tri ;
-   pagination ;
-   responsive ;
-   actions favoris/ignorer ;
-   affichage des données périmées.

## Tests d'intégration

-   base de données ;
-   scheduler ;
-   connecteur de démonstration clairement marqué ;
-   notifications en environnement de test ;
-   reprise après erreur ;
-   idempotence d'une collecte répétée.

## Critères d'acceptation initiaux

La première version du socle est acceptée si : 1. l'application démarre
avec les commandes documentées ; 2. PostgreSQL fonctionne dans Docker ;
3. les migrations s'appliquent ; 4. le backend répond au health check ;
5. le frontend communique avec l'API ; 6. le tableau de bord affiche un
état vide explicite ou des données DEMO clairement identifiées ; 7. les
tests automatisés passent ; 8. aucun secret n'est versionné ; 9. les
logs sont exploitables ; 10. une sauvegarde et une restauration sont
documentées.

Une source n'est acceptée comme opérationnelle qu'après un test réel
autorisé et documenté.

------------------------------------------------------------------------

# 18. Déploiement et exploitation

## Phase locale

Développer d'abord sur l'ordinateur de l'utilisateur avec Docker
Compose.

Fournir des commandes simples : - installation ; - démarrage ; - arrêt
; - migrations ; - tests ; - logs ; - sauvegarde ; - restauration.

## Phase serveur

Préparer ensuite un déploiement VPS : - Linux ; - Docker Compose ; -
HTTPS ; - pare-feu ; - authentification ; - sauvegardes automatiques ; -
surveillance de santé ; - redémarrage des services ; - alertes d'erreur.

Ne pas exposer PostgreSQL ou Redis directement à Internet.

Le scheduler doit éviter les exécutions concurrentes involontaires.
Prévoir un verrou ou mécanisme d'idempotence.

------------------------------------------------------------------------

# 19. Roadmap de développement

Développer en phases courtes et vérifiables.

## Phase 0 --- Audit et conception

-   inspecter l'environnement ;
-   établir l'architecture ;
-   créer `CLAUDE.md` ;
-   définir les conventions ;
-   valider les choix techniques.

Livrable : architecture documentée et dépôt initialisé.

## Phase 1 --- Socle fonctionnel

-   backend FastAPI ;
-   frontend Next.js ;
-   PostgreSQL ;
-   Docker Compose ;
-   migrations ;
-   health checks ;
-   configuration ;
-   logs ;
-   tests.

Livrable : application locale exécutable.

## Phase 2 --- Dashboard et données

-   navigation ;
-   accueil ;
-   listes et fiches ;
-   filtres ;
-   paramètres ;
-   données DEMO identifiées.

Livrable : interface utilisable connectée à l'API.

## Phase 3 --- Modèle produit/offre et premier connecteur

-   contrat de connecteur ;
-   source de test ;
-   premier connecteur réel choisi après vérification des conditions et
    de l'API ;
-   normalisation ;
-   déduplication ;
-   historique de prix.

Livrable : première collecte réelle et traçable.

## Phase 4 --- Price Radar

-   détection des variations ;
-   comparaison marchands ;
-   promotions ;
-   historique ;
-   fraîcheur.

Livrable : détection d'offres vérifiées.

## Phase 5 --- Profit Engine

-   coûts d'achat ;
-   transport ;
-   import ;
-   scénarios ;
-   lots ;
-   ROI et bénéfice ;
-   comparables et confiance.

Livrable : calculateur de rentabilité testable.

## Phase 6 --- Market Intelligence

-   intégration d'une première source de tendances autorisée ;
-   signaux ;
-   saisonnalité ;
-   tendances émergentes ;
-   explications et sources.

Livrable : première veille de marché.

## Phase 7 --- Discovery AI

-   propositions de nouveaux produits ;
-   découverte de marchands ;
-   vérification des domaines ;
-   évaluation de sources ;
-   validation humaine.

Livrable : suggestions de nouvelles pistes.

## Phase 8 --- Automatisation et notifications

-   planification de deux heures ;
-   collecte incrémentale ;
-   quotas ;
-   Telegram ;
-   déduplication d'alertes ;
-   rapport de session.

Livrable : veille quotidienne automatisée.

## Phase 9 --- Renforcement

-   davantage de connecteurs ;
-   suivi des décisions ;
-   achats et reventes réels saisis manuellement ;
-   comparaison prévisions/résultats ;
-   amélioration des scores.

Livrable : outil de sourcing enrichi par les retours réels.

## Phase 10 --- Déploiement VPS

-   configuration serveur ;
-   sécurité ;
-   sauvegardes ;
-   supervision ;
-   documentation d'exploitation.

Livrable : fonctionnement autonome.

------------------------------------------------------------------------

# 20. Méthode de collaboration avec l'utilisateur

L'utilisateur peut être débutant en développement.

Par conséquent : - explique les étapes en français simple ; - donne les
commandes exactes à copier-coller ; - précise dans quel terminal et
dossier les exécuter ; - explique les variables d'environnement sans
demander de révéler les secrets ; - signale les coûts éventuels des API
et services avant activation ; - distingue toujours les fonctions
gratuites, payantes et non disponibles ; - ne suppose pas que
l'utilisateur connaît Docker, Git ou les migrations ; - fournis des
instructions de dépannage.

Ne demande pas à l'utilisateur de prendre des décisions techniques
secondaires qui peuvent être prises raisonnablement par l'architecte.
Présente les choix importants et leurs conséquences.

------------------------------------------------------------------------

# 21. Première tâche à exécuter maintenant

**Ne développe pas toute l'application immédiatement.**

Commence par :

1.  inspecter le dossier courant et son contenu ;
2.  vérifier les versions disponibles de Python, Node.js, Git et Docker
    ;
3.  vérifier si le dépôt est déjà initialisé ;
4.  lire les éventuels fichiers existants ;
5.  proposer une architecture adaptée à l'environnement réel ;
6.  identifier les éventuels blocages ;
7.  créer un plan d'implémentation détaillé ;
8.  créer ou mettre à jour `CLAUDE.md` avec les règles essentielles de
    ce cahier des charges ;
9.  créer l'arborescence et les fichiers de configuration initiaux ;
10. implémenter uniquement le socle de la Phase 1 ;
11. lancer les tests et vérifier les démarrages backend, frontend et
    base de données ;
12. documenter les commandes exactes.

À la fin, fournir un rapport comprenant : - ce qui a été créé ; - les
fichiers importants ; - les commandes à exécuter ; - les tests passés et
échoués ; - les éventuels blocages ; - les prochaines étapes.

**Ne prétends pas que la Phase 1 est terminée si les critères
d'acceptation ne sont pas satisfaits.**

Le résultat recherché est une application fiable, évolutive, documentée
et réellement utilisable, qui transforme des données commerciales
vérifiables en opportunités d'achat-revente compréhensibles et classées.
