# Politique de données

1. **Ordre de priorité d'accès** : API officielle → flux d'affiliation autorisé → fournisseur sous
   licence → newsletter reçue légalement → import manuel (CSV/URL) → automatisation uniquement si
   explicitement permise par les conditions.
2. **Interdits** : contournement de CAPTCHA/anti‑bot/paywall/géo‑restriction, comptes multiples,
   cookies privés, scraping de Vinted, de Google Search ou de réseaux sociaux contre leurs CGU.
3. **Traçabilité obligatoire** de toute donnée externe : source, URL, date UTC de collecte, pays,
   devise d'origine, méthode d'obtention, dernière vérification, disponibilité, confiance.
4. **Fraîcheur** : toute donnée affiche son âge ; au‑delà de `STALE_AFTER_HOURS` (24 h par défaut)
   elle est signalée « périmée » ; une disponibilité non revérifiée s'affiche « à confirmer ».
5. **Données DEMO** : champ `is_demo=true` et badge « DEMO » dans l'interface. Jamais mélangées
   silencieusement aux données réelles.
6. **Minimisation (RGPD)** : aucune donnée personnelle de tiers (vendeurs particuliers, acheteurs)
   au‑delà du strict nécessaire.
7. **Rétention** : archivage des offres expirées et durée de conservation configurables (Phase 3).
8. **Secrets** : uniquement dans `.env` ou un gestionnaire de secrets ; masqués dans les journaux.
