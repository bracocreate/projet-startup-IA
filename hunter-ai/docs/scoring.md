# Scores (non implémentés — Phases 4, 5 et 9)

Principes retenus, issus du cahier des charges §10 :

- Six scores séparés : `deal_score`, `trend_score`, `source_trust_score`, `data_confidence_score`,
  `risk_score`, `resale_liquidity_score` (ce dernier seulement si les données le permettent).
- Calculs **déterministes et testés** ; un modèle de langage ne calcule ni n'invente aucun score.
- Pondération initiale du score d'opportunité (à calibrer avec les résultats réels) : rentabilité
  nette 30 %, demande/liquidité 20 %, écart au prix historique/marché 15 %, fiabilité marchand
  10 %, confiance des comparables 10 %, fraîcheur/disponibilité 10 %, préférences 5 %.
- Information critique inconnue → pénalité explicite. Risques conformité/contrefaçon/sécurité/fraude
  → filtre bloquant ou pénalité explicite, jamais compensés par la marge.
- Chaque score expose : facteurs positifs, négatifs, données manquantes, règles appliquées, date.
- Formules (Profit Engine) : coût rendu, bénéfice net, **ROI ≠ marge**, prix d'achat max,
  prix de revente min, seuil de rentabilité, scénarios pessimiste/central/optimiste ; aucune
  division par zéro, valeurs manquantes → « non déterminé ».
