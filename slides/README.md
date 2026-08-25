# Foliendecks

Zwei Bauskripte, zwei Decks:

| Skript | Deck | Zweck |
|---|---|---|
| `bau_datenmodell.py` | **BurgerMetrics — Datenmodell und Aufbau** (14 Folien) | Wie die drei Anwendungen — Shop, Warenwirtschaft, Auswertung — zusammenhängen und warum jede ein eigenes Datenmodell braucht. Diagrammgetragen. |
| `bau_deck.py` | **BurgerMetrics — Von der Kasse bis zum Bericht** (20 Folien) | Der Weg vom operativen Modell über das Auswertungsmodell bis zur geprüften Kennzahl, inklusive Auswertungsfallen und Prüfhandwerk. |

Beide fassen zusammen, was in [`../docs/`](../docs/) ausführlich steht.

---

## Warum hier nur die Skripte liegen

Die gebauten Decks (`.pptx`) und ihre PDF-Renders sind **absichtlich nicht versioniert**. Der Grund ist keine Nachlässigkeit, sondern die Schriftlizenz:

Eine PPTX bettet die verwendeten Schriften ein. In diesem Fall sind das rund **2,1 MB Schriftdaten**, darunter **GT Planar Light** und **GT Planar Medium** — die kommerziell lizenzierte Hausschrift — sowie mehrere Segoe-UI-Schnitte von Microsoft. Läge die Datei in diesem öffentlichen Repository, würden diese Schriften mitverbreitet.

Dasselbe gilt für die Master-Vorlage `template.pptx`. Sie bleibt außerhalb des Repositorys.

Versioniert ist deshalb, was gefahrlos versioniert werden kann: die Bauwege, die Diagrammquellen und die Fachbegriffsliste.

---

## Die Diagramme

Alle Diagramme des Datenmodell-Decks sind **Mermaid-Quelltext** in [`diagramme/`](diagramme/) — versioniert, diffbar, ohne Zeichenprogramm zu ändern:

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

### Rendern

```bash
npm i playwright
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" node render_mermaid.mjs
```

Das Skript schreibt zu jeder `.mmd` eine `.png` daneben und meldet deren Maße.

**Warum über einen Browser und nicht über einen SVG-Rasterer:** Mermaid setzt Beschriftungen in `<foreignObject>`, also HTML innerhalb von SVG. Das ist kein wohlgeformtes XML — `cairosvg` und verwandte Werkzeuge brechen daran mit *„mismatched tag"* ab. Die Option `flowchart.htmlLabels=false` greift in Mermaid 11 nicht mehr. Ein Browser rendert `foreignObject` nativ; deshalb Chrome, headless, mit `deviceScaleFactor: 3` für die Projektion.

### Was beim Layout zu beachten ist

Die Schriftgröße im Diagramm ist an das Seitenverhältnis gekoppelt. Mermaid setzt 15 px; auf der Folie kommt davon an:

> Schriftgrad in pt = 15 × (Bildbreite in pt ÷ Diagrammbreite in CSS-px)

Bei einer Inhaltsbreite von 903 pt und einer Inhaltshöhe von 322 pt heißt das: ein Diagramm darf höchstens rund **1130 × 400 CSS-px** groß sein, sonst fällt die Beschriftung unter 12 pt und ist im Hörsaal nicht mehr lesbar. Hohe, schmale Diagramme sind deshalb das eigentliche Problem — nicht breite.

Zwei Stolpersteine dabei:

* `direction LR` in einem Subgraph wird **ignoriert**, sobald der Subgraph selbst an einer Kante hängt. Ein `A ~~~ B` zwischen zwei Subgraphs kippt beide zurück auf TB.
* Ohne jede Kante ordnet dagre Subgraphs nebeneinander an und stapelt die Knoten darin. Wer Zeilen will, erzwingt sie mit unsichtbaren Kanten (`~~~`) zwischen den Knoten — so ist `04_wawi_bereiche.mmd` gebaut.

Die Farben stammen aus `assets/tokens.json` des Skills **thws-slides** und stehen als Theme-Block in `render_mermaid.mjs`: Grau als Normalfall, Blau nur als Akzent.

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

`fachbegriffe.txt` in diesem Ordner fängt die Fachbezeichner des Projekts ab (`dim_`, `fact_`, `raw`/`stg`/`mart`, Lift, Konfidenz, Orphan Dimension, Filialnamen). Ohne sie meldet die Rechtschreibprüfung rund 160 Fehlalarme.

Ein Restbefund bleibt und ist keiner: Die Füllwortliste des Prüfskripts enthält die Einzelwörter mehrteiliger Wendungen (`im`, `in`, `unter`, `vor`). Gewöhnliche Präpositionen zählen dadurch mit.

### Render — und warum er nötig ist

Zahlen im XML sagen nichts über Kollision, Weißraum und Lesefluss. Erst der Render zeigt sie:

```bash
soffice --headless --convert-to pdf --outdir OUT DECK.pptx
```

Keine Folie gilt als fertig, bevor sie gerendert angesehen wurde. Am Datenmodell-Deck waren drei Mängel ausschließlich so sichtbar: ein Erläuterungsband, das quer durch ein zu hoch geratenes Diagramm lief; ein Bereichsdiagramm, dessen Beschriftung auf 5,8 pt geschrumpft war; und ein Zylinder, dessen Text in Mermaid über die eigene Form hinauslief.

**Eine Eigenheit des Renders:** LibreOffice kann die eingebettete Hausschrift nicht lesen (`EOT out of spec: no blank loca table found`) und ersetzt sie. Titel erscheinen im PDF deshalb in einer fremden Schrift und brechen früher um als in PowerPoint. Ein Befund „läuft knapp über" gehört daher in PowerPoint nachgesehen, bevor Text gekürzt wird. Umgekehrt gilt: Was im Render passt, passt in PowerPoint erst recht.

---

## Aufbau des Datenmodell-Decks

| | Kapitel | Folien |
|---|---|---|
| 1 | Ein Geschäftsvorfall, drei Systeme | Systemkontext · das Sitzungsmodell des Shops |
| 2 | Das operative Modell der Warenwirtschaft | Verkaufspfad · 26 Tabellen in sieben Bereichen · was Normalisierung leistet und kostet |
| 3 | Das Auswertungsmodell | Denormalisierung · Granularität · Galaxy-Schema · die drei Modelle nebeneinander · raw/stg/mart |

## Aufbau des Fallstudien-Decks

| | Kapitel | Folien |
|---|---|---|
| 1 | Ein Lehrdatensatz wird entworfen, nicht gefunden | Anforderungen · Systemkontext · die drei Sorten eingebauter Muster |
| 2 | Vom operativen Modell zum Auswertungsmodell | 26 → 12 Tabellen · Denormalisierung · Galaxy-Schema · schiefe Dimensionen |
| 3 | Auswerten — und die Fallen, die dabei aufgehen | Fan Trap · Würfeloperationen als SQL · Lift gegen Konfidenz · Basiseffekt |
| 4 | Prüfen ist Handwerk, nicht Vertrauen | drei Rechenwege · Prüflauf · Prüfbefunde · Auslieferungskette |

Jede Zahl in beiden Decks stammt aus dem Datenbestand und ist über `dataset/verify_readme.py` nachprüfbar.
