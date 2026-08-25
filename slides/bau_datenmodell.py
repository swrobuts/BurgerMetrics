#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bau_datenmodell.py — Foliendeck "BurgerMetrics: Datenmodell und Aufbau".

Dokumentiert, wie die drei Anwendungen des Projekts zusammenhaengen und warum
sie drei verschiedene Datenmodelle brauchen: Shop, Warenwirtschaft, Auswertung.
Die Diagramme stammen aus diagramme/*.mmd und werden von render_mermaid.mjs
erzeugt — dieses Skript setzt sie nur.

    python3 bau_datenmodell.py                  # -> ../../BurgerMetrics_Datenmodell.pptx
    python3 bau_datenmodell.py -o /pfad.pptx

Voraussetzungen: pip install python-pptx, Skill thws-slides (THWS_SKILL),
gerenderte PNG in diagramme/ (node render_mermaid.mjs).
"""
import argparse
import importlib.util
import os
import struct
import sys
import types
from pathlib import Path


def finde_skill():
    if os.environ.get("THWS_SKILL"):
        p = Path(os.environ["THWS_SKILL"])
        if (p / "assets" / "template.pptx").exists():
            return p
        sys.exit(f"FEHLER: THWS_SKILL zeigt auf {p}, dort fehlt assets/template.pptx")
    basis = Path.home() / "Library/Application Support/Claude"
    treffer = sorted(basis.glob("**/skills/thws-slides/assets/template.pptx"))
    if treffer:
        return treffer[-1].parent.parent
    sys.exit('FEHLER: Skill thws-slides nicht gefunden. export THWS_SKILL="/Pfad/zu/skills/thws-slides"')


SKILL = finde_skill()
SPECS = SKILL / "assets" / "specs"


def _load_spec(name="bint"):
    sp = importlib.util.spec_from_file_location(f"spec_{name}", SPECS / f"{name}.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


# spec_loader des Skills zeigt auf <skill>/specs statt <skill>/assets/specs.
_fake = types.ModuleType("spec_loader")
_fake.load = _load_spec
_fake.SPECS_DIR = SPECS
sys.modules["spec_loader"] = _fake

sys.path.insert(0, str(SKILL / "scripts"))
import bausteine as B                                    # noqa: E402
from pptx import Presentation                            # noqa: E402
from pptx.util import Pt                                 # noqa: E402
from pptx.enum.text import PP_ALIGN                      # noqa: E402

G = B.G
BLUE, WARN, GOOD, METHOD, HINT = G.BLUE, G.WARN, G.GOOD, G.METHOD, G.HINT
CL, CW, CR = G.CONTENT_LEFT, G.CONTENT_WIDTH, G.CONTENT_RIGHT
Y0, YMAX = G.CONTENT_ZONE_Y_MIN, G.CONTENT_ZONE_Y_MAX
HOEHE = YMAX - Y0


# --- Absatzformat: as_paras() erkennt nur Listen von LISTEN als mehrere Absaetze.
#     Flache Stringlisten liefen sonst zu einem Absatz zusammen.
def _paras(x):
    if isinstance(x, list) and x and all(isinstance(e, str) for e in x):
        return [[e] for e in x]
    return x


_kachel, _band, _gegenueber = B.kachel, B.band, B.gegenueber
B.kachel = lambda s, x, y, w, h, f, t, b, gap=5: _kachel(s, x, y, w, h, f, t, _paras(b), gap)
B.band = lambda s, y, h, p, **k: _band(s, y, h, _paras(p), **k)
B.gegenueber = lambda s, y, h, l, r, **k: _gegenueber(
    s, y, h, (l[0], l[1], _paras(l[2])), (r[0], r[1], _paras(r[2])), **k)

ap = argparse.ArgumentParser(description="Foliendeck Datenmodell bauen")
ap.add_argument("-o", "--ausgabe", default=None)
args = ap.parse_args()

HIER = Path(__file__).resolve().parent
DIA = HIER / "diagramme"
TEMPLATE = SKILL / "assets" / "template.pptx"
OUT = Path(args.ausgabe) if args.ausgabe else HIER.parent.parent / "BurgerMetrics_Datenmodell.pptx"
QUELLE = "Eigene Darstellung · Diagramme aus slides/diagramme/*.mmd"

prs = Presentation(str(TEMPLATE))
LAYOUT = {l.name: l for l in prs.slide_layouts}


def neu(name):
    return prs.slides.add_slide(LAYOUT[name])


def png_groesse(p):
    d = open(p, "rb").read(33)
    return struct.unpack(">II", d[16:24])


def bild(slide, name, y=None, max_h=None, x=None, max_w=None):
    """Diagramm linksbuendig auf der Inhaltsflucht, seitenverhaeltnistreu."""
    p = DIA / f"{name}.png"
    if not p.exists():
        sys.exit(f"FEHLER: {p.name} fehlt — erst 'node render_mermaid.mjs' ausfuehren.")
    pw, ph = png_groesse(p)
    y = Y0 if y is None else y
    max_h = (YMAX - y) if max_h is None else max_h
    max_w = CW if max_w is None else max_w
    sk = min(max_w / pw, max_h / ph)
    w, h = pw * sk, ph * sk
    slide.shapes.add_picture(str(p), B.E(CL if x is None else x), B.E(y), B.E(w), B.E(h))
    return w, h


def einl(slide, text, variante="Lisa_Slide"):
    ph = B.einleitung(slide, [text], variante)
    vor = [q for q in LAYOUT[variante].placeholders if q.placeholder_format.idx == 14][0]
    ph.left, ph.top, ph.width = vor.left, vor.top, vor.width
    ph.height = Pt(63.8)
    for p in ph.text_frame.paragraphs:
        p.alignment = PP_ALIGN.JUSTIFY
        for r in p.runs:
            r.font.size = Pt(14)
    return ph


def aufraeumen(slide):
    for sh in list(slide.placeholders):
        try:
            if not sh.text_frame.text.strip():
                sh._element.getparent().remove(sh._element)
        except Exception:
            pass


def kapitel(titel):
    s = neu("Chapter")
    for sh in s.placeholders:
        if str(sh.placeholder_format.type).startswith("TITLE"):
            sh.text_frame.text = titel
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(29)
    aufraeumen(s)


# ═══════════════════════════════════════════════════ Deckblatt
s = neu("Frontpage_Digital")
for sh in s.placeholders:
    i = sh.placeholder_format.idx
    if i == 10:
        sh.text_frame.text = "BurgerMetrics"
    elif i == 11:
        sh.text_frame.text = "Datenmodell und Aufbau"
aufraeumen(s)

# ═══════════════════════════════════════════════════ Teil 1
kapitel("Ein Geschäftsvorfall, drei Systeme")

# 1 Systemkontext
s = neu("Lisa_Slide")
B.kopf(s, "Überblick", "Eine Bestellung durchläuft drei Systeme mit drei Aufgaben", QUELLE)
einl(s, "Wer eine Bestellung aufgibt, löst eine Kette aus. Der Shop nimmt sie entgegen, "
        "die Warenwirtschaft verbucht sie, die Auswertung zählt sie später mit. Jedes der "
        "drei Systeme hat eine andere Aufgabe — und deshalb ein anderes Datenmodell. Diese "
        "Unterscheidung trägt den gesamten Aufbau.")
bild(s, "01_systemkontext", y=Y0 + 10, max_h=175)
B.band(s, Y0 + 200, 62, [
    "Der gestrichelte Pfeil ist die entscheidende Stelle: Die Auswertung liest nicht aus dem "
    "operativen System, sondern aus einem periodisch erzeugten Abzug. Sonst würde eine "
    "Jahresauswertung den laufenden Kassenbetrieb ausbremsen."])

# 2 Shop-Modell
s = neu("Lisa_Slide")
B.kopf(s, "System 1 · Website", "Der Shop speichert nur, was bis zum Kaufabschluss gebraucht wird", QUELLE)
einl(s, "Ein Warenkorb ist kein Beleg. Er lebt in einer Sitzung, ändert sich mit jedem Klick "
        "und verschwindet, wenn nichts daraus wird. Entsprechend schmal ist das Modell: eine "
        "Sitzung, ihre Positionen, der Artikelstamm. Ein Kunde ist optional — bestellen kann "
        "man auch ohne Anmeldung.")
bw, _ = bild(s, "02_shop_modell", max_w=470)
B.kachel(s, CL + bw + 24, Y0, CR - (CL + bw + 24), 190, METHOD, "Worauf dieses Modell optimiert ist",
         ["Sehr viele kleine Schreibvorgänge: jeder Klick ändert den Warenkorb.",
          "Kurze Lebensdauer — abgebrochene Sitzungen werden verworfen.",
          "Keine Historie, kein Bezug zu früheren Käufen.",
          "Sobald bestellt wird, übergibt der Shop an die Warenwirtschaft und ist fertig."])

# ═══════════════════════════════════════════════════ Teil 2
kapitel("Das operative Modell der Warenwirtschaft")

# 3 Verkaufspfad
s = neu("Lisa_Slide")
B.kopf(s, "System 2 · Warenwirtschaft", "Aus dem Warenkorb wird ein Beleg mit festen Bezügen", QUELLE)
einl(s, "Mit dem Kaufabschluss wird aus einem flüchtigen Warenkorb ein Beleg, der Jahre "
        "aufbewahrt wird. Er braucht feste Bezüge: welche Filiale, welcher Kunde, welche "
        "Zahlungsart. Die Positionen hängen zwingend am Kopf — eine Bestellung ohne Position "
        "gibt es nicht.")
bw, _ = bild(s, "03_wawi_verkaufspfad", max_w=470)
B.kachel(s, CL + bw + 24, Y0, CR - (CL + bw + 24), 190, BLUE, "Die Notation lesen",
         ["Doppelstrich = genau eins, Krähenfuß = viele.",
          "kundenbestellung ||--|{ bestellposition: eine Bestellung hat mindestens eine Position.",
          "filiale ||--o{ kundenbestellung: eine Filiale kann auch null Bestellungen haben.",
          "Kreis = optional, Strich = verpflichtend."])

# 4 Bereiche
s = neu("Lisa_Slide")
B.kopf(s, "System 2 · Warenwirtschaft", "Der Verkauf ist ein Bereich von sieben — 26 Tabellen insgesamt", QUELLE)
einl(s, "Ein Warenwirtschaftssystem bildet den ganzen Betrieb ab, nicht nur den Verkauf: "
        "26 Tabellen in sieben Bereichen, jedes Merkmal genau einmal. Für die Absatzfragen "
        "der Auswertung werden davon drei Bereiche gebraucht — Stammdaten, Verkauf und die "
        "externen Wetterdaten.")
bild(s, "04_wawi_bereiche", y=Y0, max_h=185)
wb = (CW - 18) / 2
B.kachel(s, CL, Y0 + 200, wb, 122, BLUE, "Warum so viele Tabellen",
         ["Einkauf, Lager und Personal hängen am selben Artikelstamm.",
          "Jedes Merkmal steht genau einmal — das ist die dritte Normalform."])
B.kachel(s, CL + wb + 18, Y0 + 200, wb, 122, HINT, "Was davon die Auswertung braucht",
         ["Einkauf, Lager, Personal und Rechnungswesen beantworten keine Absatzfrage.",
          "Aus 26 Tabellen werden dadurch zwölf."])

# 5 Normalisierung
s = neu("Lisa_Slide")
B.kopf(s, "System 2 · Warenwirtschaft", "Drei Tabellen für einen Artikel — und warum das richtig ist", QUELLE)
einl(s, "Ein Artikel hat eine Unterkategorie, die zu einer Kategorie gehört. Im operativen "
        "Modell sind das drei Tabellen. Das wirkt umständlich, hat aber einen Grund: Jeder "
        "Kategoriename steht genau einmal. Wer ihn ändert, ändert eine Zeile — nicht "
        "vierundfünfzig.")
B.gegenueber(s, Y0, 156,
             (GOOD, "Was Normalisierung leistet",
              ["Kein Merkmal steht doppelt, also kann nichts widersprüchlich werden.",
               "Änderungen treffen genau eine Zeile.",
               "Einfüge- und Löschanomalien sind ausgeschlossen: Eine Kategorie kann angelegt werden, bevor es Artikel gibt."]),
             (HINT, "Was sie kostet",
              ["Jede Auswertung muss die Tabellen wieder zusammenführen.",
               "Umsatz je Kategorie braucht vier Tabellen und drei Verknüpfungen.",
               "Bei Millionen Zeilen und vielen gleichzeitigen Abfragen wird das spürbar."]),
             badge_l="+", badge_r="−")

# ═══════════════════════════════════════════════════ Teil 3
kapitel("Das Auswertungsmodell")

# 6 Denormalisierung
s = neu("Lisa_Slide")
B.kopf(s, "System 3 · Auswertung", "Für die Auswertung wird die Normalisierung zurückgenommen", QUELLE)
einl(s, "Das Auswertungsmodell dreht die Abwägung um. Die drei Artikel-Tabellen werden zu "
        "einer breiten Dimensionstabelle zusammengezogen. Kategorie und Unterkategorie stehen "
        "danach redundant in jeder Produktzeile — und genau das ist gewollt.")
bild(s, "05_denormalisierung", y=Y0, max_h=130)
B.kachel(s, CL, Y0 + 148, CW, 112, METHOD, "Warum die Redundanz vertretbar ist",
         ["Ein Auswertungsbestand wird periodisch neu beladen, nicht laufend fortgeschrieben.",
          "Änderungsanomalien entstehen im Schreibbetrieb — den gibt es hier nicht.",
          "Aus drei Verknüpfungen je Abfrage wird eine."])
B.band(s, Y0 + 274, 48, [
    "Faustregel: Konsistenz hat Vorrang im operativen System, Lesegeschwindigkeit im Auswertungssystem."])

# 7 Granularität
s = neu("Lisa_Slide")
B.kopf(s, "System 3 · Auswertung", "Die erste Frage an jede Faktentabelle: Welches Ereignis ist eine Zeile?", QUELLE)
einl(s, "Bestellung 1 aus dem Datenbestand, vollständig. Der Bestellkopf trägt den Rabatt und "
        "den Endbetrag, die drei Positionen tragen Menge und Einzelpreis. Beides sind Fakten — "
        "aber auf verschiedenen Ebenen. Diese Unterscheidung heißt Granularität.")
bw, _ = bild(s, "06_granularitaet", max_w=380)
B.kachel(s, CL + bw + 30, Y0, CR - (CL + bw + 30), 190, WARN, "Warum das nicht in eine Tabelle passt",
         ["Läge alles auf Positionsebene, stünde der Rabatt dreimal da — und jede Summe darüber wäre das Dreifache.",
          "Läge alles auf Bestellebene, gäbe es keine Produktanalysen mehr.",
          "Die Positionssummen ergeben hier 10,35 € und damit den Bruttobetrag, nicht den Nettobetrag von 8,80 €."])

# 8 Galaxy
s = neu("Lisa_Slide")
B.kopf(s, "System 3 · Auswertung", "Zwei Granularitäten verlangen zwei Faktentabellen", QUELLE)
einl(s, "Ein Stern-Schema hat definitionsgemäß eine Faktentabelle. Zwei Faktentabellen, die "
        "sich Dimensionen teilen, heißen Galaxy-Schema oder Fact Constellation — die "
        "naheliegende Erweiterung, sobald ein Sachverhalt auf zwei Ebenen gemessen wird. "
        "dim_product hängt nur an der Positionsebene, die übrigen Dimensionen an beiden.")
bild(s, "07_galaxy", y=Y0, max_h=HOEHE)

# 9 Die drei Modelle
s = neu("Lisa_Slide")
B.kopf(s, "Zusammenschau", "Drei Modelle, weil drei verschiedene Fragen gestellt werden", QUELLE)
einl(s, "Es gibt nicht ein richtiges Datenmodell für BurgerMetrics, sondern drei — je eines "
        "für die Aufgabe, die das System zu erfüllen hat. Wer das Auswertungsmodell in die "
        "Kasse einbaut, bekommt Inkonsistenzen; wer die Kasse auswertet, bremst den Betrieb.")
w3 = (CW - 2 * 18) / 3
for i, (t, b, c) in enumerate([
    ("Shop · Website", ["Frage: Was liegt gerade im Warenkorb?",
                        "viele kleine Schreibvorgänge",
                        "kurze Lebensdauer, keine Historie",
                        "3 Tabellen"], METHOD),
    ("Warenwirtschaft", ["Frage: Was ist verbindlich passiert?",
                         "Konsistenz vor Geschwindigkeit",
                         "dritte Normalform, keine Redundanz",
                         "26 Tabellen"], BLUE),
    ("Auswertung", ["Frage: Wie entwickelt sich das Geschäft?",
                    "Lesen über Millionen Zeilen",
                    "bewusste Redundanz, wenige Verknüpfungen",
                    "12 Tabellen"], GOOD),
]):
    B.kachel(s, CL + i * (w3 + 18), Y0, w3, 168, c, t, b)

# 10 Kette
s = neu("Lisa_Slide")
B.kopf(s, "Umsetzung", "Vom Quellsystem zum Bericht in drei Schichten", QUELLE)
einl(s, "Der Umbau geschieht nicht in einem Sprung, sondern in Schichten. Die Rohdaten bleiben "
        "unangetastet, damit jederzeit nachvollziehbar ist, was das Quellsystem geliefert hat. "
        "Erst die mittlere Schicht typisiert und benennt, erst die dritte modelliert um.")
bild(s, "08_kette", y=Y0 + 10, max_h=110)
w2 = (CW - 18) / 2
B.kachel(s, CL, Y0 + 140, w2, 150, BLUE, "Warum drei Schichten und nicht eine",
         ["raw bleibt unverändert — der Vergleich mit dem Quellsystem bleibt möglich.",
          "stg ist als Sicht umgesetzt: immer frisch, kostet keinen Speicher.",
          "mart ist materialisiert — dort wird der Ladeschritt sichtbar, dort gehört später die Historisierung hin."])
B.kachel(s, CL + w2 + 18, Y0 + 140, w2, 150, METHOD, "Womit",
         ["Die Transformation ist SQL und gehört in versionierte Dateien, nicht in ein Werkzeugfenster.",
          "DuckDB genügt für diesen Bestand: 3,7 Mio. Zeilen, 55 MB, Abfragen unter 20 ms.",
          "Ein Data Warehouse würde hier Betrieb hinzufügen, ohne Fähigkeit hinzuzufügen."])

for sl in prs.slides:
    aufraeumen(sl)
prs.save(str(OUT))
print(f"Geschrieben: {OUT.name}")
print(f"Folien: {len(prs.slides._sldIdLst)}")
if B.WARNINGS:
    print("\nWarnungen der Bausteine:")
    for x in B.WARNINGS:
        print("  -", x)
else:
    print("Keine Baustein-Warnungen.")
