#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bau_fallstudie.py — das Foliendeck zur Fallstudie BurgerMetrics.

Loest die beiden Vorgaengerdecks bau_datenmodell.py und bau_bi.py ab. Der
Bogen geht in einer Linie: von der Fachlichkeit ueber das ER-Diagramm und die
Normalformen zu den beiden operativen Anwendungen, von dort ueber den
Datenfluss ins Galaxy-Schema und weiter zu Kennzahlen, Dashboard und
Infrastruktur.

    python3 bau_fallstudie.py                  # -> ../../BurgerMetrics_Fallstudie.pptx
    python3 bau_fallstudie.py -o /pfad.pptx

Voraussetzungen: python-pptx, Skill thws-slides (THWS_SKILL), gerenderte
Diagramme (node render_mermaid.mjs) und Bildschirmfotos (node screenshots.mjs).

Alle Messwerte sind gegen die Semantikschicht in PostgreSQL geprueft (Schema
burgermetrics, db/aufbau/*.sql) — dieselbe Quelle, aus der das Dashboard liest.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckwerk as D                                     # noqa: E402

B = D.B
BLUE, WARN, GOOD, METHOD, HINT = D.BLUE, D.WARN, D.GOOD, D.METHOD, D.HINT
CL, CW, CR, Y0, YMAX, HOEHE = D.CL, D.CW, D.CR, D.Y0, D.YMAX, D.HOEHE

ap = argparse.ArgumentParser(description="Fallstudien-Foliendeck bauen")
ap.add_argument("-o", "--ausgabe", default=None)
args = ap.parse_args()
OUT = (Path(args.ausgabe) if args.ausgabe
       else D.HIER.parent.parent / "BurgerMetrics_Fallstudie.pptx")

QUELLE, Q_FOTO = D.QUELLE, D.Q_FOTO
Q_DB = ("Eigene Auswertung · Schema burgermetrics in PostgreSQL 17.6, "
        "Sichten aus db/aufbau/*.sql")
Q_EIG = "Eigene Einschätzung"
Q_MARKT = ("Gartner Magic Quadrant for Analytics and Business Intelligence "
           "Platforms, 29.06.2026; Marktanteile aus Anbieter-Trackern 2026")
Q_LAKE = ("Armbrust et al., Lakehouse, CIDR 2021; Apache Polaris "
          "Top-Level-Projekt seit Februar 2026")

deck = D.Deck()
w2 = (CW - 18) / 2
w3 = (CW - 2 * 18) / 3

# Die sechs Stationen der Kette. Sie stehen auf der Leitfrage und am Ende
# noch einmal — dazwischen markiert das Stufenband, wo das Deck gerade ist.
KETTE = ["Fachlichkeit", "ER-Modell", "Normalform", "Anwendungen",
         "Auswertung", "Entscheidung"]

# ═══════════════════════════════════════════════════ Deckblatt
deck.deckblatt("BurgerMetrics", "Von der Fachlichkeit zum Dashboard")

# ═══════════════════════════════════════════════════ Leitfrage
s = deck.neu("Lisa_Slide")
B.kopf(s, "Leitfrage", "Ein Dashboard ist das Ende einer Kette, die mit einem Satz beginnt",
       QUELLE)
deck.einl(s, "Am Anfang steht kein Diagramm, sondern eine Aussage über das Geschäft: "
             "Ein Kunde gibt eine Bestellung auf. Aus solchen Sätzen entsteht ein "
             "ER-Modell, daraus normalisierte Tabellen, darauf zwei Anwendungen, aus "
             "deren Belegen ein Auswertungsmodell und erst daraus eine Kennzahl. Wer "
             "eine Station überspringt, merkt es erst am Ende — und zahlt dort dafür.")
B.stufenband(s, Y0, 40, KETTE)
for i, (t, b, c) in enumerate([
    ("Was das Deck durchgeht",
     ["Jede Station an einem einzigen Geschäftsvorfall, vom Satz bis zur Kachel.",
      "Jedes Modell als Diagramm, jede Regel an einem Beispiel.",
      "Kein Schritt ohne die Entscheidung, die er verlangt."], BLUE),
    ("Woran Sie den Erfolg messen",
     ["Sie überführen ein ER-Diagramm in Tabellen und begründen jede Regel.",
      "Sie erkennen, welche Frage ein Modell trägt und welche nicht.",
      "Sie definieren eine Kennzahl so, dass ein Zweiter sie nachrechnet."], GOOD),
    ("Der Bestand dahinter",
     ["754.513 Bestellungen, neun Jahre, acht Filialen, vier Kanäle.",
      "Erfunden, aber durchgerechnet: Jede Zahl stammt aus einer Abfrage.",
      "Alles im Repository — Modell, Daten, Dashboard, Folien."], METHOD),
]):
    B.kachel(s, CL + i * (w3 + 18), Y0 + 58, w3, 200, c, t, b)
B.band(s, Y0 + 268, 54, [
    "Die Kette hat eine Richtung, aber keine Einbahnstraße: Wer beim Auswertungsmodell "
    "merkt, dass eine Frage nicht beantwortbar ist, geht zurück zur Fachlichkeit."])

# ═══════════════════════════════════════════════════ Teil 1
deck.kapitel("Zuerst die Fachlichkeit, dann das Modell")

s = deck.neu("Tool_Slide")
B.kopf(s, "Fallstudie", "Eine erfundene Kette, gebaut, um durchschaut zu werden", Q_FOTO)
deck.einl(s, "BurgerMetrics ist eine fiktive Fast-Food-Kette: acht Filialen in Würzburg, "
             "neun Jahre Geschichte, drei Anwendungen. Erfunden heißt nicht beliebig — "
             "der Bestand ist so konstruiert, dass jede Kennzahl nachrechenbar ist und "
             "die typischen Auswertungsfallen tatsächlich zuschnappen.", "Tool_Slide")
bw, _ = deck.foto(s, "01_start", max_w=560, max_h=HOEHE)
B.kachel(s, CL + bw + 24, Y0, CR - (CL + bw + 24), 140, BLUE, "Die drei Anwendungen",
         ["Online-Shop: die Kundensicht, mit Speisekarte und Warenkorb.",
          "Kassensystem: die operative Sicht, an der die Belege entstehen.",
          "BI-Dashboard: die Auswertungssicht mit dreizehn Themenreitern."])
B.kachel(s, CL + bw + 24, Y0 + 156, CR - (CL + bw + 24), 122, METHOD, "Warum erfunden",
         ["Echte Unternehmensdaten sind vertraulich — hier darf jeder alles sehen.",
          "Der Datengenerator ist bekannt, jede Auffälligkeit also erklärbar."])

s = deck.neu("Lisa_Slide")
B.kopf(s, "Fachlichkeit", "Sechs Sätze über das Geschäft — und was jeder im Modell erzwingt",
       QUELLE)
deck.einl(s, "Die Modellierung beginnt nicht am Rechner, sondern im Gespräch mit dem "
             "Fachbereich. Jeder Satz, den man dort zu hören bekommt, legt etwas fest: "
             "eine Entität, eine Beziehung, eine Kardinalität. Wer diese Sätze nicht "
             "aufschreibt, modelliert später gegen Vermutungen statt gegen Anforderungen.")
B.zuordnung(s, Y0, [
    ("Ein Kunde gibt Bestellungen auf.",
     "Zwei Entitäten, eine 1:n-Beziehung. Der Kunde bleibt, die Bestellung ist "
     "das Ereignis."),
    ("Eine Filiale nimmt sie entgegen.",
     "Dieselbe Form, andere Rolle: Die Filiale ist Stammdatum und steht später "
     "als Dimension zur Verfügung."),
    ("Eine Bestellung hat mindestens eine Position.",
     "Eine schwache Entität. Ohne Bestellung keine Position — und keine Bestellung "
     "ohne Position."),
    ("Jede Position meint genau einen Artikel.",
     "Artikel ist Stammdatum, Position Bewegungsdatum. Die folgenreichste Trennung "
     "des Modells."),
    ("Genau eine Zahlart begleicht sie.",
     "Ein kleiner Wertevorrat mit eigener Tabelle, damit die Liste pflegbar bleibt "
     "und Tippfehler ausscheiden."),
    ("Eine Aktion kann sie vergünstigen.",
     "Die einzige optionale Beziehung — und damit das einzige Fremdschlüsselfeld, "
     "das leer bleiben darf."),
], rh=44.0)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Systeme", "Daten entstehen vorn, verbucht wird in der Mitte, befragt wird hinten",
       QUELLE)
deck.einl(s, "Drei Anwendungen, drei klar getrennte Aufgaben. Shop und Kasse erzeugen "
             "Daten als Nebenprodukt ihrer eigentlichen Arbeit, die Warenwirtschaft "
             "macht daraus verbindliche Belege, und die Auswertung liest einen Abzug "
             "davon. Kein System greift in die Zuständigkeit eines anderen ein.")
deck.bild(s, "01_systemkontext", y=Y0 + 12, max_h=200)
B.band(s, Y0 + 226, 84, [
    "Der gestrichelte Pfeil ist die wichtigste Kante des Bildes. Links von ihm zählt "
    "Konsistenz im laufenden Betrieb: Zwei Kassen dürfen denselben Bon nicht doppelt "
    "buchen. Rechts von ihm zählt Lesegeschwindigkeit über die ganze Historie. Diese "
    "eine Grenze begründet fast jede Bauentscheidung dieses Projekts."])

s = deck.neu("Lisa_Slide")
B.kopf(s, "Zuständigkeit", "Jedes System speichert, was seine eigene Aufgabe verlangt",
       QUELLE)
deck.einl(s, "Die Versuchung, alles überall zu speichern, ist groß und teuer. Der Shop "
             "braucht keine Buchungssätze, die Warenwirtschaft keine Mausbewegungen, "
             "die Auswertung keine Sperren. Was ein System nicht speichert, kann es "
             "auch nicht falsch speichern — und niemand muss es dort pflegen.")
for i, (t, b, c) in enumerate([
    ("Online-Shop", ["Sitzung, Klickfolge, Warenkorb.",
                     "Alles flüchtig: Bis zum Kaufabschluss ist jede Zeile änderbar.",
                     "Kein Beleg, keine Buchung, keine Historie."], BLUE),
    ("Warenwirtschaft", ["Beleg mit Kopf und Positionen, Preise zum Kaufzeitpunkt.",
                         "Dauerhaft und unveränderlich — eine Korrektur ist ein neuer Beleg.",
                         "26 Tabellen in dritter Normalform."], GOOD),
    ("Auswertung", ["Ein Abzug, historisiert, absichtlich redundant.",
                    "Keine Schreibzugriffe, keine Sperren, keine Transaktionen.",
                    "Zwölf Tabellen, zwei davon mit den Fakten."], METHOD),
]):
    B.kachel(s, CL + i * (w3 + 18), Y0, w3, 196, c, t, b)
B.band(s, Y0 + 212, 84, [
    "Die Aufteilung ist keine Geschmacksfrage, sondern folgt aus den Lastprofilen: Der "
    "Shop schreibt viele kleine Änderungen und liest kaum, die Warenwirtschaft schreibt "
    "wenige und liest gezielt, die Auswertung schreibt nie und liest alles. Ein System, "
    "das alle drei Profile bedienen soll, bedient keines davon gut."])

# ═══════════════════════════════════════════════════ Teil 2
deck.kapitel("Vom Satz zum Diagramm: das ER-Modell")

s = deck.neu("Lisa_Slide")
B.kopf(s, "Notation", "Vier Bausteine, und drei davon sind fachliche Entscheidungen",
       QUELLE)
deck.einl(s, "Ein ER-Diagramm hat einen kleinen Wortschatz, und gerade deshalb ist es "
             "prüfbar: Jedes Zeichen darin lässt sich einer Aussage des Fachbereichs "
             "zuordnen. Wer eine Kardinalität nicht in einem Satz begründen kann, hat "
             "sie geraten — und rät damit über das Verhalten des späteren Systems.")
for i, (t, b, c) in enumerate([
    ("Entität", ["Ein Ding, über das man Fakten speichert: Kunde, Artikel, Bestellung.",
                 "Faustregel: Es hat eine eigene Identität und überlebt einzelne Vorgänge."], BLUE),
    ("Attribut", ["Eine Eigenschaft der Entität: Name, Preis, Datum.",
                  "Wird ein Attribut selbst zum Bezugspunkt, ist es eine eigene Entität."], BLUE),
    ("Beziehung", ["Wie zwei Entitäten zusammenhängen: \"gibt auf\", \"besteht aus\".",
                   "Das Verb aus dem Fachgespräch wird zur Beschriftung der Kante."], METHOD),
    ("Kardinalität", ["Wie viele auf jeder Seite: 1:1, 1:n, n:m — und ob null erlaubt ist.",
                      "Die folgenreichste Angabe: Sie entscheidet über Tabellen und Nullwerte."], GOOD),
]):
    x = CL + (i % 2) * (w2 + 18)
    y = Y0 + (i // 2) * 116
    B.kachel(s, x, y, w2, 104, c, t, b)
B.band(s, Y0 + 240, 70, [
    "Was ein ER-Diagramm nicht festlegt: Datentypen, Indizes, Speicherort, "
    "Zugriffsrechte. Das ist kein Mangel — es hält die fachliche Diskussion frei von "
    "technischen Fragen, die zu diesem Zeitpunkt niemand beantworten kann."])

s = deck.neu("Slide")
B.kopf(s, "Entwurf", "Sechs Entitäten, sechs Beziehungen — der erste vollständige Wurf",
       QUELLE)
deck.bild(s, "20_er_entwurf", y=150, max_h=260, max_w=520)
B.sprechblase(s, CL + 540, 142, CR - (CL + 540), 292, D.paras([
    [("So liest man die Krähenfüße", True, GOOD)],
    ["Der Doppelstrich heißt \"genau eins\", der Kreis \"null oder eins\", "
     "der Fuß \"viele\"."],
    ["KUNDE zu BESTELLUNG: ein Kunde, beliebig viele Bestellungen — auch keine."],
    ["BESTELLUNG zu POSITION: eine Bestellung, mindestens eine Position. Der "
     "Unterschied zwischen \"o{\" und \"|{\" ist eine fachliche Aussage."],
    ["Nur AKTION hängt mit einem Kreis am Beleg. Sie ist die einzige Beziehung, "
     "die fehlen darf — und damit die einzige, die später NULL zulässt."],
    ["Attribute fehlen absichtlich: Erst wenn die Beziehungen stimmen, lohnt "
     "sich das Gespräch über Felder."],
]), farbe=GOOD)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Schlüssel", "Ohne eindeutige Identität ist eine Zeile nicht wiederfindbar",
       QUELLE)
deck.einl(s, "Ein Primärschlüssel beantwortet genau eine Frage: Welche Zeile ist "
             "gemeint? Er muss eindeutig sein, darf nicht leer sein und sollte sich "
             "nicht ändern. Die dritte Bedingung wird am häufigsten verletzt — und "
             "kostet dann jede Beziehung, die auf den Schlüssel zeigt.")
B.gegenueber(s, Y0, 150,
             (WARN, "Fachlicher Schlüssel — aus den Daten",
              ["E-Mail-Adresse als Kundenschlüssel.",
               "Liest sich gut, spart eine Spalte — bis jemand die Adresse ändert.",
               "Dann wandert die Änderung durch jede Tabelle, die darauf verweist."]),
             (GOOD, "Technischer Schlüssel — vom System vergeben",
              ["customer_id als fortlaufende Zahl, ohne Bedeutung.",
               "Ändert sich nie, weil er nichts bedeutet.",
               "Die E-Mail bleibt Attribut und darf sich ändern, ohne Folgen."]),
             badge_l="!", badge_r="✓")
B.band(s, Y0 + 166, 84, [
    "Bei der Position liegt der Fall anders: Sie hat keine eigene Identität, sondern "
    "gehört zu ihrer Bestellung. Ihr Schlüssel ist deshalb zusammengesetzt — "
    "(bestell_id, positions_nr). Wer hier einen technischen Schlüssel vergibt, "
    "verschleiert die Abhängigkeit, statt sie zu modellieren."])

# ═══════════════════════════════════════════════════ Teil 3
deck.kapitel("Vom Diagramm zur Normalform")

s = deck.neu("Lisa_Slide")
B.kopf(s, "Anlass", "Eine Tabelle für alles erzeugt drei Sorten von Fehlern", QUELLE)
deck.einl(s, "Warum überhaupt normalisieren? Nicht der Ordnung wegen, sondern weil "
             "Redundanz im laufenden Betrieb Widersprüche erzeugt. Steht die Adresse "
             "einer Filiale in jeder Bestellzeile, gibt es sie hunderttausendfach — "
             "und beim Umzug ändert jemand neunhundert davon.")
B.zuordnung(s, Y0, [
    ("Änderungsanomalie",
     "Die Filiale zieht um. Die Adresse steht in 182.120 Bestellzeilen. Wird eine "
     "davon vergessen, widerspricht die Datenbank sich selbst."),
    ("Einfügeanomalie",
     "Ein neuer Artikel ist gelistet, aber noch nie verkauft. Ohne eigene "
     "Artikeltabelle lässt er sich nirgends anlegen."),
    ("Löschanomalie",
     "Die letzte Bestellung eines Kunden wird storniert. Mit ihr verschwindet die "
     "einzige Stelle, an der seine Anschrift stand."),
], rh=58.0)
B.band(s, Y0 + 196, 84, [
    "Alle drei Anomalien haben dieselbe Ursache: In einer Zeile stehen Fakten über "
    "verschiedene Dinge. Die Normalisierung trennt sie, bis jede Tabelle über genau "
    "ein Ding Auskunft gibt. Das ist die ganze Idee — die Normalformen sind nur die "
    "Prüfliste dazu."])

s = deck.neu("Slide")
B.kopf(s, "Normalisierung", "Drei Schritte, drei Regeln, fünf Tabellen", QUELLE)
deck.bild(s, "21_normalformen", y=136, max_h=110)
B.zuordnung(s, 274, [
    ("1. Normalform",
     "Jedes Feld enthält genau einen Wert. Die Artikelliste im Bestellsatz wird zu "
     "eigenen Positionszeilen."),
    ("2. Normalform",
     "Jedes Nicht-Schlüsselfeld hängt am ganzen Schlüssel. Artikelname und Listenpreis "
     "hängen nur am Artikel — sie ziehen um."),
    ("3. Normalform",
     "Kein Nicht-Schlüsselfeld hängt an einem anderen. Die Filialadresse hängt an der "
     "Filiale, nicht an der Bestellung."),
], rh=52.0, bw=180.0)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Abbildung", "Vier Regeln überführen jedes ER-Diagramm in Tabellen", QUELLE)
deck.einl(s, "Der Übergang vom Diagramm zum Schema ist kein Ermessensspielraum, "
             "sondern ein Handwerk mit vier Regeln. Wer sie kennt, kann jedes "
             "ER-Diagramm mechanisch überführen — und umgekehrt aus jedem Schema "
             "ablesen, welches Diagramm dahintersteckt.")
B.zuordnung(s, Y0, [
    ("Entität → Tabelle",
     "Jede Entität wird eine Tabelle, jedes Attribut eine Spalte, der Primärschlüssel "
     "die Identität. KUNDE wird kunde."),
    ("1:n → Fremdschlüssel",
     "Der Schlüssel der Eins-Seite wandert als Spalte auf die n-Seite. "
     "kundenbestellung bekommt kunde_id."),
    ("n:m → eigene Tabelle",
     "Eine Beziehungstabelle mit beiden Schlüsseln. Trägt sie eigene Attribute wie "
     "Menge und Preis, ist sie längst eine Entität."),
    ("optional → NULL erlaubt",
     "Die Aktion darf fehlen, also darf aktion_id leer bleiben. Jede andere "
     "Fremdschlüsselspalte wird NOT NULL."),
], rh=56.0)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Ergebnis", "Am Ende steht DDL — und jede Regel ist darin wiederzufinden",
       QUELLE)
deck.einl(s, "Die Umsetzung macht die Modellentscheidungen prüfbar: Der zusammengesetzte "
             "Schlüssel der Position steht dort ebenso wie die Nullbarkeit der Aktion. "
             "Wer das Modell ändern will, ändert zuerst das Diagramm und leitet die "
             "Anweisungen daraus ab — nicht umgekehrt.")
D.Deck.code(s, CL, Y0, CW, [
    "CREATE TABLE kundenbestellung (",
    "    bestell_id     integer PRIMARY KEY,",
    "    kunde_id       integer NOT NULL REFERENCES kunde,     -- 1:n, Pflicht",
    "    filiale_id     integer NOT NULL REFERENCES filiale,   -- 1:n, Pflicht",
    "    aktion_id      integer          REFERENCES aktion,    -- optional: NULL erlaubt",
    "    bestellt_am    timestamp NOT NULL",
    ");",
    "",
    "CREATE TABLE bestellposition (",
    "    bestell_id     integer NOT NULL REFERENCES kundenbestellung,",
    "    positions_nr   smallint NOT NULL,",
    "    artikel_id     integer NOT NULL REFERENCES artikel,",
    "    menge          smallint NOT NULL CHECK (menge > 0),",
    "    einzelpreis    numeric(8,2) NOT NULL,   -- Preis zum Kaufzeitpunkt, nicht heute",
    "    PRIMARY KEY (bestell_id, positions_nr)  -- schwache Entität",
    ");",
], size=11.5)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Abwägung", "Die dritte Normalform kauft Konsistenz mit Joins", QUELLE)
deck.einl(s, "Normalisierung ist kein Selbstzweck und keine Tugend, sondern ein Tausch. "
             "Sie beseitigt Widersprüche und erkauft das mit Verbundoperationen bei "
             "jeder Abfrage. Im operativen Betrieb ist der Tausch fast immer richtig — "
             "in der Auswertung fast immer falsch. Beides zeigt dieses Deck.")
B.klammer(s, CL, Y0, w2, 176, "Was sie schützt",
          D.paras(["Jeder Fakt steht an genau einer Stelle. Eine Änderung ist eine "
                   "Änderung, nicht neunhundert.",
                   "Die Datenbank kann Regeln erzwingen: Fremdschlüssel, Eindeutigkeit, "
                   "Prüfbedingungen.",
                   "Schreibvorgänge bleiben klein und damit schnell und sperrarm."]), GOOD)
B.klammer(s, CL + w2 + 18, Y0, w2, 176, "Was sie kostet",
          D.paras(["Eine einfache Frage berührt viele Tabellen. \"Umsatz je Kategorie\" "
                   "braucht fünf Verbunde.",
                   "Historische Wahrheit geht verloren: Der Artikelpreis von heute ist "
                   "nicht der von 2019.",
                   "Für Auswertungen über Millionen Zeilen wird der Verbund zum "
                   "Kostentreiber."]), HINT)
B.band(s, Y0 + 192, 84, [
    "Der zweite Punkt rechts ist der wichtigere und wird am häufigsten übersehen: Der "
    "Einzelpreis steht deshalb in der Position und nicht nur im Artikel. Ohne diese "
    "bewusste Redundanz ließe sich der Umsatz vergangener Jahre nie wieder korrekt "
    "rechnen — eine Preisänderung würde die Vergangenheit umschreiben."])

# ═══════════════════════════════════════════════════ Teil 4
deck.kapitel("Ein Kern, zwei Anwendungen")

s = deck.neu("Slide")
B.kopf(s, "Aufteilung", "Beide Anwendungen schreiben in denselben Kern", QUELLE)
deck.bild(s, "22_kernmodell", y=122, max_h=364)

s = deck.neu("Tool_Slide")
B.kopf(s, "Webshop", "Dieselbe Seite, zwei Sichten: Speisekarte für Kunden, Datenspur für uns",
       Q_FOTO)
wf = (CW - 18) / 2
YS = 128
B.textbox(s, CL, YS, wf, 18, [("Kundensicht", True, D.SEC)], 11.5)
B.textbox(s, CL + wf + 18, YS, wf, 18, [("Datensicht — derselbe Moment", True, BLUE)], 11.5)
_, bh2 = deck.foto(s, "02_shop", y=YS + 24, max_w=wf, max_h=246)
deck.foto(s, "02b_shop_daten", y=YS + 24, x=CL + wf + 18, max_w=wf, max_h=246)
B.band(s, YS + 24 + bh2 + 16, 76, [
    "Der Kunde sieht Speisekarte und Bestellknopf. Die zuschaltbare Datensicht zeigt, "
    "was derselbe Seitenaufruf nebenbei erzeugt: eine Sitzung mit Gerät und Herkunft, "
    "dazu jedes Ereignis mit Verweildauer. Nichts davon ist für den Kauf nötig — und "
    "genau deshalb ist es eine bewusste Entscheidung, es zu speichern."])

s = deck.neu("Lisa_Slide")
B.kopf(s, "Shop-Modell", "Bestellen braucht drei Tabellen, Beobachten zwei mehr", QUELLE)
deck.einl(s, "Der Kaufvorgang selbst kommt mit Sitzung, Warenkorbposition und Artikel "
             "aus. Alles Weitere dient der Beobachtung: Woher kam der Besuch, was wurde "
             "angesehen, wo brach er ab. Diese Trennung sollte man bewusst treffen — "
             "Verhaltensdaten sind rechtlich und fachlich etwas anderes als Belege.")
deck.bild(s, "17_webshop_er", y=Y0, max_h=318)

s = deck.neu("Tool_Slide")
B.kopf(s, "Kassensystem", "Jeder Tastendruck an der Kasse schreibt eine Zeile", Q_FOTO)
deck.einl(s, "Die Kasse ist das Gegenstück zum Shop: dieselben Artikel, dieselbe "
             "Bestellung, aber eine andere Erfassungslage. Es gibt keine Sitzung und "
             "keinen Klickweg, dafür Schicht, Terminal und Kassierer. Die Datensicht "
             "rechts zeigt, welche Felder ein einziger Bon füllt.", "Tool_Slide")
bw3, _ = deck.foto(s, "03b_pos_daten", max_w=580, max_h=HOEHE)
B.sprechblase(s, CL + bw3 + 24, Y0, CR - (CL + bw3 + 24), 250, D.paras([
    [("Was der Beleg festhält", True, GOOD)],
    ["Kopfdaten: Filiale, Terminal, Schicht, Zeitpunkt, Zahlart."],
    ["Positionen: Artikel, Menge, Einzelpreis — der Preis wird kopiert, nicht "
     "verwiesen."],
    ["Aus diesen Feldern entstehen später Umsatz, Bestellwert und Kanalanteil. "
     "Kein Feld ist für die Auswertung erfunden worden; sie nutzt, was der Betrieb "
     "ohnehin braucht."],
]), farbe=GOOD)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Übergabe", "Der Kaufabschluss macht aus Flüchtigem etwas Dauerhaftes", QUELLE)
deck.einl(s, "Zwischen Warenkorb und Beleg liegt die wichtigste Zustandsänderung des "
             "ganzen Systems. Vorher darf sich alles ändern, nachher nichts mehr. In "
             "diesem Moment werden Preise kopiert statt verwiesen — sonst würde jede "
             "spätere Preisänderung die Vergangenheit mit umschreiben.")
deck.bild(s, "19_checkout", y=Y0, max_h=200)
B.band(s, Y0 + 214, 76, [
    "Der untere Pfeil ist der Regelfall, nicht die Ausnahme: Die meisten Warenkörbe "
    "werden nie zu Bestellungen. Ein Modell, das nur den erfolgreichen Kauf abbildet, "
    "kann später nicht beantworten, woran die anderen gescheitert sind — und das ist "
    "eine der wenigen Fragen, an denen sich ein Shop verbessern lässt."])

s = deck.neu("Lisa_Slide")
B.kopf(s, "Warenwirtschaft", "Der Verkauf ist ein Bereich von sieben", QUELLE)
deck.einl(s, "Das operative System endet nicht beim Verkauf. Einkauf, Lager, Personal "
             "und Filialstamm hängen am selben Artikel und an derselben Filiale. Für "
             "die Auswertung ist nur ein Ausschnitt nötig — man sollte aber wissen, "
             "welcher Teil des Ganzen das ist.")
deck.bild(s, "04_wawi_bereiche", y=Y0, max_h=166)
B.kennzahlen(s, Y0 + 180, 80, [
    ("Tabellen operativ", "26", BLUE),
    ("Bereiche", "7", BLUE),
    ("fließen in die Auswertung", "13", METHOD),
    ("Tabellen analytisch", "12", GOOD),
])
B.band(s, Y0 + 268, 52, [
    "Das Auswertungsmodell kommt mit zwölf Tabellen aus und beantwortet trotzdem "
    "mehr Fragen — weil es andere Fragen beantwortet."])


# ═══════════════════════════════════════════════════ Teil 5
deck.kapitel("Der Weg ins Auswertungsmodell")

s = deck.neu("Lisa_Slide")
B.kopf(s, "Abgrenzung", "Zwei Systeme, zwei Lastprofile — und deshalb zwei Modelle",
       QUELLE)
deck.einl(s, "Das operative Modell ist auf Konsistenz beim Schreiben gebaut, das "
             "analytische auf Tempo beim Lesen. Diese beiden Ziele widersprechen "
             "einander: Was Schreibvorgänge klein hält, macht Auswertungen teuer. "
             "Deshalb steht am Ende nicht ein besseres Modell, sondern ein zweites.")
B.gegenueber(s, Y0, 194,
             (BLUE, "Operativ · OLTP",
              ["Arbeitseinheit: ein Vorgang. Eine Bestellung, ein Beleg, eine Buchung.",
               "Datenstand: jetzt. Was vor einer Minute galt, interessiert nicht.",
               "Modell: normalisiert, 26 Tabellen, jede Tatsache an einer Stelle.",
               "Last: viele kleine Schreibvorgänge, wenige gezielte Lesevorgänge."]),
             (METHOD, "Analytisch · OLAP",
              ["Arbeitseinheit: eine Frage. Umsatz je Filiale und Quartal über neun Jahre.",
               "Datenstand: historisch. Gerade der Vergleich mit früher ist der Zweck.",
               "Modell: bewusst redundant, zwölf Tabellen, Verbunde vorweggenommen.",
               "Last: keine Schreibvorgänge, dafür Lesevorgänge über Millionen Zeilen."]),
             badge_l="1", badge_r="2")
B.band(s, Y0 + 210, 72, [
    "Die Zahlen dazu: Das operative System beantwortet \"Was kostet diese Bestellung?\" "
    "über wenige Zeilen. Die Auswertung beantwortet \"Wie hat sich der Bestellwert seit "
    "2017 entwickelt?\" über 754.513 Bestellungen und 2.950.082 Positionen. Dieselbe "
    "Datenbanktechnik, aber keine gemeinsame Bauform."])

s = deck.neu("Lisa_Slide")
B.kopf(s, "Übernahme", "Drei Schichten trennen Rohdaten, Typisierung und Modell", QUELLE)
deck.einl(s, "Zwischen Quellsystem und Bericht liegen drei Schichten, und jede hat "
             "genau eine Aufgabe. Die Trennung kostet Speicher und spart Fehlersuche: "
             "Wenn eine Kennzahl falsch ist, zeigt die Schicht, in der sie kippt, auch "
             "die Ursache. Ohne diese Trennung sucht man im ganzen Skript.")
deck.bild(s, "08_kette", y=Y0 + 16, max_h=120)
B.zuordnung(s, Y0 + 152, [
    ("raw", "Unverändert übernommen, ohne Umbenennung und ohne Typkorrektur. "
            "Diese Schicht darf man jederzeit wegwerfen und neu ziehen."),
    ("stg", "Getypt, benannt, geprüft. Hier fällt auf, wenn ein Datum als Text "
            "ankommt — nicht erst in der Auswertung."),
    ("mart", "Das Galaxy-Schema, auf Lesetempo gebaut. Nur hier wird bewusst "
             "denormalisiert, und nur hier stehen Kennzahlen."),
], rh=48.0, bw=120.0)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Granularität", "Die erste Frage an jede Faktentabelle: Was ist eine Zeile?",
       Q_DB)
deck.einl(s, "Vor jeder Kennzahl steht die Festlegung, welches Ereignis eine Zeile "
             "bildet. Sie ist folgenreicher als jede spätere Formel: Sie entscheidet, "
             "welche Summen überhaupt zulässig sind. Wer die Granularität nicht "
             "benennen kann, kann seine Zahlen nicht verteidigen.")
deck.bild(s, "06_granularitaet", y=Y0, max_h=250, max_w=430)
B.sprechblase(s, CL + 450, Y0, CR - (CL + 450), 250, D.paras([
    [("Eine Bestellung, drei Positionen, sechs Stück", True, BLUE)],
    ["Der Bestellwert von 27,04 EUR gehört zur Bestellung, nicht zur Position. "
     "Er darf nur einmal gezählt werden — auch wenn drei Zeilen daran hängen."],
    ["Die Menge gehört zur Position. Sie über Bestellungen zu summieren, ist "
     "richtig; den Bestellwert über Positionen zu summieren, ist falsch."],
    ["2025 hat eine Bestellung im Mittel 3,95 Positionen. Genau dieser Faktor "
     "vervielfacht jeden Fehler, der die beiden Ebenen vermischt."],
]), farbe=BLUE)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Fallstricke", "Ein Verbund macht aus 3,0 Millionen Euro Umsatz 14,7 Millionen", Q_DB)
deck.einl(s, "Die Fan Trap ist der häufigste Auswertungsfehler und der unauffälligste: "
             "Die Abfrage läuft fehlerfrei, das Ergebnis ist plausibel groß, und "
             "niemand rechnet nach. Sie entsteht, sobald ein Wert der Bestellebene "
             "nach einem Verbund mit der Positionsebene summiert wird.")
D.Deck.code(s, CL, Y0, CW, [
    "-- FALSCH: der Verbund vervielfacht jede Bestellzeile mit ihren Positionen",
    "SELECT sum(o.net_total)                       -- 14.692.550,61 EUR",
    "FROM   fact_orders o JOIN fact_order_items i USING (order_id)",
    "WHERE  extract(year FROM o.date) = 2025;     -- das 4,91-Fache des Umsatzes",
    "",
    "-- RICHTIG: Werte der Bestellebene auf der Bestellebene summieren",
    "SELECT sum(net_total)                         --  2.994.771,13 EUR",
    "FROM   fact_orders",
    "WHERE  extract(year FROM date) = 2025;",
], size=11.5)
B.band(s, Y0 + 168, 92, [
    "Der Faktor 4,91 ist kein Zufall, sondern die mittlere Zahl der Positionen je "
    "Bestellung in diesem Jahr — 3,95 Artikelzeilen, gewichtet nach Bestellwert. "
    "Genau deshalb liegen Bestellungen und Positionen in zwei Faktentabellen: Die "
    "Trennung macht den Fehler nicht unmöglich, aber sie macht ihn sichtbar, weil "
    "jede Tabelle ihre Granularität im Namen trägt."])

s = deck.neu("Lisa_Slide")
B.kopf(s, "Denormalisierung", "Für die Auswertung wird die Normalisierung zurückgenommen",
       QUELLE)
deck.einl(s, "Im operativen Modell war die Aufteilung in Artikel, Unterkategorie und "
             "Kategorie richtig. In der Auswertung wird daraus eine Tabelle. Das ist "
             "kein Rückschritt, sondern dieselbe Abwägung mit umgekehrtem Vorzeichen: "
             "Hier wird nicht geschrieben, also kostet Redundanz keine Konsistenz.")
deck.bild(s, "05_denormalisierung", y=Y0 + 20, max_h=110)
B.band(s, Y0 + 154, 106, [
    "Der Preis dafür ist ein anderer: Ändert sich eine Kategoriebezeichnung, muss der "
    "Abzug neu laufen. Das ist tragbar, weil er ohnehin nachts läuft. Untragbar wäre "
    "es im operativen System, wo die Änderung sofort überall gelten muss. Dieselbe "
    "Technik, dieselbe Tabelle, gegensätzliche Bewertung — die Bauform folgt der "
    "Frage, nicht dem Geschmack."])

# ═══════════════════════════════════════════════════ Teil 6
deck.kapitel("Das Galaxy-Schema")

s = deck.neu("Lisa_Slide")
B.kopf(s, "Alternativen", "Dieselben Fakten lassen sich auf drei Arten ordnen", QUELLE)
deck.einl(s, "Das Galaxy-Schema ist eine Wahl, keine Notwendigkeit. Dieselben "
             "754.513 Bestellungen lassen sich als Data Vault ablegen, als eine "
             "einzige breite Tabelle oder eben als Sternverbund. Die drei "
             "unterscheiden sich nicht in dem, was sie speichern, sondern darin, "
             "was sie beim Ändern und beim Lesen kosten.")
deck.bild(s, "09_modellierungswege", y=Y0, max_h=222)
B.band(s, Y0 + 234, 90, [
    "Data Vault trennt Schlüssel, Beziehungen und Attribute in eigene Tabellenarten. "
    "Das trägt viele Quellsysteme und lange Historien und kostet dafür Joins — hier "
    "gibt es genau eine Quelle. One Big Table macht jede Abfrage trivial und jede "
    "Änderung teuer: 41 Spalten, nichts wiederverwendbar. Das Galaxy-Schema teilt "
    "Dimensionen zwischen mehreren Faktentabellen, und genau das verlangt dieser "
    "Fall — zwei Granularitäten, aber ein Artikelstamm und eine Zeitachse."])

s = deck.neu("Slide")
B.kopf(s, "Auswertungsmodell", "Zwei Faktentabellen teilen sich zehn Dimensionen", Q_DB)
deck.bild(s, "07_galaxy", y=120, max_h=306)
B.band(s, 432, 62, [
    "Ein Stern hat eine Faktentabelle, eine Galaxie mehrere — verbunden über geteilte "
    "Dimensionen. Weil beide dieselbe dim_date nutzen, liegen Bestellzahl und "
    "Artikelmenge auf einer Zeitachse. Solche Dimensionen heißen konform."])

s = deck.neu("Lisa_Slide")
B.kopf(s, "Semantikschicht", "Die Kennzahl wird einmal definiert, nicht je Werkzeug",
       QUELLE)
deck.einl(s, "Ein Modell allein reicht nicht: Solange jede Auswertung ihre eigene "
             "Formel mitbringt, liefern drei Berichte drei Umsatzzahlen. Die "
             "Semantikschicht legt die Rechenvorschrift zwischen Modell und Werkzeug "
             "— einmal, an einer Stelle, versioniert.")
B.gegenueber(s, Y0, 158,
             (WARN, "Ohne Semantikschicht",
              ["Jedes Werkzeug bringt seine eigene Formel mit.",
               "Der Controller rechnet brutto, das Dashboard netto, die Filiale "
               "zählt Bons.",
               "Drei Berichte, drei Umsatzzahlen — und keine ist widerlegbar."]),
             (GOOD, "Mit Semantikschicht",
              ["Die Formel steht einmal in der Datenbank, mit Kommentar.",
               "Jedes Werkzeug fragt dieselbe Sicht ab und rechnet selbst nichts.",
               "Drei Berichte, eine Umsatzzahl — und eine Stelle, die man ändert."]),
             badge_l="✗", badge_r="✓")
B.band(s, Y0 + 174, 80, [
    "In diesem Projekt sind es 36 SQL-Sichten im Schema burgermetrics. Sie legen "
    "fest, dass Umsatz die Summe von net_total nach Rabatt ist und nicht die Summe "
    "der Positionsbeträge — ein Unterschied von 37.875 EUR allein im Jahr 2025. Das "
    "Dashboard fragt 33 dieser Sichten ab und rechnet selbst nichts."])

# ═══════════════════════════════════════════════════ Teil 7
deck.kapitel("Kennzahlen, die eine Entscheidung tragen")

s = deck.neu("Lisa_Slide")
B.kopf(s, "Definition", "Drei Angaben machen aus einer Zahl eine Kennzahl", QUELLE)
deck.einl(s, "\"Der Umsatz liegt bei drei Millionen\" ist keine Kennzahl, sondern eine "
             "Behauptung. Erst Formel, Zeitraum und Grundgesamtheit machen sie "
             "prüfbar. Fehlt eine der drei Angaben, kann ein Zweiter das Ergebnis "
             "nicht reproduzieren — und dann ist es kein Berichtswesen, sondern Meinung.")
for i, (t, b, c) in enumerate([
    ("Formel", ["Welche Spalte, welche Aggregatfunktion, welche Ebene.",
                "Hier: SUM(net_total) auf der Bestellebene, also nach Rabatt.",
                "Die Ebene ist Teil der Formel, nicht Beiwerk."], BLUE),
    ("Zeitraum", ["Nach welchem Datum, und ist der Rand eingeschlossen.",
                  "Hier: Bestelldatum, Kalenderjahr, 2025 vollständig.",
                  "2026 ist angebrochen und wird deshalb nie unkommentiert verglichen."], METHOD),
    ("Grundgesamtheit", ["Welche Zeilen zählen, welche nicht.",
                         "Hier: alle Bestellungen, auch stornierte und Aktionskäufe.",
                         "Jede Ausnahme gehört in die Definition, nicht in die Fußnote."], GOOD),
]):
    B.kachel(s, CL + i * (w3 + 18), Y0, w3, 180, c, t, b)
B.band(s, Y0 + 196, 84, [
    "Der Prüfstein ist banal und wirksam: Fragt man drei Auswertungen nach dem Umsatz "
    "2025 und bekommt drei Zahlen, fehlt eine dieser drei Angaben — unabhängig davon, "
    "wie modern der Rest gebaut ist."])

s = deck.neu("Lisa_Slide")
B.kopf(s, "Prüfung", "Umsatz 2025: drei Zahlen, zwei davon zulässig", Q_DB)
deck.einl(s, "Dieselbe Frage, dieselbe Datenbank, drei Ergebnisse. Zwei davon sind "
             "korrekt und beantworten verschiedene Fragen, das dritte ist ein "
             "Verbundfehler. Wer die Definitionen nicht kennt, kann die drei nicht "
             "auseinanderhalten — und wählt am Ende die größte Zahl.")
B.zuordnung(s, Y0, [
    ("2.994.771 EUR",
     "SUM(net_total) über fact_orders. Was das Unternehmen tatsächlich erlöst hat, "
     "nach Abzug aller Rabatte. Die Zahl des Dashboards."),
    ("3.032.646 EUR",
     "SUM(gross_total), gleichbedeutend mit der Summe aller Positionsbeträge. "
     "Der Wert der verkauften Ware vor Rabatt — für Sortimentsfragen die richtige Größe."),
    ("14.692.551 EUR",
     "SUM(net_total) nach einem Verbund mit den Positionen. Kein Umsatz, sondern der "
     "4,91-fach gezählte. Läuft fehlerfrei durch und ist trotzdem falsch."),
], rh=58.0)
B.band(s, Y0 + 196, 84, [
    "Die Differenz zwischen den ersten beiden beträgt 37.875 EUR — der gesamte "
    "Rabatt des Jahres. Beide Zahlen sind verteidigbar, solange dabeisteht, welche "
    "Frage sie beantworten. Genau dafür gibt es die Semantikschicht: Sie zwingt zur "
    "Entscheidung, bevor jemand die Zahl in eine Folie schreibt."])

s = deck.neu("Slide")
B.kopf(s, "Kennzahlensystem", "Ein Umsatz zerfällt in Größen, die sich steuern lassen",
       Q_DB)
deck.bild(s, "23_kpi_baum", y=128, max_h=360, max_w=470)
B.sprechblase(s, CL + 492, 128, CR - (CL + 492), 356, D.paras([
    [("Was der Baum entscheidbar macht", True, GOOD)],
    ["Der Umsatz stieg 2025 um 5,4 Prozent. Der Baum zeigt, woher: 2,9 Punkte aus "
     "dem Bestellwert, 2,4 aus der Menge. Das Wachstum ist preisgetrieben."],
    ["Damit ist die Maßnahme eine andere: Mehr Gäste erreicht man über Standorte "
     "und Kanäle, mehr Bestellwert über Sortiment und Bündel."],
    ["Der Rabatt hängt als eigener Ast darunter, weil er die einzige Größe ist, "
     "die das Unternehmen unmittelbar selbst setzt — 0,28 EUR je Bestellung."],
    ["Jeder Knoten ist eine Sicht in der Datenbank. Der Baum ist damit nicht "
     "Didaktik, sondern der Bauplan der Semantikschicht."],
]), farbe=GOOD)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Rechenweg", "Von 754.513 Zeilen zu einer Kachel, in vier Schritten", Q_DB)
deck.einl(s, "Zwischen Faktentabelle und Kennzahlkachel liegen vier Operationen, und "
             "jede davon ist eine Entscheidung. Wer den Weg einmal ausschreibt, kann "
             "jede Zahl im Dashboard zurückverfolgen — und erkennt, an welcher Stelle "
             "eine abweichende Definition zu einer anderen Zahl führt.")
B.chevron_kette(s, Y0, 38, ["754.513 Zeilen", "WHERE · Zeitraum",
                            "GROUP BY · Auflösung", "SUM · Formel", "Kachel"])
D.Deck.code(s, CL, Y0 + 54, CW, [
    "CREATE VIEW v_kennzahlen_jahr AS            -- die Kennzahl steht in der Datenbank",
    "SELECT extract(year FROM date)::int AS jahr,   -- GROUP BY: die Auflösung",
    "       count(*)                     AS bestellungen,",
    "       sum(net_total)               AS umsatz,    -- SUM: die Formel",
    "       avg(net_total)               AS aov",
    "FROM   fact_orders                           -- die Grundgesamtheit",
    "GROUP  BY 1 ORDER BY 1;",
], size=11.5)
B.band(s, Y0 + 176, 86, [
    "Die vier Schritte sind genau die Bestandteile der Definition: Der Filter setzt "
    "den Zeitraum, das GROUP BY die Auflösung, die Aggregatfunktion die Formel. Ein "
    "GROUP BY mehr — nach branch_id — und aus derselben Kennzahl wird ein "
    "Filialvergleich, ohne dass sich die Definition ändert. Genau deshalb steht sie "
    "in der Datenbank und nicht im Diagramm."])

s = deck.neu("Tool_Slide")
B.kopf(s, "Dashboard", "Jede Kachel trägt Wert, Veränderung und Bezugsgröße", Q_FOTO)
deck.einl(s, "Eine Zahl ohne Vergleich ist nicht lesbar. Jede Kachel nennt deshalb "
             "drei Dinge: den Wert, die Veränderung gegenüber dem Vorjahr und die "
             "Bezugsgröße, aus der beides stammt. Wer die dritte Zeile weglässt, "
             "spart Platz und verliert die Prüfbarkeit.", "Tool_Slide")
bwd, bhd = deck.foto(s, "04_dash_kpi", max_w=CW, max_h=200)
B.band(s, Y0 + bhd + 20, 96, [
    "Die vier Kacheln zeigen dieselbe Größe in vier Auflösungen: Jahresumsatz, "
    "Bestellzahl, Bestellwert und die kumulierte Summe über neun Jahre. Der Sprung "
    "von 2,99 Millionen auf 14,52 Millionen ist kein Wachstum, sondern ein Wechsel "
    "des Zeitraums — deshalb steht er in der Beschriftung und nicht nur im Wert. "
    "Sämtliche Zahlen dieser Ansicht kommen beim Seitenaufruf aus der Datenbank."])

s = deck.neu("Lisa_Slide")
B.kopf(s, "Bauweise", "Das Dashboard hält keine Zahlen — es fragt sie ab", Q_EIG)
deck.einl(s, "In der ersten Fassung standen alle Zahlen fest im Quelltext der Seite. "
             "Das lief ohne Server, hatte aber eine Eigenschaft, die sich nicht "
             "aushalten ließ: Eine Zahl im HTML altert, ohne dass es jemand merkt. "
             "Heute lädt die Seite beim Aufruf 33 Sichten und baut daraus alles.")
B.klammer(s, CL, Y0, w2, 172, "Was der Umbau bringt",
          D.paras(["Eine Wahrheit: Diagramm, Kachel und Deutungstext lesen dieselbe "
                   "Sicht. Ein Widerspruch zwischen ihnen ist ausgeschlossen.",
                   "Neue Daten wirken sofort — ohne Bauschritt, ohne Änderung am HTML.",
                   "Der Wechsel der Quelle ist eine Klasse mit 34 Methoden."]), GOOD)
B.klammer(s, CL + w2 + 18, Y0, w2, 172, "Was er kostet",
          D.paras(["Die Seite braucht eine erreichbare Datenbank. Fehlt sie, zeigt "
                   "sie eine Fehlermeldung statt Zahlen — der gewollte Zustand.",
                   "Rechte und Antwortzeiten werden zum Thema: teure Aggregate müssen "
                   "materialisiert vorliegen, sonst läuft die Abfrage in eine Zeitgrenze.",
                   "Der Aufbau ist nicht mehr in einer Datei zu lesen."]), HINT)
B.band(s, Y0 + 188, 90, [
    "Der Umbau hat mehr über die Daten verraten als die Analyse davor: Erst als jede "
    "Zahl aus einer Abfrage kommen musste, fiel auf, dass mehrere Aussagen der ersten "
    "Fassung sich nicht nachrechnen ließen — darunter eine Segmentierung, die bei "
    "jeder Abfrage andere Größen lieferte. Wer eine Kennzahl nicht als Abfrage "
    "hinschreiben kann, hat sie noch nicht definiert."])

s = deck.neu("Tool_Slide")
B.kopf(s, "Segmentierung", "Aus 24.992 Kunden werden sieben adressierbare Gruppen", Q_FOTO)
deck.einl(s, "Einzelne Kunden sind keine Entscheidungsgrundlage, der Durchschnitt "
             "aller Kunden auch nicht. Die RFM-Segmentierung ordnet jeden Kunden nach "
             "Kaufabstand, Häufigkeit und Umsatz in Fünftel ein. Erst dadurch wird aus "
             "einer Gesamtzahl eine Liste, die eine Abteilung abarbeiten kann.",
         "Tool_Slide")
bw7, _ = deck.foto(s, "07_dash_rfm", max_h=HOEHE, max_w=540)
B.sprechblase(s, CL + bw7 + 24, Y0, CR - (CL + bw7 + 24), 250, D.paras([
    [("Was die Grafik entscheidbar macht", True, GOOD)],
    ["4.998 Kunden gelten als abwanderungsgefährdet — 20,0 Prozent des Bestands, "
     "im Mittel 88 Tage ohne Kauf."],
    ["Die Gruppe ist benannt, gezählt und adressierbar: eine Liste, kein Befund."],
    ["Die Farbe folgt dem Kaufabstand, nicht der Größe. Grün heißt kürzlich aktiv, "
     "rot heißt lange nicht mehr — auch bei gleicher Gruppengröße."],
]), farbe=GOOD)

s = deck.neu("Tool_Slide")
B.kopf(s, "Warenkorbanalyse", "Lift trennt echten Zusammenhang von bloßer Häufigkeit",
       Q_FOTO)
deck.einl(s, "Dass Pommes und Cola oft zusammen gekauft werden, ist keine Erkenntnis — "
             "beide sind einzeln häufig. Der Lift setzt die gemeinsame Häufigkeit ins "
             "Verhältnis zu der, die bei Unabhängigkeit zu erwarten wäre. Erst ein "
             "Wert deutlich über eins rechtfertigt ein Bündel.", "Tool_Slide")
bw6, bh6 = deck.foto(s, "06_dash_regeln", max_w=CW, max_h=196)
B.band(s, Y0 + bh6 + 18, 100, [
    "Von fünfzehn geprüften Regeln erreichen drei einen Lift über zwei. Die stärkste "
    "ist nicht die häufigste: Small Fries mit Cola 0.3l kommt auf einen Lift von 3,29 "
    "bei 90.608 gemeinsamen Bestellungen, während Medium Fries mit Cola 0.5l mit "
    "155.282 die häufigste Kombination ist, aber nur auf 2,73 kommt. Alle übrigen "
    "liegen zwischen 1,13 und 1,50 — dort kauft niemand das eine wegen des anderen."])

s = deck.neu("Lisa_Slide")
B.kopf(s, "Grenzen", "Was dieser Bestand nicht hergibt — und trotzdem gern behauptet wird",
       Q_DB)
deck.einl(s, "Zum Handwerk gehört, die Grenze des Bestands zu benennen. Die folgenden "
             "vier Aussagen wurden in der ersten Fassung des Dashboards behauptet und "
             "fielen beim Nachrechnen durch. Keine davon war böswillig — alle waren "
             "plausibel, und genau das macht sie gefährlich.")
for i, (t, b, c) in enumerate([
    ("\"Die App ist der effizienteste Kanal\"",
     ["Begründet mit dem höchsten Bestellwert. Sie hat 2025 den niedrigsten: "
      "21,47 EUR gegen 22,38 EUR im Drive-Through."], WARN),
    ("\"Drive-Through ist ein Pendlerkanal\"",
     ["Behauptet 35 Prozent der Frühbestellungen. Der Kanalmix ist über alle "
      "18 Öffnungsstunden nahezu konstant."], WARN),
    ("\"Ältere Kunden bestellen seltener\"",
     ["Die Bestellhäufigkeit liegt in allen sieben Altersgruppen zwischen 29,9 und "
      "30,4 je Kunde. Der Unterschied steckt im Bestellwert."], WARN),
    ("\"Student Discount hat den besten ROI\"",
     ["Der ausgewiesene ROI ist rechnerisch (100 − Rabattsatz) / Rabattsatz und "
      "misst nur den Rabattsatz, nicht die Wirkung."], WARN),
]):
    x = CL + (i % 2) * (w2 + 18)
    y = Y0 + (i // 2) * 120
    B.kachel(s, x, y, w2, 108, c, t, b)
B.band(s, Y0 + 248, 62, [
    "Alle vier sind aufgefallen, weil jede Zahl aus einer Abfrage kommen musste. "
    "Eine Behauptung im Fließtext prüft niemand; eine Sicht in der Datenbank schon."])

# ═══════════════════════════════════════════════════ Teil 8
deck.kapitel("Analytische Infrastruktur: der Weg dahinter")

s = deck.neu("Lisa_Slide")
B.kopf(s, "Bauarten", "Vier Wege von der Datenbank zum Bericht", Q_EIG)
deck.einl(s, "Die vier Zeilen unterscheiden sich nicht im Werkzeug, sondern darin, wo "
             "gerechnet wird. Direkt auf der operativen Datenbank ist es schnell "
             "eingerichtet, bremst den Betrieb und scheitert an der Historie. Mit "
             "Abzug und Sternschema ist es der Regelfall im Mittelstand. Eine "
             "Semantikschicht lohnt, sobald mehrere Werkzeuge dieselbe Kennzahl zeigen.")
deck.bild(s, "14_bi_architekturen", y=Y0, max_h=322)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Erblinien", "Erst das Warehouse, dann der Lake — und beide hatten recht",
       Q_LAKE)
deck.einl(s, "Die beiden Architekturen sind aus gegensätzlichen Nöten entstanden. Das "
             "Warehouse kam aus der Buchhaltung und verlangte Struktur vor dem "
             "Speichern; der Lake kam aus dem Web und wollte alles aufheben, auch was "
             "noch keine Struktur hat. Das Lakehouse versucht, beides zu haben.")
B.gegenueber(s, Y0, 166,
             (BLUE, "Data Warehouse · seit den 1990ern",
              ["Schema beim Schreiben: Was hineinkommt, ist typisiert und geprüft.",
               "Stark bei wiederkehrenden Berichten und Kennzahlen mit Definition.",
               "Schwach bei allem, was nicht vorher modelliert wurde."]),
             (METHOD, "Data Lake · seit den 2010ern",
              ["Schema beim Lesen: Dateien liegen roh, die Struktur entsteht bei der Abfrage.",
               "Stark bei Bild, Text und allem, wofür es noch keine Frage gibt.",
               "Schwach bei Konsistenz — ohne Disziplin wird daraus ein Sumpf."]),
             badge_l="1", badge_r="2")
B.band(s, Y0 + 182, 84, [
    "Das Lakehouse legt eine Tabellensemantik über die Dateien des Lake: "
    "Transaktionen, Schemaentwicklung und Zeitreisen auf offenen Formaten. "
    "Der Begriff stammt aus Armbrust et al. auf der CIDR 2021 und beschreibt "
    "keine Produktkategorie, sondern eine Schichtung."])

s = deck.neu("Lisa_Slide")
B.kopf(s, "Stand 2026", "Das Tabellenformat ist entschieden, der Katalog sortiert sich",
       Q_LAKE)
deck.einl(s, "Für die Lehre ist der Zwischenstand wichtiger als die Prognose: Bei den "
             "Dateiformaten hat sich Apache Iceberg durchgesetzt, bei der Frage, wer "
             "die Tabellen verwaltet, ist die Entscheidung noch offen. Genau dort "
             "liegt derzeit die Bindung an einen Anbieter.")
deck.bild(s, "10_lakehouse_schichten", y=Y0, max_h=240, max_w=790)
B.band(s, Y0 + 256, 66, [
    "Beim Format ist Iceberg gesetzt, Delta Lake bleibt im Databricks-Umfeld. Beim "
    "Katalog ist Apache Polaris seit Februar 2026 Top-Level-Projekt der "
    "Apache-Stiftung; daneben stehen Unity Catalog und die Dienste der Cloud-Anbieter. "
    "Wer heute baut, bindet sich beim Katalog, nicht mehr beim Format."])

s = deck.neu("Lisa_Slide")
B.kopf(s, "Organisation", "Data Mesh ist kein Bauplan, sondern ein Organigramm", Q_LAKE)
deck.einl(s, "Data Mesh beantwortet eine andere Frage als die bisherigen Ansätze: "
             "nicht wo die Daten liegen, sondern wer für sie einsteht. Fachbereiche "
             "besitzen ihre Daten als Produkt, mit Zusagen zu Qualität und "
             "Verfügbarkeit. Das ist eine Aussage über Zuständigkeit, nicht über Technik.")
deck.bild(s, "12_mesh", y=Y0 + 10, max_h=190)
B.band(s, Y0 + 216, 84, [
    "Der Ansatz trägt erst ab einer Größe, bei der eine zentrale Datenabteilung zum "
    "Engpass wird — und er verlangt in jedem Fachbereich Leute, die ein Datenprodukt "
    "betreiben können. Für ein Unternehmen mit acht Filialen ist er die falsche "
    "Antwort auf eine Frage, die sich dort nicht stellt."])

s = deck.neu("Slide")
B.kopf(s, "Einordnung", "Jede Bauart kauft Tragfähigkeit mit Aufwand", Q_EIG)
deck.bewertung(s, 140,
               ["Aufwand beim Aufbau", "trägt viele Quellen", "trägt viele Nutzer",
                "Bindung an einen Anbieter"],
               [("Eine Datenbank mit Sichten", [0.15, 0.20, 0.30, 0.05], True),
                ("Warehouse mit Sternschema", [0.55, 0.70, 0.85, 0.50], False),
                ("Lakehouse mit Katalog", [0.80, 1.00, 0.90, 0.45], False),
                ("Data Mesh", [1.00, 1.00, 1.00, 0.20], False)],
               rh=44.0, bw=260.0)
B.band(s, 372, 118, [
    "Die erste Zeile ist der Aufbau dieses Projekts, und für acht Filialen ist er "
    "richtig: Ein einziger Prozess, eine Datenbank, 36 Sichten. Die Zeilen darunter "
    "lösen Probleme, die es hier nicht gibt — mehrere Quellsysteme, hunderte "
    "gleichzeitige Nutzer, Fachbereiche mit eigener Datenhoheit. Woran man das Ende "
    "der ersten Zeile merkt: wenn der nächtliche Abzug nicht mehr bis zum Morgen "
    "fertig wird, wenn zwei Abteilungen dieselbe Kennzahl verschieden brauchen, oder "
    "wenn niemand mehr sagen kann, woher eine Zahl stammt."])

s = deck.neu("Slide")
B.kopf(s, "Werkzeugmarkt", "Das BI-Frontend ist eine Wahl zwischen vier Bauarten",
       Q_MARKT)
deck.bewertung(s, 136,
               ["Zugang für Fachbereiche", "Versionierbarkeit", "Betriebsaufwand",
                "Bindung an einen Anbieter"],
               [("Power BI · Tableau · Qlik · Looker", [1.00, 0.20, 0.55, 0.90], False),
                ("Metabase · Superset", [0.80, 0.40, 0.60, 0.15], False),
                ("Evidence · Rill · Lightdash", [0.35, 1.00, 0.35, 0.15], True),
                ("Eigene Seite auf eigener Datenbank", [0.15, 1.00, 0.35, 0.05], True)],
               rh=42.0, bw=282.0)
B.band(s, 356, 134, [
    "Marktlage 2026: Im Magic Quadrant für Analytics- und BI-Plattformen vom "
    "29. Juni 2026 stehen Microsoft, Salesforce Tableau, Google Looker, Qlik und "
    "ThoughtSpot im Führungsfeld; Gartner bewertete zwanzig Anbieter. Nach "
    "Anbieter-Trackern kommen Power BI und Tableau zusammen auf rund 40 Prozent der "
    "eingesetzten Plattformen — die Einzelwerte streuen je Quelle deutlich, weil "
    "unterschiedlich gezählt wird. Für die Lehre zählen die beiden unteren Zeilen: "
    "Was im Versionsverwaltungssystem liegt, lässt sich zeigen, nachbauen und "
    "kritisieren. Das ist bei einer Klickoberfläche schwer und bei einer Lizenz "
    "unmöglich."])

# ═══════════════════════════════════════════════════ Abschluss
s = deck.neu("Slide")
B.kopf(s, "Bauanleitung", "Fünf Schritte, die in jedem Technologiestapel dieselben sind",
       Q_EIG)
B.zuordnung(s, 132, [
    ("1 · Fachlichkeit",
     "Die Geschäftsvorfälle in Sätzen aufschreiben und mit dem Fachbereich prüfen. "
     "Kein Werkzeug nötig, und kein Schritt wird häufiger übersprungen."),
    ("2 · Modellieren",
     "ER-Diagramm, Normalformen, DDL. Hier: PostgreSQL. Genauso gut: MySQL, "
     "SQLite oder ein Blatt Papier — die Regeln sind dieselben."),
    ("3 · Übernehmen",
     "Rohdaten unverändert ablegen, typisieren, ins Auswertungsmodell überführen. "
     "Drei Schichten in versionierten SQL-Dateien; im Werkzeug heißt das dbt."),
    ("4 · Definieren",
     "Kennzahlen als Sichten, mit Formel, Zeitraum und Grundgesamtheit im Kommentar. "
     "Das ist die Semantikschicht, auch ohne Produkt dieses Namens."),
    ("5 · Zeigen",
     "Ein Frontend anhängen, das nichts selbst rechnet. Hier eine eigene Seite; "
     "sonst Metabase, Superset, Evidence oder Power BI."),
], rh=52.0, bw=180.0)

s = deck.neu("Lisa_Slide")
B.kopf(s, "Rückblick", "Sechs Stationen, und jede hat etwas ausgeschlossen", Q_EIG)
deck.einl(s, "Der Weg von der Fachlichkeit zum Dashboard ist eine Folge von "
             "Entscheidungen, nicht von Werkzeugen. Jede hat den Raum verengt: Wer "
             "die Granularität festlegt, legt fest, welche Summen zulässig sind; wer "
             "eine Kennzahl definiert, legt fest, welche Antwort gilt.")
B.stufenband(s, Y0, 40, KETTE)
B.zuordnung(s, Y0 + 58, [
    ("Ein Modell für alles",
     "Ausgeschlossen bei der Granularität: Es gibt zwei Modelle, weil es zwei "
     "Lastprofile gibt — und keines bedient beide gut."),
    ("Zahlen ohne Definition",
     "Ausgeschlossen bei der Kennzahl: Umsatz 2025 hat zwei zulässige Werte, und "
     "beide sind benannt. Die dritte Zahl war ein Verbundfehler."),
    ("Ein rechnender Bericht",
     "Ausgeschlossen beim Dashboard: Die Kennzahl steht in der Datenbank. Das "
     "Frontend zeigt sie und rechnet selbst nichts."),
], rh=54.0, bw=200.0)
B.band(s, Y0 + 256, 60, [
    "Wer diese drei Sätze begründen kann, hat die Fallstudie verstanden — und kann "
    "sie mit einem anderen Datenbestand und einem anderen Werkzeugkasten wiederholen."])

deck.speichern(OUT)
