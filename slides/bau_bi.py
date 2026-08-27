#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bau_bi.py — Foliendeck "BurgerMetrics: Von Kennzahlen zur Entscheidung".

Das Schwesterdeck zu bau_datenmodell.py. Wo jenes das operative Datenmodell
dokumentiert, geht dieses den Weg weiter: welche Kennzahlen aus dem Bestand
entstehen, wie sie definiert und geprueft werden, wie daraus ein Dashboard
wird, welche Entscheidungen es traegt und mit welchen Architekturen und
Werkzeugen man so etwas sonst baut.

    python3 bau_bi.py                  # -> ../../BurgerMetrics_BI.pptx
    python3 bau_bi.py -o /pfad.pptx

Voraussetzungen: python-pptx, Skill thws-slides (THWS_SKILL), gerenderte
Diagramme (node render_mermaid.mjs) und Bildschirmfotos (node screenshots.mjs).

Alle Messwerte stammen aus einem Lauf gegen dataset/ mit DuckDB 1.5.5.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckwerk as D                                     # noqa: E402

B = D.B
BLUE, WARN, GOOD, METHOD, HINT = D.BLUE, D.WARN, D.GOOD, D.METHOD, D.HINT
CL, CW, CR, Y0, YMAX, HOEHE = D.CL, D.CW, D.CR, D.Y0, D.YMAX, D.HOEHE

ap = argparse.ArgumentParser(description="BI-Foliendeck bauen")
ap.add_argument("-o", "--ausgabe", default=None)
args = ap.parse_args()
OUT = Path(args.ausgabe) if args.ausgabe else D.HIER.parent.parent / "BurgerMetrics_BI.pptx"

QUELLE, Q_FOTO, Q_MESS = D.QUELLE, D.Q_FOTO, D.Q_MESS
Q_MARKT = ("Gartner Magic Quadrant Analytics and BI Platforms, Juni 2026; "
           "Marktanteile aus Anbieter- und Marktbeobachterberichten 2026")
Q_EIG = "Eigene Einschätzung"

deck = D.Deck()
w2 = (CW - 18) / 2
w3 = (CW - 2 * 18) / 3

# ═══════════════════════════════════════════════════ Deckblatt
deck.deckblatt("BurgerMetrics", "Von Kennzahlen zur Entscheidung")

# ═══════════════════════════════════════════════════ Leitfrage
s = deck.neu("Lisa_Slide")
B.kopf(s, "Leitfrage", "Eine Kennzahl zählt erst, wenn sie eine Entscheidung ändert", QUELLE)
deck.einl(s, "Business Intelligence endet nicht bei der Zahl. Zwischen der Frage eines "
             "Betriebsleiters und seiner Entscheidung liegen vier Stationen, und an jeder "
             "kann die Antwort kippen: bei der Definition der Kennzahl, beim Modell, aus "
             "dem sie gerechnet wird, und beim Werkzeug, das sie zeigt.")
B.stufenband(s, Y0, 38, ["Frage", "Kennzahl", "Modell", "Werkzeug", "Entscheidung"])
for i, (t, b, c) in enumerate([
    ("Was gemessen wird", ["Umsatz ist kein Wort, sondern eine Rechenvorschrift.",
                           "Zeitraum, Grundgesamtheit und Formel gehören dazu.",
                           "Ohne diese drei Angaben ist keine Zahl prüfbar."], BLUE),
    ("Woraus gerechnet wird", ["Das Auswertungsmodell entscheidet, was überhaupt fragbar ist.",
                               "Zwei Granularitäten, zwei Faktentabellen.",
                               "Was nicht modelliert ist, kann kein Bericht zeigen."], METHOD),
    ("Was daraus folgt", ["Eine Kennzahl ohne Handlungsoption ist Dekoration.",
                          "Jede Kachel dieses Dashboards trägt eine Empfehlung.",
                          "Die letzte Prüfung ist immer: Was tun wir jetzt anders?"], GOOD),
]):
    B.kachel(s, CL + i * (w3 + 18), Y0 + 56, w3, 172, c, t, b)
B.band(s, D.Y0 + 244, 66, [
    "Dieses Deck geht die fünf Stationen von links nach rechts durch — am eigenen Bestand: "
    "754.513 Bestellungen aus neun Jahren, acht Filialen, vier Kanälen. Jede genannte Zahl "
    "ist aus den Rohdaten nachgerechnet."])

# ═══════════════════════════════════════════════════ Teil 1
deck.kapitel("Die Fallstudie: drei Systeme, eine Datenspur")

# Vorstellung
s = deck.neu("Tool_Slide")
B.kopf(s, "Fallstudie", "Eine fiktive Kette, gebaut, um durchschaut zu werden", Q_FOTO)
deck.einl(s, "BurgerMetrics ist eine erfundene Fast-Food-Kette: acht Filialen in Würzburg, "
             "neun Jahre Geschichte, drei Anwendungen. Erfunden heißt nicht beliebig — der "
             "Datenbestand ist so konstruiert, dass jede Kennzahl nachrechenbar ist und die "
             "typischen Auswertungsfallen tatsächlich zuschnappen.", "Tool_Slide")
bw, _ = deck.foto(s, "01_start", max_w=560, max_h=HOEHE)
B.kachel(s, CL + bw + 24, Y0, CR - (CL + bw + 24), 140, BLUE, "Die drei Anwendungen",
         ["Online-Shop: die Kundensicht, mit Warenkorb und Speisekarte.",
          "Kassensystem: die operative Sicht, an der die Belege entstehen.",
          "BI-Dashboard: die Auswertungssicht mit 13 Themenreitern."])
B.kachel(s, CL + bw + 24, Y0 + 156, CR - (CL + bw + 24), 122, METHOD, "Warum eine Lernumgebung",
         ["Echte Unternehmensdaten sind vertraulich — hier darf jeder alles sehen.",
          "Alle drei Systeme laufen im Browser, ohne Anmeldung und ohne Server."])

# Rollen und Datenspur
s = deck.neu("Lisa_Slide")
B.kopf(s, "Rollen", "Daten entstehen vorn, verbucht wird in der Mitte, befragt wird hinten", QUELLE)
deck.einl(s, "Jedes der drei Systeme hat genau eine Rolle. Shop und Kasse erzeugen Daten als "
             "Nebenprodukt ihrer eigentlichen Aufgabe, die Warenwirtschaft macht daraus "
             "verbindliche Belege, und die Auswertung liest einen nächtlichen Abzug davon. "
             "Kein System greift in die Zuständigkeit des anderen.")
deck.bild(s, "16_datenspur", y=Y0 + 4, max_h=232)
B.band(s, Y0 + 252, 68, [
    "Der gestrichelte Pfeil ist die wichtigste Kante des Bildes: Links von ihm zählt "
    "Konsistenz im laufenden Betrieb, rechts von ihm zählt Lesegeschwindigkeit über die "
    "ganze Historie. Diese Grenze begründet fast jede Bauentscheidung des Projekts."])

s = deck.neu("Lisa_Slide")
B.kopf(s, "Einordnung", "Vier Fragen, und nur die letzte ändert etwas", QUELLE)
deck.einl(s, "Auswertungen unterscheiden sich nicht nach Werkzeug, sondern nach der Frage, "
             "die sie beantworten. Die vier Stufen bauen aufeinander auf: Ohne verlässliche "
             "Beschreibung keine Diagnose, ohne Diagnose keine belastbare Prognose. Der "
             "Nutzen entsteht erst auf der vierten Stufe.")
B.zuordnung(s, Y0, [
    ("deskriptiv",
     "Was ist passiert? Umsatz 2025: 2.994.771 EUR aus 136.557 Bestellungen. "
     "Nachrechenbar, unstrittig — und für sich genommen folgenlos."),
    ("diagnostisch",
     "Warum? Das Wachstum von 5,4 Prozent gegenüber 2024 kommt aus dem Bestellwert "
     "(21,31 auf 21,93 EUR), nicht aus mehr Gästen."),
    ("prädiktiv",
     "Was kommt? Aus neun Jahren Wochentagsmuster lässt sich der Samstagsbedarf "
     "schätzen — mit Unsicherheit, nicht als Tatsache."),
    ("präskriptiv",
     "Was tun? Personalplanung auf die Mittagsspitze um 12 Uhr legen, in der "
     "2025 rund 21.749 Bestellungen anfielen — die größte Stunde des Tages."),
], rh=54.0)

# Website: zwei Sichten
s = deck.neu("Slide")
B.kopf(s, "System Website", "Dieselbe Seite, zwei Sichten: Speisekarte für Kunden, Datenspur für uns", Q_FOTO)
wf = (CW - 18) / 2
# Slide-Layout: Der Inhalt beginnt direkt unter dem Titel, nicht erst auf der
# Lisa-Kante — die Fotos bekommen die gewonnene Hoehe.
YS = 128
B.textbox(s, CL, YS, wf, 18, [("Kundensicht", True, D.SEC)], 11.5)
B.textbox(s, CL + wf + 18, YS, wf, 18, [("Datensicht — derselbe Moment", True, BLUE)], 11.5)
bw2, bh2 = deck.foto(s, "02_shop", y=YS + 24, max_w=wf, max_h=246)
deck.foto(s, "02b_shop_daten", y=YS + 24, x=CL + wf + 18, max_w=wf, max_h=246)
B.band(s, YS + 24 + bh2 + 16, 76, [
    "Der Kunde sieht Speisekarte und Bestellknopf. Die zuschaltbare Datensicht zeigt, was "
    "derselbe Seitenaufruf nebenbei erzeugt: eine Sitzung mit Gerät, Herkunft und Standort, "
    "einen Ereignisstrom je sichtbarer Sektion, die Klickraten der Bestellknöpfe. Dazu steht "
    "dort, welche Rechtsgrundlage dieses Beobachten überhaupt erlaubt."])

# Webshop-ER
s = deck.neu("Lisa_Slide")
B.kopf(s, "System Website", "Bestellen braucht drei Tabellen — Beobachten braucht zwei mehr", QUELLE)
deck.einl(s, "Das Bestellen selbst kommt mit Sitzung, Warenkorbposition und Artikelstamm aus. "
             "Was die Datensicht eben gezeigt hat, braucht zwei Tabellen mehr: die Sitzung "
             "trägt Herkunft, Gerät und Testvariante, und jede Interaktion wird ein Ereignis. "
             "Ein Kunde ist optional — beobachtet wird auch, wer sich nie anmeldet.")
bw5, _ = deck.bild(s, "17_webshop_er", y=Y0, max_h=HOEHE)
B.kachel(s, CL + bw5 + 20, Y0, CR - (CL + bw5 + 20), 196, GOOD, "Vom Klick zur Kachel",
         ["ereignistyp und verweildauer_ms speisen später Konversions- und Engagement-Kennzahlen.",
          "cta_variant macht den A/B-Test auswertbar.",
          "Der Laden kann das alles nicht messen — nur der Webshop sieht, was vor dem Kauf passiert."])

# Kasse: Datensicht
s = deck.neu("Tool_Slide")
B.kopf(s, "System Kasse", "Jeder Klick an der Kasse schreibt eine Zeile", Q_FOTO)
deck.einl(s, "Die Kasse des Projekts hat einen zuschaltbaren Modus, der zu jedem Bedienschritt "
             "zeigt, welcher Datensatz dabei entsteht. Wer ein Produkt antippt, sieht die Zeile "
             "in fact_order_items; wer kassiert, sieht den Kopfsatz in fact_orders. Genau diese "
             "Zeilen wertet das Dashboard später aus.", "Tool_Slide")
bw, _ = deck.foto(s, "03b_pos_daten", max_h=HOEHE)
B.sprechblase(s, CL + bw + 24, Y0, CR - (CL + bw + 24), 200, D.paras([
    [("Vom Klick zur Kennzahl", True, METHOD)],
    ["Produktauswahl füllt Menge, Einzelpreis und Positionssumme."],
    ["Der Bezahlvorgang füllt Filiale, Kanal, Zahlungsart und Zufriedenheit."],
    ["Der Kundenkartenscan verbindet die Bestellung mit dim_customer — erst dadurch "
     "werden Segmentierung und Wiederkaufsraten überhaupt rechenbar."],
]), farbe=METHOD)

# POS-ER
s = deck.neu("Lisa_Slide")
B.kopf(s, "System Kasse", "Der Kassenbeleg: zehn Felder, fünf Bezüge — drei Kennzahlen von morgen", QUELLE)
deck.einl(s, "Die Kasse schreibt in den Verkaufsbereich der Warenwirtschaft: einen Kopf je "
             "Bestellung, eine Position je Artikel. Drei Felder sind operativ nur Beiwerk des "
             "Belegs — bestellkanal, bestelldauer_min und zufriedenheit. Analytisch werden "
             "genau sie zu Kanalanteil, Wartezeitanalyse und Zufriedenheitswert des Dashboards.")
deck.bild(s, "18_pos_er", y=Y0, max_h=HOEHE)

# Abgrenzung operativ / analytisch
s = deck.neu("Lisa_Slide")
B.kopf(s, "Abgrenzung", "Transaktionssysteme antworten je Vorgang, Analysesysteme je Frage", QUELLE)
deck.einl(s, "Shop und Kasse sind Transaktionssysteme: Sie verarbeiten einen Vorgang nach dem "
             "anderen und müssen dabei jederzeit widerspruchsfrei sein. Die Auswertung stellt "
             "die umgekehrte Anforderung — eine Frage über Millionen vergangener Vorgänge. "
             "Beide Anforderungen in einem System zu erfüllen, hieße, beide schlecht zu erfüllen.")
B.gegenueber(s, Y0, 216,
             (BLUE, "Operativ · OLTP",
              ["Arbeitseinheit: ein Vorgang — eine Bestellung wird angelegt, geändert, bezahlt.",
               "Datenstand: das Jetzt. Was erledigt ist, wird nicht mehr angefasst.",
               "Modell: dritte Normalform, damit nichts doppelt steht und nichts widersprechen kann.",
               "Lastprofil: sehr viele kleine Schreibzugriffe, Antwort in Millisekunden je Vorgang."]),
             (GOOD, "Analytisch · OLAP",
              ["Arbeitseinheit: eine Frage — Umsatz je Filiale über neun Jahre.",
               "Datenstand: die Historie. Es wird gelesen und periodisch neu beladen, nie korrigiert.",
               "Modell: bewusst redundant, damit wenige Verknüpfungen genügen.",
               "Lastprofil: wenige große Lesezugriffe über Millionen Zeilen."]),
             badge_l="⇄", badge_r="Σ")
B.band(s, Y0 + 232, 54, [
    "Entscheidungsrelevant sind Daten erst in der rechten Spalte: vollständig, historisch, "
    "vergleichbar — und vom laufenden Betrieb entkoppelt, damit die Frage den Betrieb nicht stört."])

s = deck.neu("Lisa_Slide")
B.kopf(s, "Grundlage", "Der Bestand, über den in diesem Deck geredet wird", Q_MESS)
deck.einl(s, "Alle Zahlen dieses Decks stammen aus demselben Bestand und sind mit DuckDB "
             "gegen die Rohdaten nachgerechnet. Er umfasst neun Jahre, in denen die Kette von "
             "einer auf acht Filialen wuchs — diese gestaffelte Eröffnung ist der Grund, warum "
             "absolute Filialvergleiche in die Irre führen.")
B.kennzahlen(s, Y0, 88, [
    ("Bestellungen", "754.513", BLUE),
    ("Positionen", "2.950.082", BLUE),
    ("Kunden mit Bestellung", "24.992", BLUE),
    ("Filialen", "8", BLUE),
])
B.kachel(s, CL, Y0 + 104, w2, 150, HINT, "Zwei Zahlen, die auseinandergehen",
         ["dim_customer führt 25.000 Kundensätze, aber nur 24.992 haben je bestellt.",
          "Acht Kunden ohne Bestellung — im Modell zulässig, in der Kennzahl ein Unterschied.",
          "Wer Kunden zählt, muss sagen, welche der beiden Zahlen gemeint ist."])
B.kachel(s, CL + w2 + 18, Y0 + 104, w2, 150, METHOD, "Wo die Zahlen herkommen",
         ["dataset/ enthält 13 CSV-Dateien, zusammen 311,4 MB.",
          "Nach dem Laden in DuckDB belegt der Bestand 54,5 MB.",
          "dataset/verify_readme.py rechnet 79 Kennzahlen gegen die Rohdaten nach."])

# ═══════════════════════════════════════════════════ Teil 2
deck.kapitel("Kennzahlen definieren, rechnen und prüfen")

s = deck.neu("Lisa_Slide")
B.kopf(s, "Definition", "Umsatz 2025 — drei zulässige Antworten auf eine Frage", Q_MESS)
deck.einl(s, "Wer nach dem Umsatz 2025 fragt, bekommt je nach Spalte eine andere Zahl. Alle "
             "drei sind richtig gerechnet und meinen etwas anderes. Der Unterschied zwischen "
             "der ersten und der dritten beträgt 37.875 EUR — genug, um eine Zielerreichung "
             "zu kippen, zu klein, um im Diagramm aufzufallen.")
B.kennzahlen(s, Y0, 88, [
    ("SUM(gross_total)", "3.032.646 €", D.SEC),
    ("SUM(discount_amount)", "37.875 €", D.SEC),
    ("SUM(net_total)", "2.994.771 €", BLUE),
])
B.kachel(s, CL, Y0 + 104, CW, 108, BLUE, "Was das Dashboard verwendet — und warum",
         ["Das Dashboard zeigt den Nettobetrag: das, was tatsächlich vereinnahmt wurde.",
          "Die Positionssummen aus fact_order_items ergeben exakt den Bruttobetrag — "
          "Rabatte hängen am Bestellkopf, nicht an der Position.",
          "Eine Kennzahl, die den Rabatt einmal abzieht und einmal nicht, ist kein Rundungsfehler."])
B.band(s, Y0 + 224, 52, [
    "Regel: Der Name einer Kennzahl ist nie ihre Definition. Die Definition ist die Formel "
    "samt Spalte, Zeitraum und Grundgesamtheit."])

s = deck.neu("Tool_Slide")
B.kopf(s, "Umsetzung", "Acht Kacheln, acht Definitionen, ein Vergleichszeitraum", Q_FOTO)
deck.einl(s, "Die Kopfzeile des Dashboards trägt acht Kennzahlen. Jede nennt ihren Zeitraum, "
             "ihren Vorjahreswert und ihre Grundgesamtheit — der Zusatz unter der Zahl ist "
             "nicht Beiwerk, sondern der Teil, der sie prüfbar macht. Ohne ihn stünde dort "
             "eine Behauptung.", "Tool_Slide")
_, bh = deck.foto(s, "04_dash_kpi", y=Y0, max_h=168)
B.kachel(s, CL, Y0 + bh + 18, w2, 136, GOOD, "Was jede Kachel mitliefert",
         ["Zeitraum: 2025, nicht rollierende zwölf Monate.",
          "Vergleichswert und Veränderung: 2.841.075 EUR, plus 5,4 Prozent.",
          "Grundgesamtheit: 136.557 Bestellungen."])
B.kachel(s, CL + w2 + 18, Y0 + bh + 18, w2, 136, HINT, "Was sie nicht mitliefert",
         ["Die Formel. Ob Umsatz brutto oder netto gemeint ist, steht nicht auf der Kachel.",
          "Wer es wissen will, muss in den Quelltext oder in die Dokumentation sehen.",
          "In einem BI-Werkzeug übernähme das die Semantikschicht — siehe Kapitel 5."])

s = deck.neu("Slide")
B.kopf(s, "Prüfung", "Drei Angaben machen aus einer Zahl eine Kennzahl", Q_EIG)
for i, (t, b, c) in enumerate([
    ("Zeitraum", ["Vom 1.1. bis 31.12.2025, nicht rollierende zwölf Monate.",
                  "Der Bestand beginnt am 15.03.2017 und endet am 31.03.2026.",
                  "2017 und 2026 sind Rumpfjahre — Jahresvergleiche mit ihnen sind schief."], BLUE),
    ("Grundgesamtheit", ["Alle acht Filialen oder nur die seit 2017 offenen?",
                         "Alle Kanäle oder nur der Tresen?",
                         "Bei gestaffelter Eröffnung entscheidet diese Angabe über das Ergebnis."], METHOD),
    ("Formel", ["Welche Spalte, welche Aggregation, welche Verknüpfung.",
                "SUM(net_total) über fact_orders ist etwas anderes als über die Positionen.",
                "Die Formel gehört in die Dokumentation, nicht in den Kopf des Analysten."], GOOD),
]):
    B.kachel(s, CL + i * (w3 + 18), Y0, w3, 190, c, t, b)
B.band(s, Y0 + 206, 88, [
    "Ein Beispiel aus diesem Projekt: Umsatz je Quadratmeter. Über das Jahr 2025 führt "
    "BM Hauptbahnhof mit 2.197 EUR je Quadratmeter — bei nur 180 Quadratmetern Fläche. Über "
    "den gesamten Zeitraum 2017 bis 2026 lautet dieselbe Kennzahl 12.254 EUR. Beide Zahlen "
    "sind richtig; ohne die Zeitangabe ist keine von beiden brauchbar."])

s = deck.neu("Lisa_Slide")
B.kopf(s, "Prüfhandwerk", "Nachgerechnet ist etwas anderes als nachgesehen", Q_MESS)
deck.einl(s, "Ein Dashboard ist eine Behauptung über Daten. Wer es baut, muss sie unabhängig "
             "prüfen können — mit einem zweiten Rechenweg, nicht mit einem zweiten Blick auf "
             "dieselbe Abfrage. Für dieses Projekt sind alle Kennzahlen mit pandas und DuckDB "
             "getrennt nachgerechnet worden.")
B.gegenueber(s, Y0, 190,
             (GOOD, "Was eine Prüfung ist",
              ["Der Wert wird aus den Rohdaten neu berechnet, auf einem anderen Weg.",
               "Die Definition wird vorher schriftlich festgehalten, nicht nachträglich angepasst.",
               "Abweichungen werden benannt, auch wenn sie klein sind — "
               "dataset/verify_readme.py prüft 79 Angaben und meldet jede einzeln."]),
             (WARN, "Was keine ist",
              ["Die Zahl sieht plausibel aus.",
               "Zwei Kacheln im selben Dashboard zeigen dasselbe — sie stammen aus derselben Abfrage.",
               "Ein Produktfilter wie LIKE '%Cola%' trifft auch den Milchshake "
               "Chocolate: Wer Namen filtert statt Schlüssel, prüft nicht, sondern rät."]),
             badge_l="+", badge_r="−")

# ═══════════════════════════════════════════════════ Teil 3
deck.kapitel("Vom Auswertungsmodell zum Dashboard")

s = deck.neu("Lisa_Slide")
B.kopf(s, "Modell", "Was nicht modelliert ist, kann kein Bericht zeigen", QUELLE)
deck.einl(s, "Das Auswertungsmodell setzt die Grenze dessen, was gefragt werden kann. Zwei "
             "Faktentabellen messen auf zwei Ebenen: fact_orders je Bestellung, "
             "fact_order_items je Position. Umsatz je Kategorie braucht die Positionsebene, "
             "Bestellwert und Rabatt gibt es nur auf Bestellebene.")
deck.bild(s, "07_galaxy", y=Y0, max_h=HOEHE)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Rechenweg", "Der Weg einer einzigen Zahl, in vier Schritten", Q_MESS)
deck.einl(s, "Hinter der größten Kachel des Dashboards steht keine Magie, sondern eine "
             "Abfrage mit vier Schritten. Wer sie kennt, kann jede Kachel selbst nachbauen — "
             "und erkennt, an welcher Stelle eine abweichende Entscheidung eine andere Zahl "
             "erzeugen würde.")
deck.bild(s, "13_bi_kennzahlweg", y=Y0 + 4, max_h=110)
B.kachel(s, CL, Y0 + 132, CW, 118, METHOD, "Wo die Entscheidungen stecken",
         ["Der Filter legt den Zeitraum fest — Kalenderjahr, nicht rollierend.",
          "Die Gruppierung legt die Auflösung fest — hier keine, deshalb eine einzige Zahl.",
          "Die Aggregation legt die Spalte fest — net_total, nicht gross_total.",
          "Erst der vierte Schritt formatiert: 2.994.771 EUR wird zu 2,99 Mio. EUR."])
B.band(s, Y0 + 258, 64, [
    "Dieselbe Abfrage mit GROUP BY branch_id liefert die Filialtabelle, mit GROUP BY month "
    "den Verlauf. Ein Dashboard ist im Kern eine Handvoll solcher Abfragen — der Aufwand "
    "steckt in den Definitionen, nicht im SQL."])

# GROUP BY: aus der Zahl wird eine Tabelle
s = deck.neu("Tool_Slide")
B.kopf(s, "Auflösung", "Ein GROUP BY mehr, und aus der Kachel wird ein Filialvergleich", Q_FOTO)
deck.einl(s, "Dieselbe Abfrage, um GROUP BY branch_id ergänzt, liefert statt einer Zahl acht — "
             "das Balkendiagramm des Filialreiters. Die Auflösung einer Kennzahl ist damit "
             "keine Frage des Werkzeugs, sondern eine Zeile SQL. Gefährlich wird es erst bei "
             "der Deutung des Ergebnisses.", "Tool_Slide")
_, bh3 = deck.foto(s, "10_dash_filialen", y=Y0, max_h=190)
B.kachel(s, CL, Y0 + bh3 + 12, CW, 112, WARN, "Der Basiseffekt steckt schon im Balken",
         ["Das Diagramm zeigt kumulierten Umsatz 2017 bis 2026 — aber die Filialen eröffneten "
          "gestaffelt: Europastern führt auch deshalb, weil es seit 2017 mitläuft.",
          "BM Zellerau ist seit 2023 dabei und hat zugleich den höchsten Bestellwert (21,05 EUR).",
          "Vergleichbar werden die Balken erst je Betriebsmonat oder je Quadratmeter."])

s = deck.neu("Tool_Slide")
B.kopf(s, "Darstellung", "Der Titel eines Diagramms ist seine Aussage, nicht sein Etikett", Q_FOTO)
deck.einl(s, "Die Zeitreihe trägt keinen Titel wie Umsatzentwicklung, sondern einen Satz: "
             "Umsatz wächst seit 2021 kontinuierlich, Wachstum verlangsamt sich aber. Damit "
             "steht die Lesart fest, bevor jemand die Kurve deutet — und lässt sich am "
             "Diagramm überprüfen.", "Tool_Slide")
bw, _ = deck.foto(s, "05_dash_verlauf", max_w=600, max_h=HOEHE)
B.sprechblase(s, CL + bw + 24, Y0, CR - (CL + bw + 24), 232, D.paras([
    [("Drei Entscheidungen im Bild", True, METHOD)],
    ["Monatswerte statt Jahreswerte: Der Einbruch 2020 bliebe sonst unsichtbar."],
    ["Nullpunkt auf der Achse, weil die Fläche unter der Linie mitgelesen wird."],
    ["Der markierte Höchstwert ist ein einzelner Monat, kein Trend — deshalb "
     "steht die Verlangsamung im Titel und nicht der Rekord."],
]), farbe=METHOD)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Bauweise", "Dieses Dashboard rechnet nicht — es zeigt Ausgerechnetes", Q_EIG)
deck.einl(s, "Die Zahlen im Dashboard stehen fest im Quelltext der Seite. Das ist keine "
             "Abkürzung aus Bequemlichkeit, sondern eine Entscheidung mit Vor- und Nachteilen — "
             "und sie ist der Grund, warum die Seite ohne Server, ohne Datenbank und ohne "
             "Anmeldung auf GitHub Pages läuft.")
B.klammer(s, CL, Y0, w2, 170, "Was die feste Verdrahtung bringt",
          D.paras(["Keine Infrastruktur: eine HTML-Datei, überall lauffähig, in Sekunden geladen.",
                   "Nachvollziehbarkeit: Jede Zahl steht im Quelltext und ist gegen die "
                   "Rohdaten prüfbar.",
                   "Für die Lehre entfällt jede Hürde zwischen Studierenden und dem Ergebnis."]), GOOD)
B.klammer(s, CL + w2 + 18, Y0, w2, 170, "Was sie kostet",
          D.paras(["Neue Daten heißen neuer Bauschritt — im Betrieb aktualisiert sich nichts.",
                   "Kein freies Filtern jenseits der vorbereiteten Sichten.",
                   "In einem echten Betrieb gehörte hier ein BI-Werkzeug mit Verbindung "
                   "zur Datenbank hin."]), HINT)
B.band(s, Y0 + 190, 84, [
    "Die Entscheidung ist an die Aufgabe gebunden, nicht an den Geschmack: Für ein "
    "Lehrmaterial, das jederzeit ohne Zugangsdaten laufen soll, ist die feste Verdrahtung "
    "richtig. Für einen Betrieb, der morgens die Zahlen von gestern braucht, ist sie falsch. "
    "Kapitel 5 zeigt, was dann an ihre Stelle tritt."])

# ═══════════════════════════════════════════════════ Teil 4
deck.kapitel("Von der Zahl zur Entscheidung")

s = deck.neu("Tool_Slide")
B.kopf(s, "Segmentierung", "Aus 24.992 Kunden werden sieben handhabbare Gruppen", Q_FOTO)
deck.einl(s, "Einzelne Kunden sind keine Entscheidungsgrundlage, der Durchschnitt aller Kunden "
             "auch nicht. Die RFM-Segmentierung ordnet jeden Kunden nach Kaufabstand, Häufigkeit "
             "und Umsatz ein. Erst dadurch wird aus einer Gesamtzahl eine Liste, die eine "
             "Marketingabteilung abarbeiten kann.", "Tool_Slide")
bw, _ = deck.foto(s, "07_dash_rfm", max_h=HOEHE)
B.sprechblase(s, CL + bw + 24, Y0, CR - (CL + bw + 24), 236, D.paras([
    [("Was die Grafik zur Entscheidung macht", True, GOOD)],
    ["5.484 Kunden gelten als abwanderungsgefährdet — 21,9 Prozent des Bestands."],
    ["Die Gruppe ist benannt, gezählt und adressierbar: eine Liste, kein Befund."],
    ["Die Empfehlung unter der Grafik nennt Maßnahme, erwarteten Effekt und Kosten. "
     "Ohne diesen letzten Schritt bliebe es eine Sortierung."],
]), farbe=GOOD)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Ableitung", "Jede Gruppe verlangt eine andere Maßnahme", Q_EIG)
deck.einl(s, "Eine Segmentierung ist nur so viel wert wie die Unterscheidung, die sie in den "
             "Maßnahmen erlaubt. Champions und Abwanderungsgefährdete mit derselben Kampagne "
             "anzusprechen, verschenkt beide. Die Zuordnung von Segment zu Maßnahme ist eine "
             "betriebswirtschaftliche Entscheidung, keine statistische.")
B.zuordnung(s, Y0, [
    ("Champions",
     "4.082 Kunden, 16,3 Prozent, im Schnitt 842 EUR Lebenswert. Halten, nicht rabattieren — "
     "ein Rabatt an diese Gruppe kostet Marge ohne Verhaltensänderung."),
    ("Abwanderungsgefährdet",
     "5.484 Kunden, seit 132 Tagen inaktiv, 4,07 Mio. EUR Umsatzrisiko. "
     "Reaktivierung lohnt hier am ehesten, weil die Kaufbereitschaft belegt ist."),
    ("Neukunden",
     "2.027 Kunden mit erst wenigen Käufen. Ziel ist die zweite Bestellung — "
     "die Kennzahl dafür ist die Wiederkaufrate, nicht der Umsatz."),
    ("Verloren",
     "4.396 Kunden, im Schnitt 249 Tage inaktiv. Hier ist die ehrlichste Entscheidung "
     "meist, kein Geld mehr auszugeben."),
], rh=54.0)

s = deck.neu("Tool_Slide")
B.kopf(s, "Warenkorbanalyse", "Lift trennt echten Zusammenhang von bloßer Häufigkeit", Q_FOTO)
deck.einl(s, "Dass Pommes und Cola oft zusammen gekauft werden, ist keine Erkenntnis — beide "
             "sind einzeln häufig. Der Lift setzt die gemeinsame Häufigkeit ins Verhältnis zu "
             "der, die bei Unabhängigkeit zu erwarten wäre. Erst ab deutlich über 1 steckt ein "
             "Zusammenhang dahinter.", "Tool_Slide")
bw, _ = deck.foto(s, "06_dash_regeln", max_w=600, max_h=HOEHE)
B.klammer(s, CL + bw + 30, Y0, CR - (CL + bw + 30), 230, "Die Linie bei 1 ist die Nulllinie",
          D.paras(["Nur 3 der 15 untersuchten Produktpaare liegen über Lift 2.",
                   "Die grauen Paare mit Lift zwischen 1,1 und 1,5 werden häufig zusammen "
                   "gekauft, aber nicht häufiger als zufällig zu erwarten.",
                   "Eine Bündelaktion auf ein Paar mit Lift 1,1 gäbe Rabatt auf Käufe, "
                   "die ohnehin stattgefunden hätten."]), WARN)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Kennzahlenkunde", "Konfidenz überzeugt, Lift entscheidet", QUELLE)
deck.einl(s, "Support, Konfidenz und Lift beschreiben dieselbe Regel aus drei Richtungen. Wer "
             "nur die Konfidenz betrachtet, wird von häufigen Produkten in die Irre geführt: "
             "Eine Regel mit 66 Prozent Konfidenz klingt zwingend, sagt aber nichts, solange "
             "der Bezug zur Grundhäufigkeit fehlt.")
B.gegenueber(s, Y0, 190,
             (HINT, "Konfidenz — wie oft folgt B auf A",
              ["Fries + Cola 0.3l: 66,1 Prozent der Fries-Käufe enthalten auch diese Cola.",
               "Klingt nach einer starken Regel und ist leicht zu erzählen.",
               "Der Wert steigt allein dadurch, dass B insgesamt häufig ist — "
               "ein Verkaufsschlager erscheint dadurch in fast jeder Regel."]),
             (GOOD, "Lift — wie viel häufiger als zufällig",
              ["Dasselbe Paar erreicht Lift 3,29: dreimal häufiger als bei Unabhängigkeit.",
               "Lift um 1 heißt: kein nachweisbarer Zusammenhang, egal wie hoch die Konfidenz ist.",
               "Beyond Burger + Side Salad erreicht 2,28 — der bemerkenswerteste Befund, "
               "weil er ein Kaufmotiv sichtbar macht und nicht nur eine Gewohnheit."]),
             badge_l="~", badge_r="!")

s = deck.neu("Tool_Slide")
B.kopf(s, "Simulation", "Erst die Durchrechnung macht aus einer Idee eine Entscheidung", Q_FOTO)
deck.einl(s, "Die Preissimulation verbindet eine Annahme über die Preiselastizität mit den "
             "tatsächlichen Absatzmengen. Sie liefert keine Wahrheit, sondern eine "
             "Größenordnung — und sie macht die Annahme sichtbar, statt sie im Kopf des "
             "Entscheiders zu lassen.", "Tool_Slide")
bw, _ = deck.foto(s, "08_dash_simulation", max_h=HOEHE)
xa = CL + bw + 30
B.textbox(s, xa, Y0, CR - xa, 20, [("Woher jede Eingangsgröße stammt", True, BLUE)], 13)
B.ampel(s, xa, Y0 + 28, 17, [GOOD, HINT, WARN], D.paras([
    "Gemessen: Absatzmengen, Einzelpreise und Umsätze je Produkt stehen im Bestand.",
    "Geschätzt: Die Preiselastizität von −1,2 ist gesetzt, nicht aus Preisversuchen abgeleitet — "
    "deshalb steht sie als Regler da und nicht als Zahl im Text.",
    "Nicht enthalten: Reaktionen des Wettbewerbs und Ausweichkäufe auf andere Produkte.",
]), CR - xa - 32, gap=18)

# Trends als Investitionsgrundlage
s = deck.neu("Tool_Slide")
B.kopf(s, "Trends", "Eine Momentaufnahme rechtfertigt keine Investition — ein Trend schon", Q_FOTO)
deck.einl(s, "Dass 2026 noch 18,4 Prozent bar zahlen, ist eine Zahl. Dass es 2017 noch 48,9 "
             "Prozent waren und die Kurve seit neun Jahren fällt, ist ein Trend — und erst der "
             "trägt eine Entscheidung über Infrastruktur, weil er sagt, wohin sich die Lage "
             "bewegt und wie schnell.", "Tool_Slide")
bw4, _ = deck.foto(s, "11_dash_trends", max_w=560, max_h=HOEHE)
B.klammer(s, CL + bw4 + 30, Y0, CR - (CL + bw4 + 30), 240, "Was aus der Kurve folgt",
          D.paras(["Kartenterminals sind keine Option mehr, sondern Grundausstattung — "
                   "81,6 Prozent zahlen 2026 unbar.",
                   "Bargeldprozesse (Wechselgeld, Abschöpfung, Zählung) schrumpfen planbar mit.",
                   "Mobile Payment wächst von 1,0 auf 13,7 Prozent — die jüngste Zahlart "
                   "mit dem steilsten Anstieg gehört in jede neue Filiale."]), GOOD)

s = deck.neu("Slide")
B.kopf(s, "Ergebnis", "Vier Entscheidungen, die dieser Bestand tatsächlich trägt", Q_MESS)
w4 = (CW - 3 * 14) / 4
for i, (t4, b4) in enumerate([
    ("Personaleinsatz", ["Samstag 517.114 EUR, Dienstag 363.065 EUR.",
                         "42 Prozent Unterschied bei gleicher Öffnungszeit.",
                         "Die Schichtplanung folgt dem Umsatz, nicht dem Kalender."]),
    ("Sortiment", ["Beyond Burger: 30.597 Stück im Jahr 2025.",
                   "10,4 Prozent des Positionsumsatzes.",
                   "Verfügbarkeit hat hier Vorrang vor Vielfalt."]),
    ("Standort", ["BM Hauptbahnhof 2.197 EUR je Quadratmeter und Jahr.",
                  "BM Zellerau 1.375 EUR bei größerer Fläche.",
                  "Nicht die Summe entscheidet, sondern die Flächenleistung."]),
    ("Kundenbindung", ["5.484 gefährdete Kunden, 4,07 Mio. EUR Umsatzrisiko.",
                       "Eine adressierbare Liste, kein Befund.",
                       "Der Reaktivierungsversuch ist gegen diesen Betrag rechenbar."]),
]):
    B.kachel(s, CL + i * (w4 + 14), Y0, w4, 196, GOOD, t4, b4)
B.band(s, Y0 + 212, 88, [
    "Der gemeinsame Zug: Jede dieser Entscheidungen nennt eine Zahl, eine Handlung und "
    "einen Betrag, gegen den sich der Aufwand rechnen lässt. Kennzahlen, für die sich kein "
    "solcher Satz formulieren lässt, gehören nicht auf ein Dashboard, sondern in den Anhang."])

s = deck.neu("Tool_Slide")
B.kopf(s, "Verdichtung", "Am Ende steht keine Kachel, sondern ein lesbarer Bericht", Q_FOTO)
deck.einl(s, "Ein Dashboard ist ein Werkzeug für den, der täglich damit arbeitet. Wer einmal "
             "im Quartal entscheidet, braucht etwas anderes: nummerierte Abschnitte, je Befund "
             "eine Zahl und einen Satz, keine Bedienung. Dieselben Daten, eine andere "
             "Darreichungsform — und deutlich schwerer zu bauen.", "Tool_Slide")
bw, _ = deck.foto(s, "09_dash_summary", max_w=520, max_h=HOEHE)
B.sprechblase(s, CL + bw + 24, Y0, CR - (CL + bw + 24), 250, D.paras([
    [("Was diese Form verlangt", True, BLUE)],
    ["Jede Zahl steht neben ihrer Deutung — die Zahl allein sagt einem Aufsichtsrat nichts."],
    ["Die Reihenfolge ist eine Wertung: Umsatz zuerst, dann Filialen, dann Kunden."],
    ["Was hier nicht steht, ist entschieden worden: Auslassen ist die eigentliche "
     "Leistung einer Verdichtung, nicht das Zusammenstellen."],
]), farbe=BLUE)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Grenzen", "Was dieser Bestand nicht hergibt — und trotzdem gern behauptet wird", Q_EIG)
deck.einl(s, "Die häufigsten Fehler in Auswertungen sind keine Rechenfehler, sondern "
             "Überdehnungen: Ein Muster wird für eine Ursache gehalten, ein Wachstum für eine "
             "Leistung, eine Schätzung für eine Messung. Drei davon stecken in diesem Bestand "
             "und sind bewusst eingebaut.")
for i, (t, b, c) in enumerate([
    ("Keine Kausalität", ["Wetter und Umsatz laufen parallel — die Richtung sagen die Daten nicht.",
                          "Ein Regentag verändert auch Wochentag und Kanal.",
                          "Für Ursachen braucht es ein Experiment, nicht eine weitere Abfrage."], WARN),
    ("Basiseffekt", ["Filialen eröffneten zwischen 2017 und 2023 gestaffelt.",
                     "Absolute Filialumsätze vergleichen deshalb Ungleiches.",
                     "Erst die Normierung auf Betriebsmonate oder Fläche macht sie vergleichbar."], WARN),
    ("Geschätzte Annahmen", ["Die Preiselastizität von −1,2 ist gesetzt, nicht gemessen.",
                             "Der Lebenswert je Segment beruht auf der bisherigen Historie.",
                             "Beides sind Rechengrundlagen, keine Befunde — und gehören so benannt."], WARN),
]):
    B.kachel(s, CL + i * (w3 + 18), Y0, w3, 190, c, t, b)

# ═══════════════════════════════════════════════════ Teil 5
deck.kapitel("Architektur, Werkzeuge, Nachbau")

s = deck.neu("Lisa_Slide")
B.kopf(s, "Bauarten", "Vier Wege von der Datenbank zum Bericht", Q_EIG)
deck.einl(s, "Dieselbe Auswertung lässt sich sehr verschieden bauen. Die Wege unterscheiden "
             "sich darin, wo gerechnet wird und wann: im Quellsystem beim Aufruf, im Abzug beim "
             "Aufruf, in einer Semantikschicht beim Aufruf — oder vorab, wie in diesem Projekt. "
             "Jede Verschiebung nach links kostet Aktualität und spart Betrieb.")
deck.bild(s, "14_bi_architekturen", y=Y0, max_h=HOEHE)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Semantikschicht", "Die Kennzahl einmal definieren, nicht in jedem Werkzeug", QUELLE)
deck.einl(s, "Sobald mehr als ein Werkzeug auf denselben Bestand sieht, entsteht die Frage, wo "
             "die Formel für Umsatz steht. Liegt sie im Werkzeug, gibt es sie so oft wie "
             "Werkzeuge. Die Semantikschicht zieht sie heraus und stellt sie allen zur "
             "Verfügung — 2026 vor allem deshalb im Gespräch, weil auch Sprachmodelle sie brauchen.")
bw, _ = deck.bild(s, "15_bi_semantik", y=Y0 + 10, max_h=200)
B.kachel(s, CL + bw + 24, Y0, CR - (CL + bw + 24), 236, METHOD, "Womit das gebaut wird",
         ["In das Werkzeug eingebaut: Power BI, Looker (LookML), Holistics.",
          "Eigenständig, für mehrere Verbraucher: dbt Semantic Layer, Cube, AtScale.",
          "In der Datenplattform: Snowflake, Databricks.",
          "Für BurgerMetrics wäre die schlanke Form eine Datei mit SQL-Sichten — "
          "die Schicht ist ein Prinzip, kein Produkt."])
B.band(s, Y0 + 244, 78, [
    "Der Prüfstein ist banal und wirksam: Fragt man drei Berichte nach dem Umsatz 2025 und "
    "bekommt drei Zahlen, fehlt die Schicht — unabhängig davon, wie modern der Rest gebaut ist."])

s = deck.neu("Slide")
B.kopf(s, "Werkzeugmarkt", "Das BI-Frontend ist eine Wahl zwischen vier Bauarten", Q_MARKT)
deck.bewertung(s, Y0,
               ["Zugang für Fachbereiche", "Versionierbarkeit", "Betriebsaufwand",
                "Bindung an einen Anbieter"],
               [("Power BI · Tableau · Qlik", [1.00, 0.20, 0.55, 0.90], False),
                ("Metabase · Superset", [0.80, 0.40, 0.60, 0.15], False),
                ("Evidence · Rill · Lightdash", [0.35, 1.00, 0.35, 0.15], True),
                ("Eigene Seite, vorab gerechnet", [0.15, 1.00, 0.10, 0.00], True)],
               rh=42.0, bw=236.0)
B.band(s, Y0 + 234, 86, [
    "Marktlage 2026: Power BI und Tableau stellen zusammen rund 40 Prozent der eingesetzten "
    "Plattformen; im Gartner-Quadranten vom Juni 2026 stehen Microsoft, Salesforce und Qlik "
    "im Führungsfeld. Für dieses Projekt zählt die zweite und dritte Zeile: Was im "
    "Versionsverwaltungssystem liegt, lässt sich in der Lehre zeigen und nachbauen."])

# Bauanleitung, technologieoffen
s = deck.neu("Slide")
B.kopf(s, "Bauanleitung", "Vier Schritte, die in jedem Technologiestapel dieselben sind", Q_EIG)
B.zuordnung(s, Y0, [
    ("1 · Exportieren",
     "Rohdaten aus dem Quellsystem ziehen, unverändert ablegen. Hier: 13 CSV-Dateien. "
     "Anderswo: ein Datenbank-Dump, eine API, ein Excel-Export — jedes System kann das."),
    ("2 · Laden",
     "Die Rohdaten in eine analytische Datenbank übernehmen, eine Tabelle je Datei. "
     "Hier: DuckDB. Alternativen: SQLite für den Anfang, PostgreSQL im Team, "
     "BigQuery oder Snowflake, wenn der Bestand eine Maschine übersteigt."),
    ("3 · Modellieren",
     "Kennzahlen und Sichten als SQL in versionierten Dateien: raw unangetastet, stg "
     "typisiert, mart denormalisiert. Dasselbe Prinzip heißt im Werkzeug dbt — "
     "gebraucht wird das Werkzeug erst, wenn die Abhängigkeiten unübersichtlich werden."),
    ("4 · Zeigen",
     "Ein Frontend an die Datenbank hängen. Hier: eine statische Seite mit vorab "
     "gerechneten Zahlen. Alternativen: Metabase oder Superset zum Klicken, Evidence "
     "für Berichte als Code, Power BI oder Tableau im Unternehmensumfeld."),
], rh=58.0)
B.band(s, Y0 + 258, 62, [
    "Schritt 3 ist im Repo vorgeführt: dataset/wawi_mini.sql (operativer Ausschnitt, 14 Tabellen, "
    "deutsch) und dataset/wawi_zu_analytisch.sql (die Joins) erzeugen nachweislich dieselben "
    "Tabellen wie burgermetrics_mini.sql — acht von acht zeilengleich."])

s = deck.neu("Lisa_Slide")
B.kopf(s, "Nachbau", "Was davon an einem Nachmittag nachzubauen ist", Q_EIG)
deck.einl(s, "Der Aufbau dieses Projekts ist bewusst so gewählt, dass er ohne Lizenz, ohne "
             "Server und ohne Cloud-Zugang nachvollzogen werden kann. Wer die vier Schritte "
             "geht, hat am Ende dieselbe Kette vom Rohdatensatz bis zur Kachel — mit eigenen "
             "Kennzahlen und eigenen Fragen.")
B.chevron_kette(s, Y0, 40, ["1 · CSV laden", "2 · Modell bauen", "3 · Kennzahlen rechnen",
                            "4 · Bericht erzeugen"])
B.kachel(s, CL, Y0 + 58, w2, 148, METHOD, "Womit",
         ["dataset/load_duckdb.py lädt die 13 CSV-Dateien in 2,3 Sekunden.",
          "dataset/burgermetrics_mini.sql ist die 13-KB-Fassung zum Mitlesen.",
          "Für den Bericht genügt Evidence oder Metabase — beide sprechen DuckDB."])
B.kachel(s, CL + w2 + 18, Y0 + 58, w2, 148, GOOD, "Woran ihr merkt, dass es stimmt",
         ["Der Umsatz 2025 muss 2.994.771 EUR ergeben, nicht 3.032.646 EUR.",
          "Die Summe der Positionen ergibt den Bruttobetrag — wer den Nettobetrag erhält, "
          "hat die falsche Spalte erwischt.",
          "dataset/verify_readme.py sagt euch, ob 79 von 79 Angaben stimmen."])
B.band(s, Y0 + 222, 96, [
    "Der lehrreichste Teil kommt danach: eine eigene Frage stellen, für die es noch keine "
    "Kachel gibt. Wer sie beantworten will, muss Zeitraum, Grundgesamtheit und Formel selbst "
    "festlegen — und merkt dabei, dass genau darin die Arbeit steckt, nicht im Diagramm."])

sys.exit(deck.speichern(OUT))
