# STYLE — conventions typographiques

Principe : chaque niveau de texte a sa typographie. Le lecteur doit toujours pouvoir identifier la **forme** d'un passage, même quand il ne peut plus en identifier l'**auteur**.

---

## 1. Journal / récit d'Antoine (1re personne)
- Titre de chapitre : numéro + titre court, sans date.
- Date en tête d'entrée, facultative, au format d'Antoine : `Mardi 14 octobre. Coefficient 87.` (jour en toutes lettres, pas d'année, marée quand il y pense).
- **Dialogues : tiret cadratin**, sans guillemets ouvrants, une réplique par ligne. Les incises restent dans la réplique.

  ```
  — Tu n'as pas faim ?
  — J'ai mangé un Twix, dis-je. Enfin non. Un demi.
  ```

- Un propos rapporté brièvement dans le fil de la phrase se met en italique ou au discours indirect libre. Pas de guillemets pour le style direct court.
- Les messages vocaux et les messages écrits reçus sont cités **entre guillemets français** « » (c'est la seule exception : ce sont des textes, pas des voix présentes).
- Séparateur de sections : `~` seul sur une ligne.
- Pas de point-virgule, pas de points de suspension (voir `voix.md`).

## 2. *La Laisse de mer* (manuscrit d'Antoine / Paul)
- En-tête : `LA LAISSE DE MER — chapitre N` en petites capitales (markdown : `**LA LAISSE DE MER** — chapitre N`), puis le texte.
- Récit à la 3e personne, passé simple.
- **Dialogues entre guillemets français** « », avec incises classiques. (Le monde de Paul est plus « littéraire », plus convenu : c'est voulu.)
- Séparateur : `* * *`
- Annotations d'Antoine (ch. 3 surtout) : texte barré `~~…~~` pour les suppressions, et `[A. : …]` pour ses notes en marge.

## 3. Palimpseste (logs, réponses)
- Toujours en **bloc de code** (police à chasse fixe dans le .docx/.epub).
- Format :

  ```
  [08/01/2026 · 15:02:41] antoine.v > continue à partir de « Paul referma la porte »
  [08/01/2026 · 15:02:58] PALIMPSESTE > Bien sûr, Antoine. Voici une proposition de suite, dans la continuité du ton que nous avons établi ensemble :
  ```

- Réponses longues (propositions de texte) : dans le bloc de code, en paragraphes séparés.
- Métadonnées de fichier, historique de versions, CGU, mails automatiques : même traitement (bloc de code ou tableau).
- Palimpseste emploie des guillemets français, des points-virgules et des chiffres en lettres.

## 4. Chapitres indécidables (à partir du ch. 16)
- Aucun en-tête de forme. Pas de date. Narration en « il » ou en « je » sans marqueurs distinctifs, ou avec des marqueurs **contradictoires** (tiret d'Antoine + point-virgule de Palimpseste, par exemple).
- Dialogues au tiret (ce qui les rapproche du journal) mais passé simple (ce qui les rapproche du manuscrit).

## 5. Carnets manuscrits transcrits (acte III)
- En-tête : `Carnet n° 23 — transcription`.
- Ratures : `~~…~~`. Mots illisibles : `[illisible]`. Ajouts en interligne : `‹…›`.
- Au ch. 24, l'en-tête devient : `Carnet n° 24 — transcription automatique, vérifiée`. (Indice. Ne pas commenter.)

## 6. Prologue et épilogue
- Italique ? **Non** : romain, pour que la reprise au ch. 22 soit typographiquement identique. Pas de titre autre que « Prologue » / « Épilogue ».

## 7. Nombres, dates, heures
- Antoine : quantités mesurées en chiffres (`94 marches`, `18 412 €`, `4,20 m²`), heures au format `23 h 40`.
- Palimpseste : chiffres en lettres dans les textes (« quatre-vingt-quinze marches »), mais horodatage `15:02:41` dans les logs.
- Espace insécable avant `: ; ! ?` et `€` (dans les fichiers : espace normale, pandoc/typo gérera, ou script de correction à l'assemblage).

## 8. Noms
- *Mortes-eaux* et *La Laisse de mer* en italique. Palimpseste en romain, sans article dans la bouche d'Antoine au début (« Palimpseste »), avec article plus tard (« la Palimpseste », puis « elle »). **Marqueur de relation.**
