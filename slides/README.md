# Foliendeck

`bau_deck.py` erzeugt das Foliendeck **BurgerMetrics — Von der Kasse bis zum Bericht**: 20 Folien, die den Weg vom operativen Modell über das Auswertungsmodell bis zur geprüften Kennzahl nachzeichnen.

Das Deck fasst zusammen, was in [`../docs/`](../docs/) ausführlich steht, und ist als Begleitmaterial zur Fallstudie gedacht.

---

## Warum hier nur das Skript liegt

Das gebaute Deck (`.pptx`) und sein PDF-Render sind **absichtlich nicht versioniert**. Der Grund ist keine Nachlässigkeit, sondern die Schriftlizenz:

Eine PPTX bettet die verwendeten Schriften ein. In diesem Fall sind das rund **2,1 MB Schriftdaten**, darunter **GT Planar Light** und **GT Planar Medium** — die kommerziell lizenzierte Hausschrift — sowie mehrere Segoe-UI-Schnitte von Microsoft. Läge die Datei in diesem öffentlichen Repository, würden diese Schriften mitverbreitet.

Dasselbe gilt für die Master-Vorlage `template.pptx`. Sie bleibt außerhalb des Repositorys, genau wie im DABA-Kurseinheiten-Projekt die PPTX-Quelle.

Versioniert ist deshalb, was gefahrlos versioniert werden kann: der Bauweg und die Fachbegriffsliste.

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
python3 bau_deck.py                      # schreibt ../../BurgerMetrics_Fallstudie.pptx
python3 bau_deck.py -o /pfad/deck.pptx   # alternatives Ziel
```

Das Skript meldet am Ende, ob ein Baustein mehr Platz braucht, als ihm zugewiesen wurde. Solche Warnungen sind vor der Auslieferung abzuarbeiten — sie bedeuten überlaufenden Text.

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

`fachbegriffe.txt` in diesem Ordner fängt die Fachbezeichner des Projekts ab (`dim_`, `fact_`, Lift, Konfidenz, Orphan Dimension, Filialnamen). Ohne sie meldet die Rechtschreibprüfung rund 160 Fehlalarme.

### Render — und warum er nötig ist

Zahlen im XML sagen nichts über Kollision, Weißraum und Lesefluss. Erst der Render zeigt sie:

```bash
soffice --headless --convert-to pdf --outdir OUT DECK.pptx
```

Fünf Mängel dieses Decks waren ausschließlich im Render sichtbar, darunter ein abgeschnittener Untertitel auf dem Deckblatt und fehlende gestrichelte Rahmen im Schemadiagramm — Letztere hätten den zentralen Unterschied zwischen angebundenen und nicht angebundenen Dimensionen unsichtbar gemacht.

**Eine Eigenheit des Renders:** LibreOffice kann die eingebettete Hausschrift nicht lesen (`EOT out of spec: no blank loca table found`) und ersetzt sie. Titel erscheinen im PDF deshalb in einer fremden Schrift und brechen früher um als in PowerPoint. Ein Befund „läuft knapp über" gehört daher in PowerPoint nachgesehen, bevor Text gekürzt wird. Umgekehrt gilt: Was im Render passt, passt in PowerPoint erst recht.

---

## Aufbau des Decks

| | Kapitel | Folien |
|---|---|---|
| 1 | Ein Lehrdatensatz wird entworfen, nicht gefunden | Anforderungen · Systemkontext · die drei Sorten eingebauter Muster |
| 2 | Vom operativen Modell zum Auswertungsmodell | 26 → 12 Tabellen · Denormalisierung · Galaxy-Schema · schiefe Dimensionen |
| 3 | Auswerten — und die Fallen, die dabei aufgehen | Fan Trap · Würfeloperationen als SQL · Lift gegen Konfidenz · Basiseffekt |
| 4 | Prüfen ist Handwerk, nicht Vertrauen | drei Rechenwege · Prüflauf · Prüfbefunde · Auslieferungskette |

Jede Zahl im Deck stammt aus dem Datenbestand und ist über `dataset/verify_readme.py` nachprüfbar.

---

## Bekannter Stolperstein

Im Skill zeigt `spec_loader.SPECS_DIR` auf `<skill>/specs`, die Specs liegen aber unter `<skill>/assets/specs`. Alle Prüfskripte enden dadurch mit *„Spec 'bint' nicht gefunden"*. `bau_deck.py` umgeht das mit einem eigenen Loader; für die Prüfskripte hilft ein Symlink:

```bash
ln -s assets/specs "$THWS_SKILL/specs"
```
