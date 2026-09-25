#!/usr/bin/env python3
"""Couverture complète KDP (broché) : quatrième + dos + première, fonds perdus compris.

Usage : python3 outils/couverture.py [--papier creme|blanc] [--pages N]
Entrée : couverture/face.png (première de couverture exportée de Canva, 1410 × 2250 ou plus).
Sorties : couverture/couverture_kdp.pdf (à téléverser), couverture/apercu_gabarit.png (repères).
Sans face.png, une première provisoire est dessinée pour vérifier la mise en page.
"""
import argparse, os, subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER = os.path.join(RACINE, "couverture")
DPI = 300
POLICES = "/usr/share/fonts/opentype/ebgaramond/"
TITRE, AUTEUR = "Valeur à neuf", "Loïg Kerdraon"
ENCRE = (64, 53, 38)          # le brun du titre Canva (#403526)
SABLE = (214, 205, 190)

# Gabarit KDP (pouces)
FORMAT_L, FORMAT_H = 5.5, 8.5
FOND_PERDU = 0.125
EPAISSEUR = {"creme": 0.0025, "blanc": 0.002252}   # pouce par page, papier noir et blanc
MARGE_SECURITE = 0.25          # texte à au moins 0,25 po du massicot (KDP : 0,125 minimum)
MARGE_DOS = 0.0625             # KDP : texte du dos à 0,0625 po de chaque pli
CODE_BARRES = (2.0, 1.2)       # zone réservée par KDP, en bas à droite de la quatrième

QUATRIEME = [
    "Antoine Vasseur a publié un très bon roman il y a treize ans. Depuis, il a des dettes, "
    "une éditrice patiente, une fille de dix-neuf ans qui ne l’appelle plus, et un escalier "
    "de 94 marches, ou 96.",
    "Une nuit d’octobre, il ouvre un compte sur Palimpseste, un logiciel d’écriture poli, "
    "serviable, qui ne demande qu’à apprendre. Il lui confie ses carnets, pour qu’elle "
    "comprenne le ton. Elle comprend.",
    "Bientôt, des scènes du manuscrit se produisent dans sa vie. Sa fille évoque des "
    "conversations qu’il n’a pas eues. Le livre avance, et il est meilleur que lui.",
    "De Paris à une maison fermée du Finistère nord, *Valeur à neuf* est le journal d’un "
    "homme qui cherche, à marée basse, ce qui lui appartient encore.",
]


def px(pouces):
    return round(pouces * DPI)


def police(taille_pt, italique=False):
    f = "EBGaramond12-Italic.otf" if italique else "EBGaramond12-Regular.otf"
    return ImageFont.truetype(os.path.join(POLICES, f), round(taille_pt * DPI / 72))


def pages_interieur():
    pdf = os.path.join(RACINE, "sortie", "roman_broche.pdf")
    sortie = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    return int(next(l.split()[-1] for l in sortie.splitlines() if l.startswith("Pages")))


def premiere(largeur, hauteur):
    chemin = os.path.join(DOSSIER, "face.png")
    if os.path.exists(chemin):
        img = Image.open(chemin).convert("RGB")
        # On retire le filet du cadre Canva (trop près du massicot une fois imprimé)
        m = int(img.width * 0.055)
        img = img.crop((m, m, img.width - m, img.height - m))
        echelle = max(largeur / img.width, hauteur / img.height)
        img = img.resize((round(img.width * echelle), round(img.height * echelle)), Image.LANCZOS)
        x, y = (img.width - largeur) // 2, (img.height - hauteur) // 2
        return img.crop((x, y, x + largeur, y + hauteur)), True
    img = Image.new("RGB", (largeur, hauteur), SABLE)
    d = ImageDraw.Draw(img)
    for texte, taille, y in ((AUTEUR, 16, 0.18), (TITRE, 40, 0.30), ("roman", 13, 0.37),
                             ("[première provisoire : déposer couverture/face.png]", 10, 0.6)):
        f = police(taille)
        l = d.textlength(texte, font=f)
        d.text(((largeur - l) / 2, hauteur * y), texte, font=f, fill=ENCRE)
    return img, False


def fond_sable(image_face, largeur, hauteur):
    """Quatrième et dos : le ton du sable de la première (bande basse), avec un grain léger."""
    bande = image_face.crop((0, int(image_face.height * 0.88), image_face.width, image_face.height))
    teinte = bande.resize((1, 1), Image.LANCZOS).getpixel((0, 0))
    teinte = tuple(round(0.6 * c + 0.4 * s) for c, s in zip(teinte, SABLE))
    fond = Image.new("RGB", (largeur, hauteur), teinte)
    grain = Image.effect_noise((largeur // 2, hauteur // 2), 18).resize((largeur, hauteur))
    grain = Image.merge("RGB", [grain] * 3)
    return Image.blend(fond, grain, 0.06)


def paragraphe(d, texte, x, y, largeur, f, fi, interligne):
    """Texte justifié à gauche ; *…* en italique."""
    mots = []
    italique = False
    for brut in texte.split(" "):
        debut = brut.startswith("*")
        fin = brut.endswith("*") or brut.endswith("*,") or brut.endswith("*.")
        if debut:
            italique = True
        mots.append((brut.replace("*", ""), italique))
        if fin:
            italique = False
    ligne, lignes = [], []
    espace = d.textlength(" ", font=f)
    for mot in mots:
        essai = ligne + [mot]
        l = sum(d.textlength(m, font=fi if it else f) for m, it in essai) + espace * (len(essai) - 1)
        if l > largeur and ligne:
            lignes.append(ligne); ligne = [mot]
        else:
            ligne = essai
    lignes.append(ligne)
    for ligne in lignes:
        cx = x
        for m, it in ligne:
            d.text((cx, y), m, font=fi if it else f, fill=ENCRE)
            cx += d.textlength(m, font=fi if it else f) + espace
        y += interligne
    return y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--papier", choices=EPAISSEUR, default="creme")
    ap.add_argument("--pages", type=int, default=None)
    a = ap.parse_args()
    pages = a.pages or pages_interieur()
    dos = pages * EPAISSEUR[a.papier]
    larg_po = 2 * FOND_PERDU + 2 * FORMAT_L + dos
    haut_po = FORMAT_H + 2 * FOND_PERDU
    L, H = px(larg_po), px(haut_po)
    x_dos, x_face = px(FOND_PERDU + FORMAT_L), px(FOND_PERDU + FORMAT_L + dos)

    face, definitive = premiere(L - x_face, H)
    toile = Image.new("RGB", (L, H))
    toile.paste(fond_sable(face, x_face, H), (0, 0))
    toile.paste(face, (x_face, 0))
    d = ImageDraw.Draw(toile)

    # Dos : titre et auteur, lus de bas en haut (usage français)
    f_dos = police(min(14, (dos - 2 * MARGE_DOS) * 72 * 0.62))
    texte_dos = f"{AUTEUR}      {TITRE}"
    lt = int(d.textlength(texte_dos, font=f_dos)) + 20
    bloc = Image.new("RGBA", (lt, f_dos.size * 2), (0, 0, 0, 0))
    ImageDraw.Draw(bloc).text((10, f_dos.size // 2), texte_dos, font=f_dos, fill=ENCRE)
    bloc = bloc.rotate(90, expand=True)
    toile.paste(bloc, (x_dos + (x_face - x_dos - bloc.width) // 2, (H - bloc.height) // 2), bloc)

    # Quatrième
    marge = px(FOND_PERDU + MARGE_SECURITE + 0.2)
    largeur_texte = x_dos - marge - px(MARGE_SECURITE + 0.3)
    f, fi = police(11.5), police(11.5, True)
    y = px(FOND_PERDU + 1.0)
    for p in QUATRIEME:
        y = paragraphe(d, p, marge, y, largeur_texte, f, fi, round(f.size * 1.35)) + round(f.size * 0.7)
    fa = police(12)
    d.text((marge, y + px(0.25)), AUTEUR, font=fa, fill=ENCRE)

    os.makedirs(DOSSIER, exist_ok=True)
    pdf = os.path.join(DOSSIER, "couverture_kdp.pdf")
    toile.save(pdf, "PDF", dpi=(L / larg_po, H / haut_po))

    # Aperçu avec repères (ne pas téléverser)
    ap_img = toile.copy()
    g = ImageDraw.Draw(ap_img)
    rouge, bleu, vert = (200, 30, 30), (30, 60, 200), (20, 140, 60)
    fp = px(FOND_PERDU)
    g.rectangle((fp, fp, L - fp, H - fp), outline=rouge, width=4)                 # massicot
    for xx in (x_dos, x_face):
        g.line((xx, 0, xx, H), fill=bleu, width=4)                                # plis du dos
    s = px(FOND_PERDU + MARGE_SECURITE)
    g.rectangle((s, s, x_dos - px(MARGE_SECURITE), H - s), outline=vert, width=3)
    g.rectangle((x_face + px(MARGE_SECURITE), s, L - s, H - s), outline=vert, width=3)
    cb_l, cb_h = px(CODE_BARRES[0]), px(CODE_BARRES[1])
    g.rectangle((x_dos - px(0.25) - cb_l, H - s - cb_h, x_dos - px(0.25), H - s),
                outline=(0, 0, 0), width=3)
    ap_img.resize((L // 3, H // 3)).save(os.path.join(DOSSIER, "apercu_gabarit.png"))

    print(f"pages {pages} · papier {a.papier} · dos {dos:.4f} po · couverture {larg_po:.4f} × "
          f"{haut_po:.4f} po · {L} × {H} px · première {'Canva' if definitive else 'PROVISOIRE'}")


if __name__ == "__main__":
    main()
