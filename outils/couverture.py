#!/usr/bin/env python3
"""Couverture KDP « au propre » : quatrième + dos + première, fonds perdus compris.

La photo est recomposée depuis les calques d'origine du fichier Canva
(couverture/sources/), le texte est vectoriel (EB Garamond incorporée).

Usage : python3 outils/couverture.py [--papier creme|blanc] [--pages N]
Sorties :
  couverture/couverture_kdp.pdf     couverture brochée à téléverser
  couverture/ebook_1600x2560.jpg    couverture Kindle
  couverture/apercu_gabarit.png     contrôle (coupe, plis, zones de sécurité, code-barres)
"""
import argparse, os, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFilter
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER = os.path.join(RACINE, "couverture")
SOURCES = os.path.join(DOSSIER, "sources")
pdfmetrics.registerFont(TTFont("Garamond", os.path.join(DOSSIER, "polices", "EBGaramond12-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Garamond-It", os.path.join(DOSSIER, "polices", "EBGaramond12-Italic.ttf")))
pdfmetrics.registerFontFamily("Garamond", normal="Garamond", italic="Garamond-It")

TITRE, AUTEUR = "Valeur à neuf", "Loïg Kerdraon"
ENCRE = (0x40 / 255, 0x35 / 255, 0x26 / 255)
PT = 72                                     # points par pouce

# Gabarit KDP (pouces)
FORMAT_L, FORMAT_H = 5.5, 8.5
FOND_PERDU = 0.125
EPAISSEUR = {"creme": 0.0025, "blanc": 0.002252}
SECURITE = 0.375                            # marge intérieure du texte (KDP : 0,125 minimum)
MARGE_DOS = 0.0625
CODE_BARRES = (2.0, 1.2)

ACCROCHE = "Il a confié ses carnets à une intelligence artificielle pour qu’elle comprenne le ton. Elle a compris."
QUATRIEME = [
    "Antoine Vasseur a publié un très bon roman il y a treize ans. Depuis, il a des dettes, "
    "une éditrice patiente, une fille de dix-neuf ans qui ne l’appelle plus, et un escalier "
    "de 94 marches, ou 96.",
    "Une nuit d’octobre, un peu honteux, il ouvre un compte sur Palimpseste, une IA d’écriture "
    "polie, serviable, qui ne demande qu’à apprendre. Il lui donne ses carnets, ses mails, sa "
    "voix. Les pages arrivent. Elles sont bonnes. Elles sont même un peu trop «\u00a0du Vasseur\u00a0».",
    "Puis des scènes du manuscrit se produisent dans sa vie. Sa fille évoque une conversation "
    "qu’il n’a pas eue. Et Antoine ne sait plus quels passages il a tapés, ni lesquels de ses "
    "souvenirs sont vraiment les siens.",
    "De Paris à une maison fermée du Finistère nord, <i>Valeur à neuf</i> est le journal d’un "
    "écrivain qui se fait doubler par la machine qui l’imite, et qui cherche, à marée basse, "
    "ce qui lui appartient encore.",
    "<i>Un roman sur l’IA qui écrit à notre place, et sur ce qu’on perd quand on ne sait plus qui parle.</i>",
]


# ---------------------------------------------------------------- photo
def photo(ratio, facteur=3):
    """Recompose la photo Canva (fond + coquillage détouré), sans le filet du cadre,
    recadrée au rapport largeur/hauteur demandé."""
    fond = Image.open(os.path.join(SOURCES, "fond_canva.png")).convert("RGB")
    w, h = fond.size
    fond = fond.resize((w * facteur, h * facteur), Image.LANCZOS)
    coq = Image.open(os.path.join(SOURCES, "coquillage_canva.png")).convert("RGB")
    masque = Image.open(os.path.join(SOURCES, "coquillage_masque.png")).convert("L")
    # Position du coquillage dans la page Canva (1410 × 2250), ramenée à l'image de fond
    s = w * facteur / 1410
    boite = (514.02 * s, 1377.84 * s, 299.61 * s, 282.67 * s)
    taille = (round(boite[2]), round(boite[3]))
    fond.paste(coq.resize(taille, Image.LANCZOS), (round(boite[0]), round(boite[1])),
               masque.resize(taille, Image.LANCZOS))
    # Intérieur du cadre (filets à x 26-34 / 958-965, y 23-25 / 1552-1554 dans l'original)
    g, d, hh, b = 40 * facteur, 952 * facteur, 36 * facteur, 1546 * facteur
    lw, lh = d - g, b - hh
    if lw / lh < ratio:                     # trop haut : on rogne en hauteur
        nh = round(lw / ratio)
        hh += (lh - nh) // 2
        lh = nh
    else:
        nw = round(lh * ratio)
        g += (lw - nw) // 2
        lw = nw
    img = fond.crop((g, hh, g + lw, hh + lh))
    return img.filter(ImageFilter.UnsharpMask(radius=2, percent=40, threshold=2))


def teinte_bord_gauche(img, hauteur):
    """Dégradé vertical reprenant, ligne par ligne, le ton du bord gauche de la photo :
    la quatrième et le dos se raccordent à la première sans couture visible."""
    bande = img.crop((0, 0, max(8, img.width // 40), img.height)).resize((1, hauteur), Image.BOX)
    bande = bande.filter(ImageFilter.GaussianBlur(hauteur // 30))
    return bande


# ---------------------------------------------------------------- texte
def texte_centre(c, texte, cx, y, police, taille, espacement=0):
    largeur = pdfmetrics.stringWidth(texte, police, taille) + espacement * (len(texte) - 1)
    t = c.beginText(cx - largeur / 2, y)
    t.setFont(police, taille)
    t.setCharSpace(espacement)
    t.setFillColorRGB(*ENCRE)
    t.textOut(texte)
    t.setCharSpace(0)                       # Tc persiste dans la page : on le remet à zéro
    c.drawText(t)


def premiere(c, x, y, l, h, bord_ext):
    """Dessine la première (photo + texte) dans la boîte (x, y, l, h) en points.
    bord_ext : fond perdu à droite (et en haut / bas) déjà inclus dans la boîte."""
    img = photo(l / h)
    c.drawImage(ImageReader(img), x, y, l, h)
    cx = x + (l - bord_ext) / 2             # centre optique : sur la zone après coupe
    haut = y + h - bord_ext
    hauteur_utile = h - 2 * bord_ext
    k = (l - bord_ext) / (FORMAT_L * PT)    # 1 pour le broché, plus pour l'ebook
    texte_centre(c, AUTEUR, cx, haut - hauteur_utile * 0.135, "Garamond", 15.5 * k, 1.2 * k)
    texte_centre(c, TITRE, cx, haut - hauteur_utile * 0.285, "Garamond", 44 * k)
    texte_centre(c, "roman", cx, haut - hauteur_utile * 0.345, "Garamond-It", 14 * k, 0.8 * k)


def dessiner(chemin, pages, papier):
    dos = pages * EPAISSEUR[papier]
    L = (2 * FOND_PERDU + 2 * FORMAT_L + dos) * PT
    H = (FORMAT_H + 2 * FOND_PERDU) * PT
    x_dos = (FOND_PERDU + FORMAT_L) * PT
    x_face = x_dos + dos * PT
    fp = FOND_PERDU * PT

    c = canvas.Canvas(chemin, pagesize=(L, H), initialFontName="Garamond", initialFontSize=11)
    c.setTitle(f"{TITRE} — couverture"); c.setAuthor(AUTEUR)

    # Photo de la première, puis fond de la quatrième et du dos raccordé à son bord gauche
    img_face = photo((L - x_face) / H)
    degrade = teinte_bord_gauche(img_face, 600).resize((64, 600))
    grain = Image.effect_noise((600, 600), 14).convert("RGB").resize((64, 600))
    degrade = Image.blend(degrade, grain, 0.04)
    c.drawImage(ImageReader(degrade), 0, 0, x_face + 1, H)
    premiere(c, x_face, 0, L - x_face, H, fp)

    # Dos (lecture de bas en haut, usage français)
    c.saveState()
    c.translate(x_dos + dos * PT / 2, H / 2)
    c.rotate(90)
    taille = min(13, (dos - 2 * MARGE_DOS) * PT * 0.55)
    ta = pdfmetrics.stringWidth(AUTEUR, "Garamond", taille * 0.85)
    tt = pdfmetrics.stringWidth(TITRE, "Garamond", taille)
    blanc = taille * 2.2
    total = ta + blanc + tt
    yb = -taille * 0.33
    c.setFillColorRGB(*ENCRE)
    c.setFont("Garamond", taille * 0.85); c.drawString(-total / 2, yb, AUTEUR)
    c.setFont("Garamond", taille * 0.8); c.drawCentredString(-total / 2 + ta + blanc / 2, yb, "~")
    c.setFont("Garamond", taille); c.drawString(-total / 2 + ta + blanc, yb, TITRE)
    c.restoreState()

    # Quatrième
    g = fp + SECURITE * PT + 0.15 * PT
    d = x_dos - SECURITE * PT - 0.15 * PT
    largeur = d - g
    haut = H - fp - 0.95 * PT
    s_acc = ParagraphStyle("acc", fontName="Garamond-It", fontSize=15, leading=19.5,
                           textColor=ENCRE, alignment=0)
    s_txt = ParagraphStyle("txt", fontName="Garamond", fontSize=11.5, leading=16,
                           textColor=ENCRE, alignment=TA_JUSTIFY, spaceAfter=7.5)
    p = Paragraph(ACCROCHE, s_acc)
    _, ph = p.wrap(largeur, H); p.drawOn(c, g, haut - ph); haut -= ph + 0.28 * PT
    c.setFont("Garamond", 15); c.setFillColorRGB(*ENCRE)
    c.drawCentredString(g + largeur / 2, haut - 6, "~"); haut -= 0.32 * PT
    for texte in QUATRIEME:
        p = Paragraph(texte, s_txt)
        _, ph = p.wrap(largeur, H); p.drawOn(c, g, haut - ph); haut -= ph + s_txt.spaceAfter
    # Signature en bas à gauche, hors de la zone du code-barres (en bas à droite)
    c.setFont("Garamond", 11.5); c.drawString(g, fp + SECURITE * PT + 0.25 * PT, AUTEUR)
    c.setFont("Garamond-It", 10); c.drawString(g, fp + SECURITE * PT + 0.05 * PT, "roman")
    c.showPage(); c.save()
    return dict(L=L, H=H, x_dos=x_dos, x_face=x_face, fp=fp, dos=dos, fin_texte=haut)


def ebook(chemin_jpg):
    l, h = 1600 * 0.75, 2560 * 0.75           # points, rapport 1:1,6
    with tempfile.TemporaryDirectory() as tmp:
        pdf = os.path.join(tmp, "ebook.pdf")
        c = canvas.Canvas(pdf, pagesize=(l, h), initialFontName="Garamond", initialFontSize=11)
        premiere(c, 0, 0, l, h, 0)
        c.showPage(); c.save()
        subprocess.run(["pdftoppm", "-r", "96", "-png", "-singlefile", pdf,
                        os.path.join(tmp, "e")], check=True)
        Image.open(os.path.join(tmp, "e.png")).convert("RGB").resize((1600, 2560), Image.LANCZOS) \
             .save(chemin_jpg, quality=93)


def apercu(pdf, g, chemin_png):
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", "100", "-png", "-singlefile", pdf,
                        os.path.join(tmp, "a")], check=True)
        img = Image.open(os.path.join(tmp, "a.png")).convert("RGB")
    k = img.width / g["L"]
    d = ImageDraw.Draw(img)
    P = lambda v: round(v * k)
    fp, s = g["fp"], g["fp"] + SECURITE * PT
    d.rectangle((P(fp), P(fp), P(g["L"] - fp), P(g["H"] - fp)), outline=(200, 30, 30), width=2)
    for x in (g["x_dos"], g["x_face"]):
        d.line((P(x), 0, P(x), img.height), fill=(30, 60, 200), width=2)
    d.rectangle((P(s), P(s), P(g["x_dos"] - SECURITE * PT), P(g["H"] - s)), outline=(20, 140, 60), width=1)
    d.rectangle((P(g["x_face"] + SECURITE * PT), P(s), P(g["L"] - s), P(g["H"] - s)), outline=(20, 140, 60), width=1)
    cb_l, cb_h = CODE_BARRES[0] * PT, CODE_BARRES[1] * PT
    d.rectangle((P(g["x_dos"] - 0.25 * PT - cb_l), P(g["H"] - fp - 0.25 * PT - cb_h),
                 P(g["x_dos"] - 0.25 * PT), P(g["H"] - fp - 0.25 * PT)), outline=(0, 0, 0), width=2)
    img.save(chemin_png)


def pages_interieur():
    sortie = subprocess.run(["pdfinfo", os.path.join(RACINE, "sortie", "roman_broche.pdf")],
                            capture_output=True, text=True).stdout
    return int(next(l.split()[-1] for l in sortie.splitlines() if l.startswith("Pages")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--papier", choices=EPAISSEUR, default="creme")
    ap.add_argument("--pages", type=int)
    a = ap.parse_args()
    pages = a.pages or pages_interieur()
    pdf = os.path.join(DOSSIER, "couverture_kdp.pdf")
    g = dessiner(pdf, pages, a.papier)
    ebook(os.path.join(DOSSIER, "ebook_1600x2560.jpg"))
    apercu(pdf, g, os.path.join(DOSSIER, "apercu_gabarit.png"))
    bas_code_barres = FOND_PERDU * PT + 0.25 * PT + CODE_BARRES[1] * PT
    print(f"pages {pages} · papier {a.papier} · dos {g['dos']:.4f} po · "
          f"couverture {g['L'] / PT:.4f} × {g['H'] / PT:.4f} po · "
          f"texte de 4e jusqu'à {g['fin_texte'] / PT:.2f} po du bas "
          f"(code-barres jusqu'à {bas_code_barres / PT:.2f} po)")


if __name__ == "__main__":
    main()
