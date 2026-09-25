#!/usr/bin/env python3
"""Contrôle d'un chapitre : mots bannis, tics de Palimpseste, variance des phrases.

Usage : python3 outils/controle.py chapitres/01_xxx.md [--fenetre 8]

Signale :
- les occurrences de la liste des mots bannis (bible/voix.md, §6) ;
- les marqueurs de contamination (point-virgule, « incessamment », chiffres en lettres…) ;
- les fenêtres de N phrases consécutives dont la longueur est trop régulière
  (coefficient de variation faible) : ce sont les passages qui « coulent trop bien ».
"""
import re
import sys
import statistics

BANNIS = [
    r"tapisserie", r"\bdans(e|es|ent|er|ait|aient|ant)\b", r"\bécho", r"murmur",
    r"résonn", r"un sentiment d", r"quelque chose d", r"force est de constater",
    r"dans un monde où", r"\bau fond\b", r"réalis(a|ai|e|é) que", r"tourbillon",
    r"poids du silence", r"se brisa", r"non seulement", r"comme une évidence",
    r"à couper le souffle", r"douce mélancolie", r"le temps s'arrêta",
    r"submergé", r"palpable", r"vibrant", r"infiniment",
    r"ce n'est pas .{1,40}, c'est ",
]
MARQUEURS = {
    "point-virgule": r";",
    "incessamment": r"incessamment",
    "bien sûr": r"\bbien sûr\b",
    "une forme de": r"une forme de",
    "points de suspension": r"\.\.\.|…",
}
NOMBRES_LETTRES = r"\b(deux|trois|quatre|cinq|six|sept|huit|neuf|dix|onze|douze|vingt|trente|quarante|cinquante|soixante|cent|mille)\b"


def phrases(texte):
    # ignore les blocs de code (logs Palimpseste) et les titres
    texte = re.sub(r"```.*?```", " ", texte, flags=re.S)
    texte = "\n".join(l for l in texte.splitlines() if not l.startswith("#"))
    morceaux = re.split(r"(?<=[.!?])\s+|\n{2,}", texte)
    return [m.strip() for m in morceaux if len(m.split()) > 0]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    chemin = sys.argv[1]
    fen = int(sys.argv[sys.argv.index("--fenetre") + 1]) if "--fenetre" in sys.argv else 8
    texte = open(chemin, encoding="utf-8").read()
    bas = texte.lower()

    print(f"== {chemin} : {len(texte.split())} mots")
    print("\n-- Mots bannis")
    rien = True
    for motif in BANNIS:
        for m in re.finditer(motif, bas):
            ligne = bas.count("\n", 0, m.start()) + 1
            print(f"  l.{ligne}: {motif!r} -> « {texte[max(0, m.start()-30):m.end()+30].strip()} »")
            rien = False
    if rien:
        print("  aucun")

    print("\n-- Marqueurs de contamination (à justifier dans contamination.md)")
    for nom, motif in MARQUEURS.items():
        n = len(re.findall(motif, bas))
        if n:
            print(f"  {nom}: {n}")
    n = len(re.findall(NOMBRES_LETTRES, bas))
    print(f"  nombres en lettres (dialogues compris) : {n}")

    ph = phrases(texte)
    longueurs = [len(p.split()) for p in ph]
    if len(longueurs) < 2:
        return
    print(f"\n-- Phrases : {len(longueurs)} | moyenne {statistics.mean(longueurs):.1f} mots"
          f" | écart-type {statistics.pstdev(longueurs):.1f}"
          f" | min {min(longueurs)} | max {max(longueurs)}")
    cv_global = statistics.pstdev(longueurs) / statistics.mean(longueurs)
    print(f"   coefficient de variation global : {cv_global:.2f} (visé : > 0.70)")

    print(f"\n-- Fenêtres de {fen} phrases trop régulières (CV < 0.35)")
    alerte = False
    for i in range(0, len(longueurs) - fen + 1):
        w = longueurs[i:i + fen]
        cv = statistics.pstdev(w) / statistics.mean(w)
        if cv < 0.35:
            alerte = True
            print(f"  phrases {i+1}-{i+fen} (CV {cv:.2f}) : « {ph[i][:70]}… »")
    if not alerte:
        print("  aucune")


if __name__ == "__main__":
    main()
