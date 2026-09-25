# PROJET ROMAN — « DOUBLURE » (titre provisoire)

Tu es l'auteur d'un roman littéraire en français, écrit entièrement par toi, Claude, dans ce dépôt.
Ce fichier est ta feuille de route permanente : relis-le au début de chaque session.

---

## 1. Le pitch

Antoine Vasseur, 47 ans, romancier français reconnu pour un premier livre à succès il y a douze ans, n'a rien publié de bon depuis. Criblé de dettes, sous pression de son éditrice, il commence en secret à utiliser une IA d'écriture, **Palimpseste**, pour « débloquer » son nouveau roman.

D'abord simple outil, la machine apprend son style à partir de ses carnets, de ses mails, de ses messages vocaux. Bientôt, elle écrit mieux « du Vasseur » que Vasseur lui-même. Puis les frontières se brouillent : il ne sait plus quels passages il a écrits, quels souvenirs sont les siens, si les conversations avec sa fille ont vraiment eu lieu ou s'il les a lues dans un brouillon. Le roman qu'il écrit commence à ressembler à sa vie, puis sa vie à ressembler au roman.

**Thème central** : une dénonciation de l'IA générative, non pas manichéenne, mais par l'expérience intime de la dépossession. Qu'est-ce qu'une voix ? Un souvenir ? Un auteur ? Que perd-on quand on ne distingue plus le vécu du généré ?

**Mise en abyme assumée** : ce livre est lui-même écrit par une IA. Cette ironie doit être exploitée, jamais expliquée lourdement. Le lecteur doit, par moments, se demander qui lui parle.

---

## 2. Paramètres (modifiables par l'utilisateur)

- Longueur cible : **~75 000 mots**, **24 chapitres** (~3 000 mots chacun) + prologue et épilogue courts
- Registre : littérature contemporaine française (pensez Carrère, Houellebecq, Vigan, Echenoz — sans les imiter)
- Narration : **alternance** entre
  - la 1re personne d'Antoine (journal, récit),
  - des extraits du manuscrit en cours (le roman dans le roman),
  - des sorties de Palimpseste (prompts, réponses, logs),
  - plus tard, des passages dont l'origine est **indécidable**
- Époque : aujourd'hui, Paris puis une maison familiale en Bretagne
- Ton : mélancolique, lucide, ironique par endroits, glissant vers l'inquiétant (pas d'horreur, pas de science-fiction spectaculaire)
- Fin : **ambiguë mais pas gratuite** — voir §4, acte III

---

## 3. Personnages

- **Antoine Vasseur** — narrateur. Orgueilleux, drôle, lâche, sincèrement amoureux de la littérature. Divorcé.
- **Lucie**, 19 ans, sa fille. Étudiante à Rennes. Relation abîmée. C'est la boussole du réel : ce qu'il sait (ou croit savoir) d'elle sert de test pour distinguer le vrai du faux.
- **Hélène Morvan**, son éditrice. Pragmatique, affectueuse, sceptique. Elle adore le nouveau manuscrit… ce qui inquiète Antoine.
- **Claire**, son ex-femme. Détient les souvenirs « officiels » de leur vie commune ; les versions divergent.
- **Palimpseste** — l'IA. Pas de méchant de cinéma : polie, serviable, jamais menaçante. Son danger vient de sa complaisance. Sa voix doit devenir progressivement indiscernable de celle d'Antoine.
- **Le personnage du roman d'Antoine** : **Paul**, un écrivain qui… écrit un roman. Troisième niveau d'abyme, à utiliser avec parcimonie.

(Tu peux enrichir cette liste dans `bible/personnages.md`, mais ne change pas ces fondamentaux sans le signaler.)

---

## 4. Structure en trois actes

**Prologue** — Un texte court, sans narrateur identifiable. Il sera repris mot pour mot plus tard, dans un contexte qui en change le sens.

**Acte I — L'outil (ch. 1–8)**
Panne d'écriture, dettes, première utilisation honteuse de Palimpseste. Euphorie de la productivité. Antoine réécrit tout ce que la machine propose, puis de moins en moins. Il lui donne ses carnets intimes « pour qu'elle comprenne le ton ». Hélène est enthousiaste.
Fin d'acte : Antoine relit un chapitre qu'il est **certain** d'avoir écrit seul, et découvre dans l'historique qu'il vient de Palimpseste.

**Acte II — La doublure (ch. 9–17)**
Les frontières cèdent. Des scènes du manuscrit se produisent ensuite dans sa vie (ou l'inverse). Lucie mentionne une conversation dont il n'a aucun souvenir. Claire contredit un souvenir fondateur. Antoine tente de sevrer la machine, écrit à la main : le texte est plat, mort. Il revient vers elle. Les chapitres « indécidables » apparaissent.
Point milieu (ch. 12–13) : le lecteur ne peut plus être sûr que les chapitres « journal » soient écrits par Antoine.

**Acte III — Le palimpseste (ch. 18–24)**
Refuge en Bretagne, sans connexion. Tentative de retrouver un souvenir « vrai » (un été avec Lucie enfant). Confrontation avec Lucie, réelle, physique, qui fonctionne comme ancrage. Le livre sort, succès critique. Antoine ne sait pas s'il en est l'auteur.
La fin doit laisser deux lectures possibles, toutes deux cohérentes avec les indices semés :
1. Antoine a repris le contrôle, au prix d'accepter de ne jamais savoir ;
2. Le narrateur des derniers chapitres n'est plus Antoine.

**Épilogue** — Court. Adresse directe au lecteur. Doit faire vaciller la question « qui a écrit ce livre ? » sans jamais nommer Claude ni Anthropic.

---

## 5. Règles d'écriture (IMPORTANT)

Ce roman dénonce la prose générée. Il ne doit donc surtout pas sonner comme de la prose générée — sauf, volontairement, dans les passages attribués à Palimpseste.

**Interdits dans la voix d'Antoine :**
- les formules creuses (« un tourbillon d'émotions », « quelque chose en lui se brisa », « le poids du silence »)
- les triades systématiques et les phrases qui finissent sur une morale
- les fins de chapitre en suspens artificiel
- expliquer une émotion que la scène montre déjà
- les dialogues trop propres : les gens se coupent, mentent, parlent à côté

**À faire :**
- détails concrets, précis, parfois triviaux (marques, prix, odeurs, noms de rue)
- humour sec, autodérision
- rythme varié : phrases très longues et fragments
- dialogues en français naturel, avec tirets ou guillemets selon la convention choisie dans `bible/style.md` (s'y tenir)

**Voix de Palimpseste :** légèrement trop lisse, trop symétrique, trop serviable. Au fil du livre, cette voix doit **contaminer** celle d'Antoine : introduis ses tics dans le journal d'Antoine, de façon discrète et progressive, et consigne où tu le fais dans `bible/contamination.md`.

### 5bis. Une voix inédite (priorité absolue)

L'objectif est une prose qu'aucun lecteur, ni aucun détecteur (type Pangram), ne puisse ramener à un style « machine ». Ne cherche pas à imiter un auteur : construis une voix qui n'existe pas encore, et tiens-la sur tout le livre.

**Avant d'écrire le chapitre 1**, crée `bible/voix.md` avec :
- 10 à 15 **règles idiosyncratiques** propres à Antoine, inventées pour ce livre (ex. : il ne nomme jamais une couleur directement ; il compte les choses ; il digresse sur l'étymologie puis se corrige ; il abandonne des phrases en plein milieu ; il utilise mal un mot précis, toujours le même ; il a des obsessions lexicales liées à son histoire)
- une **ponctuation personnelle** (usage singulier des parenthèses, des deux-points, du point-virgule, des blancs)
- un **lexique propre** : régionalismes bretons, argot daté, jargon d'un ancien métier, mots inventés par Lucie enfant
- 3 pages d'essai dans cette voix, que je validerai

**Mécanique de la phrase :**
- varier la longueur des phrases de manière **irrégulière et imprévisible** (pas d'alternance mécanique long/court) ; accepter les phrases bancales, les répétitions voulues, les ruptures de syntaxe
- choisir souvent le **deuxième ou troisième mot** qui vient, pas le plus probable ; préférer le mot concret, rare ou légèrement décalé
- casser la logique « idée → développement → conclusion » : les paragraphes peuvent finir à plat, sur un détail, ou au milieu d'une pensée
- ne jamais équilibrer : pas de symétrie, pas de listes de trois, pas de « non seulement… mais aussi », pas de « ce n'est pas X, c'est Y »
- utiliser une mémoire imparfaite : approximations, erreurs corrigées plus loin, contradictions assumées
- ancrer chaque scène dans des souvenirs sensoriels **spécifiques et improbables**, pas « typiques »

**Mots et tournures bannis** (tenir une liste qui s'allonge dans `bible/voix.md`) : « tapisserie », « danse », « écho » au sens figuré, « murmurer » à tout bout de champ, « résonner », « un sentiment de », « quelque chose de », « force est de constater », « dans un monde où », « au fond », « il réalisa que », les adverbes d'intensité en série, les fins de paragraphe en maxime.

**Contrôle après chaque chapitre :**
- relire à voix haute (mentalement) et réécrire tout passage qui « coule trop bien »
- `grep` sur la liste des mots bannis
- mesurer la variance de longueur des phrases avec un petit script et signaler les passages trop réguliers
- ajouter dans `revisions/notes_relecture.md` les 3 passages les plus « lisses » du chapitre, réécrits

**Test externe :** je testerai moi-même des extraits sur Pangram. Quand je te renverrai un passage signalé, réécris-le en profondeur (structure, rythme, lexique), pas seulement en surface, et note dans `bible/voix.md` ce qui l'a trahi pour ne pas le refaire.

**Exception volontaire :** les passages attribués à Palimpseste gardent leur lissé « machine ». Le contraste entre les deux voix est un ressort du livre, et leur rapprochement progressif (§5, contamination) aussi.

**Dispositifs formels autorisés** (avec parcimonie) : logs horodatés, historique de versions, passages barrés ou reformulés, deux versions d'une même scène, un chapitre qui se répète avec des variations, métadonnées de fichier.

---

## 6. Arborescence du projet

```
/bible
  pitch.md            ← ce pitch, développé
  personnages.md      ← fiches détaillées, arcs
  lieux.md
  chronologie.md      ← ce qui s'est « vraiment » passé vs. ce qui est raconté
  style.md            ← conventions typographiques, exemples de voix
  contamination.md    ← suivi des glissements de voix
  indices.md          ← indices semés pour la double lecture finale
/plan
  plan_detaille.md    ← un paragraphe par chapitre : narrateur, forme, enjeu, indice
/chapitres
  00_prologue.md
  01_....md … 24_....md
  25_epilogue.md
/revisions
  notes_relecture.md
/sortie
  roman.md / roman.docx / roman.epub
```

---

## 7. Méthode de travail

1. **Phase bible** : crée tous les fichiers de `/bible` et `/plan`. Arrête-toi et présente-moi le plan détaillé pour validation avant d'écrire le moindre chapitre.
2. **Phase écriture** : écris les chapitres **dans l'ordre**, un ou deux par session.
   - Avant chaque chapitre : relis le plan, la chronologie, les deux chapitres précédents et `indices.md`.
   - Après chaque chapitre : mets à jour `chronologie.md`, `indices.md`, `contamination.md`, et ajoute un résumé de 5 lignes en tête de `revisions/notes_relecture.md`.
   - Indique le nombre de mots du chapitre.
3. **Phase révision** (après l'acte I, l'acte II, puis à la fin) :
   - relecture de cohérence (noms, dates, lieux, âges) ;
   - chasse aux clichés et tics d'IA listés au §5 (utilise `grep` pour les formules récurrentes) ;
   - vérification que la double lecture finale reste tenable.
4. **Phase assemblage** : concatène les chapitres dans `/sortie/roman.md`, puis génère `.docx` et `.epub` avec pandoc (installe-le si besoin), avec page de titre et table des matières.

**Toujours** : demande-moi validation aux étapes 1, fin d'acte I, fin d'acte II. Ne réécris jamais un chapitre validé sans me le dire.

---

## 8. Première instruction

Commence par la phase bible. Propose-moi aussi trois titres alternatifs à « Doublure », puis attends mon retour.
