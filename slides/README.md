# Foliendeck

Ein Bauskript, ein Deck:

| Skript | Deck | Zweck |
|---|---|---|
| `bau_fallstudie.py` | **Von der Fachlichkeit zum Dashboard** (53 Folien) | Die Kette in einer Linie: sechs Sätze über das Geschäft, daraus ein ER-Diagramm, daraus normalisierte Tabellen, darauf Webshop und Kasse, von deren Belegen über den Datenfluss ins Galaxy-Schema — und von dort zu Kennzahlen, Dashboard und der Frage, welche Analytics-Infrastruktur ein solches Vorhaben trägt. |

`deckwerk.py` trägt, was das Bauskript braucht: den Skill finden, den Platzhalterfehler des `spec_loader` umgehen, Absätze richtig übergeben, Diagramme und Bildschirmfotos maßstabsgetreu setzen — und melden, wenn eine Diagrammbeschriftung unter 10,5 pt fiele.

Das Deck fasst zusammen, was in [`../docs/`](../docs/) ausführlich steht.

**Vorgänger.** Bis August 2026 gab es drei Decks nebeneinander — `bau_datenmodell.py`, `bau_bi.py` und das ältere `bau_deck.py`. Sie sind in `bau_fallstudie.py` aufgegangen; die Aufteilung zerriss den Weg vom Modell zur Kennzahl genau an der Stelle, an der er zusammenhängt. Die alten Skripte stehen in der Git-Historie.

---


## Der rote Faden

**Der Bogen.** Welche Frage stellt das System — und welches Modell beantwortet sie am günstigsten? Günstig heißt drei Konten: **Schreibkosten** (einen Sachverhalt widerspruchsfrei halten), **Lesekosten** (eine Auswertung über den ganzen Bestand), **Betriebskosten** (der Apparat, der beides trägt). Das operative Modell nimmt hohe Lesekosten in Kauf, um Schreibkosten zu sparen; das Auswertungsmodell dreht das um; die Architekturen in Kapitel 4 drehen an der dritten.

**BI-Deck:** Eine Kennzahl zählt erst, wenn sie eine Entscheidung ändert. Zwischen Frage und Entscheidung liegen fünf Stationen — **Frage · Kennzahl · Modell · Werkzeug · Entscheidung** —, und an jeder kann die Antwort kippen.

| | Datenmodell-Deck | BI-Deck |
|---|---|---|
| 1 | Vom Geschäftsvorfall zum ersten Schema | Die Fallstudie: drei Systeme, eine Datenspur |
| 2 | Das operative Modell: Konsistenz zuerst | Kennzahlen definieren, rechnen und prüfen |
| 3 | Das Auswertungsmodell: Lesetempo zuerst | Vom Auswertungsmodell zum Dashboard |
| 4 | Ein Weg von vielen | Von der Zahl zur Entscheidung |
| 5 | — | Architektur, Werkzeuge, Nachbau |

Kapitel 1 des Datenmodell-Decks führt den vollständigen Modellierungsweg am Shop vor: vier Anforderungssätze → ER-Diagramm → die vier Abbildungsregeln (Entitätstyp → Tabelle, 1:n → Fremdschlüssel, n:m → eigene Tabelle, optional → NULL) → zwei CREATE TABLE, in denen jede Regel wiederzufinden ist → die Übergabe an die Warenwirtschaft beim Kaufabschluss. Die operativen Datenmodelle beider Erfassungssysteme stehen attributiert auf eigenen Folien (`17_webshop_er`, `18_pos_er`); die Zusammenführung operativ → analytisch ist im Datenmodell-Deck als SQL-Folie ausgeführt und im Repo vorführbar (`../dataset/wawi_mini.sql` + `../dataset/wawi_zu_analytisch.sql` — acht von acht Zieltabellen zeilengleich mit `burgermetrics_mini.sql`). Kapitel 1 des BI-Decks stellt die Fallstudie vor und zeigt jedes System doppelt: die Kundensicht und die zuschaltbare Datensicht (Website an/aus, Kasse an/aus). Die Folie „Transaktionssysteme antworten je Vorgang, Analysesysteme je Frage" trennt die operative von der entscheidungsrelevanten Welt; Kapitel 5 endet mit einer Bauanleitung in vier Schritten, die den Technologiestapel offen lässt (DuckDB oder SQLite oder PostgreSQL; statische Seite oder Metabase oder Evidence oder Power BI).

---

## Warum hier nur die Skripte liegen

Die gebauten Decks (`.pptx`) und ihre PDF-Renders sind **absichtlich nicht versioniert**. Der Grund ist keine Nachlässigkeit, sondern die Schriftlizenz:

Eine PPTX bettet die verwendeten Schriften ein. In diesem Fall sind das rund **2,1 MB Schriftdaten**, darunter **GT Planar Light** und **GT Planar Medium** — die kommerziell lizenzierte Hausschrift — sowie mehrere Segoe-UI-Schnitte von Microsoft. Läge die Datei in diesem öffentlichen Repository, würden diese Schriften mitverbreitet.

Dasselbe gilt für die Master-Vorlage `template.pptx`. Sie bleibt außerhalb des Repositorys.

Versioniert ist deshalb, was gefahrlos versioniert werden kann: die Bauwege, die Diagrammquellen, die Bildschirmfotos und die Fachbegriffsliste.

---

## Die Diagramme

Alle Diagramme sind **Mermaid-Quelltext** in [`diagramme/`](diagramme/) — versioniert, vergleichbar, ohne Zeichenprogramm zu ändern:

| Datei | Zeigt | Deck |
|---|---|---|
| `01_systemkontext.mmd` | Kunde → Shop/Kasse → Warenwirtschaft ⇢ Auswertung → Bericht | Datenmodell |
| `02_shop_modell.mmd` | Das schmale Sitzungsmodell des Shops (ER), namensgleich mit der DDL-Folie | Datenmodell |
| `03_wawi_verkaufspfad.mmd` | Der Verkaufspfad der Warenwirtschaft (ER) | Datenmodell |
| `04_wawi_bereiche.mmd` | 26 Tabellen in sieben Bereichen — welche in die Auswertung fließen | Datenmodell |
| `05_denormalisierung.mmd` | Drei normalisierte Artikel-Tabellen → eine breite Dimensionstabelle | Datenmodell |
| `06_granularitaet.mmd` | Bestellkopf gegen Bestellpositionen | Datenmodell |
| `07_galaxy.mmd` | Das Galaxy-Schema mit zwei Faktentabellen | beide |
| `08_kette.mmd` | Quellsystem → raw → stg → mart → Bericht | Datenmodell |
| `09_modellierungswege.mmd` | Galaxy-Schema, One Big Table und Data Vault 2.0 nebeneinander | Datenmodell |
| `10_lakehouse_schichten.mmd` | Warehouse, Lake und Lakehouse als drei Schichtfolgen | Datenmodell |
| `11_ducklake_metadaten.mmd` | Metadaten als Dateien (Iceberg, Delta) gegen Metadaten in der Datenbank (DuckLake) | Datenmodell |
| `12_mesh.mmd` | Zentrales Datenteam gegen Datenprodukte je Domäne | Datenmodell |
| `13_bi_kennzahlweg.mmd` | Von der Faktentabelle zur Kachel in vier Schritten | BI |
| `14_bi_architekturen.mmd` | Vier Wege von der Datenbank zum Bericht | BI |
| `15_bi_semantik.mmd` | Mit und ohne semantische Schicht | BI |
| `16_datenspur.mmd` | Wo Daten entstehen, verbucht und befragt werden | BI |
| `17_webshop_er.mmd` | Das Webshop-Modell mit Attributen: Sitzung, Ereignis, Warenkorb | BI |
| `18_pos_er.mmd` | Der Kassenbeleg mit Attributen: kundenbestellung und bestellposition | BI |
| `19_checkout.mmd` | Der Kaufabschluss als Übergabe: flüchtiger Warenkorb → dauerhafter Beleg | Datenmodell |

### Rendern

```bash
npm i playwright
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" node render_mermaid.mjs
```

Das Skript schreibt zu jeder `.mmd` eine `.png` daneben und meldet deren Maße.

**Warum über einen Browser und nicht über einen SVG-Rasterer:** Mermaid setzt Beschriftungen in `<foreignObject>`, also HTML innerhalb von SVG. Das ist kein wohlgeformtes XML — `cairosvg` und verwandte Werkzeuge brechen daran mit *„mismatched tag"* ab. Die Option `flowchart.htmlLabels=false` greift in Mermaid 11 nicht mehr. Ein Browser rendert `foreignObject` nativ; deshalb Chrome, headless, mit `deviceScaleFactor: 3` für die Projektion.

Das THWS-Theme geht über `mermaid.initialize()` und **nicht** als vorangestellter `%%{init}%%`-Block in die Quelle. Mermaid wertet nur die erste init-Direktive einer Datei aus; ein vorangestellter Block würde jede Direktive im `.mmd` stillschweigend verwerfen — etwa die ER-Einstellungen in `02` und `03`.

### Was beim Layout zu beachten ist

Die Schriftgröße im Diagramm ist an das Seitenverhältnis gekoppelt. Mermaid setzt 15 px; auf der Folie kommt davon an:

> Schriftgrad in pt = 15 × (Bildbreite in pt ÷ Diagrammbreite in CSS-px)

Bei einer Inhaltsbreite von 903 pt und einer Inhaltshöhe von 322 pt heißt das: ein Diagramm darf höchstens rund **1130 × 400 CSS-px** groß sein, sonst fällt die Beschriftung unter 12 pt und ist im Hörsaal nicht mehr lesbar. Hohe, schmale Diagramme sind deshalb das eigentliche Problem — nicht breite. `deckwerk.Deck.bild()` rechnet den Wert aus und warnt unterhalb von 10,5 pt.

Vier Eigenheiten, die jeweils einen Neubau gekostet haben:

* **`direction` im Subgraph wird ignoriert.** Weder `direction LR` noch `direction TB` greift zuverlässig. Was stattdessen gilt: Bei `flowchart LR` stapeln sich unverbundene Teilgraphen **untereinander** und die Knoten darin laufen waagerecht; bei `flowchart TB` stehen sie **nebeneinander** und die Knoten stapeln sich.
* **Ohne Kanten ordnet dagre die Knoten beliebig.** Wer Zeilen will, erzwingt sie mit unsichtbaren Kanten (`~~~`) — siehe `04`, `10`, `12` und `14`.
* **Teilgraphen erscheinen in umgekehrter Reihenfolge.** Wer den ersten Block oben haben will, notiert ihn zuletzt — siehe `09` und `11`.
* **ER-Diagramme brauchen eigene Abstände.** Ohne `%%{init: {"er": {...}}}%%` läuft `03_wawi_verkaufspfad` mit 637 × 482 CSS-px auf 10 pt Beschriftung hinaus; mit engeren `nodeSpacing`, `rankSpacing` und `minEntityHeight` sind es 388 × 308 und 14,4 pt.

Die Farben stammen aus `assets/tokens.json` des Skills **thws-slides**: Grau als Normalfall, Blau nur als Akzent.

---

## Die Bildschirmfotos

Das BI-Deck zeigt die drei Anwendungen des Projekts im Bild — jeweils in Kundensicht und Datensicht. Die 14 Aufnahmen liegen in [`bilder/`](bilder/) und entstehen mit `screenshots.mjs`:

```bash
python3 -m http.server 8899 --directory ../web
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" node screenshots.mjs
```

**Warum ein Skript und nicht Bilder von Hand:** Ein Screenshot altert mit der Anwendung. Wer die Aufnahme als Code hat, wiederholt sie nach jeder Änderung — in derselben Größe, mit demselben Ausschnitt, ohne Handarbeit.

Drei Dinge steuert das Skript, die von Hand mühsam wären:

* **Zustand herstellen.** Die Datensicht der Kasse zeigt erst etwas, wenn etwas gebucht ist. Das Skript tippt drei Produkte an, schaltet um und wartet die Einblendung ab.
* **Nur das Sichtbare treffen.** Die Reiter des Dashboards bleiben im DOM und sind nur ausgeblendet; `page.$('.chart-card')` erwischt sonst den ersten, versteckten, und der Screenshot läuft in einen Zeitablauf. Der Auswahlausdruck endet deshalb auf `:visible`.
* **Ballast entfernen.** Der Deutungsblock unter jedem Diagramm ist auf einer Folie zu klein zum Lesen und macht die Aufnahme unnötig hoch. Er wird vor der Aufnahme entfernt; auf der Folie steht die Deutung in der Sprechblase daneben.
* **Animationen stilllegen.** Der Datenmodus des Shops legt ein endlos animiertes Scanline-Overlay über die Seite. Die Endlosanimation kann den Screenshot-Pfad zu einem weißen Bild machen; vor der Aufnahme wird sie per eingeschobenem Stylesheet abgeschaltet — sichtbar ist der Effekt bei 1,5 Prozent Deckung ohnehin nicht.

Fotolastige Seiten werden als JPEG gespeichert, Diagramme als PNG: Der Kassenbildschirm kostet als PNG 1,8 MB und als JPEG rund ein Sechstel davon, bei der Projektion ununterscheidbar. Bei Flächenfarben und dünnen Linien erzeugt JPEG dagegen sichtbare Kanten.

---

## Voraussetzungen

```bash
pip install python-pptx
npm i playwright
```

Dazu der Skill **thws-slides** mit `assets/template.pptx` und `scripts/bausteine.py`:

```bash
export THWS_SKILL="/Pfad/zu/skills/thws-slides"
```

Ohne die Variable sucht `deckwerk.py` an den üblichen Stellen und bricht mit einer Wegbeschreibung ab, wenn es die Vorlage nicht findet.

---

## Bauen

```bash
python3 bau_fallstudie.py                       # -> ../../BurgerMetrics_Fallstudie.pptx
python3 bau_fallstudie.py -o /pfad/deck.pptx    # alternatives Ziel
```

Die Skripte melden am Ende, ob ein Baustein mehr Platz braucht, als ihm zugewiesen wurde, und beenden sich in dem Fall mit Rückgabewert 1. Solche Warnungen sind vor der Auslieferung abzuarbeiten — sie bedeuten überlaufenden Text.

---

## Prüfen

```bash
cd "$THWS_SKILL/scripts"
python3 trennstrich_check.py   DECK.pptx
python3 einleitung_budget.py   DECK.pptx
python3 formsprache_audit.py   DECK.pptx
python3 sprache_check.py       DECK.pptx --whitelist .../fachbegriffe.txt
```

`fachbegriffe.txt` fängt die Fachbezeichner des Projekts ab (`dim_`, `fact_`, `raw`/`stg`/`mart`, Lift, Konfidenz, Iceberg, Lakehouse, Metabase, Filialnamen). Ohne sie meldet die Rechtschreibprüfung mehrere hundert Fehlalarme.

Zwei Restbefunde bleiben und sind keine: Die Füllwortliste des Prüfskripts enthält die Einzelwörter mehrteiliger Wendungen (`im`, `in`, `unter`, `vor`) — gewöhnliche Präpositionen zählen dadurch mit. Und die Lesbarkeitsformel bestraft deutsche Komposita: „Betriebsmonate" hebt den Wert unabhängig davon, wie kurz der Satz ist.

Der **Formsprache-Audit** misst, wie viele verschiedene Folienstrukturen ein Deck verwendet (Ziel: 0,62 verschiedene je Folie) und ob ein Motiv in einem Kapitel über ein Drittel kommt. Beide Decks laufen zunächst darunter, weil sich „Einleitung + ein Bild + eine Kachel" von selbst wiederholt — beim BI-Deck kamen vier Screenshot-Folien mit Sprechblase in einem Kapitel zusammen. Es genügt, zwei oder drei Folien auf andere Bausteine umzustellen: eine Klammer statt einer Sprechblase, eine Ampel statt eines Textblocks, vier Kacheln statt einer Zuordnungsliste.

### Render — und warum er nötig ist

Zahlen im XML sagen nichts über Kollision, Weißraum und Lesefluss. Erst der Render zeigt sie:

```bash
soffice --headless --convert-to pdf --outdir OUT DECK.pptx
```

Keine Folie gilt als fertig, bevor sie gerendert angesehen wurde. Sechs Mängel waren ausschließlich so sichtbar: ein Erläuterungsband quer durch ein zu hoch geratenes Diagramm; ein Bereichsdiagramm mit 5,8 pt Beschriftung; ein Mermaid-Zylinder, dessen Text über die eigene Form hinauslief; zwei Vergleichsdiagramme in umgekehrter Reihenfolge; ein schwarzer Ladeschirm statt der Startseite im Bildschirmfoto; und eine Bewertungsmatrix, deren Kreise falsche Werte zeigten.

Der letzte Punkt ist der lehrreichste: `bausteine.harvey()` zeichnet teilgefüllte Kreise als PowerPoint-`PIE`-Form. **LibreOffice verwirft deren Winkelangaben** — halbvolle Kreise kamen als leere oder volle heraus, eine Zeile mit den Werten 0,25/0,10/0,10/0,10 sah aus wie eine mit lauter Höchstwerten. `deckwerk.Deck.bewertung()` arbeitet deshalb mit Rechtecken, die jedes Programm gleich darstellt.

**Eine weitere Eigenheit des Renders:** LibreOffice kann die eingebettete Hausschrift nicht lesen (`EOT out of spec: no blank loca table found`) und ersetzt sie. Titel erscheinen im PDF deshalb in einer fremden Schrift und brechen früher um als in PowerPoint. Ein Befund „läuft knapp über" gehört daher in PowerPoint nachgesehen, bevor Text gekürzt wird. Umgekehrt gilt: Was im Render passt, passt in PowerPoint erst recht.

---

## Zahlen in den Decks

Alle Messwerte stammen aus einem Lauf gegen `../dataset/` mit DuckDB 1.5.5, Median aus sieben Wiederholungen nach Warmlauf:

| | |
|---|---|
| CSV-Rohdaten | 311,4 MB |
| Datenbankdatei nach dem Laden | 54,5 MB |
| Ladezeit aus CSV | 2,3 s |
| Stern-Schema, 2 Verknüpfungen (Umsatz je Filiale und Jahr) | 3,9 ms |
| One Big Table, 0 Verknüpfungen (gleiche Frage) | 3,2 ms |
| Positionsebene, 3 Verknüpfungen (Umsatz je Kategorie und Jahr) | 14,7 ms |
| Bestellungen · Positionen | 754.513 · 2.950.082 |
| Kunden mit Bestellung (von 25.000 Sätzen) | 24.992 |
| Zeitraum | 15.03.2017 – 31.03.2026 |
| Umsatz 2025 netto · brutto | 2.994.771 € · 3.032.646 € |

Die fachlichen Zahlen sind über `../dataset/verify_readme.py` nachprüfbar.

---

## Quellen für die Alternativen- und Werkzeugkapitel

* **Lakehouse, Begriffsprägung:** M. Armbrust, A. Ghodsi, R. Xin, M. Zaharia: *Lakehouse: A New Generation of Open Platforms that Unify Data Warehousing and Advanced Analytics*, CIDR 2021 — [PDF](https://people.eecs.berkeley.edu/~matei/papers/2021/cidr_lakehouse.pdf)
* **DuckLake:** [ducklake.select](https://ducklake.select/) und das [Manifest](https://ducklake.select/manifesto/) — warum Metadaten in eine SQL-Datenbank gehören statt in Dateien. Version 1.0 seit April 2026.
* **Data Mesh:** Z. Dehghani, *Data Mesh: Delivering Data-Driven Value at Scale*, O'Reilly 2022. Zur Ernüchterung: Thoughtworks, [*The state of data mesh in 2026*](https://www.thoughtworks.com/insights/blog/data-strategy/the-state-of-data-mesh-in-2026-from-hype-to-hard-won-maturity).
* **Tabellenformate und Kataloge:** [*The State of Apache Iceberg Catalogs in June 2026*](https://dev.to/alexmercedcoder/the-state-of-apache-iceberg-catalogs-in-june-2026-265e).
* **BI-Frontends:** Gartner, *Magic Quadrant for Analytics and Business Intelligence Platforms*, veröffentlicht am 29. Juni 2026 — Microsoft, Salesforce (Tableau) und Qlik im Führungsfeld, SAP Analytics Cloud und Looker als Visionäre.
* **Semantische Schicht:** [Cube, *What Is Headless BI*](https://cube.dev/articles/what-is-headless-bi); dbt Semantic Layer (MetricFlow); zur Marktübersicht [Holistics, *Best Semantic Layers 2026*](https://www.holistics.io/blog/semantic-layers/).
* **Größenordnungen:** J. Tigani, *Big Data is Dead* (MotherDuck) — analytische Arbeitsmengen sind meist klein.

Marktanteils- und Reifegradzahlen auf den Folien stammen aus Anbieter- und Beraterberichten und sind dort als solche gekennzeichnet. Sie taugen als Größenordnung, nicht als belastbare Statistik.

---

## Aufbau des Fallstudien-Decks

| | Kapitel | Folien |
|---|---|---|
| 1 | Ein Lehrdatensatz wird entworfen, nicht gefunden | Anforderungen · Systemkontext · die drei Sorten eingebauter Muster |
| 2 | Vom operativen Modell zum Auswertungsmodell | 26 → 12 Tabellen · Denormalisierung · Galaxy-Schema · schiefe Dimensionen |
| 3 | Auswerten — und die Fallen, die dabei aufgehen | Fan Trap · Würfeloperationen als SQL · Lift gegen Konfidenz · Basiseffekt |
| 4 | Prüfen ist Handwerk, nicht Vertrauen | drei Rechenwege · Prüflauf · Prüfbefunde · Auslieferungskette |
