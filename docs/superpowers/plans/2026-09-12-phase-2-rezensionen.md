# Phase 2 — Rezensionen: Datenbank, Generator, Glättung — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 10.000 deutsche Rezensionen zu echten Bestellpositionen erzeugen, sprachlich glätten, als CSV versionieren, in beide Schemata der lebenden Datenbank laden und einen Schreibweg für den Shop bereitstellen — am Ende ist der Stand produktiv, ohne dass Robert etwas ausführt.

**Architecture:** CSV bleibt Quelle der Wahrheit: `generate_reviews.py` (DuckDB + numpy, fester Seed) schreibt `fact_reviews_roh.csv`; die Glättung in Claude Code schreibt daraus `fact_reviews.csv`. `lade_csv.py --nur fact_reviews` lädt sie nach `burgermetrics.fact_reviews`; `0021_rezensionen.sql` legt `wawi.rezension` an, kopiert den Simulationsbestand einmalig dorthin (Muster `0017`), stellt Sichten, die Schreibfunktion `rezension_anlegen()` für `anon`, den erweiterten ETL-Schritt und die Rechte bereit. Mini-Skripte, Prüfstand und Dokumentation ziehen nach.

**Tech Stack:** PostgreSQL 17.6 (selbstgehostete Supabase, Betreiberkonto aus `.env`), psycopg2, DuckDB 1.4, pandas 3, numpy 2, pytest 9; PostgREST für den späteren Shop-Weg; `ssh vps` für den Neustart des REST-Containers.

**Spec:** `docs/superpowers/specs/2026-09-12-bm-analyse-lernumgebung-design.md` — Abschnitte 3 (Datenbank), 4 (Generator und Glättung), 11 (Abnahme), 12 (Reihenfolge), 13 (Risiken).

## Global Constraints

- Arbeitsverzeichnis ist das Repo `BurgerMetrics_Website` (`Vorlesungen/Datenbasierte Fallstudien/BurgerMetrics/BurgerMetrics_Website`), Branch `bm-analyse`, am Ende ein PR auf `main`.
- Deutsch in allen Texten mit echten Umlauten (ü/ö/ä/ß); Bezeichner in Code und SQL bleiben ASCII. Sachlicher Ton, keine Bilder, keine Pointen, kein Emoji — auch nicht in den Rezensionstexten.
- Code für Anfänger: kurze Funktionen mit deutschen Namen, ein kurzer Kommentar je Funktion, keine verketteten Einzeiler.
- CSV-Dateien sind UTF-8 mit BOM (`utf-8-sig`), Zeilenende `\n`, liegen in Git LFS (`*.csv` in `.gitattributes`). Texte ohne Zeilenumbruch.
- `0021` läuft **als `postgres`** (Betreiberkonto aus `.env`), ist idempotent (zweimal fehlerfrei), setzt Rechte ausdrücklich (`GRANT SELECT` an `studi_daba`, `anon`, `authenticated`; RLS mit Policy `lesen_alle` auf beiden Tabellen).
- Sterneverteilung Ziel 5★ 38 %, 4★ 27 %, 3★ 13 %, 2★ 9 %, 1★ 13 % (Toleranz ±3 Punkte); Sterne hängen an `satisfaction_score` und `order_duration_min` der Bestellung.
- Rezensionstexte 5–500 Zeichen, 1–4 Sätze, rund 15 % umgangssprachlich (Kleinschreibung, ae/oe/ue, mehrfache Satzzeichen); keine echten Personen, keine Beleidigungen, keine Markennamen außer den Produktnamen.
- Rezensionsdatum = Bestelldatum + 0–3 Tage, höchstens `2026-03-31`; Uhrzeit 07:00–23:59 (die Rückrechnung aus `timestamptz` muss exakt sein — keine Zeiten in der Sommerzeitlücke).
- Produktionsbereite Übergabe: jede Änderung wird auf der lebenden Instanz eingespielt und am lebenden System nachgewiesen.
- Öffentlicher Schreibweg: Längen- und Ratenbegrenzung in der Datenbank, Besuchertexte werden nirgends öffentlich gerendert (das betrifft Phase 3, die Sichten hier bereiten es vor).

---

## Dateiplan

| Datei | Verantwortung |
|---|---|
| `db/skript_ausfuehren.py` (neu) | eine SQL-Datei als `postgres` in einer Transaktion ausführen, NOTICE-Zeilen zeigen |
| `db/lade_csv.py` (ändern) | Option `--nur TABELLE …`; `fact_reviews` in der Ladereihenfolge |
| `db/aufbau/0021_rezensionen.sql` (neu) | Tabellen, Bestandskopie, Sichten, Schreibfunktion, ETL-Erweiterung, Rechte, Probe |
| `dataset/rezension_bausteine.json` (neu) | die deutschen Satzbausteine |
| `dataset/generate_reviews.py` (neu) | deterministischer Generator → `fact_reviews_roh.csv` |
| `dataset/glaettung/lose_schreiben.py`, `zusammenfuehren.py`, `stichprobe.py`, `PROMPT.md` (neu) | Glättung in Losen, Zusammenführung mit Prüfung, Stichprobe |
| `dataset/fact_reviews_roh.csv`, `dataset/fact_reviews.csv` (neu, LFS) | Rohstand und geglätteter Bestand |
| `dataset/tests/test_bausteine.py`, `test_generate_reviews.py`, `test_glaettung.py`, `test_mini.py` (neu) | pytest |
| `dataset/burgermetrics_mini.sql`, `wawi_mini.sql`, `wawi_zu_analytisch.sql` (ändern) | je zwölf Rezensionen, Abbildung `rezension → fact_reviews` |
| `dataset/load_duckdb.py`, `dataset/verify_readme.py`, `dataset/README.md`, `db/README.md` (ändern) | Laden, Prüfstand, Dokumentation |
| `.gitignore` (ändern) | `dataset/glaettung/lose/` |

Reihenfolge: Task 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12. Task 3–7 (Daten) und Task 8 (SQL) sind unabhängig voneinander und können parallel laufen; Task 9 braucht beide.

---

### Task 0: Branch anlegen

**Files:** keine

- [ ] **Step 1: Branch von `main` abzweigen**

```bash
cd "/Users/robert/Library/CloudStorage/OneDrive-Persönlich/Vorlesungen/Datenbasierte Fallstudien/BurgerMetrics/BurgerMetrics_Website"
git status --short          # muss leer sein
git checkout -b bm-analyse
git branch --show-current   # bm-analyse
```

- [ ] **Step 2: LFS prüfen**

```bash
git lfs ls-files | head -3      # zeigt die vorhandenen CSV-Dateien als LFS-Objekte
ls -la dataset/fact_orders.csv  # 53 MB, keine 133-Byte-Zeigerdatei
```

---

### Task 1: `db/skript_ausfuehren.py` — Aufbauskripte als postgres fahren

**Files:**
- Create: `db/skript_ausfuehren.py`

**Interfaces:**
- Produces: `python3 db/skript_ausfuehren.py <sql-datei>` — Exit 0 und Ausgabe der NOTICE-Zeilen; bei Fehler Exit 1, Transaktion zurückgerollt.

- [ ] **Step 1: Skript schreiben**

```python
#!/usr/bin/env python3
"""skript_ausfuehren.py — führt eine SQL-Datei aus db/aufbau/ als postgres aus.

Eine Transaktion: Läuft die Datei fehlerfrei, wird sie bestätigt, sonst wird
alles zurückgerollt. Die NOTICE-Meldungen der Skripte (RAISE NOTICE) erscheinen
auf der Konsole — sie sind die Rückmeldung der Aufbauskripte.

    python3 db/skript_ausfuehren.py db/aufbau/0021_rezensionen.sql

Verbindung aus der nicht versionierten .env im Projektstamm (PGHOST, PGPORT,
PGDATABASE, PGUSER, PGPASSWORD), wie bei lade_csv.py und materialisieren.py.
"""
import os
import sys
from pathlib import Path

import psycopg2


def lade_env():
    """Liest .env im Projektstamm, ohne die Shell zu bemühen."""
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for zeile in env.read_text().splitlines():
            zeile = zeile.strip()
            if zeile and not zeile.startswith("#") and "=" in zeile:
                k, _, v = zeile.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def verbinde():
    """Öffnet die Verbindung mit dem Betreiberkonto aus der .env."""
    lade_env()
    return psycopg2.connect(
        host=os.environ["PGHOST"], port=os.environ["PGPORT"],
        dbname=os.environ["PGDATABASE"], user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"], connect_timeout=30)


def skript_ausfuehren(pfad):
    """Führt die Datei in einer Transaktion aus und gibt die NOTICE-Zeilen zurück."""
    sql = Path(pfad).read_text(encoding="utf-8")
    con = verbinde()
    try:
        with con.cursor() as cur:
            cur.execute(sql)
        con.commit()
        return [m.strip() for m in con.notices]
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def main():
    """Kommandozeile: genau eine Datei, Meldungen ausgeben, Ergebnis nennen."""
    if len(sys.argv) != 2:
        sys.exit("Aufruf: python3 db/skript_ausfuehren.py <sql-datei>")
    pfad = Path(sys.argv[1])
    if not pfad.exists():
        sys.exit(f"FEHLER: {pfad} gibt es nicht")
    print(f"Führe {pfad.name} als {os.environ.get('PGUSER', '?')} aus ...")
    try:
        for zeile in skript_ausfuehren(pfad):
            print("  " + zeile)
    except psycopg2.Error as fehler:
        sys.exit(f"Zurückgerollt: {fehler.pgerror or fehler}")
    print("Bestätigt.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Erfolgsfall prüfen**

```bash
cat > /tmp/probe_ok.sql <<'EOF'
DO $$ BEGIN RAISE NOTICE 'Probe %: Verbindung steht', 1; END $$;
EOF
python3 db/skript_ausfuehren.py /tmp/probe_ok.sql
```
Expected: `Führe probe_ok.sql als postgres aus ...`, dann `  NOTICE:  Probe 1: Verbindung steht`, dann `Bestätigt.`; Exit 0.

- [ ] **Step 3: Rollback prüfen**

```bash
cat > /tmp/probe_fehler.sql <<'EOF'
CREATE TABLE burgermetrics.zz_probe(i int);
SELECT 1/0;
EOF
python3 db/skript_ausfuehren.py /tmp/probe_fehler.sql; echo "Exit $?"
python3 - <<'EOF'
import sys; sys.path.insert(0, "db")
from skript_ausfuehren import verbinde
cur = verbinde().cursor(); cur.execute("SELECT to_regclass('burgermetrics.zz_probe')"); print("zz_probe:", cur.fetchone()[0])
EOF
```
Expected: `Zurückgerollt: ... division by zero`, `Exit 1`, `zz_probe: None` (die Tabelle wurde nicht angelegt).

- [ ] **Step 4: Commit**

```bash
git add db/skript_ausfuehren.py
git commit -m "db: skript_ausfuehren.py — Aufbauskripte als postgres in einer Transaktion fahren"
```

---

### Task 2: `lade_csv.py` — nur einzelne Tabellen laden

**Files:**
- Modify: `db/lade_csv.py`

**Interfaces:**
- Produces: `python3 db/lade_csv.py --nur fact_reviews` leert und lädt nur diese Tabelle; ohne `--nur` unverändertes Verhalten (alle zwölf plus `fact_reviews`).

- [ ] **Step 1: Kopf, Argumente und Reihenfolge ändern**

Den Modul-Docstring um die Zeile `python3 db/lade_csv.py --nur fact_reviews     # nur eine Tabelle leeren und laden` ergänzen; die Importzeile `import os, sys, time` wird zu `import argparse, os, sys, time`. Den Block ab `BASIS = ...` bis vor `con = psycopg2.connect(` durch diesen ersetzen:

```python
REIHENFOLGE = ["dim_branch", "dim_customer", "dim_date", "dim_payment_method",
               "dim_product", "dim_promotion", "dim_supplier", "dim_time_slot",
               "dim_weather", "dim_employee", "fact_orders", "fact_order_items",
               "fact_reviews"]


def argumente():
    """Liest Verzeichnis und optionale Tabellenauswahl von der Kommandozeile."""
    ap = argparse.ArgumentParser(description="dataset/*.csv per COPY in das Schema burgermetrics laden")
    ap.add_argument("verzeichnis", nargs="?", default=None,
                    help="Ordner mit den CSV-Dateien (Standard: dataset/)")
    ap.add_argument("--nur", nargs="+", metavar="TABELLE",
                    help="nur diese Tabellen leeren und neu laden")
    return ap.parse_args()


ARGS = argumente()
BASIS = Path(ARGS.verzeichnis) if ARGS.verzeichnis else Path(__file__).resolve().parent.parent / "dataset"
unbekannt = [t for t in (ARGS.nur or []) if t not in REIHENFOLGE]
if unbekannt:
    sys.exit(f"FEHLER: unbekannte Tabelle(n): {', '.join(unbekannt)} — erlaubt: {', '.join(REIHENFOLGE)}")
TABELLEN = [t for t in REIHENFOLGE if not ARGS.nur or t in ARGS.nur]
```

Die beiden Schleifen darunter laufen über `TABELLEN` statt `REIHENFOLGE`:

```python
for t in reversed(TABELLEN):
    cur.execute(f"TRUNCATE TABLE {t} CASCADE")

for t in TABELLEN:
```

- [ ] **Step 2: Argumentprüfung ohne Datenbank testen**

```bash
python3 db/lade_csv.py --nur gibt_es_nicht; echo "Exit $?"
python3 db/lade_csv.py --help | head -5
```
Expected: `FEHLER: unbekannte Tabelle(n): gibt_es_nicht — erlaubt: dim_branch, …, fact_reviews`, `Exit 1`; die Hilfe nennt `--nur`. (Der Ladelauf selbst folgt in Task 9, wenn die Tabelle existiert.)

- [ ] **Step 3: Commit**

```bash
git add db/lade_csv.py
git commit -m "db: lade_csv.py --nur TABELLE — einzelne Tabellen leeren und laden; fact_reviews in der Reihenfolge"
```

---

### Task 3: `dataset/rezension_bausteine.json` — die Satzbausteine

**Files:**
- Create: `dataset/rezension_bausteine.json`
- Test: `dataset/tests/test_bausteine.py`

**Interfaces:**
- Produces: JSON mit genau diesem Aufbau (der Generator in Task 4 liest ihn so):

```jsonc
{
  "einstieg": { "1": ["…"], "2": ["…"], "3": ["…"], "4": ["…"], "5": ["…"] },            // je Sternestufe ≥ 25 Sätze
  "produkt": {                                                                          // je Kategorie und Polarität ≥ 20 Sätze, jeder mit {produkt}
    "Burger":    { "negativ": ["…"], "neutral": ["…"], "positiv": ["…"] },
    "Side":      { … }, "Drink": { … }, "Dessert": { … }, "Breakfast": { … }
  },
  "kontext": {
    "wartezeit": { "kurz": ["…"], "mittel": ["…"], "lang": { "negativ": ["…"], "positiv": ["…"] } },  // je Liste ≥ 12
    "kanal":     { "Counter": ["…"], "Drive-Through": ["…"], "Kiosk": ["…"], "App Order": ["…"] },   // je ≥ 8, neutral beschreibend
    "filiale":   ["…"],                                                                              // ≥ 10, jeder mit {filiale}
    "preis":     { "mit_aktion": ["…"], "negativ": ["…"], "neutral": ["…"], "positiv": ["…"] }       // je ≥ 8
  },
  "schluss": { "1": ["…"], "2": ["…"], "3": ["…"], "4": ["…"], "5": ["…"] }              // je ≥ 15
}
```

Polarität: Sterne 1–2 = negativ, 3 = neutral, 4–5 = positiv. `{produkt}` wird durch den englischen Produktnamen ersetzt (z. B. „Bacon King"), `{filiale}` durch den Filialnamen (z. B. „BM Sanderring").

- [ ] **Step 1: Test schreiben**

```python
# dataset/tests/test_bausteine.py
import json
import re
from pathlib import Path

import pytest

BASIS = Path(__file__).resolve().parent.parent
EMOJI = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")


@pytest.fixture(scope="module")
def bausteine():
    return json.loads((BASIS / "rezension_bausteine.json").read_text(encoding="utf-8"))


def alle_saetze(knoten):
    """Sammelt jede Zeichenkette aus dem verschachtelten JSON ein."""
    if isinstance(knoten, str):
        return [knoten]
    if isinstance(knoten, list):
        return [s for k in knoten for s in alle_saetze(k)]
    return [s for k in knoten.values() for s in alle_saetze(k)]


def test_mindestzahlen(bausteine):
    for stufe in "12345":
        assert len(bausteine["einstieg"][stufe]) >= 25
        assert len(bausteine["schluss"][stufe]) >= 15
    for kategorie in ["Burger", "Side", "Drink", "Dessert", "Breakfast"]:
        for polaritaet in ["negativ", "neutral", "positiv"]:
            assert len(bausteine["produkt"][kategorie][polaritaet]) >= 20, (kategorie, polaritaet)
    w = bausteine["kontext"]["wartezeit"]
    assert len(w["kurz"]) >= 12 and len(w["mittel"]) >= 12
    assert len(w["lang"]["negativ"]) >= 12 and len(w["lang"]["positiv"]) >= 12
    for kanal in ["Counter", "Drive-Through", "Kiosk", "App Order"]:
        assert len(bausteine["kontext"]["kanal"][kanal]) >= 8
    assert len(bausteine["kontext"]["filiale"]) >= 10
    for schluessel in ["mit_aktion", "negativ", "neutral", "positiv"]:
        assert len(bausteine["kontext"]["preis"][schluessel]) >= 8


def test_platzhalter(bausteine):
    for kategorie, polaritaeten in bausteine["produkt"].items():
        for saetze in polaritaeten.values():
            assert all("{produkt}" in s for s in saetze), kategorie
    assert all("{filiale}" in s for s in bausteine["kontext"]["filiale"])


def test_form(bausteine):
    for satz in alle_saetze(bausteine):
        assert "\n" not in satz
        assert not EMOJI.search(satz), satz
        assert satz.strip() == satz
        assert satz[-1] in ".!?", satz
        assert 8 <= len(satz) <= 160, satz


def test_keine_doppelten(bausteine):
    saetze = alle_saetze(bausteine)
    assert len(saetze) == len(set(saetze))
```

- [ ] **Step 2: Test laufen lassen — er muss scheitern**

Run: `python3 -m pytest dataset/tests/test_bausteine.py -q`
Expected: FAIL mit `FileNotFoundError` (die JSON-Datei fehlt).

- [ ] **Step 3: Bausteine schreiben**

`dataset/rezension_bausteine.json` mit dem Aufbau aus den Interfaces anlegen. Stil: Alltagsdeutsch von Gästen eines Schnellrestaurants, sachlich bis verärgert, ohne Beleidigungen, ohne Emoji, ohne Namen realer Personen. Jede Liste erfüllt die Mindestzahl aus dem Test. Beispiele, an denen sich die übrigen Sätze orientieren:

```json
{
  "einstieg": {
    "1": ["Das war leider ein Reinfall.", "Ich bin selten so enttäuscht aus einem Restaurant gegangen.", "Von diesem Besuch bleibt nur Ärger."],
    "2": ["Das war unter dem, was ich erwartet hatte.", "Nicht gut, aber auch nicht katastrophal.", "Es gab mehr Minuspunkte als Pluspunkte."],
    "3": ["Ganz in Ordnung, mehr aber auch nicht.", "Durchschnittlich, weder gut noch schlecht.", "Es war okay für zwischendurch."],
    "4": ["Insgesamt ein guter Besuch.", "Hat mir gut gefallen, mit kleinen Abstrichen.", "Solide Leistung, ich war zufrieden."],
    "5": ["Rundum zufrieden, das passt.", "Besser geht es bei einer Burgerkette kaum.", "Ein sehr guter Besuch von Anfang bis Ende."]
  },
  "produkt": {
    "Burger": {
      "negativ": ["Der {produkt} war trocken und lauwarm.", "Beim {produkt} war das Brötchen matschig und das Fleisch zu wenig gewürzt.", "Der {produkt} sah anders aus als auf dem Bild und schmeckte fad."],
      "neutral": ["Der {produkt} war in Ordnung, aber nichts Besonderes.", "Am {produkt} gibt es nichts auszusetzen, er bleibt aber austauschbar."],
      "positiv": ["Der {produkt} war saftig, gut belegt und heiß.", "Beim {produkt} stimmt alles: Fleisch, Sauce, Brötchen.", "Der {produkt} ist für mich der beste Burger der Karte."]
    },
    "Side": {
      "negativ": ["Die {produkt} waren fettig und nicht mehr knusprig.", "Die Portion {produkt} war klein und kalt."],
      "neutral": ["Die {produkt} waren okay, nicht mehr.", "{produkt} wie überall, unauffällig."],
      "positiv": ["Die {produkt} waren knusprig und gut gesalzen.", "Die Portion {produkt} war reichlich und frisch."]
    },
    "Drink": {
      "negativ": ["Der {produkt} war lauwarm und schal.", "{produkt} viel zu süß und ohne Eis serviert."],
      "neutral": ["{produkt} war wie erwartet, nichts Besonderes.", "Der {produkt} war in Ordnung."],
      "positiv": ["Der {produkt} war kalt und erfrischend.", "{produkt} gut gekühlt, genau richtig zum Essen."]
    },
    "Dessert": {
      "negativ": ["Der {produkt} schmeckte nach Tiefkühltruhe.", "{produkt} war klebrig süß und nicht frisch."],
      "neutral": ["{produkt} war okay als Nachtisch.", "Der {produkt} war in Ordnung, nicht mehr."],
      "positiv": ["Der {produkt} war ein guter Abschluss, frisch und nicht zu süß.", "{produkt} hat gut geschmeckt, gern wieder."]
    },
    "Breakfast": {
      "negativ": ["Der {produkt} war kalt und die Eier gummiartig.", "{produkt} am Morgen war eine Enttäuschung, alles lieblos."],
      "neutral": ["{produkt} war ein normales Frühstück, nichts Besonderes.", "Der {produkt} war okay für einen schnellen Start."],
      "positiv": ["Der {produkt} war ein gutes Frühstück, warm und schnell.", "{produkt} frisch zubereitet, so soll es sein."]
    }
  },
  "kontext": {
    "wartezeit": {
      "kurz":   ["Die Bestellung war nach wenigen Minuten fertig.", "Es ging schnell, kaum Wartezeit."],
      "mittel": ["Die Wartezeit war normal für ein volles Lokal.", "Ein paar Minuten warten, das war in Ordnung."],
      "lang":   { "negativ": ["Über zehn Minuten Wartezeit sind für einen Imbiss zu viel.", "Die lange Wartezeit hat den Besuch verdorben."],
                  "positiv": ["Es hat zwar gedauert, aber das Essen hat es ausgeglichen.", "Trotz längerer Wartezeit ein guter Besuch."] }
    },
    "kanal": {
      "Counter": ["Bestellt haben wir an der Theke.", "Am Counter war die Bedienung freundlich."],
      "Drive-Through": ["Wir haben am Drive-Through bestellt.", "Abgeholt am Drive-Through, im Auto gegessen."],
      "Kiosk": ["Die Bestellung lief über das Kiosk-Terminal.", "Am Kiosk bestellt, das ging ohne Schlange."],
      "App Order": ["Vorbestellt über die App und abgeholt.", "Bestellung per App, Abholung am Schalter."]
    },
    "filiale": ["Das war in der Filiale {filiale}.", "Besucht haben wir {filiale}.", "Filiale {filiale}, am Abend gut besucht."],
    "preis": {
      "mit_aktion": ["Mit der Aktion war der Preis fair.", "Dank Rabatt hat sich das gelohnt."],
      "negativ": ["Für den Preis hätte ich mehr erwartet.", "Zu teuer für das, was auf dem Tablett lag."],
      "neutral": ["Der Preis war üblich für eine Kette.", "Preislich im normalen Rahmen."],
      "positiv": ["Der Preis war für die Portion in Ordnung.", "Gutes Preis-Leistungs-Verhältnis."]
    }
  },
  "schluss": {
    "1": ["Ich komme nicht wieder.", "Keine Empfehlung von mir."],
    "2": ["Beim nächsten Mal probiere ich etwas anderes.", "Es gibt bessere Alternativen in der Nähe."],
    "3": ["Kann man machen, muss man aber nicht.", "Vielleicht gebe ich noch eine zweite Chance."],
    "4": ["Gern wieder.", "Empfehlung mit kleinen Abstrichen."],
    "5": ["Klare Empfehlung.", "Wir kommen bestimmt wieder."]
  }
}
```

Die vollständige Datei enthält je Liste die Mindestzahl unterschiedlicher Sätze; Produktsätze variieren Zubereitung, Temperatur, Frische, Portion, Würze und Aussehen. Mengenangaben bleiben allgemein („über zehn Minuten"), damit sie zu jeder Bestellung passen.

- [ ] **Step 4: Test laufen lassen — er muss bestehen**

Run: `python3 -m pytest dataset/tests/test_bausteine.py -q`
Expected: `4 passed`.

- [ ] **Step 5: Commit**

```bash
git add dataset/rezension_bausteine.json dataset/tests/test_bausteine.py
git commit -m "dataset: Satzbausteine für die Rezensionen, mit Prüfung von Umfang und Form"
```

---

### Task 4: `dataset/generate_reviews.py` — der Generator

**Files:**
- Create: `dataset/generate_reviews.py`
- Test: `dataset/tests/test_generate_reviews.py`

**Interfaces:**
- Consumes: `dataset/rezension_bausteine.json` (Task 3), CSV-Dateien `fact_orders.csv`, `fact_order_items.csv`, `dim_product.csv`, `dim_customer.csv`, `dim_branch.csv`, `dim_date.csv`.
- Produces: Funktionen `lade_kandidaten(basis: Path) -> pandas.DataFrame`, `erzeuge_rezensionen(kandidaten, bausteine, anzahl: int, seed: int) -> pandas.DataFrame` mit Spalten `review_id, date, time, customer_id, product_id, branch_id, order_id, stars, review_text, source`; Kommandozeile `python3 dataset/generate_reviews.py [--anzahl N] [--seed S] [--ausgabe PFAD]`, Standard 10.000 / 2026 / `dataset/fact_reviews_roh.csv`.

- [ ] **Step 1: Tests schreiben**

```python
# dataset/tests/test_generate_reviews.py
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

BASIS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASIS))
import generate_reviews as g  # noqa: E402


@pytest.fixture(scope="module")
def kandidaten():
    return g.lade_kandidaten(BASIS)


@pytest.fixture(scope="module")
def bausteine():
    return json.loads((BASIS / "rezension_bausteine.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def probe(kandidaten, bausteine):
    return g.erzeuge_rezensionen(kandidaten, bausteine, anzahl=3000, seed=2026)


def test_kandidaten_sind_bewertete_bestellungen_ohne_extras(kandidaten):
    assert kandidaten.satisfaction_score.notna().all()
    assert (kandidaten.category != "Extra").all()
    assert len(kandidaten) > 500_000


def test_spalten_und_umfang(probe):
    assert list(probe.columns) == ["review_id", "date", "time", "customer_id", "product_id",
                                   "branch_id", "order_id", "stars", "review_text", "source"]
    assert len(probe) == 3000
    assert list(probe.review_id) == list(range(1, 3001))
    assert probe.order_id.is_unique
    assert (probe.source == "simulation").all()


def test_regeln_je_zeile(probe, kandidaten):
    assert probe.stars.between(1, 5).all()
    laengen = probe.review_text.str.len()
    assert laengen.between(5, 500).all()
    assert not probe.review_text.str.contains("\n").any()
    assert (probe.date <= "2026-03-31").all()
    bestelldatum = probe.merge(kandidaten[["order_id", "date"]].drop_duplicates("order_id"),
                               on="order_id", suffixes=("", "_bestellung"))
    assert (pd.to_datetime(bestelldatum.date) >= pd.to_datetime(bestelldatum.date_bestellung)).all()
    stunden = probe.time.str[:2].astype(int)
    assert stunden.between(7, 23).all()
    assert probe.time.str.match(r"^\d{2}:\d{2}:\d{2}$").all()


def test_sterneverteilung(probe):
    anteile = probe.stars.value_counts(normalize=True) * 100
    for sterne, soll in [(5, 38), (4, 27), (3, 13), (2, 9), (1, 13)]:
        assert abs(anteile[sterne] - soll) <= 3, (sterne, anteile[sterne])


def test_sterne_haengen_an_zufriedenheit(probe, kandidaten):
    zusammen = probe.merge(kandidaten[["order_id", "satisfaction_score", "order_duration_min"]]
                           .drop_duplicates("order_id"), on="order_id")
    assert zusammen.stars.corr(zusammen.satisfaction_score) > 0.3
    assert zusammen.stars.corr(zusammen.order_duration_min) < -0.05


def test_deterministisch(kandidaten, bausteine):
    a = g.erzeuge_rezensionen(kandidaten, bausteine, anzahl=300, seed=7)
    b = g.erzeuge_rezensionen(kandidaten, bausteine, anzahl=300, seed=7)
    assert a.equals(b)


def test_umgangssprache_anteil(probe):
    klein = probe.review_text.str.match(r"^[a-z]").mean()
    assert 0.10 <= klein <= 0.20
```

- [ ] **Step 2: Tests laufen lassen — sie müssen scheitern**

Run: `python3 -m pytest dataset/tests/test_generate_reviews.py -q`
Expected: FAIL mit `ModuleNotFoundError: No module named 'generate_reviews'`.

- [ ] **Step 3: Generator schreiben**

```python
#!/usr/bin/env python3
"""
generate_reviews.py — erzeugt 10.000 Rezensionen zu echten Bestellpositionen.

Fachlicher Hintergrund
----------------------
Jede Rezension hängt an einer bewerteten Bestellung (satisfaction_score ist
gesetzt) und an einem Produkt daraus. Die Sterne folgen einer latenten Größe
aus Zufriedenheit und Bestelldauer der Bestellung, einem Produktniveau und
Rauschen. So findet die Sentiment-Analyse später einen Zusammenhang, den man
nachrechnen kann. Der Text entsteht aus Satzbausteinen je Sternestufe
(rezension_bausteine.json); rund 15 Prozent sind umgangssprachlich.

Verwendung
----------
    python3 generate_reviews.py                    # schreibt fact_reviews_roh.csv
    python3 generate_reviews.py --anzahl 500       # kleiner Probelauf
    python3 generate_reviews.py --ausgabe /pfad/x.csv

Zwei Läufe mit demselben Seed liefern byte-identische Dateien. Der geglättete
Bestand fact_reviews.csv entsteht danach in glaettung/ (siehe README).
"""
import argparse
import json
from datetime import date, timedelta
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

BASIS = Path(__file__).resolve().parent
ENCODING = "utf-8-sig"
LETZTER_TAG = date(2026, 3, 31)           # Ende von dim_date
ANTEIL_UMGANGSSPRACHE = 0.15
# Feste Abweichung je Produkt von der mittleren Bewertung (0 = Durchschnitt).
PRODUKTNIVEAU = {
    "Truffle Deluxe": 0.4, "Smashed Burger": 0.3, "BBQ Smokehouse": 0.25, "Crispy Chicken Deluxe": 0.2,
    "Beyond Burger": 0.15, "Craft Lemonade": 0.2, "Fresh OJ": 0.15, "Sweet Potato Fries": 0.15,
    "Fish Burger": -0.3, "Kids Burger": -0.2, "Water 0.5l": -0.1, "Coleslaw": -0.2,
    "Hash Browns": -0.15, "Donut": -0.1, "Scrambled Eggs & Toast": -0.2, "Onion Rings": -0.1,
}
# Kumulierte Anteile der Sterne 1 bis 4 — die Schwellen liegen auf diesen
# Quantilen der latenten Größe, dadurch stimmt die Verteilung exakt.
STERNE_QUANTILE = [0.13, 0.22, 0.35, 0.62]
# Uhrzeit der Rezension: Stunden 7 bis 23 mit Abendspitze.
STUNDEN = list(range(7, 24))
STUNDEN_GEWICHT = [1, 1, 2, 2, 3, 4, 4, 3, 3, 3, 4, 5, 6, 6, 5, 4, 3]


def lade_kandidaten(basis):
    """Liest bewertete Bestellpositionen ohne Extras samt Gewicht aus den CSV-Dateien."""
    con = duckdb.connect()
    pfad = lambda name: str((basis / f"{name}.csv").resolve()).replace("'", "''")
    return con.execute(f"""
        SELECT o.order_id, o.date, o.branch_id, o.customer_id, o.order_channel,
               o.order_duration_min, o.satisfaction_score, o.promo_id,
               i.product_id, p.product_name, p.category, c.has_app, b.branch_name,
               (extract(year FROM o.date) - 2016)
               * CASE o.order_channel WHEN 'App Order' THEN 3 WHEN 'Kiosk' THEN 1.5 ELSE 1 END
               * CASE WHEN c.has_app THEN 2 ELSE 1 END AS gewicht
        FROM read_csv_auto('{pfad("fact_orders")}', header = true) o
        JOIN read_csv_auto('{pfad("fact_order_items")}', header = true) i USING (order_id)
        JOIN read_csv_auto('{pfad("dim_product")}', header = true) p USING (product_id)
        JOIN read_csv_auto('{pfad("dim_customer")}', header = true) c USING (customer_id)
        JOIN read_csv_auto('{pfad("dim_branch")}', header = true) b USING (branch_id)
        WHERE o.satisfaction_score IS NOT NULL AND p.category <> 'Extra'
        ORDER BY o.order_id, i.order_item_id
    """).df()


def ziehe_stichprobe(kandidaten, anzahl, rng):
    """Wählt gewichtet Bestellungen aus und je Bestellung eine Position."""
    je_bestellung = kandidaten.groupby("order_id").gewicht.first()
    gewichte = je_bestellung.values / je_bestellung.values.sum()
    gewaehlt = rng.choice(je_bestellung.index.values, size=anzahl, replace=False, p=gewichte)
    positionen_je_bestellung = kandidaten.groupby("order_id").indices
    zeilen = [rng.choice(positionen_je_bestellung[order_id]) for order_id in gewaehlt]
    return kandidaten.iloc[zeilen].reset_index(drop=True)


def berechne_sterne(stichprobe, rng):
    """Latente Größe aus Zufriedenheit, Dauer, Produktniveau und Rauschen; Quantile setzen die Schwellen."""
    median_dauer = stichprobe.order_duration_min.median()
    niveau = stichprobe.product_name.map(PRODUKTNIVEAU).fillna(0.0)
    z = (1.2 * (stichprobe.satisfaction_score - 3.8)
         - 0.03 * (stichprobe.order_duration_min - median_dauer)
         + niveau + rng.normal(0, 0.6, len(stichprobe)))
    schwellen = np.quantile(z, STERNE_QUANTILE)
    return pd.Series(1 + np.searchsorted(schwellen, z, side="right"), index=stichprobe.index)


def polaritaet(sterne):
    """Sterne 1–2 negativ, 3 neutral, 4–5 positiv."""
    if sterne <= 2:
        return "negativ"
    if sterne == 3:
        return "neutral"
    return "positiv"


def wartezeit_klasse(minuten):
    """Bestelldauer in drei Klassen für die Kontextsätze."""
    if minuten <= 4:
        return "kurz"
    if minuten <= 9:
        return "mittel"
    return "lang"


def kontextsatz(zeile, sterne, bausteine, rng):
    """Ein Satz zu Wartezeit, Kanal, Filiale oder Preis — passend zur Bestellung."""
    art = rng.choice(["wartezeit", "kanal", "filiale", "preis"], p=[0.4, 0.25, 0.2, 0.15])
    k = bausteine["kontext"]
    if art == "wartezeit":
        klasse = wartezeit_klasse(zeile.order_duration_min)
        if klasse == "lang":
            return rng.choice(k["wartezeit"]["lang"]["positiv" if sterne >= 4 else "negativ"])
        return rng.choice(k["wartezeit"][klasse])
    if art == "kanal":
        return rng.choice(k["kanal"][zeile.order_channel])
    if art == "filiale":
        return rng.choice(k["filiale"]).replace("{filiale}", zeile.branch_name)
    if zeile.promo_id != 0:
        return rng.choice(k["preis"]["mit_aktion"])
    return rng.choice(k["preis"][polaritaet(sterne)])


def umgangssprachlich(text, rng):
    """Kleinschreibung, ae/oe/ue statt Umlaute, gelegentlich mehrfache Satzzeichen."""
    text = text.lower()
    for alt, neu in [("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")]:
        text = text.replace(alt, neu)
    if rng.random() < 0.5:
        text = text.rstrip(".") + rng.choice(["!!", "...", "!"])
    return text


def erzeuge_text(zeile, sterne, bausteine, rng):
    """Einstieg, Produktsatz, optional Kontext und Schluss — ein bis vier Sätze."""
    stufe = str(sterne)
    saetze = [rng.choice(bausteine["einstieg"][stufe])]
    produkt = rng.choice(bausteine["produkt"][zeile.category][polaritaet(sterne)])
    saetze.append(produkt.replace("{produkt}", zeile.product_name))
    if rng.random() < 0.55:
        saetze.append(kontextsatz(zeile, sterne, bausteine, rng))
    if sterne != 3 and rng.random() < 0.35:
        saetze.append(rng.choice(bausteine["schluss"][stufe]))
    text = " ".join(saetze)
    if len(text) > 500:
        text = " ".join(saetze[:2])       # Einstieg und Produktsatz reichen immer unter 500 Zeichen
    if rng.random() < ANTEIL_UMGANGSSPRACHE:
        text = umgangssprachlich(text, rng)
    return text


def erzeuge_zeitpunkt(bestelldatum, rng):
    """Datum 0–3 Tage nach der Bestellung (höchstens Ende des Kalenders), Uhrzeit mit Abendspitze."""
    tag = min(pd.Timestamp(bestelldatum).date() + timedelta(days=int(rng.integers(0, 4))), LETZTER_TAG)
    stunde = rng.choice(STUNDEN, p=np.array(STUNDEN_GEWICHT) / sum(STUNDEN_GEWICHT))
    return tag.isoformat(), f"{stunde:02d}:{int(rng.integers(0, 60)):02d}:{int(rng.integers(0, 60)):02d}"


def erzeuge_rezensionen(kandidaten, bausteine, anzahl=10_000, seed=2026):
    """Der ganze Lauf: Stichprobe, Sterne, Texte, Zeitpunkte, Nummerierung."""
    rng = np.random.default_rng(seed)
    stichprobe = ziehe_stichprobe(kandidaten, anzahl, rng)
    sterne = berechne_sterne(stichprobe, rng)
    zeilen = []
    for i, zeile in stichprobe.iterrows():
        datum, uhrzeit = erzeuge_zeitpunkt(zeile.date, rng)
        zeilen.append({
            "date": datum, "time": uhrzeit,
            "customer_id": int(zeile.customer_id), "product_id": int(zeile.product_id),
            "branch_id": int(zeile.branch_id), "order_id": int(zeile.order_id),
            "stars": int(sterne[i]), "review_text": erzeuge_text(zeile, int(sterne[i]), bausteine, rng),
            "source": "simulation"})
    ergebnis = pd.DataFrame(zeilen).sort_values(["date", "time", "order_id"]).reset_index(drop=True)
    ergebnis.insert(0, "review_id", range(1, len(ergebnis) + 1))
    return ergebnis


def main():
    """Kommandozeile: Kandidaten laden, erzeugen, schreiben, Verteilung nennen."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--anzahl", type=int, default=10_000)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--ausgabe", default=str(BASIS / "fact_reviews_roh.csv"))
    args = ap.parse_args()

    bausteine = json.loads((BASIS / "rezension_bausteine.json").read_text(encoding="utf-8"))
    print("Lade bewertete Bestellpositionen ...")
    kandidaten = lade_kandidaten(BASIS)
    print(f"  {len(kandidaten):,} Kandidaten".replace(",", "."))
    ergebnis = erzeuge_rezensionen(kandidaten, bausteine, args.anzahl, args.seed)
    ergebnis.to_csv(args.ausgabe, index=False, encoding=ENCODING, lineterminator="\n")
    anteile = (ergebnis.stars.value_counts(normalize=True).sort_index() * 100).round(1)
    print(f"Geschrieben: {args.ausgabe} ({len(ergebnis):,} Zeilen)".replace(",", "."))
    print("Sterne-Anteile in Prozent:", anteile.to_dict())


if __name__ == "__main__":
    main()
```

Hinweis zur Laufzeit: `lade_kandidaten` liest rund 140 MB CSV (DuckDB, wenige Sekunden); `ziehe_stichprobe` sucht je gewählter Bestellung ihre Positionen — für 10.000 Bestellungen einige Sekunden. Sollte `test_umgangssprache_anteil` knapp scheitern, liegt es an der Rundung der Stichprobe, nicht am Anteil: `ANTEIL_UMGANGSSPRACHE` bleibt 0,15.

- [ ] **Step 4: Tests laufen lassen — sie müssen bestehen**

Run: `python3 -m pytest dataset/tests/test_generate_reviews.py -q`
Expected: `7 passed` (Laufzeit rund eine Minute, weil die Kandidaten einmal geladen werden).

- [ ] **Step 5: Commit**

```bash
git add dataset/generate_reviews.py dataset/tests/test_generate_reviews.py
git commit -m "dataset: generate_reviews.py — 10.000 Rezensionen zu bewerteten Bestellungen, deterministisch"
```

---

### Task 5: Rohstand erzeugen und versionieren

**Files:**
- Create: `dataset/fact_reviews_roh.csv` (LFS)

- [ ] **Step 1: Zwei Läufe, gleicher Hash**

```bash
python3 dataset/generate_reviews.py --ausgabe /tmp/lauf1.csv
python3 dataset/generate_reviews.py --ausgabe /tmp/lauf2.csv
shasum -a 256 /tmp/lauf1.csv /tmp/lauf2.csv
```
Expected: beide Zeilen zeigen denselben Hash; die Ausgabe nennt `10.000 Zeilen` und Anteile nahe 13/9/13/27/38.

- [ ] **Step 2: Rohstand in das Repo schreiben und sichten**

```bash
python3 dataset/generate_reviews.py
python3 - <<'EOF'
import pandas as pd
r = pd.read_csv("dataset/fact_reviews_roh.csv", encoding="utf-8-sig")
print(len(r), r.review_id.is_unique, r.order_id.is_unique, r.review_text.str.len().describe()[["min","mean","max"]].round(1).to_dict())
print(r.sample(8, random_state=1)[["stars", "review_text"]].to_string())
EOF
```
Expected: `10000 True True {'min': ≥ 5, 'mean': ~90, 'max': ≤ 500}` und acht lesbare Texte, deren Ton zu den Sternen passt.

- [ ] **Step 3: Commit als LFS-Objekt**

```bash
git add dataset/fact_reviews_roh.csv
git lfs ls-files | grep fact_reviews_roh      # muss die Datei als LFS-Objekt zeigen
git commit -m "dataset: fact_reviews_roh.csv — Rohstand der 10.000 Rezensionen (Seed 2026)"
```

---

### Task 6: Werkzeuge für die Glättung

**Files:**
- Create: `dataset/glaettung/lose_schreiben.py`, `dataset/glaettung/zusammenfuehren.py`, `dataset/glaettung/stichprobe.py`, `dataset/glaettung/PROMPT.md`
- Modify: `.gitignore`
- Test: `dataset/tests/test_glaettung.py`

**Interfaces:**
- Consumes: `dataset/fact_reviews_roh.csv` (Task 5).
- Produces: `lose_schreiben.py` → `dataset/glaettung/lose/los_001.csv … los_100.csv` (Spalten `review_id, stars, review_text`, 100 Zeilen je Los); `zusammenfuehren.py` liest `lose/geglaettet_NNN.csv` (Spalten `review_id, review_text`) und schreibt `dataset/fact_reviews.csv`; Funktionen `pruefe_text(alt: str, neu: str) -> list[str]` (Befunde, leer = gut) und `zusammenfuehren(roh: DataFrame, geglaettet: DataFrame) -> tuple[DataFrame, list[str]]`.

- [ ] **Step 1: Tests schreiben**

```python
# dataset/tests/test_glaettung.py
import sys
from pathlib import Path

import pandas as pd

BASIS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASIS / "glaettung"))
import zusammenfuehren as z  # noqa: E402
import lose_schreiben as l  # noqa: E402


def roh_beispiel():
    return pd.DataFrame({
        "review_id": [1, 2, 3], "date": ["2025-01-01"] * 3, "time": ["12:00:00"] * 3,
        "customer_id": [5, 6, 7], "product_id": [1, 2, 3], "branch_id": [1, 1, 2], "order_id": [10, 11, 12],
        "stars": [5, 1, 3],
        "review_text": ["Rundum zufrieden, das passt. Der Classic Burger war saftig, gut belegt und heiß.",
                        "Das war leider ein Reinfall. Der Cheeseburger war trocken und lauwarm.",
                        "Ganz in Ordnung, mehr aber auch nicht. Die Small Fries waren okay, nicht mehr."],
        "source": ["simulation"] * 3})


def test_pruefe_text_gut():
    assert z.pruefe_text("Der Burger war gut und heiß.", "Der Burger kam heiß und schmeckte gut.") == []


def test_pruefe_text_befunde():
    alt = "Der Burger war gut und heiß."
    assert any("Zeilenumbruch" in b for b in z.pruefe_text(alt, "Der Burger\nwar gut."))
    assert any("zu lang" in b for b in z.pruefe_text(alt, alt + " " + "Und noch ein sehr langer Zusatz. " * 3))
    assert any("zu kurz" in b for b in z.pruefe_text(alt, "Gut."))
    assert any("leer" in b for b in z.pruefe_text(alt, "   "))


def test_zusammenfuehren_ersetzt_und_meldet():
    roh = roh_beispiel()
    geglaettet = pd.DataFrame({"review_id": [1, 2, 99],
                               "review_text": ["Rundum zufrieden. Der Classic Burger kam saftig, gut belegt und heiß an den Tisch.",
                                               "Ein Reinfall: Der Cheeseburger war trocken und nur lauwarm.",
                                               "Unbekannte Kennung."]})
    ergebnis, befunde = z.zusammenfuehren(roh, geglaettet)
    assert ergebnis.loc[ergebnis.review_id == 1, "review_text"].item().startswith("Rundum zufrieden. Der Classic")
    assert ergebnis.loc[ergebnis.review_id == 3, "review_text"].item() == roh.loc[2, "review_text"]
    assert list(ergebnis.columns) == list(roh.columns)
    assert any("99" in b for b in befunde)
    assert any("3" in b and "roh" in b for b in befunde)


def test_zusammenfuehren_behaelt_sterne_und_reihenfolge():
    roh = roh_beispiel()
    geglaettet = pd.DataFrame({"review_id": [2], "review_text": ["Leider ein Reinfall, der Cheeseburger war trocken und lauwarm."]})
    ergebnis, _ = z.zusammenfuehren(roh, geglaettet)
    assert list(ergebnis.stars) == [5, 1, 3]
    assert list(ergebnis.review_id) == [1, 2, 3]


def test_lose_schreiben(tmp_path):
    roh = pd.concat([roh_beispiel()] * 70, ignore_index=True)
    roh["review_id"] = range(1, len(roh) + 1)
    dateien = l.lose_schreiben(roh, tmp_path, groesse=100)
    assert len(dateien) == 3
    erstes = pd.read_csv(dateien[0], encoding="utf-8")
    assert list(erstes.columns) == ["review_id", "stars", "review_text"]
    assert len(erstes) == 100 and len(pd.read_csv(dateien[-1], encoding="utf-8")) == 10
```

- [ ] **Step 2: Tests laufen lassen — sie müssen scheitern**

Run: `python3 -m pytest dataset/tests/test_glaettung.py -q`
Expected: FAIL mit `ModuleNotFoundError: No module named 'zusammenfuehren'`.

- [ ] **Step 3: `lose_schreiben.py`**

```python
#!/usr/bin/env python3
"""lose_schreiben.py — teilt den Rohstand in Lose à 100 Rezensionen für die Glättung.

    python3 dataset/glaettung/lose_schreiben.py          # schreibt lose/los_001.csv …

Jedes Los trägt review_id, stars und review_text. Die Lose werden nicht
versioniert (gitignore); der Rohstand bleibt jederzeit aus generate_reviews.py
reproduzierbar.
"""
from pathlib import Path

import pandas as pd

HIER = Path(__file__).resolve().parent
ROH = HIER.parent / "fact_reviews_roh.csv"


def lose_schreiben(roh, ordner, groesse=100):
    """Schreibt die Zeilen in nummerierte Lose und gibt die Dateipfade zurück."""
    ordner = Path(ordner)
    ordner.mkdir(parents=True, exist_ok=True)
    dateien = []
    for nummer, start in enumerate(range(0, len(roh), groesse), start=1):
        los = roh.iloc[start:start + groesse][["review_id", "stars", "review_text"]]
        pfad = ordner / f"los_{nummer:03d}.csv"
        los.to_csv(pfad, index=False, encoding="utf-8", lineterminator="\n")
        dateien.append(pfad)
    return dateien


def main():
    """Rohstand lesen, Lose schreiben, Anzahl nennen."""
    roh = pd.read_csv(ROH, encoding="utf-8-sig")
    dateien = lose_schreiben(roh, HIER / "lose")
    print(f"{len(dateien)} Lose in {HIER / 'lose'} geschrieben")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: `zusammenfuehren.py`**

```python
#!/usr/bin/env python3
"""zusammenfuehren.py — baut aus Rohstand und geglätteten Losen den Bestand fact_reviews.csv.

    python3 dataset/glaettung/zusammenfuehren.py

Regeln je Text: 5 bis 500 Zeichen, kein Zeilenumbruch, Länge höchstens
30 Prozent vom Rohtext entfernt. Rezensionen ohne geglätteten Text behalten
den Rohtext — das wird gemeldet, ist aber kein Fehler (Abbruchkriterium der
Spec). Unbekannte Kennungen und Regelverstöße sind Fehler: Exit-Code 1, und
die Ausgabedatei wird nicht geschrieben.
"""
import sys
from pathlib import Path

import pandas as pd

HIER = Path(__file__).resolve().parent
ROH = HIER.parent / "fact_reviews_roh.csv"
ZIEL = HIER.parent / "fact_reviews.csv"
LOSE = HIER / "lose"


def pruefe_text(alt, neu):
    """Prüft einen geglätteten Text gegen die Regeln; leere Liste heißt in Ordnung."""
    befunde = []
    if not isinstance(neu, str) or not neu.strip():
        return ["Text ist leer"]
    if "\n" in neu or "\r" in neu:
        befunde.append("Text enthält einen Zeilenumbruch")
    if len(neu) < 5:
        befunde.append("Text ist zu kurz (unter 5 Zeichen)")
    if len(neu) > 500:
        befunde.append("Text ist zu lang (über 500 Zeichen)")
    if len(neu) > 1.3 * len(alt) + 10:
        befunde.append(f"Text ist zu lang gegenüber dem Rohtext ({len(neu)} statt {len(alt)} Zeichen)")
    if len(neu) < 0.7 * len(alt) - 10:
        befunde.append(f"Text ist zu kurz gegenüber dem Rohtext ({len(neu)} statt {len(alt)} Zeichen)")
    return befunde


def lade_lose(ordner):
    """Liest alle geglätteten Lose zu einer Tabelle review_id, review_text zusammen."""
    dateien = sorted(Path(ordner).glob("geglaettet_*.csv"))
    if not dateien:
        return pd.DataFrame({"review_id": pd.Series(dtype=int), "review_text": pd.Series(dtype=str)})
    return pd.concat([pd.read_csv(d, encoding="utf-8") for d in dateien], ignore_index=True)


def zusammenfuehren(roh, geglaettet):
    """Ersetzt die Texte per review_id; gibt den Bestand und die Befunde zurück."""
    befunde = []
    bekannt = set(roh.review_id)
    for kennung in geglaettet.review_id:
        if kennung not in bekannt:
            befunde.append(f"FEHLER: unbekannte review_id {kennung}")
    if geglaettet.review_id.duplicated().any():
        befunde.append("FEHLER: review_id kommt in den Losen mehrfach vor")
    neu = dict(zip(geglaettet.review_id, geglaettet.review_text))
    ergebnis = roh.copy()
    fehlend = []
    for i, zeile in ergebnis.iterrows():
        if zeile.review_id not in neu:
            fehlend.append(int(zeile.review_id))
            continue
        for befund in pruefe_text(zeile.review_text, neu[zeile.review_id]):
            befunde.append(f"FEHLER: review_id {zeile.review_id}: {befund}")
        ergebnis.at[i, "review_text"] = neu[zeile.review_id].strip()
    if fehlend:
        befunde.append(f"{len(fehlend)} Rezensionen ohne geglätteten Text, roh belassen (z. B. {fehlend[:5]})")
    return ergebnis, befunde


def main():
    """Rohstand und Lose lesen, zusammenführen, Befunde ausgeben, Bestand schreiben."""
    roh = pd.read_csv(ROH, encoding="utf-8-sig")
    geglaettet = lade_lose(LOSE)
    ergebnis, befunde = zusammenfuehren(roh, geglaettet)
    for befund in befunde:
        print("  " + befund)
    if any(b.startswith("FEHLER") for b in befunde):
        sys.exit("Abbruch: Fehler in den Losen, fact_reviews.csv nicht geschrieben.")
    ergebnis.to_csv(ZIEL, index=False, encoding="utf-8-sig", lineterminator="\n")
    print(f"{len(geglaettet)} von {len(roh)} Texten geglättet, geschrieben: {ZIEL}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: `stichprobe.py`**

```python
#!/usr/bin/env python3
"""stichprobe.py — zeigt 50 zufällige Rezensionen mit Sternen zum Gegenlesen.

    python3 dataset/glaettung/stichprobe.py [--seed 1]
"""
import argparse
from pathlib import Path

import pandas as pd

ZIEL = Path(__file__).resolve().parent.parent / "fact_reviews.csv"


def main():
    """50 Zeilen ziehen und Sterne neben Text ausgeben."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    r = pd.read_csv(ZIEL, encoding="utf-8-sig")
    for _, zeile in r.sample(50, random_state=args.seed).sort_values("stars").iterrows():
        print(f"{zeile.review_id:>5}  {zeile.stars}★  {zeile.review_text}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: `PROMPT.md` — der Auftrag je Los**

```markdown
# Auftrag: ein Los Rezensionen sprachlich glätten

Du bekommst die Datei `LOS` (CSV, Spalten `review_id, stars, review_text`, 100 Zeilen).
Die Texte sind synthetische deutsche Rezensionen von Gästen einer Burgerkette,
zusammengesetzt aus Satzbausteinen. Formuliere jeden Text so um, dass er wie
eine natürliche Rezension klingt.

Regeln, ohne Ausnahme:

1. Bedeutung und Polarität bleiben: Was gelobt oder bemängelt wird, bleibt gelobt oder bemängelt. Die Sterne (`stars`) sind vorgegeben — der Text muss dazu passen.
2. Produktnamen (englisch, z. B. „Bacon King", „Small Fries") und Filialnamen („BM Sanderring") bleiben wörtlich erhalten.
3. Keine neuen Fakten: keine Zahlen, Namen, Orte, Daten oder Ereignisse, die nicht im Text stehen.
4. Länge: höchstens 30 Prozent kürzer oder länger als das Original, immer 5 bis 500 Zeichen, ein bis vier Sätze.
5. Stilebene bleibt: Ein Text, der klein geschrieben ist oder „ae/oe/ue" statt Umlaute verwendet, bleibt in dieser Schreibweise. Alle anderen Texte in korrektem Deutsch mit echten Umlauten.
6. Kein Emoji, keine Beleidigungen, keine Anrede des Lesers, kein Englisch außer den Produktnamen. Keine Zeilenumbrüche im Text.
7. Jede `review_id` genau einmal, keine Zeile auslassen, keine hinzufügen.

Schreibe das Ergebnis als CSV nach `ZIEL` (UTF-8, Kopfzeile `review_id,review_text`,
Texte in doppelten Anführungszeichen, innere Anführungszeichen verdoppelt). Verwende
Python mit `csv.QUOTE_ALL` zum Schreiben, damit die Datei sicher lesbar ist. Prüfe zum
Schluss mit pandas, dass die Datei 100 Zeilen hat und die `review_id`-Menge der
Eingabe entspricht. Antworte nur mit „Los NNN: 100 Texte geschrieben" oder dem Fehler.
```

- [ ] **Step 7: `.gitignore` ergänzen**

Am Ende von `.gitignore` anfügen:

```
# Lose der Rezensionsglättung — Zwischenstand, reproduzierbar aus fact_reviews_roh.csv
dataset/glaettung/lose/
```

- [ ] **Step 8: Tests laufen lassen — sie müssen bestehen**

Run: `python3 -m pytest dataset/tests/test_glaettung.py -q`
Expected: `5 passed`.

- [ ] **Step 9: Commit**

```bash
git add dataset/glaettung/lose_schreiben.py dataset/glaettung/zusammenfuehren.py dataset/glaettung/stichprobe.py dataset/glaettung/PROMPT.md dataset/tests/test_glaettung.py .gitignore
git commit -m "dataset: Glättung der Rezensionen in Losen — Werkzeuge, Prüfregeln, Auftragstext"
```

---

### Task 7: Glättung durchführen und Bestand einfrieren

**Files:**
- Create: `dataset/fact_reviews.csv` (LFS)

Dieser Task wird von der Hauptsitzung orchestriert (Subagenten schreiben, die Sitzung prüft). Er ist der zeitaufwendigste Schritt der Phase.

- [ ] **Step 1: Lose schreiben**

```bash
python3 dataset/glaettung/lose_schreiben.py
ls dataset/glaettung/lose | wc -l        # 100
```

- [ ] **Step 2: Lose in Wellen glätten**

Für jedes Los `los_NNN.csv` einen Subagenten (general-purpose) mit dem Inhalt von `dataset/glaettung/PROMPT.md` beauftragen; `LOS` und `ZIEL` durch die absoluten Pfade `…/dataset/glaettung/lose/los_NNN.csv` und `…/dataset/glaettung/lose/geglaettet_NNN.csv` ersetzen. Zehn Subagenten je Welle im Hintergrund, nächste Welle nach Abschluss der vorigen. Reihenfolge der Lose zufällig (`python3 -c "import random; l=list(range(1,101)); random.Random(2026).shuffle(l); print(l)"`), damit ein vorzeitiger Abbruch keinen zusammenhängenden Zeitraum ungeglättet lässt.

Nach jeder Welle:

```bash
ls dataset/glaettung/lose/geglaettet_*.csv | wc -l
python3 dataset/glaettung/zusammenfuehren.py | tail -5
```
Expected: die Zahl steigt um zehn; `zusammenfuehren.py` meldet keine `FEHLER`-Zeilen. Meldet es welche, das betroffene Los mit demselben Auftrag wiederholen (Datei vorher löschen).

Abbruchkriterium (Spec 4.2): Reicht die Zeit nicht für alle Lose, endet der Task nach der letzten vollständigen Welle; der Stand („n von 10.000 geglättet") wird in Task 11 in `dataset/README.md` genannt.

- [ ] **Step 3: Zusammenführen und Stichprobe lesen**

```bash
python3 dataset/glaettung/zusammenfuehren.py
python3 dataset/glaettung/stichprobe.py --seed 1
```
Expected: `10000 von 10000 Texten geglättet` (oder der erreichte Stand), keine `FEHLER`. Die 50 Texte werden gelesen: Passt der Ton zu den Sternen, bleiben Produktnamen erhalten, gibt es Fremdkörper (Englisch, Emoji, neue Fakten)? Auffällige Kennungen mit `grep -n "^<id>," dataset/fact_reviews.csv` prüfen und das zugehörige Los wiederholen.

- [ ] **Step 4: Prüfung wie in Task 5, dann Commit**

```bash
python3 - <<'EOF'
import pandas as pd
r = pd.read_csv("dataset/fact_reviews.csv", encoding="utf-8-sig")
roh = pd.read_csv("dataset/fact_reviews_roh.csv", encoding="utf-8-sig")
assert len(r) == 10000 and list(r.columns) == list(roh.columns)
assert (r.drop(columns="review_text") == roh.drop(columns="review_text")).all().all(), "nur der Text darf sich ändern"
print("geändert:", (r.review_text != roh.review_text).sum(), "| Länge min/mean/max:", r.review_text.str.len().agg(["min","mean","max"]).round(0).tolist())
EOF
git add dataset/fact_reviews.csv
git lfs ls-files | grep "fact_reviews.csv"
git commit -m "dataset: fact_reviews.csv — geglätteter Bestand der 10.000 Rezensionen"
```

---

### Task 8: `db/aufbau/0021_rezensionen.sql`

**Files:**
- Create: `db/aufbau/0021_rezensionen.sql`

**Interfaces:**
- Consumes: Schemata `wawi` und `burgermetrics` (0001–0020), Muster aus `0017` (Bestandskopie), `0018` (Schreibfunktion, Rechte), `0019` (ETL, Probe, Aufräumen).
- Produces: Tabellen `burgermetrics.fact_reviews`, `wawi.rezension`; Sichten `wawi.stg_fact_reviews`, `wawi.v_rezension_produkt`, `wawi.v_kundenstimmen`, `wawi.v_rezension_letzte`, `burgermetrics.v_rezension_produkt`; Funktionen `wawi.rezension_anlegen(artikel_id bigint, sterne integer, inhalt text, filiale_id bigint DEFAULT NULL, sitzung text DEFAULT NULL) RETURNS jsonb`, `burgermetrics.uebernahme_aus_wawi() RETURNS TABLE (neue_tage, neue_bestellungen, neue_positionen, neue_rezensionen)`, `wawi.etl_probe()` (dritte Zeile `fact_reviews`), `wawi.uebungsrezensionen_loeschen() RETURNS TABLE (aus_burgermetrics integer, aus_wawi integer)`. Phase 3 ruft `rezension_anlegen` per PostgREST (`POST /rest/v1/rpc/rezension_anlegen`, `Content-Profile: wawi`) und liest `v_rezension_produkt`, `v_kundenstimmen`, `v_rezension_letzte`.

- [ ] **Step 1: Skript schreiben**

```sql
-- 0021_rezensionen.sql
-- Zweck: Rezensionen als dritter Sachverhalt der Fallstudie — operativ in
--        wawi.rezension (der Shop schreibt sie), analytisch in
--        burgermetrics.fact_reviews (Grain: eine Rezension).
--
--        Ladeweg wie beim Bestand: dataset/fact_reviews.csv ist die Quelle
--        der Wahrheit. lade_csv.py --nur fact_reviews fuellt fact_reviews;
--        dieses Skript kopiert die Simulationszeilen einmalig nach
--        wawi.rezension (Muster 0017). Danach fuehrt der Weg nur noch
--        vorwaerts: Shop -> wawi.rezension -> uebernahme_aus_wawi() ->
--        fact_reviews.
--
--        Rechte werden ausdruecklich gesetzt und nicht ueber Default-
--        Privileges geerbt: GRANT SELECT an studi_daba, anon, authenticated;
--        Row Level Security mit lesen_alle auf beiden Tabellen. Schreiben
--        darf anon nur ueber rezension_anlegen(): Sterne 1-5, Text 5-500
--        Zeichen, hoechstens 20 Rezensionen je Sitzung in zehn Minuten und
--        200 je Stunde insgesamt.
--
-- Aufruf (als postgres):
--   python3 db/skript_ausfuehren.py db/aufbau/0021_rezensionen.sql   -- Tabellen anlegen
--   python3 db/lade_csv.py --nur fact_reviews                        -- CSV laden
--   python3 db/skript_ausfuehren.py db/aufbau/0021_rezensionen.sql   -- Bestand nach wawi kopieren
--   python3 db/materialisieren.py                                    -- neue Sicht materialisieren
--   SELECT * FROM wawi.etl_probe();                                   -- 0 und 0, auch fuer fact_reviews
--
-- Voraussetzung: 0001-0020 sind gelaufen; als postgres ausfuehren.
-- Objekte: burgermetrics.fact_reviews, burgermetrics.v_rezension_produkt,
--          wawi.rezension, wawi.stg_fact_reviews, wawi.v_rezension_produkt,
--          wawi.v_kundenstimmen, wawi.v_rezension_letzte,
--          wawi.rezension_anlegen(), wawi.uebungsrezensionen_loeschen();
--          neu gefasst: wawi.stg_dim_date, burgermetrics.uebernahme_aus_wawi(),
--          wawi.etl_probe().
-- Ruecknahme: siehe Ende der Datei.
-- Idempotent: ja — die Bestandskopie laeuft nur, wenn wawi.rezension noch
--             keine Simulationszeilen hat.

SET search_path TO wawi, burgermetrics;

-- ---------------------------------------------------------------------------
-- Analytisch: eine Zeile je Rezension. order_id bleibt leer, wenn die
-- Rezension ohne Bestellbezug entstand (Shop ohne Kundenkonto).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS burgermetrics.fact_reviews (
  review_id    bigint PRIMARY KEY,
  date         date NOT NULL REFERENCES burgermetrics.dim_date(date),
  time         time,
  customer_id  bigint REFERENCES burgermetrics.dim_customer(customer_id),
  product_id   bigint NOT NULL REFERENCES burgermetrics.dim_product(product_id),
  branch_id    bigint REFERENCES burgermetrics.dim_branch(branch_id),
  order_id     bigint REFERENCES burgermetrics.fact_orders(order_id) ON DELETE SET NULL,
  stars        smallint NOT NULL CHECK (stars BETWEEN 1 AND 5),
  review_text  text NOT NULL,
  source       text NOT NULL CHECK (source IN ('simulation', 'shop'))
);
CREATE INDEX IF NOT EXISTS ix_bm_reviews_date     ON burgermetrics.fact_reviews(date);
CREATE INDEX IF NOT EXISTS ix_bm_reviews_product  ON burgermetrics.fact_reviews(product_id);
CREATE INDEX IF NOT EXISTS ix_bm_reviews_customer ON burgermetrics.fact_reviews(customer_id);
COMMENT ON TABLE burgermetrics.fact_reviews IS
  'Rezensionen, Grain: eine Rezension. source = simulation (CSV-Bestand) oder shop '
  '(Uebungsrezensionen aus dem Online-Shop, per ETL uebernommen).';

ALTER TABLE burgermetrics.fact_reviews ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS lesen_alle ON burgermetrics.fact_reviews;
CREATE POLICY lesen_alle ON burgermetrics.fact_reviews FOR SELECT USING (true);

-- ---------------------------------------------------------------------------
-- Operativ: die Rezension, wie der Shop sie anlegt. kunde_id und
-- bestellung_id sind optional — der Shop kennt keinen Kunden; der
-- Simulationsbestand traegt beides.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS wawi.rezension (
  rezension_id   bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  artikel_id     bigint NOT NULL REFERENCES wawi.artikel(artikel_id),
  kunde_id       bigint REFERENCES wawi.kunde(kunde_id),
  bestellung_id  bigint REFERENCES wawi.kundenbestellung(bestellung_id) ON DELETE SET NULL,
  filiale_id     bigint REFERENCES wawi.filiale(filiale_id),
  sterne         smallint NOT NULL CHECK (sterne BETWEEN 1 AND 5),
  inhalt         text NOT NULL CHECK (char_length(inhalt) BETWEEN 5 AND 500),
  erstellt_am    timestamptz NOT NULL DEFAULT now(),
  quelle         text NOT NULL CHECK (quelle IN ('simulation', 'shop')),
  sitzung        text
);
CREATE INDEX IF NOT EXISTS ix_wawi_rezension_artikel ON wawi.rezension(artikel_id);
CREATE INDEX IF NOT EXISTS ix_wawi_rezension_kunde   ON wawi.rezension(kunde_id);
CREATE INDEX IF NOT EXISTS ix_wawi_rezension_quelle  ON wawi.rezension(quelle, erstellt_am);
CREATE INDEX IF NOT EXISTS ix_wawi_rezension_sitzung ON wawi.rezension(sitzung, erstellt_am);
COMMENT ON TABLE wawi.rezension IS
  'Rezension eines Artikels. quelle = simulation (aus dem CSV-Bestand kopiert) oder '
  'shop (im Online-Shop geschrieben). Nur der Shop schreibt, ueber rezension_anlegen().';
COMMENT ON COLUMN wawi.rezension.quelle IS
  'simulation = kuratierter Bestand aus fact_reviews.csv; shop = Uebungsrezension aus dem Online-Shop.';

ALTER TABLE wawi.rezension ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS lesen_alle ON wawi.rezension;
CREATE POLICY lesen_alle ON wawi.rezension FOR SELECT USING (true);

-- ---------------------------------------------------------------------------
-- Bestandskopie: die Simulationszeilen einmalig ins operative Schema, mit
-- denselben Kennungen (Muster 0017). Datum und Uhrzeit werden zu einem
-- Zeitstempel in Europe/Berlin; die Uhrzeiten liegen zwischen 07:00 und
-- 23:59, damit die Rueckrechnung in stg_fact_reviews exakt ist.
-- ---------------------------------------------------------------------------
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM wawi.rezension WHERE quelle = 'simulation';
  IF n > 0 THEN
    RAISE NOTICE 'wawi.rezension: Simulationsbestand vorhanden (% Zeilen), nichts zu tun.', n;
    RETURN;
  END IF;
  SELECT count(*) INTO n FROM burgermetrics.fact_reviews WHERE source = 'simulation';
  IF n = 0 THEN
    RAISE NOTICE 'burgermetrics.fact_reviews ist leer — erst lade_csv.py --nur fact_reviews, dann dieses Skript erneut.';
    RETURN;
  END IF;
  INSERT INTO wawi.rezension
        (rezension_id, artikel_id, kunde_id, bestellung_id, filiale_id, sterne, inhalt,
         erstellt_am, quelle, sitzung)
  SELECT r.review_id, r.product_id, r.customer_id, r.order_id, r.branch_id, r.stars, r.review_text,
         (r.date + COALESCE(r.time, TIME '12:00')) AT TIME ZONE 'Europe/Berlin', 'simulation', NULL
  FROM   burgermetrics.fact_reviews r
  WHERE  r.source = 'simulation'
  ORDER  BY r.review_id;
  GET DIAGNOSTICS n = ROW_COUNT;
  RAISE NOTICE 'wawi.rezension: % Rezensionen uebernommen.', n;
  PERFORM setval(pg_get_serial_sequence('wawi.rezension', 'rezension_id'),
                 GREATEST((SELECT max(rezension_id) FROM wawi.rezension), 1));
END $$;

ANALYZE wawi.rezension;
ANALYZE burgermetrics.fact_reviews;

-- ---------------------------------------------------------------------------
-- stg: alle Rezensionen im Auswertungsvokabular, Spaltenfolge wie
-- fact_reviews. Die Probe vergleicht beide Seiten vollstaendig.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW wawi.stg_fact_reviews AS
SELECT r.rezension_id                                          AS review_id,
       (r.erstellt_am AT TIME ZONE 'Europe/Berlin')::date       AS date,
       (r.erstellt_am AT TIME ZONE 'Europe/Berlin')::time(0)    AS time,
       r.kunde_id                                              AS customer_id,
       r.artikel_id                                            AS product_id,
       r.filiale_id                                            AS branch_id,
       r.bestellung_id                                         AS order_id,
       r.sterne                                                AS stars,
       r.inhalt                                                AS review_text,
       r.quelle                                                AS source
FROM   wawi.rezension r;

-- Zeitdimension: neue Tage koennen jetzt auch aus Rezensionen stammen.
-- Gleiche Spaltenliste wie in 0019, deshalb CREATE OR REPLACE.
CREATE OR REPLACE VIEW wawi.stg_dim_date AS
WITH tage AS (
  SELECT b.bestelldatum AS tag FROM wawi.kundenbestellung b
  UNION
  SELECT (r.erstellt_am AT TIME ZONE 'Europe/Berlin')::date FROM wawi.rezension r
)
SELECT DISTINCT
       to_char(t.tag, 'YYYYMMDD')::bigint        AS date_id,
       t.tag                                    AS date,
       extract(year FROM t.tag)::int            AS year,
       'Q' || extract(quarter FROM t.tag)::int  AS quarter,
       extract(month FROM t.tag)::int           AS month,
       to_char(t.tag, 'FMMonth')                AS month_name,
       extract(week FROM t.tag)::int            AS calendar_week,
       extract(day FROM t.tag)::int             AS day_of_month,
       extract(isodow FROM t.tag)::int          AS day_of_week,
       to_char(t.tag, 'FMDay')                  AS day_name,
       extract(isodow FROM t.tag) >= 6          AS is_weekend,
       false                                    AS is_holiday,
       NULL::text                               AS holiday_name,
       NULL::text                               AS special_event,
       CASE WHEN extract(month FROM t.tag) IN (3, 4, 5)   THEN 'Spring'
            WHEN extract(month FROM t.tag) IN (6, 7, 8)   THEN 'Summer'
            WHEN extract(month FROM t.tag) IN (9, 10, 11) THEN 'Autumn'
            ELSE 'Winter' END                   AS season
FROM   tage t
WHERE  NOT EXISTS (SELECT 1 FROM burgermetrics.dim_date d WHERE d.date = t.tag);

-- ---------------------------------------------------------------------------
-- Sichten fuer den Shop (Phase 3). Alle mit Schema qualifiziert, wie in 0018.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS wawi.v_rezension_produkt CASCADE;
CREATE VIEW wawi.v_rezension_produkt AS
SELECT a.artikel_id,
       a.name,
       count(r.rezension_id)::int                                   AS anzahl,
       round(avg(r.sterne), 1)                                      AS sterne_mittel,
       max((r.erstellt_am AT TIME ZONE 'Europe/Berlin')::date)      AS letzte
FROM   wawi.artikel a
LEFT JOIN wawi.rezension r ON r.artikel_id = a.artikel_id
GROUP  BY a.artikel_id, a.name
ORDER  BY a.artikel_id;
COMMENT ON VIEW wawi.v_rezension_produkt IS
  'Je Artikel: Anzahl und mittlere Sterne aller Rezensionen (Simulation und Shop). '
  'Der Shop zeigt daraus die Bewertung am Produkt.';

-- Nur Simulationstexte: Was Besucher schreiben, erscheint nirgends oeffentlich.
DROP VIEW IF EXISTS wawi.v_kundenstimmen CASCADE;
CREATE VIEW wawi.v_kundenstimmen AS
SELECT s.artikel_id, s.rezension_id, s.sterne, s.inhalt,
       (s.erstellt_am AT TIME ZONE 'Europe/Berlin')::date AS datum
FROM  (SELECT r.*,
              row_number() OVER (PARTITION BY r.artikel_id
                                 ORDER BY r.erstellt_am DESC, r.rezension_id DESC) AS rang
       FROM   wawi.rezension r
       WHERE  r.quelle = 'simulation') s
WHERE  s.rang <= 3
ORDER  BY s.artikel_id, s.rang;
COMMENT ON VIEW wawi.v_kundenstimmen IS
  'Die drei juengsten Rezensionen je Artikel aus dem Simulationsbestand — die einzigen '
  'Texte, die der Shop anzeigt. Besuchertexte (quelle = shop) bleiben ausgeschlossen.';

DROP VIEW IF EXISTS wawi.v_rezension_letzte CASCADE;
CREATE VIEW wawi.v_rezension_letzte AS
SELECT r.rezension_id,
       r.sitzung,
       a.name                              AS artikel,
       f.name                              AS filiale,
       r.sterne,
       r.inhalt,
       r.erstellt_am,
       EXISTS (SELECT 1 FROM burgermetrics.fact_reviews x
               WHERE x.review_id = r.rezension_id) AS im_warehouse
FROM   wawi.rezension r
JOIN   wawi.artikel a ON a.artikel_id = r.artikel_id
LEFT JOIN wawi.filiale f ON f.filiale_id = r.filiale_id
WHERE  r.quelle = 'shop'
ORDER  BY r.erstellt_am DESC
LIMIT  50;
COMMENT ON VIEW wawi.v_rezension_letzte IS
  'Die 50 juengsten Uebungsrezensionen aus dem Shop. im_warehouse sagt, ob der '
  'ETL-Schritt sie schon nach burgermetrics uebernommen hat.';

-- ---------------------------------------------------------------------------
-- Semantikschicht: Bewertung je Produkt. Als Sicht angelegt; materialisieren.py
-- wandelt sie um. Beim zweiten Lauf kann sie schon materialisiert sein, daher
-- die Abfrage der Relationsart (Muster 0018).
-- ---------------------------------------------------------------------------
DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT c.relkind
           FROM   pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE  n.nspname = 'burgermetrics' AND c.relname = 'v_rezension_produkt'
             AND  c.relkind IN ('v', 'm') LOOP
    EXECUTE format('DROP %s IF EXISTS burgermetrics.v_rezension_produkt CASCADE',
                   CASE WHEN r.relkind = 'm' THEN 'MATERIALIZED VIEW' ELSE 'VIEW' END);
  END LOOP;
END $$;
CREATE VIEW burgermetrics.v_rezension_produkt AS
SELECT p.product_id,
       p.product_name,
       p.category,
       count(r.review_id)::int                                                            AS anzahl,
       round(avg(r.stars), 2)                                                             AS sterne_mittel,
       round(100.0 * count(r.review_id) FILTER (WHERE r.stars >= 4) / NULLIF(count(r.review_id), 0), 1) AS anteil_positiv_pct,
       round(100.0 * count(r.review_id) FILTER (WHERE r.stars <= 2) / NULLIF(count(r.review_id), 0), 1) AS anteil_negativ_pct
FROM   burgermetrics.dim_product p
LEFT JOIN burgermetrics.fact_reviews r ON r.product_id = p.product_id
GROUP  BY p.product_id, p.product_name, p.category
ORDER  BY p.product_id;
COMMENT ON VIEW burgermetrics.v_rezension_produkt IS
  'Rezensionen je Produkt: Anzahl, mittlere Sterne, Anteil positiv (4-5) und negativ (1-2). '
  'Kennzahl der Semantikschicht fuer Notebooks, Power BI und Tableau.';

-- ---------------------------------------------------------------------------
-- Schreiben: eine Rezension anlegen. Muster bestellung_anlegen (0018):
-- Parameter heissen wie die Spalten, SECURITY DEFINER, festgenagelter
-- search_path. quelle ist fest 'shop', kunde_id bleibt leer.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION wawi.rezension_anlegen(
  artikel_id  bigint,
  sterne      integer,
  inhalt      text,
  filiale_id  bigint DEFAULT NULL,
  sitzung     text   DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = wawi, pg_temp
AS $$
#variable_conflict use_variable
DECLARE
  v_jetzt     timestamptz := now();
  v_text      text        := btrim(regexp_replace(COALESCE(inhalt, ''), '\s+', ' ', 'g'));
  v_id        bigint;
  v_name      text;
  v_kuerzlich integer;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM artikel a WHERE a.artikel_id = artikel_id) THEN
    RAISE EXCEPTION 'unbekannter Artikel: %', artikel_id USING ERRCODE = '23503';
  END IF;
  IF sterne IS NULL OR sterne < 1 OR sterne > 5 THEN
    RAISE EXCEPTION 'sterne muss zwischen 1 und 5 liegen, nicht %', sterne USING ERRCODE = '22023';
  END IF;
  IF char_length(v_text) < 5 OR char_length(v_text) > 500 THEN
    RAISE EXCEPTION 'der Text braucht 5 bis 500 Zeichen, nicht %', char_length(v_text)
      USING ERRCODE = '22023';
  END IF;
  IF filiale_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM filiale f WHERE f.filiale_id = filiale_id) THEN
    RAISE EXCEPTION 'unbekannte Filiale: %', filiale_id USING ERRCODE = '23503';
  END IF;

  -- Bremse je Sitzung: 20 Rezensionen in zehn Minuten reichen fuer jede Uebung.
  IF sitzung IS NOT NULL THEN
    SELECT count(*) INTO v_kuerzlich
    FROM   rezension r
    WHERE  r.sitzung = sitzung AND r.erstellt_am > v_jetzt - interval '10 minutes';
    IF v_kuerzlich >= 20 THEN
      RAISE EXCEPTION 'zu viele Rezensionen in kurzer Zeit — bitte kurz warten'
        USING ERRCODE = '53400';
    END IF;
  END IF;
  -- Notbremse insgesamt: Der Weg ist oeffentlich; 200 Shop-Rezensionen je
  -- Stunde decken einen ganzen Kurs ab, ein Skript nicht.
  SELECT count(*) INTO v_kuerzlich
  FROM   rezension r
  WHERE  r.quelle = 'shop' AND r.erstellt_am > v_jetzt - interval '1 hour';
  IF v_kuerzlich >= 200 THEN
    RAISE EXCEPTION 'zu viele Rezensionen in der letzten Stunde — bitte spaeter erneut'
      USING ERRCODE = '53400';
  END IF;

  INSERT INTO rezension (artikel_id, kunde_id, bestellung_id, filiale_id, sterne, inhalt,
                         erstellt_am, quelle, sitzung)
  VALUES (artikel_id, NULL, NULL, filiale_id, sterne, v_text, v_jetzt, 'shop', sitzung)
  RETURNING rezension.rezension_id INTO v_id;

  SELECT a.name INTO v_name FROM artikel a WHERE a.artikel_id = artikel_id;
  RETURN jsonb_build_object(
    'rezension_id', v_id,
    'artikel',      v_name,
    'sterne',       sterne,
    'erstellt_am',  v_jetzt,
    'quelle',       'shop');
END $$;
COMMENT ON FUNCTION wawi.rezension_anlegen IS
  'Legt eine Shop-Rezension an: prueft Artikel, Sterne, Textlaenge, Filiale und '
  'bremst Massenanfragen. Einziger Schreibweg fuer anon auf wawi.rezension.';

-- ---------------------------------------------------------------------------
-- ETL neu gefasst: vierte Rueckgabespalte, deshalb DROP + CREATE. Der Rumpf
-- entspricht 0019 plus dem Block fuer die Rezensionen.
-- ---------------------------------------------------------------------------
DROP FUNCTION IF EXISTS burgermetrics.uebernahme_aus_wawi();
CREATE FUNCTION burgermetrics.uebernahme_aus_wawi()
RETURNS TABLE (neue_tage integer, neue_bestellungen integer, neue_positionen integer,
               neue_rezensionen integer)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = burgermetrics, wawi, pg_temp
AS $$
DECLARE
  n_tage integer; n_best integer; n_pos integer; n_rez integer;
BEGIN
  INSERT INTO burgermetrics.dim_date
        (date_id, date, year, quarter, month, month_name, calendar_week, day_of_month,
         day_of_week, day_name, is_weekend, is_holiday, holiday_name, special_event, season)
  SELECT s.date_id, s.date, s.year, s.quarter, s.month, s.month_name, s.calendar_week,
         s.day_of_month, s.day_of_week, s.day_name, s.is_weekend, s.is_holiday,
         s.holiday_name, s.special_event, s.season
  FROM   wawi.stg_dim_date s;
  GET DIAGNOSTICS n_tage = ROW_COUNT;

  INSERT INTO burgermetrics.fact_orders
        (order_id, date, time, hour, branch_id, customer_id, payment_id, promo_id,
         order_channel, item_count, distinct_items, gross_total, discount_amount,
         net_total, order_duration_min, satisfaction_score)
  SELECT s.order_id, s.date, s.time, s.hour, s.branch_id, s.customer_id, s.payment_id,
         s.promo_id, s.order_channel, s.item_count, s.distinct_items, s.gross_total,
         s.discount_amount, s.net_total, s.order_duration_min, s.satisfaction_score
  FROM   wawi.stg_fact_orders s
  WHERE  NOT EXISTS (SELECT 1 FROM burgermetrics.fact_orders o WHERE o.order_id = s.order_id)
  ORDER  BY s.order_id;
  GET DIAGNOSTICS n_best = ROW_COUNT;

  INSERT INTO burgermetrics.fact_order_items
        (order_item_id, order_id, product_id, quantity, unit_price, line_total)
  SELECT s.order_item_id, s.order_id, s.product_id, s.quantity, s.unit_price, s.line_total
  FROM   wawi.stg_fact_order_items s
  WHERE  NOT EXISTS (SELECT 1 FROM burgermetrics.fact_order_items i
                     WHERE i.order_item_id = s.order_item_id)
    AND  EXISTS (SELECT 1 FROM burgermetrics.fact_orders o WHERE o.order_id = s.order_id)
  ORDER  BY s.order_item_id;
  GET DIAGNOSTICS n_pos = ROW_COUNT;

  INSERT INTO burgermetrics.fact_reviews
        (review_id, date, time, customer_id, product_id, branch_id, order_id, stars,
         review_text, source)
  SELECT s.review_id, s.date, s.time, s.customer_id, s.product_id, s.branch_id, s.order_id,
         s.stars, s.review_text, s.source
  FROM   wawi.stg_fact_reviews s
  WHERE  NOT EXISTS (SELECT 1 FROM burgermetrics.fact_reviews r WHERE r.review_id = s.review_id)
  ORDER  BY s.review_id;
  GET DIAGNOSTICS n_rez = ROW_COUNT;

  RETURN QUERY SELECT n_tage, n_best, n_pos, n_rez;
END $$;
COMMENT ON FUNCTION burgermetrics.uebernahme_aus_wawi IS
  'ETL wawi -> burgermetrics: fehlende Kalendertage, Bestellungen, Positionen und '
  'Rezensionen einfuegen. Danach materialisieren.py --neu, sonst zeigt das Dashboard den alten Stand.';

-- Probe: dritte Zeile fuer die Rezensionen, sonst wie 0019.
CREATE OR REPLACE FUNCTION wawi.etl_probe()
RETURNS TABLE (tabelle text, nur_in_wawi bigint, nur_in_burgermetrics bigint)
LANGUAGE sql
SECURITY DEFINER
SET search_path = wawi, burgermetrics, pg_temp
AS $$
  WITH w AS (SELECT order_id, date, hour, branch_id, customer_id, payment_id, promo_id,
                    order_channel, item_count, gross_total, discount_amount, net_total,
                    order_duration_min, satisfaction_score
             FROM wawi.stg_fact_orders),
       b AS (SELECT order_id, date, hour, branch_id, customer_id, payment_id, promo_id,
                    order_channel, item_count, gross_total, discount_amount, net_total,
                    order_duration_min, satisfaction_score
             FROM burgermetrics.fact_orders),
       rw AS (SELECT review_id, date, time, customer_id, product_id, branch_id, order_id,
                     stars, review_text, source
              FROM wawi.stg_fact_reviews),
       rb AS (SELECT review_id, date, time, customer_id, product_id, branch_id, order_id,
                     stars, review_text, source
              FROM burgermetrics.fact_reviews)
  SELECT 'fact_orders'::text,
         (SELECT count(*) FROM (SELECT * FROM w EXCEPT SELECT * FROM b) x),
         (SELECT count(*) FROM (SELECT * FROM b EXCEPT SELECT * FROM w) x)
  UNION ALL
  SELECT 'fact_order_items',
         (SELECT count(*) FROM (SELECT * FROM wawi.stg_fact_order_items
                                EXCEPT SELECT * FROM burgermetrics.fact_order_items) x),
         (SELECT count(*) FROM (SELECT * FROM burgermetrics.fact_order_items
                                EXCEPT SELECT * FROM wawi.stg_fact_order_items) x)
  UNION ALL
  SELECT 'fact_reviews',
         (SELECT count(*) FROM (SELECT * FROM rw EXCEPT SELECT * FROM rb) x),
         (SELECT count(*) FROM (SELECT * FROM rb EXCEPT SELECT * FROM rw) x);
$$;

-- Aufraeumen: Uebungsrezensionen aus beiden Schemata; der Bestand bleibt.
CREATE OR REPLACE FUNCTION wawi.uebungsrezensionen_loeschen()
RETURNS TABLE (aus_burgermetrics integer, aus_wawi integer)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = wawi, burgermetrics, pg_temp
AS $$
DECLARE
  n_bm integer; n_w integer;
BEGIN
  DELETE FROM burgermetrics.fact_reviews r WHERE r.source = 'shop';
  GET DIAGNOSTICS n_bm = ROW_COUNT;
  DELETE FROM wawi.rezension r WHERE r.quelle = 'shop';
  GET DIAGNOSTICS n_w = ROW_COUNT;
  RETURN QUERY SELECT n_bm, n_w;
END $$;

-- ---------------------------------------------------------------------------
-- Rechte, ausdruecklich. Betriebsfunktionen verlieren ihr PUBLIC-EXECUTE
-- (die neu erzeugte uebernahme_aus_wawi haette es sonst wieder).
-- ---------------------------------------------------------------------------
GRANT SELECT ON wawi.rezension, wawi.stg_fact_reviews, wawi.v_rezension_produkt,
                wawi.v_kundenstimmen, wawi.v_rezension_letzte TO anon, authenticated;
GRANT SELECT ON burgermetrics.fact_reviews, burgermetrics.v_rezension_produkt TO anon, authenticated;

REVOKE ALL ON FUNCTION wawi.rezension_anlegen(bigint, integer, text, bigint, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION wawi.rezension_anlegen(bigint, integer, text, bigint, text) TO anon, authenticated;
REVOKE ALL ON FUNCTION burgermetrics.uebernahme_aus_wawi()  FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION wawi.etl_probe()                     FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION wawi.uebungsrezensionen_loeschen()   FROM PUBLIC, anon, authenticated;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'studi_daba') THEN
    GRANT SELECT ON wawi.rezension, wawi.stg_fact_reviews, wawi.v_rezension_produkt,
                    wawi.v_kundenstimmen, wawi.v_rezension_letzte TO studi_daba;
    GRANT SELECT ON burgermetrics.fact_reviews, burgermetrics.v_rezension_produkt TO studi_daba;
    REVOKE EXECUTE ON FUNCTION wawi.rezension_anlegen(bigint, integer, text, bigint, text) FROM studi_daba;
  END IF;
END $$;

-- ---------------------------------------------------------------------------
-- Probe: beide Schemata tragen denselben Simulationsbestand; die Rechte sind
-- wie vorgesehen. Bricht mit EXCEPTION ab, wenn nicht.
-- ---------------------------------------------------------------------------
DO $$
DECLARE
  v_sim bigint; v_fr bigint;
  v_fn  text := 'wawi.rezension_anlegen(bigint, integer, text, bigint, text)';
BEGIN
  SELECT count(*) INTO v_sim FROM wawi.rezension WHERE quelle = 'simulation';
  SELECT count(*) INTO v_fr  FROM burgermetrics.fact_reviews WHERE source = 'simulation';
  IF v_sim <> v_fr THEN
    RAISE EXCEPTION 'Simulationsbestand: % Zeilen in wawi, % in burgermetrics', v_sim, v_fr;
  END IF;
  IF NOT has_function_privilege('anon', v_fn, 'EXECUTE') THEN
    RAISE EXCEPTION 'anon darf rezension_anlegen() nicht ausfuehren';
  END IF;
  IF NOT has_table_privilege('anon', 'wawi.v_kundenstimmen', 'SELECT') THEN
    RAISE EXCEPTION 'anon liest v_kundenstimmen nicht';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'studi_daba') THEN
    IF NOT has_table_privilege('studi_daba', 'wawi.rezension', 'SELECT')
       OR NOT has_table_privilege('studi_daba', 'burgermetrics.fact_reviews', 'SELECT') THEN
      RAISE EXCEPTION 'studi_daba liest die Rezensionen nicht';
    END IF;
    IF has_table_privilege('studi_daba', 'wawi.rezension', 'INSERT')
       OR has_table_privilege('studi_daba', 'burgermetrics.fact_reviews', 'INSERT') THEN
      RAISE EXCEPTION 'studi_daba darf Rezensionen schreiben';
    END IF;
    IF has_function_privilege('studi_daba', v_fn, 'EXECUTE') THEN
      RAISE EXCEPTION 'studi_daba darf rezension_anlegen() ausfuehren';
    END IF;
  END IF;
  RAISE NOTICE 'Rezensionen: % Simulationszeilen in beiden Schemata; Rechte wie vorgesehen.', v_sim;
END $$;

-- Ruecknahme:
--   DROP FUNCTION wawi.uebungsrezensionen_loeschen();
--   DROP FUNCTION wawi.rezension_anlegen(bigint, integer, text, bigint, text);
--   DROP VIEW wawi.v_rezension_letzte, wawi.v_kundenstimmen, wawi.v_rezension_produkt, wawi.stg_fact_reviews;
--   DROP MATERIALIZED VIEW burgermetrics.v_rezension_produkt;   -- oder DROP VIEW vor materialisieren.py
--   DROP TABLE wawi.rezension;
--   DROP TABLE burgermetrics.fact_reviews;
--   uebernahme_aus_wawi(), etl_probe() und stg_dim_date aus 0019 erneut einspielen.
```

- [ ] **Step 2: Erster Lauf (Tabellen leer) — muss durchlaufen**

```bash
python3 db/skript_ausfuehren.py db/aufbau/0021_rezensionen.sql
```
Expected: NOTICE `burgermetrics.fact_reviews ist leer — erst lade_csv.py --nur fact_reviews, dann dieses Skript erneut.`, NOTICE `Rezensionen: 0 Simulationszeilen in beiden Schemata; Rechte wie vorgesehen.`, `Bestätigt.` Bricht das Skript mit einem SQL-Fehler ab, wird der Fehler behoben und der Lauf wiederholt — es ist idempotent.

- [ ] **Step 3: Zweiter Lauf sofort danach — muss ebenfalls durchlaufen**

Run: `python3 db/skript_ausfuehren.py db/aufbau/0021_rezensionen.sql`
Expected: dieselben Meldungen, `Bestätigt.`

- [ ] **Step 4: Schreibfunktion einmal von Hand prüfen (als postgres, dann aufräumen)**

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0, "db")
from skript_ausfuehren import verbinde
con = verbinde(); con.autocommit = True; cur = con.cursor()
cur.execute("SELECT wawi.rezension_anlegen(1, 5, 'Probelauf aus dem Aufbau, wird gleich gelöscht.', 2, 'aufbau-probe')")
print("angelegt:", cur.fetchone()[0])
for sql in ["SELECT wawi.rezension_anlegen(1, 6, 'Sechs Sterne gibt es nicht.')",
            "SELECT wawi.rezension_anlegen(999, 5, 'Diesen Artikel gibt es nicht.')",
            "SELECT wawi.rezension_anlegen(1, 5, 'kurz')"]:
    try:
        cur.execute(sql); print("FEHLT: keine Ausnahme bei", sql)
    except Exception as e:
        print("abgewiesen:", str(e).splitlines()[0])
cur.execute("SELECT * FROM wawi.v_rezension_letzte"); print("letzte:", cur.fetchall())
cur.execute("SELECT * FROM burgermetrics.uebernahme_aus_wawi()"); print("ETL:", cur.fetchone())
cur.execute("SELECT * FROM wawi.etl_probe()"); print("Probe:", cur.fetchall())
cur.execute("SELECT * FROM wawi.uebungsrezensionen_loeschen()"); print("gelöscht:", cur.fetchone())
EOF
```
Expected: `angelegt: {'rezension_id': 1, 'artikel': 'Classic Burger', …}`; drei Zeilen `abgewiesen: …` (Sterne, Artikel, Textlänge); `letzte:` eine Zeile mit `im_warehouse = False`; `ETL: (1, 0, 0, 1)` — der heutige Tag fehlt in `dim_date` (endet 2026-03-31) und wird ergänzt, wie bei Übungsbestellungen; `Probe:` drei Zeilen mit `0, 0`; `gelöscht: (1, 1)`.

- [ ] **Step 5: Commit**

```bash
git add db/aufbau/0021_rezensionen.sql
git commit -m "db: 0021 Rezensionen — wawi.rezension, fact_reviews, Schreibweg fuer den Shop, ETL, Rechte, Probe"
```

---

### Task 9: In Betrieb nehmen — laden, kopieren, materialisieren, nachweisen

**Files:** keine neuen; Zustand der lebenden Datenbank.

**Interfaces:**
- Consumes: `dataset/fact_reviews.csv` (Task 7), `0021` (Task 8), `lade_csv.py --nur` (Task 2), `skript_ausfuehren.py` (Task 1).
- Produces: 10.000 Zeilen in `burgermetrics.fact_reviews` und `wawi.rezension`; `burgermetrics.v_rezension_produkt` materialisiert; PostgREST kennt die neuen Objekte.

- [ ] **Step 1: CSV laden**

Run: `python3 db/lade_csv.py --nur fact_reviews`
Expected: eine Zeile `fact_reviews  10.000 Zeilen  …s` und `Fertig — eine Transaktion, alles oder nichts.` Scheitert der COPY an einem Datum außerhalb von `dim_date` oder an einer Fremdschlüsselverletzung, ist der Generator die Ursache (Task 4), nicht der Lader.

- [ ] **Step 2: Bestandskopie nach wawi**

Run: `python3 db/skript_ausfuehren.py db/aufbau/0021_rezensionen.sql`
Expected: NOTICE `wawi.rezension: 10000 Rezensionen uebernommen.` und `Rezensionen: 10000 Simulationszeilen in beiden Schemata; Rechte wie vorgesehen.`

- [ ] **Step 3: Sicht materialisieren**

Run: `python3 db/materialisieren.py`
Expected: `38 Objekte im Schema burgermetrics`, `… v_rezension_produkt  materialisiert`, `ANALYZE gelaufen.` (Der Lauf baut alle Sichten neu — rund eine Minute.)

- [ ] **Step 4: Probe und Kennzahlen**

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0, "db")
from skript_ausfuehren import verbinde
cur = verbinde().cursor()
cur.execute("SELECT * FROM wawi.etl_probe()"); print("Probe:", cur.fetchall())
cur.execute("SELECT stars, count(*) FROM burgermetrics.fact_reviews GROUP BY 1 ORDER BY 1"); print("Sterne:", cur.fetchall())
cur.execute("SELECT product_name, anzahl, sterne_mittel FROM burgermetrics.v_rezension_produkt ORDER BY anzahl DESC LIMIT 3"); print("Top:", cur.fetchall())
cur.execute("SELECT corr(r.stars, o.satisfaction_score) FROM burgermetrics.fact_reviews r JOIN burgermetrics.fact_orders o USING (order_id)"); print("corr Sterne~Zufriedenheit:", round(cur.fetchone()[0], 3))
EOF
```
Expected: `Probe: [('fact_orders', 0, 0), ('fact_order_items', 0, 0), ('fact_reviews', 0, 0)]`, fünf Sternezeilen mit Summe 10.000, drei Produkte, Korrelation > 0,3.

- [ ] **Step 5: Nachweis als studi_daba**

```bash
python3 - <<'EOF'
import psycopg2
con = psycopg2.connect(host="supabase.butscher.cloud", port=5433, dbname="postgres", user="studi_daba", password="thws")
con.autocommit = True; cur = con.cursor()
cur.execute("SELECT count(*) FROM fact_reviews"); print("fact_reviews:", cur.fetchone()[0])
cur.execute("SELECT count(*) FROM rezension"); print("wawi.rezension:", cur.fetchone()[0])
cur.execute("SELECT product_name, sterne_mittel FROM burgermetrics.v_rezension_produkt ORDER BY sterne_mittel DESC LIMIT 1"); print("beste:", cur.fetchone())
try:
    cur.execute("SELECT wawi.rezension_anlegen(1, 5, 'Das darf studi_daba nicht.')"); print("FEHLT: Schreibweg offen")
except Exception as e:
    print("abgewiesen:", str(e).splitlines()[0])
EOF
```
Expected: `fact_reviews: 10000`, `wawi.rezension: 10000`, eine `beste:`-Zeile, `abgewiesen: permission denied for function rezension_anlegen`.

- [ ] **Step 6: PostgREST neu starten und den REST-Weg nachweisen**

```bash
ssh vps 'cd /root/supabase/docker && docker compose restart rest' 2>&1 | tail -2
sleep 8
ANON=$(grep -o "schluessel: '[^']*'" web/js/konfiguration.js | cut -d"'" -f2)
curl -s "https://supabase.butscher.cloud/rest/v1/v_rezension_produkt?select=name,anzahl,sterne_mittel&limit=2" -H "apikey: $ANON" -H "Accept-Profile: wawi"; echo
curl -s "https://supabase.butscher.cloud/rest/v1/v_kundenstimmen?select=artikel_id,sterne,inhalt&limit=1" -H "apikey: $ANON" -H "Accept-Profile: wawi"; echo
curl -s -X POST "https://supabase.butscher.cloud/rest/v1/rpc/rezension_anlegen" -H "apikey: $ANON" -H "Content-Profile: wawi" -H "Content-Type: application/json" \
  -d '{"artikel_id": 2, "sterne": 4, "inhalt": "Probe ueber PostgREST, wird gleich geloescht.", "sitzung": "aufbau-probe"}'; echo
python3 - <<'EOF'
import sys; sys.path.insert(0, "db")
from skript_ausfuehren import verbinde
con = verbinde(); con.autocommit = True; cur = con.cursor()
cur.execute("SELECT rezension_id, artikel, sterne, im_warehouse FROM wawi.v_rezension_letzte"); print("letzte:", cur.fetchall())
cur.execute("SELECT * FROM wawi.uebungsrezensionen_loeschen()"); print("gelöscht:", cur.fetchone())
EOF
```
Expected: zwei JSON-Antworten mit Daten; die RPC-Antwort `{"rezension_id": …, "artikel": "Cheeseburger", "sterne": 4, …}`; `letzte:` eine Zeile, `gelöscht: (0, 1)`. Antwortet PostgREST mit `Could not find the function` oder `relation does not exist`, war der Neustart nicht wirksam — `ssh vps 'docker ps --format "{{.Names}} {{.Status}}" | grep rest'` prüfen und den Neustart wiederholen.

- [ ] **Step 7: Zwischenstand festhalten**

Kein Commit nötig (nur Datenbankzustand). In `docs/superpowers/plans/2026-09-12-phase-2-rezensionen.md` diesen Task abhaken; die Zahlen aus Step 4 (Sterne, Korrelation) für Task 11 notieren.

---

### Task 10: Mini-Skripte — zwölf Rezensionen, neun von neun zeilengleich

**Files:**
- Modify: `dataset/burgermetrics_mini.sql`, `dataset/wawi_mini.sql`, `dataset/wawi_zu_analytisch.sql`
- Test: `dataset/tests/test_mini.py`

**Interfaces:**
- Produces: Tabelle `fact_reviews` in `burgermetrics_mini.sql`, Tabelle `rezension` in `wawi_mini.sql`, Sicht `fact_reviews_neu` in `wawi_zu_analytisch.sql`; die Mini-Bestände werden in Phase 6 vom BM-Lab in PGlite geladen.

- [ ] **Step 1: Test schreiben (DuckDB, alle drei Skripte, neun Vergleiche)**

```python
# dataset/tests/test_mini.py
from pathlib import Path

import duckdb
import pytest

BASIS = Path(__file__).resolve().parent.parent
ZIELE = ["dim_product", "dim_branch", "dim_customer", "dim_payment_method", "dim_promotion",
         "dim_date", "fact_orders", "fact_order_items", "fact_reviews"]


@pytest.fixture(scope="module")
def con():
    """Lädt wawi_mini, baut die Sichten, lädt burgermetrics_mini daneben."""
    c = duckdb.connect()
    for datei in ["wawi_mini.sql", "wawi_zu_analytisch.sql", "burgermetrics_mini.sql"]:
        c.execute((BASIS / datei).read_text(encoding="utf-8"))
    return c


def test_zwoelf_rezensionen(con):
    assert con.execute("SELECT count(*) FROM rezension").fetchone()[0] == 12
    assert con.execute("SELECT count(*) FROM fact_reviews").fetchone()[0] == 12


@pytest.mark.parametrize("ziel", ZIELE)
def test_zeilengleich(con, ziel):
    n = con.execute(f"""
        SELECT count(*) FROM (
          (SELECT * FROM {ziel}_neu EXCEPT SELECT * FROM {ziel})
          UNION ALL
          (SELECT * FROM {ziel} EXCEPT SELECT * FROM {ziel}_neu)) t""").fetchone()[0]
    assert n == 0, ziel


def test_rezensionen_haengen_an_mini_bestellungen(con):
    fehlend = con.execute("""
        SELECT count(*) FROM fact_reviews r
        WHERE NOT EXISTS (SELECT 1 FROM fact_orders o WHERE o.order_id = r.order_id)
           OR NOT EXISTS (SELECT 1 FROM dim_product p WHERE p.product_id = r.product_id)
           OR NOT EXISTS (SELECT 1 FROM dim_date d WHERE d.date = r.date)""").fetchone()[0]
    assert fehlend == 0
```

- [ ] **Step 2: Test laufen lassen — er muss scheitern**

Run: `python3 -m pytest dataset/tests/test_mini.py -q`
Expected: FAIL — `rezension`/`fact_reviews` existieren nicht. (Scheitert schon `test_zeilengleich[dim_date]` an `monthname()`-Unterschieden, ist das ein Vorbefund der bestehenden Skripte: melden, nicht in diesem Task beheben.)

- [ ] **Step 3: `burgermetrics_mini.sql` ergänzen**

Am Ende der Datei anfügen; die Kontrollzahlen im Kopfkommentar um `SELECT COUNT(*) FROM fact_reviews;  -->  12` ergänzen.

```sql
DROP TABLE IF EXISTS fact_reviews;
CREATE TABLE fact_reviews (review_id INTEGER PRIMARY KEY, date DATE, time TIME, customer_id INTEGER, product_id INTEGER, branch_id INTEGER, order_id INTEGER, stars INTEGER, review_text VARCHAR(500), source VARCHAR(10));
INSERT INTO fact_reviews (review_id, date, time, customer_id, product_id, branch_id, order_id, stars, review_text, source) VALUES
  (1, '2018-05-13', '18:40:00', 21454, 4, 1, 19540, 4, 'Der Bacon King war saftig und gut belegt. Am Drive-Through ging es zügig.', 'simulation'),
  (2, '2018-10-11', '19:05:00', 22612, 36, 2, 33218, 3, 'Der Milkshake Strawberry war in Ordnung, aber sehr süß. Neun Minuten Wartezeit sind für einen Imbiss zu viel.', 'simulation'),
  (3, '2019-04-05', '13:20:00', 5967, 10, 3, 50804, 5, 'Der Beyond Burger schmeckt besser als erwartet, gut gewürzt und heiß serviert. Gern wieder.', 'simulation'),
  (4, '2020-04-23', '12:15:00', 1943, 8, 1, 107470, 2, 'Der Kids Burger war trocken und lauwarm. Für den Preis hätte ich mehr erwartet.', 'simulation'),
  (5, '2020-10-03', '09:30:00', 249, 21, 3, 130918, 1, 'Vierzehn Minuten Wartezeit für einen Side Salad, und der war nicht frisch. Das war nichts.', 'simulation'),
  (6, '2021-10-04', '20:45:00', 16010, 37, 3, 191492, 5, 'Über die App bestellt, nach zwei Minuten abgeholt. Der Fresh OJ war frisch gepresst und kalt.', 'simulation'),
  (7, '2022-10-02', '18:10:00', 8315, 10, 1, 298962, 4, 'Solider Beyond Burger, die Fries dazu waren knusprig. Die Filiale BM Europastern war gut besucht.', 'simulation'),
  (8, '2023-04-01', '14:00:00', 8662, 18, 4, 353674, 3, 'Die Chicken Nuggets 6pc waren okay, nicht mehr. Die Portion ist klein für den Preis.', 'simulation'),
  (9, '2023-10-07', '19:30:00', 23371, 20, 4, 424018, 2, 'Onion Rings waren fettig und weich statt knusprig. Schade, sonst mag ich die Filiale.', 'simulation'),
  (10, '2024-05-01', '08:20:00', 9669, 40, 6, 494362, 5, 'Die Craft Lemonade ist erfrischend und nicht zu süß. Bestellung am Drive-Through lief problemlos.', 'simulation'),
  (11, '2025-10-03', '13:05:00', 14240, 13, 2, 690739, 4, 'Die Green Goddess Bowl war frisch und reichlich. Elf Minuten Wartezeit am Counter waren allerdings lang.', 'simulation'),
  (12, '2026-02-12', '15:50:00', 19890, 32, 4, 737635, 3, 'Der Coffee war heiß, aber dünn. Service am Counter freundlich und schnell.', 'simulation');
```

- [ ] **Step 4: `wawi_mini.sql` ergänzen**

Am Ende der Datei anfügen (Kopfkommentar: „15 der 27 Tabellen" bleibt unangetastet, aber der Satz „befuellt mit denselben 19 Bestellungen" bekommt den Zusatz „und zwoelf Rezensionen"):

```sql
-- Rezensionen: der Shop schreibt sie, der ETL-Schritt nimmt sie mit. quelle wie
-- bei kundenbestellung: 'simulation' ist der kuratierte Bestand, 'shop' entsteht
-- an der Oberflaeche. erstellt_am ist Ortszeit Europe/Berlin.
DROP TABLE IF EXISTS rezension; CREATE TABLE rezension (rezension_id INTEGER PRIMARY KEY, artikel_id INTEGER, kunde_id INTEGER, bestellung_id INTEGER, filiale_id INTEGER, sterne INTEGER, inhalt VARCHAR(500), erstellt_am TIMESTAMP, quelle VARCHAR(10));
INSERT INTO rezension VALUES
  (1, 4, 21454, 19540, 1, 4, 'Der Bacon King war saftig und gut belegt. Am Drive-Through ging es zügig.', '2018-05-13 18:40:00', 'simulation'),
  (2, 36, 22612, 33218, 2, 3, 'Der Milkshake Strawberry war in Ordnung, aber sehr süß. Neun Minuten Wartezeit sind für einen Imbiss zu viel.', '2018-10-11 19:05:00', 'simulation'),
  (3, 10, 5967, 50804, 3, 5, 'Der Beyond Burger schmeckt besser als erwartet, gut gewürzt und heiß serviert. Gern wieder.', '2019-04-05 13:20:00', 'simulation'),
  (4, 8, 1943, 107470, 1, 2, 'Der Kids Burger war trocken und lauwarm. Für den Preis hätte ich mehr erwartet.', '2020-04-23 12:15:00', 'simulation'),
  (5, 21, 249, 130918, 3, 1, 'Vierzehn Minuten Wartezeit für einen Side Salad, und der war nicht frisch. Das war nichts.', '2020-10-03 09:30:00', 'simulation'),
  (6, 37, 16010, 191492, 3, 5, 'Über die App bestellt, nach zwei Minuten abgeholt. Der Fresh OJ war frisch gepresst und kalt.', '2021-10-04 20:45:00', 'simulation'),
  (7, 10, 8315, 298962, 1, 4, 'Solider Beyond Burger, die Fries dazu waren knusprig. Die Filiale BM Europastern war gut besucht.', '2022-10-02 18:10:00', 'simulation'),
  (8, 18, 8662, 353674, 4, 3, 'Die Chicken Nuggets 6pc waren okay, nicht mehr. Die Portion ist klein für den Preis.', '2023-04-01 14:00:00', 'simulation'),
  (9, 20, 23371, 424018, 4, 2, 'Onion Rings waren fettig und weich statt knusprig. Schade, sonst mag ich die Filiale.', '2023-10-07 19:30:00', 'simulation'),
  (10, 40, 9669, 494362, 6, 5, 'Die Craft Lemonade ist erfrischend und nicht zu süß. Bestellung am Drive-Through lief problemlos.', '2024-05-01 08:20:00', 'simulation'),
  (11, 13, 14240, 690739, 2, 4, 'Die Green Goddess Bowl war frisch und reichlich. Elf Minuten Wartezeit am Counter waren allerdings lang.', '2025-10-03 13:05:00', 'simulation'),
  (12, 32, 19890, 737635, 4, 3, 'Der Coffee war heiß, aber dünn. Service am Counter freundlich und schnell.', '2026-02-12 15:50:00', 'simulation');
```

- [ ] **Step 5: `wawi_zu_analytisch.sql` ergänzen**

Vor dem Abschnitt „Gleichheitsbeweis" einfügen und dort „acht" durch „neun" ersetzen (sowie `fact_reviews` in die Aufzählung aufnehmen):

```sql
-- ── fact_reviews: Zeitstempel wird zu Datum und Uhrzeit, sonst Umbenennung ──
CREATE OR REPLACE VIEW fact_reviews_neu AS
SELECT rezension_id                         AS review_id,
       CAST(erstellt_am AS DATE)            AS date,
       CAST(erstellt_am AS TIME)            AS time,
       kunde_id                             AS customer_id,
       artikel_id                           AS product_id,
       filiale_id                           AS branch_id,
       bestellung_id                        AS order_id,
       sterne                               AS stars,
       inhalt                               AS review_text,
       quelle                               AS source
FROM rezension;
```

- [ ] **Step 6: Test laufen lassen — er muss bestehen**

Run: `python3 -m pytest dataset/tests/test_mini.py -q`
Expected: `11 passed`. Scheitert `test_zeilengleich[fact_reviews]` an Typen (z. B. `VARCHAR` gegen `VARCHAR(500)`), die Spaltentypen in `burgermetrics_mini.sql` an die Sicht angleichen — nicht umgekehrt.

- [ ] **Step 7: Commit**

```bash
git add dataset/burgermetrics_mini.sql dataset/wawi_mini.sql dataset/wawi_zu_analytisch.sql dataset/tests/test_mini.py
git commit -m "dataset: Mini-Bestand mit zwoelf Rezensionen — neun von neun Zieltabellen zeilengleich"
```

---

### Task 11: Lader, Prüfstand und Dokumentation

**Files:**
- Modify: `dataset/load_duckdb.py`, `dataset/verify_readme.py`, `dataset/README.md`, `db/README.md`

**Interfaces:**
- Consumes: Zahlen aus Task 9 Step 4 (Sterneverteilung, Korrelation) und Task 7 (Stand der Glättung).

- [ ] **Step 1: `load_duckdb.py`**

In `TABELLEN` nach `("fact_order_items", "fact_order_items.csv"),` die Zeile `("fact_reviews", "fact_reviews.csv"),` einfügen; in `SOLL` `"fact_reviews": 10_000,`. Den Satz im Docstring „Lädt alle 13 Tabellen" gibt es dort nicht — aber in `README.md` (Step 4).

Run: `python3 dataset/load_duckdb.py --lokal --klein && rm -f dataset/burger_metrics.duckdb`
Expected: eine Zeile `OK    fact_reviews  10.000 Zeilen`.

- [ ] **Step 2: Kennzahlen berechnen**

```bash
python3 - <<'EOF'
import pandas as pd
r = pd.read_csv("dataset/fact_reviews.csv", encoding="utf-8-sig")
fo = pd.read_csv("dataset/fact_orders.csv", encoding="utf-8-sig", usecols=["order_id", "satisfaction_score", "order_duration_min", "order_channel"])
z = r.merge(fo, on="order_id")
print("Anteile %:", (r.stars.value_counts(normalize=True).sort_index() * 100).round(1).to_dict())
print("Ø Sterne:", round(r.stars.mean(), 2))
print("corr Zufriedenheit:", round(z.stars.corr(z.satisfaction_score), 3), "| corr Dauer:", round(z.stars.corr(z.order_duration_min), 3))
print("Ø Sterne je Kanal:", z.groupby("order_channel").stars.mean().round(2).to_dict())
print("Anteil klein geschrieben %:", round(r.review_text.str.match(r"^[a-z]").mean() * 100, 1))
print("Länge Ø Zeichen:", round(r.review_text.str.len().mean(), 0), "| mit Filiale:", int(r.branch_id.notna().sum()))
EOF
```
Die ausgegebenen Werte werden in Step 3 und Step 4 eingetragen.

- [ ] **Step 3: `verify_readme.py` erweitern**

Vor `bestanden = sum(_ergebnisse)` einfügen; die mit `<…>` markierten Zahlen durch die Werte aus Step 2 ersetzen (dieselben Zahlen stehen dann in README.md):

```python
    print("\n--- Rezensionen ---")
    rz = lade("fact_reviews.csv")
    pruefe("Rezensionen", len(rz), 10_000, 0)
    pruefe("Rezensionen: je Bestellung hoechstens eine", rz.order_id.is_unique, 1, 0)
    anteile = rz.stars.value_counts(normalize=True) * 100
    for sterne, erwartet in [(5, <Anteil 5>), (4, <Anteil 4>), (3, <Anteil 3>), (2, <Anteil 2>), (1, <Anteil 1>)]:
        pruefe(f"Anteil {sterne} Sterne (%)", anteile[sterne], erwartet, 0.02)
    pruefe("Rezensionen: Sterne im Mittel", rz.stars.mean(), <Ø Sterne>)
    rzo = rz.merge(fo[["order_id", "satisfaction_score", "order_duration_min"]], on="order_id")
    pruefe("Korrelation Sterne~Zufriedenheit", rzo.stars.corr(rzo.satisfaction_score), <corr Zufriedenheit>, 0.05)
    pruefe("Korrelation Sterne~Dauer", rzo.stars.corr(rzo.order_duration_min), <corr Dauer>, 0.10)
    pruefe("Rezensionen umgangssprachlich (%)", rz.review_text.str.match(r"^[a-z]").mean() * 100, <Anteil klein>, 0.05)
```

Run: `python3 dataset/verify_readme.py | tail -12`
Expected: alle neuen Zeilen `OK`, Schlusszeile `==> 90 von 90 Angaben bestaetigt, 0 abweichend` (79 + 11); Exit 0.

- [ ] **Step 4: `dataset/README.md`**

Änderungen, jeweils an der genannten Stelle:

1. Kopf: „754.513 Bestellungen · 2.950.082 Bestellpositionen · 25.000 Kunden" um „· 10.000 Rezensionen" ergänzen; „nachgerechnet am 25. August 2026" bleibt, darunter ein Satz: „Die Rezensionen kamen am <Datum> hinzu (siehe Prüfstand)."
2. Galaxy-Schema-Diagramm: unter `fact_order_items` einen Block ergänzen:

   ```
                   fact_reviews ◀──── dim_product · dim_customer · dim_branch · dim_date
                      (Rezension)     order_id → fact_orders (optional)
                      10.000 Zeilen
   ```
   und der Satz danach: „Seit September 2026 gibt es eine dritte Faktentabelle, `fact_reviews`, mit einer Zeile je Rezension. Sie hängt über `order_id` an der Bestellung, aus der die Rezension stammt."
3. Dateitabelle: Zeilen `| fact_reviews.csv | Fakt | 10.000 | Rezensionen mit Sternen und deutschem Text, eine je Bestellung; sprachlich geglättet |` und `| fact_reviews_roh.csv | Fakt | 10.000 | derselbe Bestand vor der Glättung — Ausgabe von generate_reviews.py |`.
4. Schlüsselbeziehungen: `fact_reviews.order_id → fact_orders.order_id`, `fact_reviews.product_id → dim_product.product_id`, `fact_reviews.customer_id → dim_customer.customer_id`, `fact_reviews.branch_id → dim_branch.branch_id`, `fact_reviews.date → dim_date.date`.
5. Neuer Abschnitt nach „Anomalien und Fallstricke":

   ```markdown
   ### Rezensionen

   | # | Muster | Befund |
   |---|--------|--------|
   | 22 | **Sterne folgen der Bestellung** | Jede Rezension gehört zu einer bewerteten Bestellung. Die Sterne korrelieren mit `satisfaction_score` (r = <corr Zufriedenheit>) und negativ mit `order_duration_min` (r = <corr Dauer>). Wer den Text nach Polarität klassifiziert, kann das Ergebnis gegen die Sterne prüfen. |
   | 23 | **Schiefe Verteilung** | <Anteil 5> % fünf Sterne, <Anteil 4> % vier, <Anteil 3> % drei, <Anteil 2> % zwei, <Anteil 1> % ein Stern — wie auf Bewertungsportalen. Ein Klassifikator, der immer „positiv" sagt, liegt schon bei <Anteil 4 + Anteil 5> % richtig; Accuracy allein ist deshalb kein Gütemaß. |
   | 24 | **Umgangssprache** | Rund <Anteil klein> % der Texte sind klein geschrieben und ersetzen Umlaute durch ae/oe/ue. Vorverarbeitung (Kleinschreibung, Umlautnormierung) ist Teil der Aufgabe. |
   ```
6. Abschnitt „Fortgeschritten (Data Mining)": Zeile `15. **Sentiment-Analyse:** Polarität der Rezensionstexte gegen die Sterne prüfen (`fact_reviews.csv`)` anfügen.
7. „In eine Datenbank laden": „Lädt alle 13 Tabellen" → „Lädt alle 14 Tabellen".
8. Neuer Abschnitt vor „Prüfstand":

   ```markdown
   ### Rezensionen neu erzeugen

   ```bash
   python3 generate_reviews.py                 # fact_reviews_roh.csv, Seed 2026, byte-identisch
   python3 glaettung/lose_schreiben.py         # 100 Lose à 100 Texte
   # … Lose sprachlich glätten (glaettung/PROMPT.md) …
   python3 glaettung/zusammenfuehren.py        # fact_reviews.csv, mit Prüfung
   ```

   Der Rohstand ist deterministisch; die Glättung ist es nicht, deshalb ist `fact_reviews.csv` der eingefrorene Bestand. Stand: <n> von 10.000 Texten geglättet.
   ```
9. Prüfstand: „**79 Angaben, alle bestätigt**" → „**90 Angaben, alle bestätigt** (Stand <Datum>: 79 zum Bestand vom 25. August 2026, 11 zu den Rezensionen)".
10. „Der Rückweg": „jede der acht Zieltabellen" → „jede der neun Zieltabellen"; in der Tabelle bei `wawi_mini.sql` „…19 Bestellungen wie `burgermetrics_mini.sql`" → „…19 Bestellungen und zwölf Rezensionen wie `burgermetrics_mini.sql`".

- [ ] **Step 5: `db/README.md`**

1. Tabelle „Aufbau in fünf Schritten": nach der Zeile `0020_demo_rolle.sql` die Zeile `| `aufbau/0021_rezensionen.sql` | Rezensionen: `wawi.rezension`, `fact_reviews`, Schreibweg `rezension_anlegen()` für den Shop, ETL und Probe erweitert — zweimal ausführen, dazwischen `lade_csv.py --nur fact_reviews` |`; nach `materialisieren.py` die Zeile `| `skript_ausfuehren.py` | führt ein Aufbauskript als `postgres` in einer Transaktion aus und zeigt die NOTICE-Meldungen |`.
2. Den Codeblock `cp .env.example .env … python3 db/lade_csv.py` um `python3 db/lade_csv.py --nur fact_reviews   # nur eine Tabelle` und `python3 db/skript_ausfuehren.py db/aufbau/0021_rezensionen.sql` ergänzen.
3. Neuer Abschnitt nach „Direkt auf die Datenbank: die Rolle `studi_daba`":

   ```markdown
   ## Rezensionen: vom Shop ins Warehouse

   Seit `0021` gibt es einen dritten Sachverhalt. Operativ schreibt der Shop über
   `wawi.rezension_anlegen(artikel_id, sterne, inhalt, filiale_id, sitzung)` — die
   einzige Schreibfunktion neben `bestellung_anlegen()`, mit denselben Riegeln:
   Prüfung der Eingaben, 20 Rezensionen je Sitzung in zehn Minuten, 200 je Stunde
   insgesamt. Der Simulationsbestand (`dataset/fact_reviews.csv`) liegt in beiden
   Schemata mit denselben Kennungen; `uebernahme_aus_wawi()` trägt Shop-Rezensionen
   nach `fact_reviews`, `etl_probe()` vergleicht beide Seiten, und
   `uebungsrezensionen_loeschen()` räumt die Übungsrezensionen wieder ab.

   Öffentlich sichtbar sind nur Aggregate (`v_rezension_produkt`) und die drei
   jüngsten Simulationstexte je Artikel (`v_kundenstimmen`). Was Besucher schreiben,
   erscheint nirgends auf einer Seite — nur in `v_rezension_letzte` für die
   Übungsgruppe. `studi_daba` liest alles, schreibt nichts und darf die Funktion nicht
   aufrufen; das prüft die Probe am Ende von `0021`.

   Nach jeder Änderung an Sichten oder Funktionen braucht PostgREST einen Neustart
   (`docker compose restart rest` auf dem Server), sonst kennt es die neuen Objekte
   nicht.
   ```

- [ ] **Step 6: Commit**

```bash
python3 dataset/verify_readme.py > /dev/null && echo "verify_readme: Exit 0"
git add dataset/load_duckdb.py dataset/verify_readme.py dataset/README.md db/README.md
git commit -m "dataset/db: Rezensionen dokumentiert — Lader, Prüfstand (90 Angaben), README"
```

---

### Task 12: Pull Request und Abnahme der Phase

**Files:** keine

- [ ] **Step 1: Alle Tests und Prüfungen in einem Lauf**

```bash
python3 -m pytest dataset/tests -q
python3 dataset/verify_readme.py | tail -1
git lfs ls-files | grep -c fact_reviews        # 2
git status --short                             # leer
```
Expected: alle Tests bestanden, `90 von 90`, `2`, kein offener Stand.

- [ ] **Step 2: Push und PR**

```bash
git push -u origin bm-analyse
gh pr create --base main --head bm-analyse --title "Phase 2: Rezensionen — Datenbank, Generator, Glättung" --body "$(cat <<'EOF'
## Was
- `0021_rezensionen.sql`: `wawi.rezension`, `burgermetrics.fact_reviews`, Sichten, `rezension_anlegen()` für den Shop, ETL und Probe erweitert, Rechte ausdrücklich
- `generate_reviews.py` + Bausteine: 10.000 Rezensionen zu bewerteten Bestellungen, deterministisch; Glättung in Losen mit Prüfung
- `fact_reviews_roh.csv`, `fact_reviews.csv` (LFS); Mini-Skripte mit zwölf Rezensionen (neun von neun zeilengleich)
- `lade_csv.py --nur`, `skript_ausfuehren.py`, Lader und Prüfstand (90 Angaben), README

## Stand auf der Instanz
- 10.000 Rezensionen in beiden Schemata, `etl_probe()` 0/0/0, `v_rezension_produkt` materialisiert, PostgREST neu gestartet, REST-Schreibweg geprüft und aufgeräumt
- `studi_daba` liest alles, schreibt nichts

Spec: docs/superpowers/specs/2026-09-12-bm-analyse-lernumgebung-design.md · Plan: docs/superpowers/plans/2026-09-12-phase-2-rezensionen.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Merge und Nachweis**

Merge über `gh pr merge --merge --delete-branch=false` (Robert hat die Umsetzung freigegeben; der PR dient der Nachvollziehbarkeit). Danach:

```bash
git checkout main && git pull --ff-only origin main
git log --oneline -3
gh run list --limit 1        # der Pages-Workflow läuft, auch wenn sich web/ nicht geändert hat
```
Expected: `main` enthält die Phase-2-Commits; der Workflow endet mit `completed success`. Anschließend `git checkout bm-analyse && git merge --ff-only main` (oder den Branch für Phase 3 neu von `main` abzweigen).

- [ ] **Step 4: Abnahmezeilen der Spec abhaken**

Spec Abschnitt 11: `0021`, Generator, Glättung und „Übergabe je Phase" (Datenbankteil) sind erfüllt; Shop, Notebooks, Dash, Deck, BM-Lab folgen in den Phasen 3–6.

---

## Selbstprüfung des Plans (durchgeführt)

- **Spec-Abdeckung:** 3.1 Tabelle, Funktion, Sichten, Rücksetzen → Task 8; 3.2 `fact_reviews`, Semantiksicht, ETL → Task 8; 3.3 Ladeweg, Mini-Skripte → Task 2, 9, 10; 3.4 Rechte und Proben, Ausführung als postgres → Task 1, 8, 9; 4.1 Generator → Task 3–5; 4.2 Glättung → Task 6–7; 4.3 Dokumentation → Task 11; 11 Abnahme → Task 9, 12; 12 Reihenfolge → Task 0–12. Dokumentation in `docs/02`, `05`, `07`, `08` folgt laut Spec in Phase 7 und ist hier bewusst nicht enthalten.
- **Platzhalter:** Die `<…>`-Werte in Task 11 sind Messwerte, die erst nach Task 7 und 9 feststehen; Step 2 dort berechnet sie. Sonst keine.
- **Schnittstellen:** Spaltenfolge `review_id, date, time, customer_id, product_id, branch_id, order_id, stars, review_text, source` in Generator, CSV, `fact_reviews`, `stg_fact_reviews`, `etl_probe()` und Mini-Sicht identisch; Funktionssignatur `rezension_anlegen(bigint, integer, text, bigint, text)` in Skript, Grants, Probe und Tests gleich; `uebernahme_aus_wawi()` überall mit vier Rückgabespalten.
