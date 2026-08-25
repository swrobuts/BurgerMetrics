# Foliendecks

Zwei Bauskripte, zwei Decks:

| Skript | Deck | Zweck |
|---|---|---|
| `bau_datenmodell.py` | **BurgerMetrics — Datenmodell und Aufbau** (25 Folien) | Wie die drei Anwendungen — Shop, Warenwirtschaft, Auswertung — zusammenhängen, warum jede ein eigenes Datenmodell braucht, und wie sich der gewählte Weg zu den Alternativen verhält. Diagrammgetragen. |
| `bau_deck.py` | **BurgerMetrics — Von der Kasse bis zum Bericht** (20 Folien) | Der Weg vom operativen Modell über das Auswertungsmodell bis zur geprüften Kennzahl, inklusive Auswertungsfallen und Prüfhandwerk. |

Beide fassen zusammen, was in [`../docs/`](../docs/) ausführlich steht.

---

## Der rote Faden des Datenmodell-Decks

Das Deck folgt einer Frage: **Welche Frage stellt das System — und welches Modell beantwortet sie am günstigsten?** Günstig heißt dabei nicht nur schnell. Jede Modellentscheidung verschiebt Kosten zwischen drei Konten:

* **Schreibkosten** — was es kostet, einen Sachverhalt widerspruchsfrei zu halten. Steigt mit jeder Stelle, an der dasselbe Merkmal steht.
* **Lesekosten** — was eine Auswertung über den ganzen Bestand kostet. Steigt mit der Zahl der Verknüpfungen je Abfrage.
* **Betriebskosten** — was der Apparat kostet, der beides am Laufen hält. Steigt mit jeder zusätzlichen Komponente und Zuständigkeit.

Das operative Modell nimmt hohe Lesekosten in Kauf, um Schreibkosten zu sparen; das Auswertungsmodell dreht das um. Kapitel 4 zeigt Architekturen, die vor allem an der dritten Kostenart drehen.

| | Kapitel | Folien |
|---|---|---|
| 1 | Ein Geschäftsvorfall, drei Systeme | Systemkontext · das Sitzungsmodell des Shops |
| 2 | Das operative Modell: Konsistenz zuerst | Verkaufspfad · 26 Tabellen in sieben Bereichen · was Normalisierung leistet und kostet |
| 3 | Das Auswertungsmodell: Lesetempo zuerst | Denormalisierung · Granularität · Galaxy-Schema · die drei Modelle nebeneinander · raw/stg/mart |
| 4 | Ein Weg von vielen | fünf Entscheidungen · Galaxy gegen OBT und Data Vault · Warehouse und Lake · Lakehouse und der Stand 2026 · DuckLake · Data Mesh · Einordnung · Schwellen für einen Wechsel |

---

## Warum hier nur die Skripte liegen

Die gebauten Decks (`.pptx`) und ihre PDF-Renders sind **absichtlich nicht versioniert**. Der Grund ist keine Nachlässigkeit, sondern die Schriftlizenz:

Eine PPTX bettet die verwendeten Schriften ein. In diesem Fall sind das rund **2,1 MB Schriftdaten**, darunter **GT Planar Light** und **GT Planar Medium** — die kommerziell lizenzierte Hausschrift — sowie mehrere Segoe-UI-Schnitte von Microsoft. Läge die Datei in diesem öffentlichen Repository, würden diese Schriften mitverbreitet.

Dasselbe gilt für die Master-Vorlage `template.pptx`. Sie bleibt außerhalb des Repositorys.

Versioniert ist deshalb, was gefahrlos versioniert werden kann: die Bauwege, die Diagrammquellen und die Fachbegriffsliste.

---

## Die Diagramme

Alle Diagramme des Datenmodell-Decks sind **Mermaid-Quelltext** in [`diagramme/`](diagramme/) — versioniert, vergleichbar, ohne Zeichenprogramm zu ändern:

| Datei | Zeigt |
|---|---|
| `01_systemkontext.mmd` | Kunde → Shop/Kasse → Warenwirtschaft ⇢ Auswertung → Bericht |
| `02_shop_modell.mmd` | Das schmale Sitzungsmodell des Shops (ER) |
| `03_wawi_verkaufspfad.mmd` | Der Verkaufspfad der Warenwirtschaft (ER) |
| `04_wawi_bereiche.mmd` | 26 Tabellen in sieben Bereichen — welche in die Auswertung fließen |
| `05_denormalisierung.mmd` | Drei normalisierte Artikel-Tabellen → eine breite Dimensionstabelle |
| `06_granularitaet.mmd` | Bestellkopf gegen Bestellpositionen |
| `07_galaxy.mmd` | Das Galaxy-Schema mit zwei Faktentabellen |
| `08_kette.mmd` | Quellsystem → raw → stg → mart → Bericht |
| `09_modellierungswege.mmd` | Galaxy-Schema, One Big Table und Data Vault 2.0 nebeneinander |
| `10_lakehouse_schichten.mmd` | Warehouse, Lake und Lakehouse als drei Schichtfolgen |
| `11_ducklake_metadaten.mmd` | Metadaten als Dateien (Iceberg, Delta) gegen Metadaten in der Datenbank (DuckLake) |
| `12_mesh.mmd` | Zentrales Datenteam gegen Datenprodukte je Domäne |

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

Bei einer Inhaltsbreite von 903 pt und einer Inhaltshöhe von 322 pt heißt das: ein Diagramm darf höchstens rund **1130 × 400 CSS-px** groß sein, sonst fällt die Beschriftung unter 12 pt und ist im Hörsaal nicht mehr lesbar. Hohe, schmale Diagramme sind deshalb das eigentliche Problem — nicht breite. `bild()` in `bau_datenmodell.py` rechnet den Wert aus und warnt unterhalb von 10,5 pt.

Vier Eigenheiten, die jeweils einen Neubau gekostet haben:

* **`direction` im Subgraph wird ignoriert.** Weder `direction LR` noch `direction TB` greift zuverlässig. Was stattdessen gilt: Bei `flowchart LR` stapeln sich unverbundene Teilgraphen **untereinander** und die Knoten darin laufen waagerecht; bei `flowchart TB` stehen sie **nebeneinander** und die Knoten stapeln sich. So sind `04`, `10` und `12` gebaut.
* **Ohne Kanten ordnet dagre die Knoten beliebig.** Wer Zeilen will, erzwingt sie mit unsichtbaren Kanten (`~~~`) — siehe `04_wawi_bereiche.mmd` und `10_lakehouse_schichten.mmd`.
* **Teilgraphen erscheinen in umgekehrter Reihenfolge.** Wer den ersten Block oben haben will, notiert ihn zuletzt — siehe `09` und `11`.
* **ER-Diagramme brauchen eigene Abstände.** Ohne `%%{init: {"er": {...}}}%%` läuft `03_wawi_verkaufspfad` mit 637 × 482 CSS-px auf 10 pt Beschriftung hinaus; mit engeren `nodeSpacing`, `rankSpacing` und `minEntityHeight` sind es 388 × 308 und 14,4 pt.

Die Farben stammen aus `assets/tokens.json` des Skills **thws-slides**: Grau als Normalfall, Blau nur als Akzent.

---

## Voraussetzungen

```bash
pip install python-pptx
```

Dazu der Skill **thws-slides** mit `assets/template.pptx` und `scripts/bausteine.py`. Der Pfad wird über eine Umgebungsvariable gesetzt:

```bash
export THWS_SKILL="/Pfad/zu/skills/thws-slides"
```

Ohne die Variable sucht das Skript an der Standardstelle der lokalen Skill-Installation und bricht mit einer Wegbeschreibung ab, wenn es die Vorlage nicht findet.

---

## Bauen

```bash
python3 bau_datenmodell.py               # -> ../../BurgerMetrics_Datenmodell.pptx
python3 bau_deck.py                      # -> ../../BurgerMetrics_Fallstudie.pptx
python3 bau_datenmodell.py -o /pfad.pptx # alternatives Ziel
```

Beide Skripte melden am Ende, ob ein Baustein mehr Platz braucht, als ihm zugewiesen wurde. Solche Warnungen sind vor der Auslieferung abzuarbeiten — sie bedeuten überlaufenden Text.

---

## Prüfen

Die Werkzeuge des Skills laufen gegen das gebaute Deck:

```bash
cd "$THWS_SKILL/scripts"
python3 trennstrich_check.py   DECK.pptx
python3 einleitung_budget.py   DECK.pptx
python3 formsprache_audit.py   DECK.pptx
python3 sprache_check.py       DECK.pptx --whitelist .../fachbegriffe.txt
```

`fachbegriffe.txt` in diesem Ordner fängt die Fachbezeichner des Projekts ab (`dim_`, `fact_`, `raw`/`stg`/`mart`, Lift, Konfidenz, Iceberg, Lakehouse, Filialnamen). Ohne sie meldet die Rechtschreibprüfung rund 200 Fehlalarme.

Ein Restbefund bleibt und ist keiner: Die Füllwortliste des Prüfskripts enthält die Einzelwörter mehrteiliger Wendungen (`im`, `in`, `unter`, `vor`). Gewöhnliche Präpositionen zählen dadurch mit.

Der **Formsprache-Audit** misst, wie viele verschiedene Folienstrukturen ein Deck verwendet (Ziel: mindestens 0,62 verschiedene je Folie). Ein diagrammgetragenes Deck läuft leicht darunter, weil sich „Einleitung + ein Bild + eine Kachel" von selbst wiederholt. Zwei Folien auf andere Bausteine umzustellen — hier eine Sprechblase statt einer Kachel und zwei Klammern statt eines Bandes — hat gereicht.

### Render — und warum er nötig ist

Zahlen im XML sagen nichts über Kollision, Weißraum und Lesefluss. Erst der Render zeigt sie:

```bash
soffice --headless --convert-to pdf --outdir OUT DECK.pptx
```

Keine Folie gilt als fertig, bevor sie gerendert angesehen wurde. Am Datenmodell-Deck waren fünf Mängel ausschließlich so sichtbar: ein Erläuterungsband, das quer durch ein zu hoch geratenes Diagramm lief; ein Bereichsdiagramm, dessen Beschriftung auf 5,8 pt geschrumpft war; ein Zylinder, dessen Text in Mermaid über die eigene Form hinauslief; zwei Vergleichsdiagramme in umgekehrter Reihenfolge; und eine Bewertungsmatrix, deren Kreise falsche Werte zeigten.

Der letzte Punkt ist der lehrreichste: `bausteine.harvey()` zeichnet teilgefüllte Kreise als PowerPoint-`PIE`-Form. **LibreOffice verwirft deren Winkelangaben** — halbvolle Kreise kamen als leere oder volle heraus, eine Zeile mit den Werten 0,25/0,10/0,10/0,10 sah aus wie eine mit lauter Höchstwerten. Die Matrix arbeitet deshalb mit Rechtecken, die jedes Programm gleich darstellt.

**Eine weitere Eigenheit des Renders:** LibreOffice kann die eingebettete Hausschrift nicht lesen (`EOT out of spec: no blank loca table found`) und ersetzt sie. Titel erscheinen im PDF deshalb in einer fremden Schrift und brechen früher um als in PowerPoint. Ein Befund „läuft knapp über" gehört daher in PowerPoint nachgesehen, bevor Text gekürzt wird. Umgekehrt gilt: Was im Render passt, passt in PowerPoint erst recht.

---

## Zahlen im Deck

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
| Zeitraum | 15.03.2017 – 31.03.2026 |

Die fachlichen Zahlen sind über `../dataset/verify_readme.py` nachprüfbar.

---

## Quellen für Kapitel 4

Die Architekturfolien geben den Stand 2026 wieder. Wer nachschlagen will:

* **Lakehouse, Begriffsprägung:** M. Armbrust, A. Ghodsi, R. Xin, M. Zaharia: *Lakehouse: A New Generation of Open Platforms that Unify Data Warehousing and Advanced Analytics*, CIDR 2021 — [PDF](https://people.eecs.berkeley.edu/~matei/papers/2021/cidr_lakehouse.pdf)
* **DuckLake:** [ducklake.select](https://ducklake.select/) und das [Manifest](https://ducklake.select/manifesto/) — die Begründung, warum Metadaten in eine SQL-Datenbank gehören statt in Dateien. Version 1.0 seit April 2026.
* **Data Mesh:** Z. Dehghani, *Data Mesh: Delivering Data-Driven Value at Scale*, O'Reilly 2022. Zur Ernüchterung: Thoughtworks, [*The state of data mesh in 2026*](https://www.thoughtworks.com/insights/blog/data-strategy/the-state-of-data-mesh-in-2026-from-hype-to-hard-won-maturity).
* **Tabellenformate und Kataloge:** [*The State of Apache Iceberg Catalogs in June 2026*](https://dev.to/alexmercedcoder/the-state-of-apache-iceberg-catalogs-in-june-2026-265e) — Polaris, Glue, Nessie, Unity, Lakekeeper im Vergleich.
* **Größenordnungen:** J. Tigani, *Big Data is Dead* (MotherDuck) — die Beobachtung, dass analytische Arbeitsmengen meist klein sind.

Die Marktanteils- und Reifegradzahlen auf den Folien stammen aus Anbieter- und Beraterberichten und sind auf den Folien als solche gekennzeichnet. Sie taugen als Größenordnung, nicht als belastbare Statistik.

---

## Aufbau des Fallstudien-Decks

| | Kapitel | Folien |
|---|---|---|
| 1 | Ein Lehrdatensatz wird entworfen, nicht gefunden | Anforderungen · Systemkontext · die drei Sorten eingebauter Muster |
| 2 | Vom operativen Modell zum Auswertungsmodell | 26 → 12 Tabellen · Denormalisierung · Galaxy-Schema · schiefe Dimensionen |
| 3 | Auswerten — und die Fallen, die dabei aufgehen | Fan Trap · Würfeloperationen als SQL · Lift gegen Konfidenz · Basiseffekt |
| 4 | Prüfen ist Handwerk, nicht Vertrauen | drei Rechenwege · Prüflauf · Prüfbefunde · Auslieferungskette |
