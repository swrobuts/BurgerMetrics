#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bau_datenmodell.py — Foliendeck "BurgerMetrics: Datenmodell und Aufbau".

Dokumentiert, wie die drei Anwendungen des Projekts zusammenhaengen und warum
sie drei verschiedene Datenmodelle brauchen: Shop, Warenwirtschaft, Auswertung.
Das Schlusskapitel ordnet den gewaehlten Weg in die Alternativen ein — Data
Warehouse, Data Lake, Lakehouse, Data Mesh.

Die Diagramme stammen aus diagramme/*.mmd und werden von render_mermaid.mjs
erzeugt — dieses Skript setzt sie nur. Das gemeinsame Geruest steht in
deckwerk.py.

    python3 bau_datenmodell.py                  # -> ../../BurgerMetrics_Datenmodell.pptx
    python3 bau_datenmodell.py -o /pfad.pptx

Voraussetzungen: pip install python-pptx, Skill thws-slides (THWS_SKILL),
gerenderte PNG in diagramme/ (node render_mermaid.mjs).

Alle Messwerte im Deck stammen aus einem Lauf gegen den Datenbestand in
dataset/ (DuckDB 1.5.5, Median aus sieben Wiederholungen nach Warmlauf).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deckwerk as D                                     # noqa: E402

B = D.B
BLUE, WARN, GOOD, METHOD, HINT = D.BLUE, D.WARN, D.GOOD, D.METHOD, D.HINT
CL, CW, CR, Y0, YMAX, HOEHE = D.CL, D.CW, D.CR, D.Y0, D.YMAX, D.HOEHE

ap = argparse.ArgumentParser(description="Foliendeck Datenmodell bauen")
ap.add_argument("-o", "--ausgabe", default=None)
args = ap.parse_args()
OUT = Path(args.ausgabe) if args.ausgabe else D.HIER.parent.parent / "BurgerMetrics_Datenmodell.pptx"

QUELLE = D.QUELLE
Q_MESS = ("Eigene Messung · DuckDB 1.5.5 auf dataset/, Median aus sieben Läufen · "
          "Diagramme aus slides/diagramme/*.mmd")
Q_LIT = ("Eigene Darstellung nach Armbrust u. a., Lakehouse, CIDR 2021; "
         "Marktzahlen 2026 aus Anbieter- und Beraterberichten")
Q_MESH = ("Eigene Darstellung nach Dehghani, Data Mesh, 2022; "
          "Reifegrad- und Erfolgszahlen aus Beraterberichten 2025/2026")
Q_EIG = "Eigene Einschätzung · Diagramme aus slides/diagramme/*.mmd"
Q_DUCK = "Eigene Darstellung nach dem DuckLake-Manifest, ducklake.select, Stand 2026"

deck = D.Deck()

# ═══════════════════════════════════════════════════ Deckblatt
deck.deckblatt("BurgerMetrics", "Datenmodell und Aufbau")

# ═══════════════════════════════════════════════════ Der rote Faden
s = deck.neu("Lisa_Slide")
B.kopf(s, "Leitfrage", "Ein Datenmodell ist eine Antwort — und sie hat einen Preis", QUELLE)
deck.einl(s, "Dieses Deck folgt einer einzigen Frage: Welche Frage stellt das System, und "
        "welches Modell beantwortet sie am günstigsten? Günstig heißt nicht nur schnell. "
        "Jede Modellentscheidung verschiebt Kosten zwischen drei Konten, und keine "
        "Entscheidung senkt alle drei zugleich.")
B.chevron_kette(s, Y0, 38, ["1 · Drei Systeme, drei Fragen",
                            "2 · Konsistenz zuerst",
                            "3 · Lesetempo zuerst",
                            "4 · Ein Weg von vielen"])
w3 = (CW - 2 * 18) / 3
for i, (t, b, c) in enumerate([
    ("Schreibkosten", ["Was kostet es, einen Sachverhalt widerspruchsfrei zu halten?",
                       "Steigt mit jeder Stelle, an der dasselbe Merkmal steht.",
                       "Zahlt das operative System."], BLUE),
    ("Lesekosten", ["Was kostet eine Auswertung über den ganzen Bestand?",
                    "Steigt mit der Zahl der Verknüpfungen je Abfrage.",
                    "Zahlt das Auswertungssystem."], GOOD),
    ("Betriebskosten", ["Was kostet der Apparat, der beides am Laufen hält?",
                        "Steigt mit jeder zusätzlichen Komponente und Zuständigkeit.",
                        "Zahlt die Organisation — Thema von Kapitel 4."], METHOD),
]):
    B.kachel(s, CL + i * (w3 + 18), Y0 + 56, w3, 172, c, t, b)
B.band(s, Y0 + 242, 66, [
    "Das operative Modell nimmt hohe Lesekosten in Kauf, um Schreibkosten zu sparen. Das "
    "Auswertungsmodell dreht das um. Kapitel 4 zeigt Architekturen, die vor allem an der "
    "dritten Kostenart drehen — und was sie dafür verlangen."])

# ═══════════════════════════════════════════════════ Teil 1
deck.kapitel("Vom Geschäftsvorfall zum ersten Schema")

# Systemkontext
s = deck.neu("Lisa_Slide")
B.kopf(s, "Überblick", "Eine Bestellung durchläuft drei Systeme mit drei Aufgaben", QUELLE)
deck.einl(s, "Wer eine Bestellung aufgibt, löst eine Kette aus: Der Shop nimmt sie entgegen, die "
        "Warenwirtschaft verbucht sie, die Auswertung zählt sie später mit. Im Datenbestand "
        "sind das 754.513 Bestellungen aus neun Jahren, acht Filialen und vier Bestellkanälen — "
        "erfasst zwischen dem 15. März 2017 und dem 31. März 2026.")
deck.bild(s, "01_systemkontext", y=Y0 + 10, max_h=175)
B.band(s, Y0 + 200, 62, [
    "Der gestrichelte Pfeil ist die entscheidende Stelle: Die Auswertung liest nicht aus dem "
    "operativen System, sondern aus einem periodisch erzeugten Abzug. Sonst würde eine "
    "Jahresauswertung über 3,7 Millionen Zeilen den laufenden Kassenbetrieb ausbremsen."])

# Modellierungsweg 1: vom Satz zum Modell
s = deck.neu("Lisa_Slide")
B.kopf(s, "Modellierung · Schritt 1", "Vier Sätze Fachlichkeit, vier Entscheidungen im Modell", QUELLE)
deck.einl(s, "Ein Datenmodell beginnt nicht im Werkzeug, sondern in der Fachsprache. Am Beispiel "
        "des Online-Shops: Vier Sätze, wie sie in jedem Anforderungsgespräch fallen, tragen "
        "bereits alle Entscheidungen des Modells. Die Substantive werden zu Entitäten, die "
        "Verben zu Beziehungen — und die Nebensätze zu Kardinalitäten.")
B.zuordnung(s, Y0, [
    ("Ein Besucher öffnet die Speisekarte.",
     "Ein Substantiv mit eigenen Merkmalen wird eine Entität: SITZUNG, mit Kennung, "
     "Beginn, Gerät und Herkunft."),
    ("Er legt Artikel in den Warenkorb.",
     "Ein Verb zwischen zwei Entitäten wird eine Beziehung: Sitzung–Artikel. Die Menge "
     "gehört zur Beziehung, nicht zum Artikel — derselbe Artikel liegt in vielen Körben."),
    ("Angemeldet ist er nur manchmal.",
     "Eine Kann-Formulierung wird eine optionale Beziehung: der Kreis am Kundenende "
     "der Verbindungslinie."),
    ("Wird nichts bestellt, verfällt alles.",
     "Eine Aussage über Lebensdauer wird eine Modellgrenze: keine Historie, keine "
     "Archivpflicht — der Warenkorb ist kein Beleg."),
], rh=52.0, bw=286.0)

# Modellierungsweg 2: das ER-Diagramm (bisherige Shop-Folie, neu gerahmt)
s = deck.neu("Lisa_Slide")
B.kopf(s, "Modellierung · Schritt 2", "Der Shop speichert nur, was bis zum Kaufabschluss gebraucht wird", QUELLE)
deck.einl(s, "Aus den vier Sätzen entsteht dieses Entity-Relationship-Diagramm: drei Kernentitäten, "
        "eine optionale Beziehung zum Kunden. Es ist bewusst schmal — jede weitere Tabelle "
        "müsste eine fachliche Frage beantworten, die der Shop vor dem Kaufabschluss "
        "tatsächlich stellt.")
bw, _ = deck.bild(s, "02_shop_modell", max_w=470)
B.kachel(s, CL + bw + 24, Y0, CR - (CL + bw + 24), 190, METHOD, "Worauf dieses Modell optimiert ist",
         ["Sehr viele kleine Schreibvorgänge: jeder Klick ändert den Warenkorb.",
          "Kurze Lebensdauer — abgebrochene Sitzungen werden verworfen.",
          "Keine Historie, kein Bezug zu früheren Käufen.",
          "Mit dem Kaufabschluss übergibt der Shop an die Warenwirtschaft und ist fertig."])

# Modellierungsweg 3: Ueberfuehrungsregeln
s = deck.neu("Lisa_Slide")
B.kopf(s, "Modellierung · Schritt 3", "Vier Regeln überführen jedes ER-Diagramm in Tabellen", QUELLE)
deck.einl(s, "Der Weg vom Diagramm zum relationalen Schema folgt festen Abbildungsregeln — er ist "
        "Handwerk, keine Kunst. Dieselben vier Regeln, die hier den Shop übersetzen, tragen "
        "auch die 26 Tabellen der Warenwirtschaft; sie unterscheiden sich nur in der Zahl "
        "der Anwendungen.")
B.zuordnung(s, Y0, [
    ("Entitätstyp",
     "wird eine Tabelle, sein Schlüsselattribut der Primärschlüssel: aus SITZUNG wird "
     "die Tabelle sitzung mit session_id als Schlüssel."),
    ("1:n-Beziehung",
     "wird ein Fremdschlüssel auf der n-Seite: jede bestellposition der Warenwirtschaft "
     "trägt ihre bestellung_id."),
    ("n:m-Beziehung",
     "wird eine eigene Tabelle mit beiden Schlüsseln: Sitzung–Artikel wird "
     "warenkorbposition, das Beziehungsattribut menge zieht mit ein. Im "
     "Warenwirtschaftsmodell entsteht artikel_allergen nach derselben Regel."),
    ("Optionale Beziehung",
     "wird ein Fremdschlüssel, der leer bleiben darf: kunde_id in sitzung ist NULL, "
     "solange sich niemand anmeldet."),
], rh=52.0)

# Modellierungsweg 4: DDL
s = deck.neu("Lisa_Slide")
B.kopf(s, "Modellierung · Schritt 4", "Am Ende stehen zwei CREATE TABLE — jede Regel ist wiederzufinden",
       "Eigene Darstellung · Syntax geprüft in DuckDB und PostgreSQL")
deck.einl(s, "Das Ergebnis der vier Regeln ist ausführbarer Code. In den zwei Anweisungen steckt "
        "der ganze Weg: die Entität als Tabelle, der zusammengesetzte Schlüssel aus der "
        "n:m-Beziehung, das Beziehungsattribut menge und der Fremdschlüssel, der leer "
        "bleiben darf. Was im Diagramm der Krähenfuß war, heißt hier REFERENCES.")
D.Deck.code(s, CL, Y0, 462, [
    "CREATE TABLE sitzung (",
    "  session_id   VARCHAR PRIMARY KEY,",
    "  beginn       TIMESTAMP NOT NULL,",
    "  device_type  VARCHAR,",
    "  referrer     VARCHAR,",
    "  kunde_id     INTEGER REFERENCES kunde",
    "               -- NULL = nicht angemeldet",
    ");",
    "",
    "CREATE TABLE warenkorbposition (",
    "  session_id  VARCHAR  REFERENCES sitzung,",
    "  artikel_id  INTEGER  REFERENCES artikel,",
    "  menge       INTEGER  NOT NULL CHECK (menge > 0),",
    "  PRIMARY KEY (session_id, artikel_id)",
    ");",
])
B.kachel(s, CL + 462 + 24, Y0, CR - (CL + 462 + 24), 210, GOOD, "Woran die Regeln zu erkennen sind",
         ["Regel 1: sitzung ist die Tabelle zur Entität, session_id ihr Primärschlüssel.",
          "Regel 3: warenkorbposition trägt beide Schlüssel — zusammengesetzt als "
          "Primärschlüssel — und das Beziehungsattribut menge.",
          "Regel 4: kunde_id darf NULL sein — der Kreis aus dem Diagramm.",
          "NOT NULL und CHECK sichern, was fachlich gilt: keine leere, keine negative Menge."])

# Uebergabe an die Warenwirtschaft
s = deck.neu("Lisa_Slide")
B.kopf(s, "Übergabe", "Der Kaufabschluss ist eine Übergabe: aus flüchtig wird dauerhaft", QUELLE)
deck.einl(s, "Mit dem Kaufabschluss wechseln die Daten das System und den Charakter. Der Shop "
        "reicht seinen Warenkorb an die Warenwirtschaft weiter, die daraus einen Beleg "
        "macht — mit festen Bezügen auf Filiale, Zahlungsart und Aktion. Ein Detail trägt "
        "weit: Der Warenkorb verweist auf Preise, der Beleg kopiert sie.")
deck.bild(s, "19_checkout", y=Y0 + 6, max_h=200)
B.band(s, Y0 + 226, 92, [
    "Warum kopieren statt verweisen? Ein Beleg hält den Preis zum Kaufzeitpunkt fest, auch "
    "wenn der Listenpreis morgen steigt. Deshalb trägt bestellposition ein eigenes Feld "
    "einzelpreis — und deshalb lässt sich neun Jahre später noch korrekt auswerten, was 2017 "
    "eine Cola kostete. Genau diese kopierten Preise stehen heute in den CSV-Dateien."])

# ═══════════════════════════════════════════════════ Teil 2
deck.kapitel("Das operative Modell: Konsistenz zuerst")

# Verkaufspfad
s = deck.neu("Lisa_Slide")
B.kopf(s, "System 2 · Warenwirtschaft", "Aus dem Warenkorb wird ein Beleg mit festen Bezügen", QUELLE)
deck.einl(s, "Mit dem Kaufabschluss wird aus einem flüchtigen Warenkorb ein Beleg, der Jahre "
        "aufbewahrt wird. Er braucht feste Bezüge: welche Filiale, welcher Kunde, welche "
        "Zahlungsart. Die Positionen hängen zwingend am Kopf — im Bestand sind es im Mittel "
        "3,91 Positionen je Bestellung, nie null.")
bw, _ = deck.bild(s, "03_wawi_verkaufspfad", max_w=470, max_h=295)
B.kachel(s, CL + bw + 24, Y0, CR - (CL + bw + 24), 190, BLUE, "Die Notation lesen",
         ["Doppelstrich = genau eins, Krähenfuß = viele.",
          "kundenbestellung ||--|{ bestellposition: eine Bestellung hat mindestens eine Position.",
          "filiale ||--o{ kundenbestellung: eine Filiale kann auch null Bestellungen haben.",
          "Kreis = optional, Strich = verpflichtend."])

# Bereiche
s = deck.neu("Lisa_Slide")
B.kopf(s, "System 2 · Warenwirtschaft", "Der Verkauf ist ein Bereich von sieben — 26 Tabellen insgesamt", QUELLE)
deck.einl(s, "Ein Warenwirtschaftssystem bildet den ganzen Betrieb ab, nicht nur den Verkauf: "
        "26 Tabellen in sieben Bereichen, jedes Merkmal genau einmal. Für die Absatzfragen "
        "der Auswertung werden davon drei Bereiche gebraucht — Stammdaten, Verkauf und die "
        "externen Wetterdaten.")
deck.bild(s, "04_wawi_bereiche", y=Y0, max_h=185)
wb = (CW - 18) / 2
B.kachel(s, CL, Y0 + 200, wb, 122, BLUE, "Warum so viele Tabellen",
         ["Einkauf, Lager und Personal hängen am selben Artikelstamm.",
          "Jedes Merkmal steht genau einmal — das ist die dritte Normalform."])
B.kachel(s, CL + wb + 18, Y0 + 200, wb, 122, HINT, "Was davon die Auswertung braucht",
         ["Einkauf, Lager, Personal und Rechnungswesen beantworten keine Absatzfrage.",
          "Aus 26 Tabellen werden dadurch zwölf."])

# Normalisierung
s = deck.neu("Lisa_Slide")
B.kopf(s, "System 2 · Warenwirtschaft", "Drei Tabellen für einen Artikel — und warum das richtig ist", QUELLE)
deck.einl(s, "Ein Artikel hat eine Unterkategorie, die zu einer Kategorie gehört. Im operativen "
        "Modell sind das drei Tabellen. Das wirkt umständlich, hat aber einen Grund: Jeder "
        "Kategoriename steht genau einmal. Wer ihn ändert, ändert eine Zeile — nicht "
        "siebenundfünfzig, so viele Produkte führt der Bestand.")
B.gegenueber(s, Y0, 190,
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
deck.kapitel("Das Auswertungsmodell: Lesetempo zuerst")

# Denormalisierung
s = deck.neu("Lisa_Slide")
B.kopf(s, "System 3 · Auswertung", "Für die Auswertung wird die Normalisierung zurückgenommen", QUELLE)
deck.einl(s, "Das Auswertungsmodell dreht die Abwägung um. Die drei Artikel-Tabellen werden zu "
        "einer breiten Dimensionstabelle zusammengezogen. Kategorie und Unterkategorie stehen "
        "danach redundant in jeder der 57 Produktzeilen — und genau das ist gewollt.")
deck.bild(s, "05_denormalisierung", y=Y0, max_h=130)
B.kachel(s, CL, Y0 + 148, CW, 112, METHOD, "Warum die Redundanz vertretbar ist",
         ["Ein Auswertungsbestand wird periodisch neu beladen, nicht laufend fortgeschrieben.",
          "Änderungsanomalien entstehen im Schreibbetrieb — den gibt es hier nicht.",
          "Aus drei Verknüpfungen je Abfrage wird eine."])
B.band(s, Y0 + 274, 48, [
    "Faustregel: Konsistenz hat Vorrang im operativen System, Lesegeschwindigkeit im Auswertungssystem."])

# Die Zusammenführung als SQL
s = deck.neu("Lisa_Slide")
B.kopf(s, "System 3 · Auswertung", "Die Zusammenführung ist eine Abfrage — zwei Joins, eine Dimension",
       "Eigene Darstellung · vorführbar mit dataset/wawi_mini.sql und wawi_zu_analytisch.sql")
deck.einl(s, "Was die vorige Folie als Pfeil zeichnet, ist im Werkzeug eine einzige Abfrage: "
             "zwei Joins lösen die Normalisierung auf, die AS-Klauseln übersetzen die deutschen "
             "Betriebsbegriffe ins Auswertungsvokabular der CSV-Dateien. Mehr passiert bei "
             "einer Dimension nicht — und dasselbe Muster trägt alle sieben Zieltabellen.")
D.Deck.code(s, CL, Y0, 470, [
    "CREATE VIEW dim_product AS",
    "SELECT a.artikel_id   AS product_id,",
    "       a.name         AS product_name,",
    "       k.name         AS category,",
    "       u.name         AS subcategory,",
    "       a.vegetarisch  AS is_vegetarian,",
    "       a.listenpreis  AS unit_price",
    "FROM artikel a",
    "JOIN artikelunterkategorie u",
    "     USING (unterkategorie_id)",
    "JOIN artikelkategorie k",
    "     USING (kategorie_id);",
])
B.kachel(s, CL + 470 + 24, Y0, CR - (CL + 470 + 24), 168, METHOD, "Zwei Handgriffe, sieben Mal",
         ["Zusammenführen: Verknüpfungen auflösen, die sonst jede Abfrage neu bezahlt.",
          "Benennen: aus artikel wird dim_product, aus netto_gesamt wird net_total — das ist die stg-Schicht.",
          "Aus operativem NULL (keine Aktion) wird die Dimensionszeile 0, No Promotion."])
B.kachel(s, CL + 470 + 24, Y0 + 184, CR - (CL + 470 + 24), 116, GOOD, "Der Beweis läuft im Repo",
         ["wawi_mini.sql: der operative Ausschnitt, 14 Tabellen, deutsch.",
          "wawi_zu_analytisch.sql: die Sichten — acht von acht Zieltabellen zeilengleich mit burgermetrics_mini.sql."])

# Granularität
s = deck.neu("Lisa_Slide")
B.kopf(s, "System 3 · Auswertung", "Die erste Frage an jede Faktentabelle: Welches Ereignis ist eine Zeile?", QUELLE)
deck.einl(s, "Bestellung 1 aus dem Datenbestand, vollständig. Der Bestellkopf trägt den Rabatt und "
        "den Endbetrag, die drei Positionen tragen Menge und Einzelpreis. Beides sind Fakten — "
        "aber auf verschiedenen Ebenen. Diese Unterscheidung heißt Granularität.")
bw, _ = deck.bild(s, "06_granularitaet", max_w=380)
B.sprechblase(s, CL + bw + 30, Y0, CR - (CL + bw + 30), 196, D.paras([
    [("Warum das nicht in eine Tabelle passt", True, WARN)],
    ["Läge alles auf Positionsebene, stünde der Rabatt dreimal da — und jede Summe darüber wäre das Dreifache."],
    ["Läge alles auf Bestellebene, gäbe es keine Produktanalysen mehr."],
    ["Die Positionssummen ergeben hier 10,35 € und damit den Bruttobetrag, nicht den Nettobetrag von 8,80 €."],
]), farbe=WARN)

# Galaxy
s = deck.neu("Lisa_Slide")
B.kopf(s, "System 3 · Auswertung", "Zwei Granularitäten verlangen zwei Faktentabellen", QUELLE)
deck.einl(s, "Ein Stern-Schema hat definitionsgemäß eine Faktentabelle. Zwei Faktentabellen, die "
        "sich Dimensionen teilen, heißen Galaxy-Schema oder Fact Constellation — die "
        "naheliegende Erweiterung, sobald ein Sachverhalt auf zwei Ebenen gemessen wird. "
        "dim_product hängt nur an der Positionsebene, die übrigen Dimensionen an beiden.")
deck.bild(s, "07_galaxy", y=Y0, max_h=HOEHE)

# Die drei Modelle
s = deck.neu("Lisa_Slide")
B.kopf(s, "Zusammenschau", "Drei Modelle, weil drei verschiedene Fragen gestellt werden", QUELLE)
deck.einl(s, "Es gibt nicht ein richtiges Datenmodell für BurgerMetrics, sondern drei — je eines "
        "für die Aufgabe, die das System zu erfüllen hat. Eingebaut in die Kasse, erzeugte das "
        "Auswertungsmodell Inkonsistenzen; ausgewertet im Kassensystem, bremste jede Jahresabfrage "
        "den Betrieb. Die Trennung löst beide Probleme zugleich.")
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
                    "Lesen über 3,7 Millionen Zeilen",
                    "bewusste Redundanz, wenige Verknüpfungen",
                    "12 Tabellen"], GOOD),
]):
    B.kachel(s, CL + i * (w3 + 18), Y0, w3, 168, c, t, b)

# Kette
s = deck.neu("Lisa_Slide")
B.kopf(s, "Umsetzung", "Vom Quellsystem zum Bericht in drei Schichten", Q_MESS)
deck.einl(s, "Der Umbau geschieht nicht in einem Sprung, sondern in Schichten. Für BurgerMetrics sind "
        "die CSV-Dateien die raw-Schicht: unangetastet, damit jederzeit nachvollziehbar bleibt, "
        "was das Quellsystem geliefert hat. Erst die mittlere Schicht typisiert und benennt, "
        "erst die dritte modelliert um.")
deck.bild(s, "08_kette", y=Y0 + 10, max_h=110)
w2 = (CW - 18) / 2
B.kachel(s, CL, Y0 + 140, w2, 150, BLUE, "Warum drei Schichten und nicht eine",
         ["raw bleibt unverändert — der Vergleich mit dem Quellsystem bleibt möglich.",
          "stg ist als Sicht umgesetzt: immer frisch, kostet keinen Speicher.",
          "mart ist materialisiert — dort wird der Ladeschritt sichtbar, dort gehört später die Historisierung hin."])
B.kachel(s, CL + w2 + 18, Y0 + 140, w2, 150, METHOD, "Womit",
         ["Die Transformation ist SQL und gehört in versionierte Dateien, nicht in ein Werkzeugfenster.",
          "Der gesamte Bestand lädt in 2,3 Sekunden aus CSV und belegt danach 54,5 MB.",
          "Ein Data Warehouse würde hier Betrieb hinzufügen, ohne Fähigkeit hinzuzufügen."])

# ═══════════════════════════════════════════════════ Teil 4
deck.kapitel("Ein Weg von vielen")

# Fünf Entscheidungen
s = deck.neu("Slide")
B.kopf(s, "Rückblick", "Fünf Entscheidungen — und was jede von ihnen ausgeschlossen hat", Q_EIG)
B.zuordnung(s, Y0, [
    ("Wo auswerten?",
     "Gewählt: ein eigener Abzug in einer zweiten Datenbank. Verworfen: direkt im "
     "Kassensystem auswerten — Jahresabfragen hätten den laufenden Betrieb ausgebremst."),
    ("Wie modellieren?",
     "Gewählt: Galaxy-Schema mit zwei Granularitäten. Verworfen: One Big Table und "
     "Data Vault 2.0 — beide lösen andere Probleme als dieses."),
    ("Wie transformieren?",
     "Gewählt: SQL in versionierten Dateien, drei Schichten. Verworfen: eine Klickstrecke "
     "im ETL-Werkzeug — nicht vergleichbar, nicht wiederholbar."),
    ("Womit rechnen?",
     "Gewählt: DuckDB, ein Prozess, eine Datei. Verworfen: Data Warehouse, Data Lake, "
     "Lakehouse — bei 54,5 MB Bestand alles Aufwand ohne Gegenwert."),
    ("Wer verantwortet?",
     "Gewählt: ein zentrales Modell, eine Zuständigkeit. Verworfen: Data Mesh mit "
     "Datenprodukten je Domäne — es gibt hier nur eine Domäne."),
], rh=52.0)

# Drei Wege zu modellieren
s = deck.neu("Lisa_Slide")
B.kopf(s, "Alternative 1 · Modellierung", "Dieselben Fakten lassen sich auf drei Arten ordnen", QUELLE)
deck.einl(s, "Das Galaxy-Schema ist eine Wahl, keine Notwendigkeit. One Big Table spart jede "
        "Verknüpfung, kostet dafür Speicher und schließt die Positionsebene aus. Data Vault "
        "2.0 trennt Schlüssel, Beziehungen und Merkmale und hält jede Änderung historisiert — "
        "um den Preis, dass die Rohschicht ohne Hilfsschichten kaum abfragbar ist.")
deck.bild(s, "09_modellierungswege", y=Y0, max_h=238)
B.band(s, Y0 + 250, 66, [
    "Der Bestand liegt in beiden Formen vor: obt_orders.csv hat 41 Spalten und 754.513 Zeilen "
    "und beantwortet die Filialfrage in 3,2 statt 3,9 Millisekunden. Der Unterschied ist "
    "messbar und bei dieser Größe bedeutungslos — die Positionsebene fehlt dafür ganz."])

# Warehouse und Lake
s = deck.neu("Lisa_Slide")
B.kopf(s, "Alternative 2 · Architektur", "Zwei Erblinien: erst das Warehouse, dann der Lake", Q_LIT)
deck.einl(s, "Beide Bauarten beantworten dieselbe Frage — wo die Auswertungsdaten liegen sollen — "
        "und beide scheitern an je einer Seite. Das Warehouse verlangt die Struktur vor dem "
        "Schreiben, der Lake verschiebt sie auf das Lesen. Das ist der ganze Gegensatz, alles "
        "Weitere folgt daraus.")
B.gegenueber(s, Y0, 190,
             (BLUE, "Data Warehouse · schema-on-write",
              ["Die Struktur steht fest, bevor eine Zeile geschrieben wird.",
               "Starke Zusicherungen: Transaktionen, Typen, Rechte, feste Kennzahlendefinitionen.",
               "Preis: unstrukturierte Daten passen nicht hinein, Speicher und Rechenwerk "
               "sind aneinander gebunden, ein Anbieterwechsel ist teuer."]),
             (HINT, "Data Lake · schema-on-read",
              ["Alles darf hinein, die Struktur entsteht erst beim Lesen.",
               "Billiger Objektspeicher, beliebige Rechenwerke, auch Bilder und Text.",
               "Preis: ohne Katalog und Zusicherungen entsteht ein Data Swamp — Dateien, "
               "die niemand mehr deuten kann."]),
             badge_l="1", badge_r="2")

# Lakehouse
s = deck.neu("Lisa_Slide")
B.kopf(s, "Alternative 3 · Architektur", "Das Lakehouse legt Tabellensemantik über die Dateien", Q_LIT)
deck.einl(s, "Das Lakehouse — 2021 von Armbrust, Ghodsi, Xin und Zaharia so benannt — behält den "
        "billigen Objektspeicher und holt die fehlenden Zusicherungen als eigene Schicht "
        "zurück: ein Tabellenformat über den Parquet-Dateien, dazu ein Katalog. Genau diese "
        "zwei Kästen unterscheiden es vom Lake.")
deck.bild(s, "10_lakehouse_schichten", y=Y0, max_h=300)

# Lakehouse: Stand 2026
s = deck.neu("Slide")
B.kopf(s, "Alternative 3 · Stand 2026", "Das Format ist entschieden, der Katalog ist es nicht", Q_LIT)
B.kachel(s, CL, Y0, w2, 150, BLUE, "Wo sich der Markt geeinigt hat",
         ["Apache Iceberg gilt als die Richtung, auf die sich die großen Anbieter zubewegen.",
          "Delta UniForm schreibt eine Tabelle einmal und legt Iceberg-Metadaten daneben.",
          "Über die Hälfte der Organisationen setzt nach Marktberichten Lakehouse-Muster ein."])
B.kachel(s, CL + w2 + 18, Y0, w2, 150, HINT, "Wo es offen ist",
         ["Der Katalog ist die neue Bindungsstelle: Polaris, Glue, Nessie, Unity, Lakekeeper.",
          "Apache Polaris ist seit Februar 2026 ein Projekt oberster Ebene der Apache-Stiftung.",
          "Wer heute wählt, wählt vor allem einen Katalog — nicht ein Dateiformat."])
B.band(s, Y0 + 170, 76, [
    "Für die Lehre ist das die eigentliche Beobachtung: Der Streit hat sich von der Frage "
    "nach dem Dateiformat zur Frage nach dem Verzeichnis verschoben. Offene Dateien allein "
    "schaffen keine Unabhängigkeit, solange der Katalog geschlossen bleibt — und am Katalog "
    "hängen Rechte, Schnappschüsse und der Schemaverlauf."])

# DuckLake
s = deck.neu("Lisa_Slide")
B.kopf(s, "Alternative 4 · Gegenentwurf", "DuckLake stellt die Frage anders: Warum Metadaten in Dateien?", Q_DUCK)
deck.einl(s, "Iceberg und Delta legen ihre Metadaten selbst als Dateien ab und brauchen für einen "
        "Lesevorgang mehrere Anfragen hintereinander. Für die Konsistenz mussten beide am Ende "
        "doch eine Datenbank als Katalog vorsehen. DuckLake zieht daraus den Schluss, alle "
        "Metadaten gleich in diese Datenbank zu legen — Version 1.0 seit April 2026.")
deck.bild(s, "11_ducklake_metadaten", y=Y0, max_h=HOEHE)

# Data Mesh
s = deck.neu("Lisa_Slide")
B.kopf(s, "Alternative 5 · Organisation", "Data Mesh ist kein Bauplan, sondern ein Organigramm", Q_MESH)
deck.einl(s, "Data Mesh beantwortet nicht, wo die Daten liegen, sondern wer sie verantwortet: nicht "
        "ein zentrales Datenteam, sondern die Fachdomäne, die sie erzeugt — als Datenprodukt "
        "mit Zusagen, unter gemeinsamen Regeln auf einer geteilten Plattform. Das ist eine "
        "Aussage über Zuständigkeiten, nicht über Dateiformate.")
deck.bild(s, "12_mesh", y=Y0, max_h=200)
B.klammer(s, CL, Y0 + 216, w2, 106, "Was davon geblieben ist",
          D.paras(["Verantwortung liegt bei der Domäne, in der die Daten entstehen.",
                  "Daten gelten als Produkt mit Zusagen an ihre Abnehmer."]), GOOD)
B.klammer(s, CL + w2 + 18, Y0 + 216, w2, 106, "Was sich nicht durchgesetzt hat",
          D.paras(["Nach Beraterberichten hat nur etwa ein Fünftel der Organisationen die nötige Reife.",
                  "In einer Erhebung von Oktober 2025 erreichten hybride Formen ihre Ziele häufiger."]), WARN)

# Bewertung
s = deck.neu("Slide")
B.kopf(s, "Einordnung", "Jede Bauart kauft Tragfähigkeit mit Aufwand", Q_EIG)
deck.bewertung(s, Y0,
          ["Datenmenge, die sie trägt", "Betriebsaufwand",
           "Bindung an einen Anbieter", "Aufwand für die Organisation"],
          [("Ein Prozess · DuckDB, DuckLake", [0.25, 0.10, 0.10, 0.10], True),
           ("Data Warehouse", [0.85, 0.60, 0.90, 0.40], False),
           ("Data Lake", [1.00, 0.75, 0.25, 0.40], False),
           ("Lakehouse", [1.00, 0.70, 0.30, 0.50], False),
           ("Data Mesh", [1.00, 0.90, 0.30, 1.00], False)])
B.band(s, Y0 + 286, 36, [
    "Längerer Balken = mehr davon. Die hervorgehobene Zeile ist der hier gewählte Weg."])

# Schluss
s = deck.neu("Lisa_Slide")
B.kopf(s, "Ergebnis", "Warum hier ein einziger Prozess genügt — und woran man das Ende merkt", Q_MESS)
deck.einl(s, "Die Wahl gegen jede dieser Architekturen ist keine grundsätzliche, sondern eine über "
        "die Größenordnung. Der gesamte Bestand — 754.513 Bestellungen und 2.950.082 "
        "Positionen — belegt nach dem Laden 54,5 MB und antwortet in Millisekunden. Ein "
        "verteiltes System hätte hier nichts zu verteilen.")
B.kennzahlen(s, Y0, 86, [
    ("CSV-Rohdaten", "311,4 MB", D.SEC),
    ("nach dem Laden", "54,5 MB", BLUE),
    ("Stern-Schema, 2 Verknüpfungen", "3,9 ms", BLUE),
    ("Positionsebene, 3 Verknüpfungen", "14,7 ms", BLUE),
])
B.kachel(s, CL, Y0 + 102, w2, 168, GOOD, "Warum das trägt",
         ["Analytische Arbeitsmengen sind meist klein: Der Median liegt nach Erhebungen "
          "unter 100 GB, dieser Bestand um drei Größenordnungen darunter.",
          "Ein Prozess, eine Datei, keine Zuständigkeitsgrenze — nichts davon muss betrieben werden.",
          "Parquet und SQL bleiben lesbar, auch wenn das Werkzeug gewechselt wird."])
B.kachel(s, CL + w2 + 18, Y0 + 102, w2, 168, WARN, "Woran man den Wechsel merkt",
         ["Der Bestand passt nicht mehr auf eine Maschine — dann Objektspeicher und Lakehouse.",
          "Viele schreiben gleichzeitig — dann ein Tabellenformat mit Transaktionen.",
          "Mehrere Fachbereiche streiten über Kennzahlendefinitionen — dann ist es eine "
          "Organisationsfrage, und erst dann lohnt der Blick auf Data Mesh."])

sys.exit(deck.speichern(OUT))
