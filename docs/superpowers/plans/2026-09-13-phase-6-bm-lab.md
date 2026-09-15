# Phase 6: BM-Lab — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Lernumgebung **BM-Lab** unter `web/lab/` — acht Labs mit rund 41 Übungen, einer echten PostgreSQL-Datenbank im Browser (PGlite mit den Schemata `wawi` und `burgermetrics` des Miniaturbestands), Regal-Simulator für Power BI und Tableau, Abnahmelauf `node web/lab/tools/verify.mjs` ohne Befund, veröffentlicht über den vorhandenen Pages-Workflow unter `https://swrobuts.github.io/BurgerMetrics/lab/`.

**Architecture:** Die Laufzeit stammt aus der Lernumgebung WInf-SP (`Vorlesungen/Lernumgebungen/WInf-SP`): `assets/winf.js` wird zu `assets/bm.js` (nur Deutsch, `bm:*`-Schlüssel, acht Labs, zwei Schemata beim Säen, ohne Terminal-, Deploy- und SQLite-Pfade), `assets/winf.css` zu `assets/bm.css` (Palette aus Spec §2.3), `pruefung.js`, `jsonpruefung.js`, `regal.js` und `assets/pglite/` werden unverändert übernommen. Jedes Lab ist eine HTML-Seite plus `data/uebungen/lab-0N.json` nach dem Autorenleitfaden `tools/AUTORENLEITFADEN.md` der Vorlage; die Übungstypen `sql`, `quiz`, `zuordnen`, `checkliste`, `reihenfolge`, `regal`, `json` bleiben. Der Abnahmelauf `tools/verify.mjs` prüft Struktur, Deutsch-Pflicht, Lösbarkeit und führt jede SQL-Lösung gegen die Browser-Datenbank aus.

**Tech Stack:** statisches HTML/CSS/ES-Module ohne Build-Schritt; PGlite 0.5.5 (PostgreSQL im Browser, aus `WInf-SP/assets/pglite`, rund 19 MB); Node 26 für `tools/verify.mjs`, `tools/sql.mjs` und Playwright-Sichtprüfungen; Python 3.12 (`/Users/robert/miniforge3/bin/python3`, psycopg2) für `tools/gen_daten.py`; GitHub Pages aus `web/` (`.github/workflows/static.yml`, `web/.nojekyll` vorhanden).

**Spec:** `docs/superpowers/specs/2026-09-12-bm-analyse-lernumgebung-design.md`, Abschnitte 1 (Ziel, Ton), 2.1 (Orte, Vorlage), 2.2 (Datenbank), 2.3 (Farben), 9 (BM-Lab: Aufbau, Labs, Veröffentlichen), 11 (Abnahme, Zeile „BM-Lab“), 12 (Reihenfolge), 13 (Risiken: Tableau und Nur-Lese-Transaktionen). Vorlage: `/Users/robert/Library/CloudStorage/OneDrive-Persönlich/Vorlesungen/Lernumgebungen/WInf-SP` mit `tools/AUTORENLEITFADEN.md` (verbindlich für Aufbau, Ton und JSON-Format, mit den Abweichungen in den Global Constraints).

## Global Constraints

- **Repository und Zweig:** `/Users/robert/Library/CloudStorage/OneDrive-Persönlich/Vorlesungen/Datenbasierte Fallstudien/BurgerMetrics/BurgerMetrics_Website`, Branch `bm-analyse` (steht auf `main`, 228d9f8). Alles unter `web/lab/` wird versioniert (auch die 19 MB PGlite). Commits: `git -c core.fileMode=false add …`, Nachricht deutsch, Trailer `Co-Authored-By: <ausführendes Modell> <noreply@anthropic.com>`. Ein PR auf `main` am Ende; Merge nur nach Rückfrage bei Robert.
- **Vorlage WInf-SP:** Pfad `/Users/robert/Library/CloudStorage/OneDrive-Persönlich/Vorlesungen/Lernumgebungen/WInf-SP` (nur lesen, nie ändern). Der Autorenleitfaden `tools/AUTORENLEITFADEN.md` gilt für Aufbau der Seiten (Kopf, Seitennavigation, Lab-Kopf, `main`, Abschnitte, Übungsblock, Zusammenfassung), Dramaturgie (Problem → Begriffe → Inbetriebnahme mit Lizenz/Kosten → Handgriffe → Stolpersteine mit wörtlichen Fehlermeldungen → Spielplatz → Übungen → Zusammenfassung), Befehlskarten, Nachbildungen (`.shot`), Kopiervorlagen und das JSON-Format — **mit diesen Abweichungen:** (1) **nur Deutsch**: kein `<span lang="en">`, keine `en`-Felder im JSON; Texte stehen direkt (`<p>…</p>`) oder als `<span lang="de">`; JSON-Textfelder sind `{ "de": "…" }`; der Abnahmelauf prüft, dass `de` vorhanden und `en` abwesend ist. (2) Die Fallstudie ist **BurgerMetrics** (nicht Velo City): acht Filialen in Würzburg, 754.513 Bestellungen 2017–2026; im Lab liegt der Miniaturbestand (19 Bestellungen, 55 Positionen, 12 Rezensionen) in zwei Schemata. (3) Keine Terminal-, Deploy- oder SQLite-Übungen; die Seitendatenbank ist überall `data-datenbank="postgres"`. (4) Sprachumschalter und `?lang=`-Verweise entfallen; Betriebssystemwahl (mac/win) bleibt in der Laufzeit, Seiten zeigen sie nur, wenn sie OS-abhängige Zeilen haben.
- **Ton und Sprache (Spec §1):** sachlich, „Sie“, keine Ausrufezeichen, keine Bilder, Pointen oder Personifizierungen; echte Umlaute in allen sichtbaren Texten und Kommentaren; Bezeichner ASCII; englische Fachbegriffe bleiben englisch (Import, DirectQuery, Extract, Measure, Grain, Fan Trap, Lift, Notebook, Runtime …). Jede Angabe zu Version, Lizenz, Kontingent trägt den Stand („Stand 09/2026“) und stammt aus `slides/quellen_analyse.md` (lokal, Belegliste des Decks) oder aus diesem Plan; nichts erfinden, Unverifiziertes als „nach Herstellerangabe zu prüfen“ kennzeichnen.
- **Übungen** sind aus dem Text lösbar; `sql`- und `json`-Übungen haben `hinweis` und `loesung`; jede SQL-Lösung läuft mit `node web/lab/tools/sql.mjs "…"` gegen die Browser-Datenbank, bevor sie ins JSON kommt (die Lösungen in diesem Plan sind bereits so geprüft, Stand 13.09.2026). Übungs-IDs `W0N-01` …, Befehlskarten `B01` …; Zahl der Übungen je Lab = Eintrag `uebungen` in `LABS` (bm.js): 01: 6, 02: 5, 03: 5, 04: 5, 05: 5, 06: 5, 07: 5, 08: 5 (41 gesamt).
- **Zugangsdaten:** nur das Demo-Konto `studi_daba`/`thws` (öffentlich, nur lesend) erscheint; das Betreiberkonto nie. Die Labs schreiben nie in die echte Datenbank; Schreibübungen laufen in PGlite.
- **Farben (Spec §2.3):** Leitfarbe `#C2410C` (Flächen mit weißer Schrift, Text, Links), zweite Signalfarbe `#9A3412` (Hover, Links), Akzent `#ED7004` (Linien, Badges, Fortschritt — nie als Schriftfarbe), Aufhellung `#FDF1E7` (Hinweiskästen, aktive Navigation), dunkle Schrift auf Aufhellung `#7C2D12`.
- **Abnahme (Spec §9.3, §11):** `node web/lab/tools/verify.mjs` ohne Befund; jede SQL-Lösung geprüft; Sichtprüfung jeder Seite im Browser (Kopf, Navigation, Übungen, Datenbankband „bereit“); nach dem Merge Aufruf von `https://swrobuts.github.io/BurgerMetrics/lab/`. Lokal: `cd web && python3 -m http.server 8731` → `http://localhost:8731/lab/`. Für Browserprüfungen steht der Playwright-MCP zur Verfügung (Seite laden, auf das Datenbankband warten, Konsole auf Fehler prüfen, Bildschirmfoto).
- **Umgebung des Ausführenden:** Node 26 (`node`), Python `/Users/robert/miniforge3/bin/python3` (psycopg2, pandas), `gh`, Playwright-MCP. Wenn das Edit-Werkzeug Schreibzugriffe in einen Worktree unter `BurgerMetrics/.claude/worktrees/…` umleiten will: mit Python/Bash direkt im Repository schreiben und per `grep`/`ls` verifizieren.

---

## Fakten für die Labs (geprüft 13.09.2026)

**Miniaturbestand im Browser** (`data/wawi_mini.sql` → Schema `wawi`, 15 Tabellen; `data/burgermetrics_mini.sql` → Schema `burgermetrics`, 10 Tabellen; `data/bm_sichten.sql` → sechs Sichten): 19 Bestellungen (`fact_orders` = `kundenbestellung`), 55 Positionen, 12 Rezensionen (alle `source = 'simulation'`), Umsatz gesamt 200,85 €, Fan Trap 649,16 € (Faktor 3,23), 31 Artikel in 6 Kategorien, 5 Filialen mit Bestellungen (BM Europastern 7 · 84,75 €, BM Sanderring 4 · 38,30 €, BM Heuchelhof 4 · 36,47 €, BM Hauptbahnhof 2 · 26,38 €, BM Mainfrankenpark 2 · 14,95 €), Jahre 2017–2026 mit je 2 Bestellungen (2026: 1). Suchpfad der Browser-Datenbank wie in der echten: `wawi, burgermetrics` — `v_rezension_produkt` gibt es in beiden Schemata, ohne Präfix gewinnt `wawi`.

**Echte Datenbank** (PostgreSQL 17.6, `supabase.butscher.cloud:5433/postgres`, Rolle `studi_daba`, Kennwort `thws`): `wawi` 16 Tabellen + 10 Sichten, `burgermetrics` 14 Tabellen + 38 materialisierte Sichten; 754.513 Bestellungen, 2.950.082 Positionen, 10.000 Rezensionen, 25.000 Kunden; 2025: 136.557 Bestellungen, 2.994.771,13 €. Grenzen der Rolle: `statement_timeout 10min`, `idle_in_transaction_session_timeout 5min`, `default_transaction_read_only = on`, 20 Sitzungen, kein EXECUTE auf `wawi.bestellung_anlegen` und `wawi.rezension_anlegen`. Wörtliche Meldungen: `ERROR:  cannot execute INSERT in a read-only transaction`, `ERROR:  cannot execute CREATE TABLE in a read-only transaction`, `ERROR:  permission denied for function bestellung_anlegen`, bei falschem Präfix `ERROR:  relation "public.xyz" does not exist`.

**Werkzeuge (Stand 09/2026, Quellen in `slides/quellen_analyse.md`):** psql aus PostgreSQL 17 (17.11); DBeaver Community 26.2.0 (30.08.2026, Apache-2.0); DataGrip 2026.2 (für Studierende kostenlos, JetBrains Student Pack, jährlich erneuern); Power BI Desktop Update August 2026, PostgreSQL-Connector mit eingebautem Npgsql (seit 12/2019, 4.0.17 seit 10/2024), Modi Import und DirectQuery (DirectQuery: Grenze 1.000.000 Zeilen je Abfrageergebnis), Option „Beziehungen aus Datenquellen beim ersten Laden importieren“ standardmäßig aktiv; Tableau Desktop 2026.2 (27.08.2026), PostgreSQL-Connector mit Treiber, Live gegen Extract (`.hyper`), Tableau Desktop Public Edition nur Dateien/Google Drive/OData mit 15 Mio. Zeilen je Arbeitsmappe, Studentenlizenz seit 01.02.2025 eingestellt; DuckDB 1.5.5 (22.07.2026), LTS 1.4; Git LFS bei GitHub 10 GiB Bandbreite je Monat, CSV-Bestand 15 Dateien · 315 MB; pandas 3.0, SQLAlchemy 2.0, psycopg2 2.9; Open-Meteo CC BY 4.0 (unter 10.000 Aufrufen je Tag frei, „Weather data by Open-Meteo.com“), OpenHolidays API und OpenLigaDB ODbL, Destatis DL-DE BY 2.0, Paket `holidays` MIT.

**Notebook-Befunde (notebooks/00–08, ausgeführt 13.09.2026):** RFM-Segmente aus Python = `v_rfm_kunde`; K-Means: Silhouette bevorzugt k = 2, gewählt k = 4 (Cluster 3: 6.084 Kunden, Recency 11,1 Tage, Frequenz 36,1, Umsatz 698,0 €; Cluster 2: 1.910 Kunden, Recency 337,9 Tage); Warenkorb: Chicken Nuggets 6pc → BBQ-Sauce Lift 11,23 (Q1 2025) / 8,97 (gesamt), Medium Fries–Bier Lift 1,00; Prognose (BM Europastern): MAE Gradient Boosting 169,0 €, lineare Regression 172,4 €, naiver Mittelwert 286,6 €; Zufriedenheit: Trefferquote 50,6 % gegen Basisrate 50,4 %, Bestelldauer 36 % Wichtigkeit; Ausreißer: z-Score 79, IQR 213, Isolation Forest 178 (contamination 0,01), Kiliani 56 Filialtage (z 3,25); Sentiment: Wortliste 71,6 %, TF-IDF 100,0 % (Generatortexte), BERT 94,2 %; Wetter: r = 0,791 roh, −0,054 ohne Jahreszeit, Temperatur 41,64 €/°C ohne Monatskontrolle (p < 0,001), p = 0,171 mit; Heimspiel −251,50 € in der Regression, Gegenprobe +40,3 € gegen −1,3 € (Artefakt); VPI: 2025 nominal +5,4 %, real +3,2 %.

---

## Dateistruktur

| Datei | Verantwortung |
|---|---|
| `dataset/burgermetrics_mini.sql` (ändern, 31 Zeilen) | Booleans in `dim_product` als TRUE/FALSE — läuft dann in PostgreSQL/PGlite |
| `web/lab/tools/gen_daten.py` (neu) | kopiert die Mini-Skripte aus `dataset/`, schreibt `data/regal-bestellungen.json` (2.000 Bestellungen aus `obt_orders`, Demo-Konto) |
| `web/lab/data/{wawi_mini.sql, burgermetrics_mini.sql, bm_sichten.sql, regal-bestellungen.json}` (neu) | Browser-Datenbank und Regal-Daten |
| `web/lab/assets/{bm.css, bm.js, pruefung.js, jsonpruefung.js, regal.js}`, `web/lab/assets/pglite/` (neu) | Laufzeit |
| `web/lab/tools/{verify.mjs, sql.mjs}` (neu) | Abnahme und SQL-Probe |
| `web/lab/index.html`, `web/lab/README.md` (neu) | Übersicht, Autorenhinweise |
| `web/lab/lab-01-zugang.html` … `lab-08-extern.html` + `web/lab/data/uebungen/lab-01.json` … `lab-08.json` (neu) | die acht Labs |
| `web/lab/vorlagen/*` (neu) | Kopiervorlagen: `verbindung-psql.txt`, `verbindung-dbeaver.txt`, `verbindung-sqlalchemy.py`, `notebook-verbindungszelle.py`, `duckdb-laden.py`, `powerbi-measures.dax`, `tableau-berechnete-felder.txt`, `open-meteo.py` |
| `Vorlesungen/Lernumgebungen/BM-Lab.md` (neu, außerhalb des Repos) | drei Zeilen: Pfad und Adresse |
| `docs/superpowers/specs/…-design.md` (ändern) | Stand-Absatz Phase 6 in §11 |

Regal-Felder (`regal.felder`, in Lab 04 und 05 gleich): Dimensionen `monat` (geordnet, `2025-01` … `2025-12`), `wochentag` (Mo…So), `stunde` (geordnet, 7…23), `filiale`, `kanal`, `zahlart`, `loyalty`, `saison`; Kennzahlen `order_id` (Kennung — Σ darüber ist die Falle, COUNT zählt Bestellungen), `umsatz` (€), `positionen`, `zufriedenheit` (nur bewertete Bestellungen, AVG ignoriert Lücken).

---

### Task 1: Datengrundlage — Mini-Skripte, Sichten, Regal-Daten, PGlite, SQL-Probe

**Files:**
- Modify: `dataset/burgermetrics_mini.sql` (Booleans in `dim_product`)
- Create: `web/lab/tools/gen_daten.py`, `web/lab/tools/sql.mjs`, `web/lab/data/bm_sichten.sql`, `web/lab/data/wawi_mini.sql`, `web/lab/data/burgermetrics_mini.sql`, `web/lab/data/regal-bestellungen.json`, `web/lab/assets/pglite/` (Kopie)

**Interfaces:**
- Consumes: `WInf-SP/assets/pglite/` (PGlite 0.5.5, ES-Module `index.js` + Chunks + WASM), Demo-Konto der Datenbank.
- Produces: `node web/lab/tools/sql.mjs "<SQL>"` — lädt beide Schemata und die Sichten wie der Browser und druckt das Ergebnis (Exit 0; bei SQL-Fehler Meldung und Exit 1); `data/bm_sichten.sql` mit den Sichten `burgermetrics.v_kennzahlen_jahr`, `v_umsatz_monat`, `v_kanal_jahr`, `v_rezension_produkt`, `wawi.v_rezension_produkt`, `wawi.v_rezension_letzte`; `data/regal-bestellungen.json` (Liste von 2.000 Objekten mit `order_id, monat, wochentag, stunde, filiale, kanal, zahlart, loyalty, saison, umsatz, positionen, zufriedenheit`); Task 2 verwendet dieselbe Saatfolge in `bm.js`.

- [ ] **Step 1: Booleans im Mini-Skript korrigieren**

`dataset/burgermetrics_mini.sql` schreibt in `dim_product` die Spalte `is_vegetarian` als `0`/`1`; PostgreSQL (und damit PGlite) lehnt das ab („column “is_vegetarian" is of type boolean but expression is of type integer"). Alle anderen Booleans stehen schon als TRUE/FALSE.

```bash
cd "/Users/robert/Library/CloudStorage/OneDrive-Persönlich/Vorlesungen/Datenbasierte Fallstudien/BurgerMetrics/BurgerMetrics_Website"
/Users/robert/miniforge3/bin/python3 - <<'PY'
import re, pathlib
p = pathlib.Path("dataset/burgermetrics_mini.sql")
zeilen = p.read_text(encoding="utf-8").splitlines()
aus = []; im_block = False; n = 0
for z in zeilen:
    if z.startswith("INSERT INTO dim_product"): im_block = True
    elif im_block and (not z.strip() or z.startswith("DROP") or z.startswith("INSERT")): im_block = False
    if im_block and z.startswith("  ("):
        neu = re.sub(r"^(\s*\(\d+, '[^']*', '[^']*', '[^']*', )([01])(, )",
                     lambda m: m.group(1) + ("TRUE" if m.group(2) == "1" else "FALSE") + m.group(3), z)
        n += neu != z; z = neu
    aus.append(z)
p.write_text("\n".join(aus) + "\n", encoding="utf-8")
print("ersetzt:", n)
PY
grep -c "', [01], " dataset/burgermetrics_mini.sql
/Users/robert/miniforge3/bin/python3 -c "
import duckdb; con = duckdb.connect(); con.execute(open('dataset/burgermetrics_mini.sql', encoding='utf-8').read())
print(con.sql('SELECT count(*) FROM fact_orders').fetchone(), con.sql('SELECT count(*) FROM dim_product WHERE is_vegetarian').fetchone())"
```

Erwartet: `ersetzt: 31`, danach `0` Treffer für `', [01], `, DuckDB meldet `(19,) (26,)` — das Skript läuft weiterhin in DuckDB.

- [ ] **Step 2: Sichten für den Browser-Bestand**

```bash
mkdir -p web/lab/data web/lab/tools web/lab/assets
cat > web/lab/data/bm_sichten.sql <<'SQL'
-- bm_sichten.sql — Sichten der Semantikschicht auf dem Miniaturbestand des BM-Lab.
-- In der Datenbank der Fallstudie sind sie materialisiert (db/aufbau/0005 ff.);
-- hier reichen einfache Sichten auf 19 Bestellungen. Erwartet die Schemata
-- wawi und burgermetrics (Saatfolge in assets/bm.js und tools/sql.mjs).

CREATE VIEW burgermetrics.v_kennzahlen_jahr AS
SELECT extract(year FROM date)::int AS jahr, count(*) AS bestellungen,
       round(sum(net_total), 2) AS umsatz, round(avg(net_total), 2) AS aov
FROM burgermetrics.fact_orders GROUP BY 1;

CREATE VIEW burgermetrics.v_umsatz_monat AS
SELECT to_char(date, 'YYYY-MM') AS monat, count(*) AS bestellungen, round(sum(net_total), 2) AS umsatz
FROM burgermetrics.fact_orders GROUP BY 1;

CREATE VIEW burgermetrics.v_kanal_jahr AS
WITH je_kanal AS (
  SELECT extract(year FROM date)::int AS jahr, order_channel AS kanal, count(*) AS bestellungen
  FROM burgermetrics.fact_orders GROUP BY 1, 2)
SELECT jahr, kanal, bestellungen,
       round(100.0 * bestellungen / sum(bestellungen) OVER (PARTITION BY jahr), 1) AS anteil_pct
FROM je_kanal;

CREATE VIEW burgermetrics.v_rezension_produkt AS
SELECT p.product_id, p.product_name, p.category, count(r.review_id) AS anzahl,
       round(avg(r.stars), 2) AS sterne_mittel,
       round(100.0 * avg(CASE WHEN r.stars >= 4 THEN 1 ELSE 0 END), 1) AS anteil_positiv_pct
FROM burgermetrics.dim_product p LEFT JOIN burgermetrics.fact_reviews r USING (product_id)
GROUP BY p.product_id, p.product_name, p.category;

CREATE VIEW wawi.v_rezension_produkt AS
SELECT a.artikel_id, a.name, count(r.rezension_id) AS anzahl,
       round(avg(r.sterne), 2) AS sterne_mittel, max(r.erstellt_am) AS letzte
FROM wawi.artikel a LEFT JOIN wawi.rezension r USING (artikel_id)
GROUP BY a.artikel_id, a.name;

CREATE VIEW wawi.v_rezension_letzte AS
SELECT r.rezension_id, a.name AS artikel, r.sterne, r.inhalt, r.erstellt_am, r.quelle
FROM wawi.rezension r JOIN wawi.artikel a USING (artikel_id);
SQL
```

- [ ] **Step 3: `tools/gen_daten.py` — Kopien und Regal-Daten**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_daten.py — Datengrundlage des BM-Lab erzeugen.

Kopiert die Mini-Skripte aus dataset/ (eine Quelle der Wahrheit) nach data/ und
zieht 2.000 Bestellungen des Jahres 2025 als flache Tabelle für den
Regal-Simulator (Lab 04 und 05) aus burgermetrics.obt_orders — mit dem
Demo-Konto, deterministisch über md5(order_id).

Aufruf:  python3 web/lab/tools/gen_daten.py   (aus dem Repository-Wurzelverzeichnis)
"""
import json
import shutil
from pathlib import Path

import psycopg2

HIER = Path(__file__).resolve().parent
LAB = HIER.parent
REPO = LAB.parent.parent
VERBINDUNG = "postgresql://studi_daba:thws@supabase.butscher.cloud:5433/postgres"
TAGE = {1: "Mo", 2: "Di", 3: "Mi", 4: "Do", 5: "Fr", 6: "Sa", 7: "So"}


def kopiere_mini_skripte():
    # Die Skripte gehören nach dataset/; das Lab bekommt Kopien, weil Pages nur web/ ausliefert
    for name in ("wawi_mini.sql", "burgermetrics_mini.sql"):
        shutil.copyfile(REPO / "dataset" / name, LAB / "data" / name)
        print(f"kopiert: data/{name}")


def hole_regal_daten():
    # 2.000 Bestellungen aus 2025, jede Zeile so, wie man sie auf ein Regal legen würde
    sql = """
        SELECT order_id, to_char(date, 'YYYY-MM') AS monat, extract(isodow FROM date)::int AS wochentag,
               hour AS stunde, branch_name AS filiale, order_channel AS kanal, payment_type AS zahlart,
               loyalty_tier AS loyalty, season AS saison, net_total::float AS umsatz,
               item_count AS positionen, satisfaction_score::float AS zufriedenheit
        FROM burgermetrics.obt_orders
        WHERE year = 2025
        ORDER BY md5(order_id::text)
        LIMIT 2000"""
    with psycopg2.connect(VERBINDUNG) as con, con.cursor() as cur:
        cur.execute(sql)
        spalten = [c[0] for c in cur.description]
        zeilen = [dict(zip(spalten, z)) for z in cur.fetchall()]
    for z in zeilen:
        z["wochentag"] = TAGE[z["wochentag"]]
    zeilen.sort(key=lambda z: z["order_id"])
    (LAB / "data" / "regal-bestellungen.json").write_text(json.dumps(zeilen, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"geschrieben: data/regal-bestellungen.json ({len(zeilen)} Zeilen, {len(spalten)} Spalten)")


if __name__ == "__main__":
    kopiere_mini_skripte()
    hole_regal_daten()
```

```bash
/Users/robert/miniforge3/bin/python3 web/lab/tools/gen_daten.py
/Users/robert/miniforge3/bin/python3 -c "
import json; d = json.load(open('web/lab/data/regal-bestellungen.json'))
print(len(d), sorted({z['monat'] for z in d}) == [f'2025-{m:02d}' for m in range(1, 13)], sorted({z['wochentag'] for z in d}), min(z['stunde'] for z in d), max(z['stunde'] for z in d), sum(z['zufriedenheit'] is not None for z in d))"
```

Erwartet: `2000 True ['Di', 'Do', 'Fr', 'Mi', 'Mo', 'Sa', 'So'] 6 23 451`.

- [ ] **Step 4: PGlite übernehmen**

```bash
cp -R "/Users/robert/Library/CloudStorage/OneDrive-Persönlich/Vorlesungen/Lernumgebungen/WInf-SP/assets/pglite" web/lab/assets/pglite
ls web/lab/assets/pglite | wc -l; du -sh web/lab/assets/pglite
```

Erwartet: 57 Dateien, rund 19 MB (`index.js`, Chunks, `pglite.wasm`, `pglite.data`).

- [ ] **Step 5: `tools/sql.mjs` — SQL gegen die Browser-Datenbank ohne Browser**

```javascript
/**
 * BM-Lab · SQL ohne Browser ausprobieren
 *
 *   node tools/sql.mjs "SELECT count(*) FROM fact_orders"
 *   node tools/sql.mjs --datei abfrage.sql
 *
 * Lädt dieselbe Saat wie die Seite (Schema wawi aus wawi_mini.sql, Schema
 * burgermetrics aus burgermetrics_mini.sql, dazu bm_sichten.sql, Suchpfad
 * wawi, burgermetrics) in PGlite und druckt das letzte Ergebnis mit Spalten.
 * Gedacht, um Musterlösungen zu prüfen, bevor sie in eine Übung wandern.
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const WURZEL = join(dirname(fileURLToPath(import.meta.url)), '..')
const lies = (p) => readFileSync(join(WURZEL, p), 'utf8')

/** Saatfolge — identisch mit saeen() in assets/bm.js. */
export const SAAT = [
  ['CREATE SCHEMA wawi; SET search_path TO wawi;', 'data/wawi_mini.sql'],
  ['CREATE SCHEMA burgermetrics; SET search_path TO burgermetrics;', 'data/burgermetrics_mini.sql'],
  ['SET search_path TO wawi, burgermetrics;', 'data/bm_sichten.sql']
]

export async function neueDatenbank () {
  const { PGlite } = await import(join(WURZEL, 'assets/pglite/index.js'))
  const db = await PGlite.create()
  for (const [vorspann, datei] of SAAT) {
    await db.exec(vorspann)
    await db.exec(lies(datei))
  }
  await db.exec('SET search_path TO wawi, burgermetrics')
  return db
}

export async function fuehreAus (db, sql) {
  const teile = await db.exec(sql, { rowMode: 'array' })
  const letzte = [...teile].reverse().find(t => t.fields && t.fields.length) || { fields: [], rows: [] }
  return { spalten: letzte.fields.map(f => f.name), zeilen: letzte.rows }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const rest = process.argv.slice(2)
  if (!rest.length) { console.error('Aufruf: node tools/sql.mjs "SQL" | --datei pfad'); process.exit(2) }
  const sql = rest[0] === '--datei' ? readFileSync(rest[1], 'utf8') : rest.join(' ')
  const db = await neueDatenbank()
  try {
    const r = await fuehreAus(db, sql)
    if (!r.spalten.length) console.log('(keine Tabelle)')
    else {
      console.log(r.spalten.join(' | '))
      for (const z of r.zeilen.slice(0, 50)) console.log(z.map(v => v instanceof Date ? v.toISOString().slice(0, 10) : String(v)).join(' | '))
      console.log(`-- ${r.zeilen.length} Zeilen`)
    }
  } catch (e) {
    console.log('FEHLER: ' + e.message)
    process.exitCode = 1
  } finally { await db.close() }
}
```

```bash
cd web/lab
node tools/sql.mjs "SELECT count(*) AS bestellungen, (SELECT count(*) FROM fact_order_items) AS positionen, (SELECT round(sum(net_total), 2) FROM fact_orders) AS umsatz, (SELECT count(*) FROM fact_reviews) AS rezensionen FROM fact_orders" 2>/dev/null
node tools/sql.mjs "SELECT round(sum(o.net_total), 2) AS fan_trap FROM fact_orders o JOIN fact_order_items i USING (order_id)" 2>/dev/null
node tools/sql.mjs "SELECT * FROM v_rezension_produkt ORDER BY anzahl DESC, artikel_id LIMIT 1" 2>/dev/null
node tools/sql.mjs "SELECT jahr, umsatz FROM v_kennzahlen_jahr ORDER BY jahr DESC LIMIT 2" 2>/dev/null
node tools/sql.mjs "SELECT kaputt" 2>/dev/null; echo "Exit $?"
cd ../..
```

Erwartet: `19 | 55 | 200.85 | 12`; `649.16`; die wawi-Sicht (Spalten `artikel_id | name | anzahl | sterne_mittel | letzte`, erste Zeile `10 | Beyond Burger | 2 | 4.50 | …`); `2026 | 12.04` und `2025 | 20.21`; zuletzt `FEHLER: column "kaputt" does not exist` mit `Exit 1`. (Die Warnung „Module type … not specified“ von Node ist Rauschen des PGlite-Pakets; `2>/dev/null` blendet sie aus.)

- [ ] **Step 6: Commit**

```bash
git -c core.fileMode=false add dataset/burgermetrics_mini.sql web/lab/tools/gen_daten.py web/lab/tools/sql.mjs web/lab/data web/lab/assets/pglite
git -c core.fileMode=false commit -m "lab: Datengrundlage — Mini-Skripte in PGlite lauffähig, Sichten, Regal-Daten, PGlite-Assets" -m "Co-Authored-By: <Modell> <noreply@anthropic.com>"
```

---

### Task 2: Laufzeit und Gestalt — bm.css, bm.js, Prüfmodule, index.html, verify.mjs, README

**Files:**
- Create: `web/lab/assets/bm.css`, `web/lab/assets/bm.js`, `web/lab/assets/pruefung.js`, `web/lab/assets/jsonpruefung.js`, `web/lab/assets/regal.js` (Kopien), `web/lab/index.html`, `web/lab/tools/verify.mjs`, `web/lab/README.md`

**Interfaces:**
- Consumes: `tools/sql.mjs` (`neueDatenbank()`, `fuehreAus()`, `SAAT`) aus Task 1; `WInf-SP/assets/winf.js`, `winf.css`, `index.html`, `tools/verify.mjs` als Vorlagen.
- Produces: die Laufzeit, die jede Lab-Seite mit `<script type="module" src="assets/bm.js">` einbindet; `LABS` mit acht Einträgen (`id`, `nr`, `datei`, `uebungen`, `titel: {de}`, `voraussetzung`, `zeit`, `ziel`); Platzhalter wie im Leitfaden (`data-befehl`, `data-uebung`, `data-datenbank="postgres"`, `data-sql-konsole`, `data-json-konsole`, `data-regal`, `data-einordnung`, `data-fortschritt`, `data-lab-nav`); `node tools/verify.mjs` (Exit 0 ohne Befund) mit den Prüfungen aus Schritt 5.

- [ ] **Step 1: `bm.css` aus `winf.css`**

```bash
W="/Users/robert/Library/CloudStorage/OneDrive-Persönlich/Vorlesungen/Lernumgebungen/WInf-SP"
cp "$W/assets/winf.css" web/lab/assets/bm.css
cp "$W/assets/pruefung.js" "$W/assets/jsonpruefung.js" "$W/assets/regal.js" web/lab/assets/
```

Dann in `bm.css`: Kopfkommentar auf „BM-Lab · Gestalt der Lernumgebung (aus WInf-SP-Lab, Palette Spec §2.3)“ ändern; die Palette in `:root` ersetzen — `--primary: #C2410C`, `--primary-d: #7C2D12`, `--primary-l: #FDF1E7`, `--signal: #ED7004`, `--signal-l: #FDF1E7`, `--accent: #9A3412`, `--on-primary: #FFFFFF`, `--ink: #1C1917`, `--ink-soft: #57534E`, `--line: #E7E5E4`, `--bg-soft: #FAF8F5`; den zweiten `:root`/Dark-Block (Zeilen mit `--accent: #963041`, `--primary-l: #F6EAEC`) auf `--accent: #9A3412`, `--primary-l: #FDF1E7`; Terminal-Grund `--term-bg: #1C1917`, `--term-fg: #F5F5F4`, `--term-dim: #A8A29E` (die Konsolenklassen bleiben, weil die SQL-Konsole sie nutzt). Die Kommentare der Variablen auf Deutsch belassen, Farbnamen anpassen („Orange“ statt „Bordeaux“, „Akzent“ statt „Gold“). Sonst nichts ändern — die Klassen `nur-mac`, `nur-win` usw. bleiben.

Prüfung: `grep -c "7A1F2E\|E0B44C\|A0303F\|963041" web/lab/assets/bm.css` → `0`; `grep -c "C2410C" web/lab/assets/bm.css` → `≥ 1`.

- [ ] **Step 2: `bm.js` aus `winf.js`**

```bash
cp "$W/assets/winf.js" web/lab/assets/bm.js
```

Änderungen in `bm.js` (mit einem Python-Skript oder Edit, danach `node --check web/lab/assets/bm.js`):

1. Kopfkommentar: „BM-Lab · Laufzeit der Lernumgebung … Abgeleitet von der WInf-SP-Laufzeit (winf.js): nur Deutsch, eine Datenbankmaschine (PGlite mit zwei Schemata), ohne Terminal- und Deploy-Simulator.“ Die Liste der Bauformen: `quiz, zuordnen, checkliste, sql, json, reihenfolge, regal`.
2. Importe: die Zeilen `import … from './terminal.js'` und `import … from './deploy.js'` entfernen; `pruefung.js`, `jsonpruefung.js`, `regal.js` bleiben.
3. Sprache: `SPRACHSCHLUESSEL = 'bm:sprache'`, `OSSCHLUESSEL = 'bm:os'`; `setzeSprache` behält `data-lang="de"` — in `initSprache()` immer `setzeSprache('de')` (keine URL-Auswertung, kein localStorage-Lesen); die `?lang=en`-Umschreibung der `data-lab-link`-Verweise (Zeilen mit `'?lang=en'` in `setzeSprache`, `baueLabNavigation`, `karteFortschritt`) entfernen; `initTitel()` nimmt nur `document.title` (kein `winf:titel-en`). `txt()` bleibt (liefert `o.de`).
4. Ereignisnamen `winf:sprache`, `winf:os`, `winf:fortschritt`, `winf:datenbank` → `bm:sprache`, `bm:os`, `bm:fortschritt`, `bm:datenbank`; `fortschrittSchluessel = (lab) => \`bm:fortschritt:${lab}\``.
5. `TERMINAL_HINWEISE` und alles, was nur der Terminal-Nachbildung dient (`baueTerminal`, der Zweig `typ === 'terminal'` in `baueBox`, der Block `for (const halter of document.querySelectorAll('[data-terminal]'))` in `starteLab`), entfernen; ebenso `baueDeploy`, den Zweig `typ === 'deploy'`, den Block `[data-deploy]`; ebenso `ladeSqlJs`, den `sqlite`-Zweig in `holeDb`, `saeen`, `fuehre` und die Option `data-engine="sqlite"`.
6. Datenbank: `MASCHINEN` ersetzen durch

```javascript
/** Saatfolge — identisch mit tools/sql.mjs: zwei Schemata wie in der echten Datenbank, dann die Sichten. */
const SAAT = [
  ['CREATE SCHEMA wawi; SET search_path TO wawi;', 'data/wawi_mini.sql'],
  ['CREATE SCHEMA burgermetrics; SET search_path TO burgermetrics;', 'data/burgermetrics_mini.sql'],
  ['SET search_path TO wawi, burgermetrics;', 'data/bm_sichten.sql']
]
const SUCHPFAD = 'SET search_path TO wawi, burgermetrics'
```

`holeSaat(datei)` liest und cacht je Datei; `saeen(h)` lässt alle Schemata außer `pg_*`/`information_schema` fallen (wie bisher), legt `public` neu an, führt dann `SAAT` der Reihe nach aus (`await h.db.exec(vorspann); await h.db.exec(await holeSaat(datei))`) und zuletzt `SUCHPFAD`. Vor jeder Prüfung einer Übung wird wie bisher neu gesät, damit `CREATE TABLE`-Übungen wiederholbar sind. Das Datenbankband (`baueDbBand`) meldet „PostgreSQL im Browser (PGlite) · Schemata wawi und burgermetrics · 19 Bestellungen, 12 Rezensionen“; Texte der Band-Zustände (`dbLaedt`, `dbBereit`, `fehlerSql` …) auf BurgerMetrics umschreiben (nur `de`).
7. `LABS`:

```javascript
const LABS = [
  { id: 'lab-01', nr: '01', datei: 'lab-01-zugang.html', uebungen: 6,
    titel: { de: 'Zugang und Datenbank' }, voraussetzung: null, zeit: { de: '90 Minuten' },
    ziel: { de: 'Sich mit dem Demo-Konto verbinden, beide Schemata lesen und sagen können, was die Rolle darf und was nicht.' } },
  { id: 'lab-02', nr: '02', datei: 'lab-02-daten.html', uebungen: 5,
    titel: { de: 'Daten beschaffen' }, voraussetzung: { de: 'Lab 01' }, zeit: { de: '75 Minuten' },
    ziel: { de: 'Für jedes Werkzeug den passenden Weg zu den Daten wählen: Datenbank, CSV aus Git LFS oder DuckDB.' } },
  { id: 'lab-03', nr: '03', datei: 'lab-03-datenmodell.html', uebungen: 5,
    titel: { de: 'Analytisches Datenmodell' }, voraussetzung: { de: 'Lab 01' }, zeit: { de: '105 Minuten' },
    ziel: { de: 'Aus dem operativen Modell in vier Schritten ein Auswertungsmodell bauen und die Fan Trap erkennen.' } },
  { id: 'lab-04', nr: '04', datei: 'lab-04-powerbi.html', uebungen: 5,
    titel: { de: 'Power BI' }, voraussetzung: { de: 'Lab 02, Lab 03' }, zeit: { de: '105 Minuten' },
    ziel: { de: 'PostgreSQL anbinden, Beziehungen aus Fremdschlüsseln prüfen, Kennzahlen als Measures definieren und einen Bericht bauen.' } },
  { id: 'lab-05', nr: '05', datei: 'lab-05-tableau.html', uebungen: 5,
    titel: { de: 'Tableau' }, voraussetzung: { de: 'Lab 02, Lab 03' }, zeit: { de: '90 Minuten' },
    ziel: { de: 'Live und Extract unterscheiden, Dimension und Measure richtig legen und ein Dashboard bauen, das eine Frage beantwortet.' } },
  { id: 'lab-06', nr: '06', datei: 'lab-06-python.html', uebungen: 5,
    titel: { de: 'Python und Colab' }, voraussetzung: { de: 'Lab 01' }, zeit: { de: '75 Minuten' },
    ziel: { de: 'Ein Notebook so führen, dass es von oben nach unten gegen die Datenbank durchläuft — ohne Zugangsdaten im Repository.' } },
  { id: 'lab-07', nr: '07', datei: 'lab-07-datamining.html', uebungen: 5,
    titel: { de: 'Data Mining' }, voraussetzung: { de: 'Lab 03, Lab 06' }, zeit: { de: '90 Minuten' },
    ziel: { de: 'Zu einer Frage das passende Verfahren wählen, die Kennzahl lesen und den Fallstrick benennen.' } },
  { id: 'lab-08', nr: '08', datei: 'lab-08-extern.html', uebungen: 5,
    titel: { de: 'Externe Daten und Sentiment' }, voraussetzung: { de: 'Lab 03, Lab 07' }, zeit: { de: '90 Minuten' },
    ziel: { de: 'Externe Quellen über das Datum anbinden, ihre Lizenz nennen und den Weg einer Rezension vom Shop bis zur Sicht verfolgen.' } }
]
```

8. `karteFortschritt` (Startseite) und `baueEinordnung` bleiben; Texte, die noch `en` haben, auf `{ de }` kürzen (alle `{ de: …, en: … }`-Literale in der Datei: `en`-Teil entfernen — ein Regex `,\s*en:\s*'(?:[^'\\]|\\.)*'` je Literal, danach `node --check`).

Prüfung: `node --check web/lab/assets/bm.js`; `grep -c "terminal.js\|deploy.js\|sqljs\|winf:\|lang=en\|en:" web/lab/assets/bm.js` → `0`; `grep -c "bm:fortschritt" web/lab/assets/bm.js` → `≥ 1`.

- [ ] **Step 3: `index.html`**

Aus `WInf-SP/index.html` ableiten (Kopf mit `assets/bm.css`, Favicon-SVG mit `%23C2410C`, kein Sprachumschalter): Hero „BM-Lab“ mit Untertitel „Lernumgebung zur Fallstudie BurgerMetrics · Datenbasierte Fallstudien“, drei Sätzen zum Aufbau (acht Labs, dieselbe Datenbank wie Shop und Dashboard, alles im Browser) und Knöpfen „Lab 01 beginnen“ (`lab-01-zugang.html`) und „Zur Fallstudie“ (`../`); Kette (`.kette`): 01–03 „Zugang, Daten, Modell“ → 04–06 „Werkzeuge: Power BI, Tableau, Python“ → 07–08 „Analyse: Data Mining, externe Daten“; `<div data-fortschritt></div>`; `.labs-grid` mit acht `.lab-card` (Nummer, Titel, `.sub` mit Werkzeugen, `.desc` ein Satz, `.meta` „n Übungen · m Min“ aus `LABS`); Abschnitt „Verweise“ mit vier Karten: Startseite der Fallstudie (`../`), Online-Shop (`../shop.html`), Dashboard (`../dashboard.html`), Notebooks im Repository (`https://github.com/swrobuts/BurgerMetrics/tree/main/notebooks`); Abschnitt „Ausprobieren, nicht nachlesen“ (PGlite: PostgreSQL 17 im Browser, kein Konto, kein Server, Daten bleiben auf dem Rechner; Regal-Simulator; Fortschritt im Browser gespeichert, Knopf „Fortschritt zurücksetzen“ aus der Laufzeit); Fußzeile „THWS · Datenbasierte Fallstudien · BM-Lab“. `<script type="module" src="assets/bm.js"></script>`.

- [ ] **Step 4: Startseite im Browser prüfen**

```bash
cd web && (python3 -m http.server 8731 > /tmp/lab8731.log 2>&1 &) && sleep 2 && cd ..
```

Mit dem Playwright-MCP `http://localhost:8731/lab/` öffnen: acht Karten sichtbar, Fortschrittsleiste „0 von 41 Übungen“, keine Konsolenfehler (`browser_console_messages`), Bildschirmfoto. Server danach beenden: `pkill -f "http.server 8731"`.

- [ ] **Step 5: `tools/verify.mjs`**

Aus `WInf-SP/tools/verify.mjs` ableiten — Abschnitt 1 (Struktur) übernehmen und anpassen, Abschnitt 2 (Terminal-Lösungswege) durch Abschnitt 2 (SQL-Lösungen) ersetzen, Abschnitt 3 (Zusicherungen) auf die neuen Prüfungen beziehen:

- Importe: `pruefung.js` entfällt (keine Terminalübungen), `jsonpruefung.js` und `regal.js` bleiben, `deploy.js`/`terminal.js` entfallen; dazu `import { neueDatenbank, fuehreAus } from './sql.mjs'`.
- `LABS` aus `assets/bm.js` lesen (Regex wie bisher, Datei `assets/bm.js`).
- **Deutsch-Pflicht** statt Zweisprachigkeit: jedes Textfeld (`titel`, `aufgabe`, `rueckmeldung`, `hinweis`, Fragen, Optionen, Erklärungen, Einträge, `bedeutet`, Feld-`titel`) hat `de` (nicht leer) und **kein** `en`; in jeder HTML-Seite kein `lang="en"`, kein `data-lang-btn`, kein `?lang=`.
- Übrige Strukturprüfungen bleiben: Platzhalter ↔ JSON, Zahl der Übungen = `LABS`, Antwortindizes, `mehrfach`, Zuordnungsziele, Reihenfolge (`start` ≠ `richtig`, Lösung erfüllt), JSON-Übungen (Lösung besteht, Start besteht nicht), Regal (Lösung erfüllt Ziel, Felder vollständig), Befehlskarten, verlinkte Vorlagen/Dateien existieren, `data-lab`, große Nummer, Seitennavigation ↔ Abschnitte, `data-einordnung`/`data-fortschritt`/`data-lab-nav`, genau ein `data-datenbank="postgres"` je Seite mit SQL-Übungen, kein `data-terminal`/`data-deploy`/`data-datenbank="sqlite"`, keine PITM-/WInf-Reste (`winf.css`, `winf.js`, `winf:`, `WInf-SP`, `Velo City`).
- **Abschnitt 2, SQL:** eine PGlite-Datenbank je Lab; für jede Übung vom Typ `sql`: neu säen (Schemata fallen lassen wie `saeen()` in bm.js, dann `SAAT`), `vorher` ausführen (falls vorhanden), `loesung` ausführen — darf nicht scheitern; ohne `kontrolle` muss die Lösung mindestens eine Zeile liefern und `start` darf nicht dasselbe Ergebnis liefern wie die Lösung (sonst ist die Aufgabe schon gelöst); mit `kontrolle`: `kontrolle` läuft nach der Lösung und liefert mindestens eine Zeile. Befund je Übung mit der Fehlermeldung.
- Abschnitt 3: Zusicherungen für die neuen Prüfungen (z. B. ein `en`-Feld in einem Testobjekt wird gemeldet; eine SQL-Lösung mit Syntaxfehler wird gemeldet).
- Ausgabe wie bisher (`FEHL …` je Befund, am Ende `n Zusicherungen, m Fehler`), Exit 1 bei Fehlern.

Prüfung ohne Labs: `node web/lab/tools/verify.mjs 2>/dev/null | tail -3` → 0 Fehler (die Lab-Schleife ist leer; die Startseite und `bm.css`/`bm.js` werden geprüft).

- [ ] **Step 6: `README.md`**

Deutsch, Aufbau: Was das BM-Lab ist (acht Labs, Browser-Datenbank, Fallstudie), Verzeichnisstruktur (wie Spec §9.1), lokal starten (`cd web && python3 -m http.server 8731`), Autorenhinweise (Verweis auf `WInf-SP/tools/AUTORENLEITFADEN.md` mit den vier Abweichungen aus den Global Constraints; ein Lab = HTML + JSON + Vorlagen; Übungstypen; Datenbankband einmal je Seite oberhalb der ersten SQL-Übung), Daten (Saatfolge, Kontrollzahlen 19/55/200,85/12/649,16; `gen_daten.py` als einzige Quelle für `data/`), Abnahmelauf (`node tools/verify.mjs`, `node tools/sql.mjs "…"`, Sichtprüfung im Browser), Veröffentlichung (Pages aus `web/`, Adresse). Kein Terminal, kein Deploy, kein SQLite.

- [ ] **Step 7: Commit**

```bash
git -c core.fileMode=false add web/lab/assets web/lab/index.html web/lab/tools/verify.mjs web/lab/README.md
git -c core.fileMode=false commit -m "lab: Laufzeit bm.js/bm.css, Startseite, Abnahmelauf verify.mjs, README" -m "Co-Authored-By: <Modell> <noreply@anthropic.com>"
```

---

## Schablone für die Lab-Tasks 3–10

Jedes Lab-Task liefert `web/lab/lab-0N-name.html`, `web/lab/data/uebungen/lab-0N.json` und die genannten Kopiervorlagen unter `web/lab/vorlagen/`. Es ändert **nichts anderes** (nicht `bm.js`, nicht `bm.css`, nicht `index.html`, keine anderen Labs); fehlt ein CSS-Baustein, wird er im Bericht genannt. Vorgehen in jedem Lab-Task, in dieser Reihenfolge:

1. **Vorlagen lesen:** `WInf-SP/tools/AUTORENLEITFADEN.md` vollständig; `WInf-SP/lab-08-supabase.html` + `data/uebungen/lab-08.json` (Seite mit Datenbank, SQL-Übungen, Checkliste); dazu das im Task genannte Muster-Lab. `web/lab/README.md` (Abweichungen: nur Deutsch, BurgerMetrics, kein Terminal/Deploy/SQLite).
2. **HTML** nach dem Leitfaden (Abschnitt 2): Kopf mit `assets/bm.css`, Titel „Lab 0N · Name · BM-Lab“, Favicon-SVG mit `%23C2410C`, Header ohne Sprachknöpfe (Logo „BM-Lab“, „← Zur Übersicht“), Seitennavigation mit einem Link je `section-block`, Lab-Kopf (`lab-num-big`, `lab-title`, `lab-intro`, `lernziele`, `data-einordnung`), `main` mit den Abschnitten des Tasks, Übungsblock mit `data-uebung`-Platzhaltern und `data-fortschritt`, Zusammenfassung mit `data-lab-nav`, `<script type="module" src="assets/bm.js"></script>`. Seiten mit SQL-Übungen tragen genau einmal `<div data-datenbank="postgres"></div>` oberhalb der ersten SQL-Übung (im Abschnitt „Spielplatz“ oder direkt vor den Übungen) und eine freie Konsole `<div data-sql-konsole data-start="…"></div>`.
3. **Texte:** deutsch, „Sie“, sachlich (Global Constraints); jeder Abschnitt trägt die im Task genannten Aussagen; Zahlen aus dem Abschnitt „Fakten für die Labs“; Versions- und Lizenzangaben mit „Stand 09/2026“. Wörtliche Fehlermeldungen in `<code>`. Verweise auf andere Labs mit Nummer („Lab 03“), auf Notebooks mit Nummer und Dateiname, auf das Deck „Analyse“ bei Bedarf, auf das Repository `github.com/swrobuts/BurgerMetrics`.
4. **JSON** nach Leitfaden Abschnitt 3, nur `de`-Felder; die Übungen wörtlich wie im Task (Titel, Aufgabe, Hinweis, Lösung, Rückmeldung dürfen sprachlich geglättet, aber nicht inhaltlich geändert werden; SQL-Lösungen exakt). `rueckmeldung` erklärt das Warum in zwei bis drei Sätzen.
5. **Prüfen:** `cd web/lab && node tools/sql.mjs "<loesung>"` für jede SQL-Lösung (Ergebnis wie im Task); `/Users/robert/miniforge3/bin/python3 -c "import json; json.load(open('data/uebungen/lab-0N.json'))"`; `node tools/verify.mjs 2>/dev/null | grep -E "FEHL|Zusicherungen|Fehler"` — kein `FEHL` für dieses Lab; Browser: `cd web && python3 -m http.server 8731 &`, mit dem Playwright-MCP `http://localhost:8731/lab/lab-0N-name.html` öffnen, warten, bis das Datenbankband „bereit“ meldet (Seiten mit SQL), Konsole ohne Fehler, jede Übungsbox sichtbar (Zahl der `.uebung`-Boxen = Übungen des Labs), eine SQL-Übung mit der Musterlösung durchspielen (Eingabe, „Prüfen“, grünes Ergebnis), Bildschirmfoto der Seite; Server beenden.
6. **Commit:** `git -c core.fileMode=false add web/lab/lab-0N-*.html web/lab/data/uebungen/lab-0N.json web/lab/vorlagen/…` mit Nachricht `lab: Lab 0N — <Name>` und Trailer.
7. **Bericht:** Abschnittsliste, Übungsliste mit Typen, Vorlagen, Ergebnis von `verify.mjs`, Browserprüfung, offene Punkte.

---

### Task 3: Lab 01 — Zugang und Datenbank

**Files:** Create `web/lab/lab-01-zugang.html`, `web/lab/data/uebungen/lab-01.json`, `web/lab/vorlagen/verbindung-psql.txt`, `web/lab/vorlagen/verbindung-dbeaver.txt`. Muster-Lab zusätzlich: `WInf-SP/lab-09-datagrip.html` (Nachbildung eines Verbindungsdialogs).

**Abschnitte (ids):** `warum` — Warum eine Rolle: das Demo-Konto ist absichtlich öffentlich (Kennwort `thws` steht im Quelltext `db/aufbau/0020_demo_rolle.sql`), nur lesend, der Bestand ist synthetisch; wer schreiben will, nimmt DuckDB (Lab 02) oder eine eigene Instanz. `verbindung` — die fünf Angaben (Host `supabase.butscher.cloud`, Port `5433`, Datenbank `postgres`, Benutzer `studi_daba`, Kennwort `thws`), als URI `postgresql://studi_daba:thws@supabase.butscher.cloud:5433/postgres`; Befehlskarte B01 (psql-Aufruf mit `\dn`, `\dt wawi.*`, `\dm burgermetrics.*`, Erklärung jedes Metabefehls), B02 (URI-Bestandteile). `werkzeuge` — psql (PostgreSQL 17, Kommandozeile), DBeaver Community 26.2.0 (Apache-2.0), DataGrip 2026.2 (Student Pack); Nachbildung 1: DBeaver-Dialog „Connect to a database → PostgreSQL“ mit den Feldern Host/Port/Database/Username/Password und Callouts; Nachbildung 2: DataGrip „Data Sources and Drivers“ mit „Test Connection“; Hinweis zur Werkzeugauswahl (`auswahl-hinweis`). `schemata` — zwei Schemata: `wawi` (operativ, 3NF, Shop und Kasse schreiben) und `burgermetrics` (Galaxy-Schema, 38 materialisierte Sichten); Suchpfad `wawi, burgermetrics`, Präfix nötig, wenn ein Name doppelt ist (`v_rezension_produkt`); B03 (`SHOW search_path`, `SELECT * FROM v_rezension_produkt LIMIT 1` gegen `burgermetrics.v_rezension_produkt`). `sichten` — Sichten als Vertrag: jede Kennzahl genau einmal definiert (`v_kennzahlen_jahr`: Umsatz 2025 = 2.994.771,13 €), materialisiert, Dashboard/Notebooks/Dash lesen dieselbe Sicht; im Lab sind es einfache Sichten auf 19 Bestellungen. `grenzen` — Rechte als Ampel/Tabelle: erlaubt (SELECT auf alles in beiden Schemata, `kurzname()`), begrenzt (10 min je Abfrage, 5 min Leerlauf in offener Transaktion, 20 Sitzungen), verboten (INSERT/UPDATE/DELETE/CREATE, `bestellung_anlegen()`, `rezension_anlegen()`, Schema `public`). `stolper` — mit wörtlichen Meldungen: `ERROR:  relation "public.fact_orders" does not exist` (falsches Präfix), `ERROR:  cannot execute INSERT in a read-only transaction`, `ERROR:  permission denied for function bestellung_anlegen`, `ERROR:  canceling statement due to statement timeout` (nach zehn Minuten), `FATAL:  too many connections for role "studi_daba"` (mehr als 20 Sitzungen; Wortlaut von PostgreSQL). `spielplatz` — Datenbankband und freie SQL-Konsole (`data-start="SELECT * FROM v_kennzahlen_jahr ORDER BY jahr;"`). `uebungen`, `zusammenfassung`.

**Vorlagen:** `verbindung-psql.txt` (psql-Aufruf und die drei Metabefehle, kommentiert), `verbindung-dbeaver.txt` (die fünf Feldwerte, Treiber PostgreSQL, Hinweis SSL aus, Stand 09/2026).

**Übungen (`lab-01.json`):**

```json
[
  { "id": "W01-01", "typ": "sql",
    "titel": { "de": "Wie viele Tabellen hat jedes Schema?" },
    "aufgabe": { "de": "<p>Zählen Sie je Schema die Tabellen (<code>table_type = 'BASE TABLE'</code>) in <code>information_schema.tables</code> — nur die Schemata <code>wawi</code> und <code>burgermetrics</code>, sortiert nach Schemaname.</p><p>Erwartet werden zwei Spalten: <code>table_schema</code>, <code>tabellen</code>.</p>" },
    "start": "SELECT table_schema\nFROM information_schema.tables\n",
    "loesung": "SELECT table_schema, count(*) AS tabellen\nFROM information_schema.tables\nWHERE table_schema IN ('wawi', 'burgermetrics') AND table_type = 'BASE TABLE'\nGROUP BY table_schema\nORDER BY table_schema",
    "sortiert": true,
    "hinweis": { "de": "<p><code>information_schema.tables</code> kennt jede Tabelle und Sicht; <code>table_type</code> unterscheidet <code>BASE TABLE</code> und <code>VIEW</code>. Gruppieren Sie nach <code>table_schema</code>.</p>" },
    "rueckmeldung": { "de": "Im Browser sind es 15 und 10 Tabellen; in der echten Datenbank 16 und 14, dazu 38 materialisierte Sichten in burgermetrics — die stehen nicht in information_schema.tables, sondern in pg_matviews." } },

  { "id": "W01-02", "typ": "sql",
    "titel": { "de": "Der Suchpfad entscheidet, welche Sicht Sie bekommen" },
    "aufgabe": { "de": "<p>Die Startabfrage liest <code>v_rezension_produkt</code> ohne Schema — und trifft die Sicht in <code>wawi</code>. Gefragt ist die Sicht des Auswertungsmodells: je Produkt mit mindestens einer Rezension <code>product_name</code>, <code>category</code>, <code>anzahl</code> und <code>sterne_mittel</code>, sortiert nach <code>sterne_mittel</code> absteigend, dann <code>product_name</code>.</p>" },
    "start": "SELECT *\nFROM v_rezension_produkt\nLIMIT 5\n",
    "loesung": "SELECT product_name, category, anzahl, sterne_mittel\nFROM burgermetrics.v_rezension_produkt\nWHERE anzahl > 0\nORDER BY sterne_mittel DESC, product_name",
    "sortiert": true,
    "hinweis": { "de": "<p>Schreiben Sie das Schema davor: <code>burgermetrics.v_rezension_produkt</code>. Die Spalte <code>category</code> gibt es nur dort.</p>" },
    "rueckmeldung": { "de": "Der Suchpfad wawi, burgermetrics löst einen Namen im ersten Schema auf, das ihn kennt. Die Dash-App der Fallstudie qualifiziert deshalb jede Sicht; in Werkzeugen mit Schemabaum wählen Sie das Schema im Navigator." } },

  { "id": "W01-03", "typ": "sql",
    "titel": { "de": "Die Sicht als Vertrag" },
    "aufgabe": { "de": "<p>Lesen Sie aus <code>v_kennzahlen_jahr</code> die Spalten <code>jahr</code>, <code>bestellungen</code> und <code>umsatz</code> für die Jahre ab 2024, aufsteigend nach Jahr. Rechnen Sie nichts selbst — die Sicht definiert die Kennzahl.</p>" },
    "start": "SELECT *\nFROM v_kennzahlen_jahr\n",
    "loesung": "SELECT jahr, bestellungen, umsatz\nFROM v_kennzahlen_jahr\nWHERE jahr >= 2024\nORDER BY jahr",
    "sortiert": true,
    "hinweis": { "de": "<p><code>WHERE jahr >= 2024</code> und <code>ORDER BY jahr</code>; drei Spalten, nicht <code>*</code>.</p>" },
    "rueckmeldung": { "de": "Dieselbe Sicht liefert dem Dashboard, den Notebooks und der Dash-App ihre Zahlen. Wer die Definition ändert, ändert alle Leser auf einmal — das ist der Sinn der Semantikschicht." } },

  { "id": "W01-04", "typ": "quiz",
    "titel": { "de": "Was die Rolle darf" },
    "aufgabe": { "de": "<p>Drei Fragen zur Rolle <code>studi_daba</code>.</p>" },
    "fragen": [
      { "frage": { "de": "Welche Anweisung führt die Rolle aus?" },
        "optionen": [ { "de": "SELECT count(*) FROM wawi.rezension" }, { "de": "INSERT INTO wawi.rezension (…) VALUES (…)" }, { "de": "CREATE TABLE probe (x int)" }, { "de": "SELECT wawi.bestellung_anlegen(…)" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Die Rolle liest beide Schemata. INSERT und CREATE TABLE scheitern an der nur lesenden Transaktion, bestellung_anlegen() ist ihr entzogen (permission denied)." } },
      { "frage": { "de": "SELECT * FROM v_rezension_produkt ohne Präfix liefert …" },
        "optionen": [ { "de": "die Sicht aus wawi, weil wawi im Suchpfad vorn steht" }, { "de": "die Sicht aus burgermetrics, weil sie materialisiert ist" }, { "de": "einen Fehler, weil der Name doppelt vorkommt" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "PostgreSQL nimmt das erste Schema im Suchpfad, das den Namen kennt. Ein Fehler entsteht nicht; man bekommt nur andere Spalten als erwartet." } },
      { "frage": { "de": "Warum stehen die Kennzahlen in materialisierten Sichten?" },
        "optionen": [ { "de": "Damit jede Kennzahl genau einmal definiert ist und schnell gelesen wird" }, { "de": "Weil die Rolle keine Tabellen lesen darf" }, { "de": "Weil Sichten in PostgreSQL immer materialisiert sind" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Eine Sicht ist die Definition, die Materialisierung macht sie schnell. Tabellen darf die Rolle lesen; gewöhnliche Sichten werden bei jedem Aufruf neu berechnet." } }
    ],
    "rueckmeldung": { "de": "Die Rolle ist die Leseöffnung des Bestands. Alles, was sie nicht darf, gehört in Ihre eigene Datenbank." } },

  { "id": "W01-05", "typ": "zuordnen",
    "titel": { "de": "Meldung und Ursache" },
    "aufgabe": { "de": "<p>Ordnen Sie jede Meldung der Ursache zu.</p>" },
    "ziele": [ { "id": "praefix", "text": { "de": "falsches oder fehlendes Schema" } }, { "id": "readonly", "text": { "de": "nur lesende Transaktion der Rolle" } }, { "id": "recht", "text": { "de": "fehlendes Ausführungsrecht" } }, { "id": "grenze", "text": { "de": "Zeit- oder Sitzungsgrenze" } } ],
    "paare": [
      { "begriff": { "de": "relation \"public.fact_orders\" does not exist" }, "ziel": "praefix" },
      { "begriff": { "de": "cannot execute INSERT in a read-only transaction" }, "ziel": "readonly" },
      { "begriff": { "de": "permission denied for function bestellung_anlegen" }, "ziel": "recht" },
      { "begriff": { "de": "canceling statement due to statement timeout" }, "ziel": "grenze" },
      { "begriff": { "de": "cannot execute CREATE TABLE in a read-only transaction" }, "ziel": "readonly" },
      { "begriff": { "de": "too many connections for role \"studi_daba\"" }, "ziel": "grenze" }
    ],
    "rueckmeldung": { "de": "Vier Ursachen, sechs Meldungen. Die read-only-Meldungen sind der zweite Riegel neben den fehlenden Rechten; die Grenzen schützen die Instanz vor Versehen." } },

  { "id": "W01-06", "typ": "checkliste",
    "titel": { "de": "Die echte Verbindung herstellen" },
    "aufgabe": { "de": "<p>Verbinden Sie ein Werkzeug Ihrer Wahl — psql, DBeaver oder DataGrip — mit der Datenbank der Fallstudie. Diese Liste gilt für alle drei.</p>" },
    "schritte": [
      { "text": { "de": "Werkzeug installiert: psql (mit PostgreSQL 17), DBeaver Community 26.2 oder DataGrip 2026.2 (Student Pack)." } },
      { "text": { "de": "Neue Verbindung mit Host <code>supabase.butscher.cloud</code>, Port <code>5433</code>, Datenbank <code>postgres</code>, Benutzer <code>studi_daba</code>, Kennwort <code>thws</code>; SSL nicht erzwungen. Test Connection meldet Erfolg." } },
      { "text": { "de": "Im Schemabaum (oder mit <code>\\dn</code>) sind <code>wawi</code> und <code>burgermetrics</code> sichtbar." } },
      { "text": { "de": "<code>SELECT count(*) FROM burgermetrics.fact_orders;</code> liefert <code>754513</code>." } },
      { "text": { "de": "<code>SELECT jahr, umsatz FROM burgermetrics.v_kennzahlen_jahr WHERE jahr = 2025;</code> liefert <code>2994771.13</code>." } },
      { "text": { "de": "<code>INSERT INTO wawi.rezension (artikel_id, sterne, inhalt, quelle) VALUES (1, 5, 'Probe', 'shop');</code> scheitert mit <code>cannot execute INSERT in a read-only transaction</code> — die Rolle schreibt nicht." } }
    ],
    "rueckmeldung": { "de": "Wenn der letzte Schritt scheitert, ist alles richtig: Die Rolle liest und schreibt nicht. Die Verbindung brauchen Sie in Lab 04, 05 und 06 wieder." } }
]
```

Befehlskarten: B01 `psql "postgresql://studi_daba:thws@supabase.butscher.cloud:5433/postgres"` mit `\dn`, `\dt wawi.*`, `\dm burgermetrics.*`, `\q` (Teile erklärt); B02 die URI mit Teilen `postgresql://`, `studi_daba:thws@`, `supabase.butscher.cloud:5433`, `/postgres`; B03 `SHOW search_path;` und die beiden `SELECT … LIMIT 1` mit Ausgabe der Spaltenköpfe (`artikel_id | name | anzahl | sterne_mittel | letzte` gegen `product_id | product_name | category | anzahl | sterne_mittel | anteil_positiv_pct`).

Prüfung der SQL-Lösungen mit `node tools/sql.mjs`: W01-01 → `burgermetrics | 10`, `wawi | 15`; W01-02 → 11 Zeilen, erste `Craft Lemonade | Drink | 1 | 5.00`; W01-03 → 3 Zeilen (2024 | 2 | 14.95, 2025 | 2 | 20.21, 2026 | 1 | 12.04).

---

### Task 4: Lab 02 — Daten beschaffen

**Files:** Create `web/lab/lab-02-daten.html`, `web/lab/data/uebungen/lab-02.json`, `web/lab/vorlagen/duckdb-laden.py`. Muster-Lab zusätzlich: `WInf-SP/lab-06-sqlite.html` (Abschnitte zu Datei-Datenbanken).

**Abschnitte:** `wege` — drei Wege zu denselben Daten (Datenbank am Connector, CSV aus Git LFS, DuckDB lokal) und wer dabei rechnet. `lfs` — Git LFS: Zeigerdatei erkennen (`version https://git-lfs.github.com/spec/v1`, 133 Byte statt 51 MB), B01 (`git lfs install`, `git clone https://github.com/swrobuts/BurgerMetrics.git`, `ls -lh dataset/fact_orders.csv`, `git lfs pull`), Kontingent 10 GiB Bandbreite je Monat (Stand 09/2026), 15 Dateien · 315 MB je Klon → rund 30 Klone; deshalb lesen die Notebooks große Tabellen aus der Datenbank. `duckdb` — DuckDB als Python-Paket (1.5.5, LTS 1.4; Stand 09/2026), B02 (`python3 dataset/load_duckdb.py --lokal`, prüft die Zeilenzahlen), B03 (`read_csv`, `CREATE TABLE … AS`, eine Abfrage, die in PostgreSQL wortgleich läuft), Messwerte aus Deck 2 (Laden 2,3 s, Datei 54,5 MB, Umsatz je Filiale und Jahr 3,9 ms). `formate` — Exportformate: CSV (überall lesbar, keine Typen), Parquet (Typen, Spalten, Kompression; `fact_orders` 51 MB → 10,7 MB), Excel (1.048.576 Zeilen je Blatt), `.hyper` (Tableau-Extract); B04 (`to_parquet`/`to_csv` aus Notebook 00 mit `export/`). `werkzeuge` — Tabelle „was in welches Werkzeug“: Power BI → Connector (Import), Tableau Desktop → Connector (Live/Extract), Tableau Public → CSV, Colab → `lade_sql()`, lokal ohne Server → DuckDB. `stolper` — Zeigerdatei statt Daten; Colab liest LFS-Zeiger, wenn `raw.githubusercontent.com` ohne LFS-Media genutzt wird (Notebooks nehmen `media.githubusercontent.com/media/…`); pandas 3 speichert Text als `str`, DuckDB 1.4 lehnt ihn beim `register()` ab (Hilfsfunktion `fuer_duckdb()` in Notebook 00/01); `statement_timeout` bei Vollabzügen. `spielplatz` (Datenbankband, Konsole mit `data-start="SELECT b.branch_name, count(*) FROM fact_orders o JOIN dim_branch b USING (branch_id) GROUP BY 1 ORDER BY 2 DESC;"`), `uebungen`, `zusammenfassung`.

**Vorlage:** `duckdb-laden.py` — kommentiertes Skript: `duckdb.connect("burger_metrics.duckdb")`, zwei `read_csv`-Tabellen, die Abfrage aus B03, `con.close()`.

**Übungen (`lab-02.json`):**

```json
[
  { "id": "W02-01", "typ": "sql",
    "titel": { "de": "Umsatz je Filiale — in DuckDB und PostgreSQL gleich" },
    "aufgabe": { "de": "<p>Je Filiale (<code>branch_name</code>) die Zahl der Bestellungen und den Umsatz (<code>sum(net_total)</code>, auf zwei Stellen gerundet), absteigend nach Umsatz. Die Abfrage soll wortgleich in DuckDB laufen — also nur Standard-SQL.</p>" },
    "start": "SELECT b.branch_name\nFROM fact_orders o\nJOIN dim_branch b USING (branch_id)\n",
    "loesung": "SELECT b.branch_name, count(*) AS bestellungen, round(sum(o.net_total), 2) AS umsatz\nFROM fact_orders o\nJOIN dim_branch b USING (branch_id)\nGROUP BY b.branch_name\nORDER BY umsatz DESC",
    "sortiert": true,
    "hinweis": { "de": "<p><code>USING (branch_id)</code> verbindet gleichnamige Spalten; <code>round(sum(…), 2)</code> rundet die Summe. Gruppieren nach <code>b.branch_name</code>.</p>" },
    "rueckmeldung": { "de": "USING, count(*), round() und GROUP BY sind Standard-SQL — DuckDB und PostgreSQL liefern dieselben fünf Zeilen. Unterschiede beginnen bei Datumsfunktionen und Typnamen." } },

  { "id": "W02-02", "typ": "sql",
    "titel": { "de": "Menge und Umsatz je Kategorie" },
    "aufgabe": { "de": "<p>Aus den Positionen: je <code>category</code> die verkaufte Menge (<code>sum(quantity)</code>) und der Positionsumsatz (<code>sum(line_total)</code>, zwei Stellen), absteigend nach Menge, bei Gleichstand nach Kategorie.</p>" },
    "start": "SELECT p.category\nFROM fact_order_items i\nJOIN dim_product p USING (product_id)\n",
    "loesung": "SELECT p.category, sum(i.quantity) AS menge, round(sum(i.line_total), 2) AS umsatz\nFROM fact_order_items i\nJOIN dim_product p USING (product_id)\nGROUP BY p.category\nORDER BY menge DESC, p.category",
    "sortiert": true,
    "hinweis": { "de": "<p>Mengen entstehen in <code>fact_order_items</code>, die Kategorie steht in <code>dim_product</code>. Zwei Sortierschlüssel: <code>menge DESC, p.category</code>.</p>" },
    "rueckmeldung": { "de": "Getränke führen bei der Menge, Burger beim Umsatz je Stück — das Positionsniveau ist der richtige Grain für Mengen, nicht die Bestellung." } },

  { "id": "W02-03", "typ": "reihenfolge",
    "titel": { "de": "Vom Klon zur eigenen DuckDB-Datei" },
    "aufgabe": { "de": "<p>Bringen Sie die Schritte in die Reihenfolge, in der sie auf einem frischen Rechner nötig sind.</p>" },
    "eintraege": [
      { "id": "install", "text": { "de": "git lfs install — einmal je Rechner" } },
      { "id": "clone", "text": { "de": "git clone https://github.com/swrobuts/BurgerMetrics.git" } },
      { "id": "pruefen", "text": { "de": "ls -lh dataset/fact_orders.csv — 51M, nicht 133 Byte" } },
      { "id": "laden", "text": { "de": "python3 dataset/load_duckdb.py --lokal" } },
      { "id": "abfragen", "text": { "de": "SELECT count(*) FROM fact_orders; — 754513" } }
    ],
    "richtig": ["install", "clone", "pruefen", "laden", "abfragen"],
    "start": ["abfragen", "laden", "clone", "pruefen", "install"],
    "rueckmeldung": { "de": "Die Prüfung mit ls -lh gehört vor das Laden: Wer Zeigerdateien lädt, bekommt eine leere Datenbank ohne Fehlermeldung." } },

  { "id": "W02-04", "typ": "quiz",
    "titel": { "de": "LFS, Parquet und Colab" },
    "aufgabe": { "de": "<p>Drei Fragen zu den Datenwegen.</p>" },
    "fragen": [
      { "frage": { "de": "Eine geklonte fact_orders.csv ist 133 Byte groß und beginnt mit „version https://git-lfs.github.com/spec/v1“. Was ist passiert?" },
        "optionen": [ { "de": "Git LFS war beim Klonen nicht installiert; die Datei ist ein Zeiger" }, { "de": "Die Datei ist auf GitHub gelöscht worden" }, { "de": "Die CSV ist komprimiert und muss entpackt werden" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Ohne LFS-Filter liegt nur der Zeiger auf den Speicher vor. git lfs install, dann git lfs pull holt die Daten nach." } },
      { "frage": { "de": "Was hat Parquet, was CSV nicht hat?" },
        "optionen": [ { "de": "Datentypen je Spalte und Kompression" }, { "de": "Lesbarkeit in jedem Texteditor" }, { "de": "Eine Grenze von 1.048.576 Zeilen" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Parquet speichert spaltenweise mit Typen und komprimiert; fact_orders schrumpft von 51 MB auf 10,7 MB. Die Zeilengrenze gehört zu Excel, die Lesbarkeit zu CSV." } },
      { "frage": { "de": "Warum lesen die Notebooks große Tabellen aus der Datenbank und nicht aus Git LFS?" },
        "optionen": [ { "de": "Jeder Download zählt auf das LFS-Kontingent des Repositorys (10 GiB je Monat)" }, { "de": "Colab kann keine CSV-Dateien lesen" }, { "de": "Die Datenbank ist immer schneller als eine lokale Datei" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Ein Kurs, der 315 MB je Notebook-Lauf zieht, erschöpft das Kontingent nach rund 30 Läufen. lade_csv() ist deshalb auf Dimensionen beschränkt." } }
    ],
    "rueckmeldung": { "de": "Der Weg entscheidet, wer rechnet und wer zahlt: Am Connector rechnet die Datenbank, bei LFS zahlt das Repository die Bandbreite, bei DuckDB rechnet Ihr Rechner." } },

  { "id": "W02-05", "typ": "zuordnen",
    "titel": { "de": "Welches Ziel, welcher Weg" },
    "aufgabe": { "de": "<p>Ordnen Sie jedem Ziel den passenden Weg zu den Daten zu.</p>" },
    "ziele": [ { "id": "connector", "text": { "de": "Connector zur Datenbank (studi_daba)" } }, { "id": "csv", "text": { "de": "CSV-Datei aus dem Export" } }, { "id": "duckdb", "text": { "de": "DuckDB auf den CSV-Dateien" } }, { "id": "parquet", "text": { "de": "Parquet-Datei" } } ],
    "paare": [
      { "begriff": { "de": "Power BI Desktop, Import der Sichten" }, "ziel": "connector" },
      { "begriff": { "de": "Tableau Desktop Public Edition" }, "ziel": "csv" },
      { "begriff": { "de": "Notebook in Colab, lade_sql()" }, "ziel": "connector" },
      { "begriff": { "de": "SQL üben ohne Server, eigene Tabellen anlegen" }, "ziel": "duckdb" },
      { "begriff": { "de": "Abgabe mit erhaltenen Datentypen an ein anderes Team" }, "ziel": "parquet" },
      { "begriff": { "de": "Tableau Desktop mit Live-Verbindung" }, "ziel": "connector" }
    ],
    "rueckmeldung": { "de": "Die Public Edition von Tableau kennt keine Datenbankverbindung — der Export aus Notebook 00 (CSV und Parquet unter notebooks/export/) ist ihr Weg." } }
]
```

Prüfung: W02-01 → 5 Zeilen (`BM Europastern | 7 | 84.75` zuerst); W02-02 → 6 Zeilen (`Drink | 28 | 91.06` zuerst).

---

### Task 5: Lab 03 — Analytisches Datenmodell

**Files:** Create `web/lab/lab-03-datenmodell.html`, `web/lab/data/uebungen/lab-03.json`. Muster-Lab zusätzlich: `WInf-SP/lab-10-etl.html` (Übungen mit `kontrolle`, Aufbau in Schritten).

**Abschnitte:** `frage` — die Frage bestimmt das Modell („Umsatz je Filiale und Jahr“): Kennzahl (Summe `netto_gesamt` nach Rabatt), Auflösung (Filiale, Jahr), Zeitraum; welche Tabellen die Frage braucht und welche nicht. `grain` — was ist eine Zeile: Bestellung (Betrag entsteht dort) gegen Position (Menge entsteht dort); im Bestand 754.513 gegen 2.950.082, im Browser 19 gegen 55; Beispiel Bestellung 457 (31.03.2017, 27,04 €, drei Positionen: Bacon King 2 × 7,99, Sprite 0,3 l 3 × 2,19, Classic Burger 1 × 4,49). `dimensionen` — drei Stammdatentabellen werden eine Dimension: B01 (`CREATE TABLE dim_product_neu AS SELECT … JOIN artikelunterkategorie … JOIN artikelkategorie …`, englische Spaltennamen als Absicht), Denormalisierung ist hier tragbar, weil niemand schreibt. `fakten` — Schlüssel, Maße, degenerierte Dimension (`order_channel`): B02 (`CREATE TABLE fact_orders_neu AS SELECT bestellung_id AS order_id, …`). `sicht` — die Sicht beantwortet die Frage: B03 (`CREATE VIEW v_umsatz_filiale_jahr AS …`), Abgleich mit dem fertigen Schema (in Notebook 01 Differenz 0,00 auf acht Filialen). `fantrap` — B04 (falsch mit JOIN auf Positionen 649,16 € gegen richtig 200,85 €, Faktor 3,23 im Browser; im Bestand 14.692.551 € gegen 2.994.771 €, Faktor 4,9), Regel: auf dem Grain aggregieren, auf dem der Betrag entsteht. `rezensionen` — die dritte Faktentabelle: `fact_reviews` (Grain eine Rezension, fünf Fremdschlüssel, `stars`, `review_text`, `source`), ETL-Weg Shop → `rezension_anlegen()` → `wawi.rezension` → `stg_fact_reviews` → `uebernahme_aus_wawi()` → `fact_reviews` → `v_rezension_produkt`, `etl_probe()` = 0/0/0; im Browser 12 Rezensionen, alle `simulation`. `stolper` — wörtlich: `ERROR:  relation "dim_product_neu" already exists` (zweiter Lauf ohne DROP — im Lab wird vor jeder Prüfung neu gesät), `ERROR:  column "o.net_total" must appear in the GROUP BY clause or be used in an aggregate function`, `ERROR:  cannot execute CREATE TABLE in a read-only transaction` (dieselbe Übung gegen die echte Datenbank), Fan Trap läuft fehlerfrei und ist trotzdem falsch. `spielplatz` (Datenbankband, Konsole `data-start="SELECT * FROM kundenbestellung ORDER BY bestelldatum LIMIT 5;"`), `uebungen`, `zusammenfassung`.

Hinweis im Text: Die Übungen legen Tabellen und Sichten in der Browser-Datenbank an; `CREATE TABLE` ohne Schema landet im ersten Schema des Suchpfads (`wawi`); vor jeder Prüfung sät die Seite neu, deshalb braucht es kein `DROP`.

**Übungen (`lab-03.json`):**

```json
[
  { "id": "W03-01", "typ": "sql",
    "titel": { "de": "Schritt 1: Aus drei Tabellen wird dim_product_neu" },
    "aufgabe": { "de": "<p>Legen Sie mit <code>CREATE TABLE dim_product_neu AS SELECT …</code> eine Dimension an: <code>artikel_id</code> als <code>product_id</code>, <code>name</code> als <code>product_name</code>, den Kategorienamen als <code>category</code>, den Unterkategorienamen als <code>subcategory</code> — aus <code>wawi.artikel</code>, <code>wawi.artikelunterkategorie</code> und <code>wawi.artikelkategorie</code>.</p><p>Geprüft wird: <code>SELECT count(*) AS produkte, count(DISTINCT category) AS kategorien FROM dim_product_neu</code>.</p>" },
    "start": "CREATE TABLE dim_product_neu AS\nSELECT a.artikel_id AS product_id, a.name AS product_name\nFROM wawi.artikel a\n",
    "loesung": "CREATE TABLE dim_product_neu AS\nSELECT a.artikel_id AS product_id, a.name AS product_name, k.name AS category, u.name AS subcategory\nFROM wawi.artikel a\nJOIN wawi.artikelunterkategorie u USING (unterkategorie_id)\nJOIN wawi.artikelkategorie k USING (kategorie_id)",
    "kontrolle": "SELECT count(*) AS produkte, count(DISTINCT category) AS kategorien FROM dim_product_neu",
    "hinweis": { "de": "<p>Zwei Verbunde: <code>artikel → artikelunterkategorie</code> über <code>unterkategorie_id</code>, <code>artikelunterkategorie → artikelkategorie</code> über <code>kategorie_id</code>. Beide Tabellen haben eine Spalte <code>name</code> — mit Alias unterscheiden.</p>" },
    "rueckmeldung": { "de": "31 Produkte, 6 Kategorien. Im operativen Modell war die Kategorie zwei Verbunde entfernt; in der Dimension steht sie neben dem Produkt. Redundanz kostet hier nichts, weil in dim_product niemand schreibt." } },

  { "id": "W03-02", "typ": "sql",
    "titel": { "de": "Schritt 2: Die Faktentabelle fact_orders_neu" },
    "aufgabe": { "de": "<p>Legen Sie <code>fact_orders_neu</code> aus <code>wawi.kundenbestellung</code> an mit den Spalten <code>order_id</code> (aus <code>bestellung_id</code>), <code>date</code> (<code>bestelldatum</code>), <code>branch_id</code> (<code>filiale_id</code>), <code>customer_id</code> (<code>kunde_id</code>), <code>order_channel</code> (<code>bestellkanal</code>) und <code>net_total</code> (<code>netto_gesamt</code>).</p><p>Geprüft wird: <code>SELECT count(*) AS bestellungen, round(sum(net_total), 2) AS umsatz FROM fact_orders_neu</code>.</p>" },
    "start": "CREATE TABLE fact_orders_neu AS\nSELECT bestellung_id AS order_id\nFROM wawi.kundenbestellung\n",
    "loesung": "CREATE TABLE fact_orders_neu AS\nSELECT bestellung_id AS order_id, bestelldatum AS date, filiale_id AS branch_id, kunde_id AS customer_id,\n       bestellkanal AS order_channel, netto_gesamt AS net_total\nFROM wawi.kundenbestellung",
    "kontrolle": "SELECT count(*) AS bestellungen, round(sum(net_total), 2) AS umsatz FROM fact_orders_neu",
    "hinweis": { "de": "<p>Nur umbenennen, nichts verknüpfen: Der Grain bleibt die Bestellung. Schlüssel (branch_id, customer_id), Maß (net_total) und die degenerierte Dimension order_channel bleiben in der Tabelle.</p>" },
    "rueckmeldung": { "de": "19 Bestellungen, 200,85 € — dieselben Zahlen wie in burgermetrics.fact_orders. Die Faktentabelle ist kundenbestellung in anderer Gestalt; jede Spalte hat jetzt eine Rolle." } },

  { "id": "W03-03", "typ": "sql",
    "titel": { "de": "Schritt 3: Die Sicht, die die Frage beantwortet" },
    "aufgabe": { "de": "<p>Legen Sie die Sicht <code>v_umsatz_filiale_jahr</code> an: je Filiale (<code>f.name</code> als <code>filiale</code>) und Jahr (<code>extract(year FROM bestelldatum)::int</code> als <code>jahr</code>) die Zahl der Bestellungen (<code>bestellungen</code>) und den Umsatz (<code>round(sum(netto_gesamt), 2)</code> als <code>umsatz</code>) — aus <code>wawi.kundenbestellung</code> und <code>wawi.filiale</code>.</p><p>Geprüft wird: <code>SELECT * FROM v_umsatz_filiale_jahr ORDER BY jahr, filiale</code>.</p>" },
    "start": "CREATE VIEW v_umsatz_filiale_jahr AS\nSELECT f.name AS filiale\nFROM wawi.kundenbestellung o\nJOIN wawi.filiale f USING (filiale_id)\n",
    "loesung": "CREATE VIEW v_umsatz_filiale_jahr AS\nSELECT f.name AS filiale, extract(year FROM o.bestelldatum)::int AS jahr,\n       count(*) AS bestellungen, round(sum(o.netto_gesamt), 2) AS umsatz\nFROM wawi.kundenbestellung o\nJOIN wawi.filiale f USING (filiale_id)\nGROUP BY 1, 2",
    "kontrolle": "SELECT * FROM v_umsatz_filiale_jahr ORDER BY jahr, filiale",
    "hinweis": { "de": "<p><code>GROUP BY 1, 2</code> gruppiert nach den ersten beiden Spalten der Auswahl. <code>::int</code> macht aus dem Jahr eine ganze Zahl.</p>" },
    "rueckmeldung": { "de": "15 Zeilen: Filiale und Jahr sind der Grain der Antwort. In Notebook 01 liefert dieselbe Sicht auf dem ganzen Bestand acht Zeilen für 2025, zeilengleich mit burgermetrics — Differenz 0,00." } },

  { "id": "W03-04", "typ": "sql",
    "titel": { "de": "Die Fan Trap nachrechnen" },
    "aufgabe": { "de": "<p>Berechnen Sie in einer Abfrage zwei Spalten: <code>mit_join</code> = <code>sum(o.net_total)</code> über <code>fact_orders o JOIN fact_order_items i USING (order_id)</code>, und <code>ohne_join</code> = <code>sum(net_total)</code> aus <code>fact_orders</code> allein (als Unterabfrage). Beide auf zwei Stellen gerundet.</p>" },
    "start": "SELECT round(sum(o.net_total), 2) AS mit_join\nFROM fact_orders o\n",
    "loesung": "SELECT round(sum(o.net_total), 2) AS mit_join,\n       (SELECT round(sum(net_total), 2) FROM fact_orders) AS ohne_join\nFROM fact_orders o\nJOIN fact_order_items i USING (order_id)",
    "hinweis": { "de": "<p>Die Unterabfrage <code>(SELECT round(sum(net_total), 2) FROM fact_orders)</code> steht als zweite Spalte in der Auswahlliste.</p>" },
    "rueckmeldung": { "de": "649,16 € gegen 200,85 € — jede Bestellung wird so oft gezählt, wie sie Positionen hat. Die Abfrage läuft fehlerfrei; erst die zweite Rechnung zeigt den Fehler. Im Bestand: 14.692.551 € gegen 2.994.771 €." } },

  { "id": "W03-05", "typ": "quiz",
    "titel": { "de": "Grain, Denormalisierung, ETL" },
    "aufgabe": { "de": "<p>Drei Fragen zum Modell.</p>" },
    "fragen": [
      { "frage": { "de": "Welche Kennzahl gehört auf den Grain der Position?" },
        "optionen": [ { "de": "Die verkaufte Menge je Produkt" }, { "de": "Der Bestellwert nach Rabatt" }, { "de": "Die Bestelldauer" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Mengen entstehen je Position; Bestellwert und Bestelldauer entstehen je Bestellung und gehören nach fact_orders." } },
      { "frage": { "de": "Warum ist die Redundanz in dim_product tragbar, im operativen Modell aber nicht?" },
        "optionen": [ { "de": "In der Auswertung schreibt niemand; Änderungen laufen über den nächtlichen Abzug" }, { "de": "Weil Dimensionstabellen klein sind" }, { "de": "Weil PostgreSQL Redundanz automatisch bereinigt" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Redundanz kostet Konsistenz nur beim Schreiben. Die Größe ist kein Argument, und PostgreSQL bereinigt nichts von selbst." } },
      { "frage": { "de": "Welche Funktion übernimmt neue Shop-Rezensionen aus wawi.rezension nach fact_reviews?" },
        "optionen": [ { "de": "burgermetrics.uebernahme_aus_wawi()" }, { "de": "wawi.rezension_anlegen()" }, { "de": "wawi.etl_probe()" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "rezension_anlegen() schreibt die Rezension operativ, etl_probe() vergleicht beide Seiten; die Übernahme macht uebernahme_aus_wawi() — bewusst aufgerufen, nicht automatisch." } }
    ],
    "rueckmeldung": { "de": "Vier Entscheidungen in fester Reihenfolge — Frage, Grain, Dimensionen, Fakten — und eine Sicht, die den Nachweis liefert. Die Rezensionen laufen denselben Weg wie die Bestellungen." } }
]
```

Prüfung mit `node tools/sql.mjs "<loesung>; <kontrolle>"`: W03-01 → `31 | 6`; W03-02 → `19 | 200.85`; W03-03 → 15 Zeilen, erste `BM Europastern | 2017 | 2 | 19.84`; W03-04 → `649.16 | 200.85`.

---

### Task 6: Lab 04 — Power BI

**Files:** Create `web/lab/lab-04-powerbi.html`, `web/lab/data/uebungen/lab-04.json`, `web/lab/vorlagen/powerbi-measures.dax`. Muster-Lab: `WInf-SP/lab-12-powerbi.html` + `lab-12.json` (Struktur, Nachbildungen, Regal-Übungen — Inhalt auf BurgerMetrics übertragen, Velo City ersetzen).

**Abschnitte:** `warum` — was Power BI hier leistet (Modell mit Beziehungen, Measures, Bericht) und was nicht (Kennzahldefinition gehört in die Sicht, Lab 01). `begriffe` — Import gegen DirectQuery (Import kopiert in den Speicher; DirectQuery fragt bei jedem Bild, Grenze 1.000.000 Zeilen je Ergebnis; Microsoft empfiehlt Import; Stand 09/2026), Beziehung (Kardinalität *:1, Filterrichtung), Measure gegen berechnete Spalte, Filterkontext. `verbinden` — Start → Daten abrufen → PostgreSQL-Datenbank, Server `supabase.butscher.cloud:5433`, Datenbank `postgres`, Authentifizierung Datenbank; Npgsql seit 12/2019 eingebaut; Nachbildung 1: Navigator mit den Ordnern `burgermetrics` und `wawi` und angehakten `dim_*`/`fact_*`; Befehlskarte B01 (Klickweg 🖱). `modell` — Option „Beziehungen aus Datenquellen beim ersten Laden importieren“ (Standard an): 13 Fremdschlüssel werden 13 Beziehungen (5 an `fact_orders`, 2 an `fact_order_items`, 5 an `fact_reviews`, `dim_employee → dim_branch`); von Hand: Kreis `fact_reviews → fact_orders → dim_date` (eine Beziehung inaktiv, das Datum direkt bleibt aktiv), `dim_weather`/`dim_time_slot` ohne Fremdschlüssel; `obt_orders` nicht laden; Nachbildung 2: Modellansicht (Stern um `fact_orders`). `dax` — B02 Measures: `Umsatz = SUM(fact_orders[net_total])`, `Bestellungen = COUNTROWS(fact_orders)`, `Bestellwert = DIVIDE([Umsatz], [Bestellungen])`, `Ø Sterne = AVERAGE(fact_reviews[stars])`, `Umsatz 2025 = CALCULATE([Umsatz], dim_date[year] = 2025)`; Kontrollzahl 2.994.771,13 € für 2025; Vorlage `powerbi-measures.dax`. `bericht` — Kacheln (Umsatz, Bestellungen, Bestellwert, Ø Sterne), Balken Umsatz je Filiale, Linie je Monat; Regeln aus dem Deck (Nullpunkt bei Balken, Aussagentitel). `stolper` — wörtlich/verhaltensgetreu: „Wir können keine Verbindung herstellen … Npgsql“ (alte Desktop-Version vor 12/2019 → aktualisieren), Summe in jeder Zeile gleich (Beziehung fehlt), Measure auf zusammengeführter Tabelle = Fan Trap (14,7 statt 3,0 Mio.), DirectQuery auf `fact_order_items` scheitert an der Zeilengrenze, zwanzig Sitzungen der Rolle im Hörsaal. `simulator` — `<div data-regal="frei" data-variante="powerbi"></div>` (Spielplatz), Erklärung der Felder. `uebungen`, `zusammenfassung`.

**Regal-Definition (`regal` im JSON, in Lab 05 identisch):**

```json
"regal": {
  "daten": "data/regal-bestellungen.json",
  "felder": [
    { "id": "monat", "typ": "dimension", "geordnet": true, "titel": { "de": "Monat" }, "reihenfolge": ["2025-01","2025-02","2025-03","2025-04","2025-05","2025-06","2025-07","2025-08","2025-09","2025-10","2025-11","2025-12"] },
    { "id": "wochentag", "typ": "dimension", "titel": { "de": "Wochentag" }, "reihenfolge": ["Mo","Di","Mi","Do","Fr","Sa","So"] },
    { "id": "stunde", "typ": "dimension", "geordnet": true, "titel": { "de": "Stunde" }, "reihenfolge": [6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23] },
    { "id": "filiale", "typ": "dimension", "titel": { "de": "Filiale" } },
    { "id": "kanal", "typ": "dimension", "titel": { "de": "Kanal" } },
    { "id": "zahlart", "typ": "dimension", "titel": { "de": "Zahlart" } },
    { "id": "loyalty", "typ": "dimension", "titel": { "de": "Loyalty-Stufe" } },
    { "id": "saison", "typ": "dimension", "titel": { "de": "Saison" } },
    { "id": "order_id", "typ": "kennzahl", "titel": { "de": "Bestell-ID" }, "erklaerung": { "de": "Eine Kennung — Σ darüber ist die klassische Falle. COUNT zählt Bestellungen." } },
    { "id": "umsatz", "typ": "kennzahl", "titel": { "de": "Umsatz (€)" } },
    { "id": "positionen", "typ": "kennzahl", "titel": { "de": "Positionen" } },
    { "id": "zufriedenheit", "typ": "kennzahl", "titel": { "de": "Zufriedenheit" }, "erklaerung": { "de": "Nur bewertete Bestellungen tragen einen Wert; AVG ignoriert die Lücken." } }
  ]
},
"spielplaetze": { "frei": { "variante": "powerbi", "startBelegung": { "spalten": [], "zeilen": [], "farbe": null, "filter": {} } } }
```

**Übungen (`lab-04.json`):**

```json
[
  { "id": "W04-01", "typ": "regal", "variante": "powerbi",
    "titel": { "de": "Umsatz je Filiale als Balken" },
    "aufgabe": { "de": "<p>Legen Sie <strong>Filiale</strong> auf die Spalten und die <strong>Summe des Umsatzes</strong> auf die Zeilen. Es entsteht ein senkrechtes Balkendiagramm mit acht Balken.</p>" },
    "ziel": { "spalten": ["filiale"], "zeilen": ["SUM:umsatz"] },
    "loesungBelegung": { "spalten": ["filiale"], "zeilen": [ { "feld": "umsatz", "agg": "SUM" } ], "farbe": null, "filter": {} },
    "rueckmeldung": { "de": "Dimension auf Spalten, Kennzahl auf Zeilen — die Grundform jedes Vergleichs. Der Nullpunkt bleibt sichtbar, weil Länge den Wert kodiert." } },

  { "id": "W04-02", "typ": "regal", "variante": "powerbi",
    "titel": { "de": "Bestellungen je Monat — zählen, nicht summieren" },
    "aufgabe": { "de": "<p>Legen Sie <strong>Monat</strong> auf die Spalten und die <strong>Bestell-ID</strong> auf die Zeilen — aber mit <strong>COUNT</strong>, nicht mit SUM. Eine Kennung wird gezählt, nicht addiert. Es entsteht eine Linie über zwölf Monate.</p>" },
    "ziel": { "spalten": ["monat"], "zeilen": ["COUNT:order_id"] },
    "loesungBelegung": { "spalten": ["monat"], "zeilen": [ { "feld": "order_id", "agg": "COUNT" } ], "farbe": null, "filter": {} },
    "rueckmeldung": { "de": "Power BI schlägt für jede Zahlenspalte die Summe vor — auch für Kennungen. Die Summe der Bestellnummern ist eine Zahl ohne Bedeutung; COUNTROWS(fact_orders) ist das richtige Measure." } },

  { "id": "W04-03", "typ": "quiz",
    "titel": { "de": "Import, Beziehungen, Measures" },
    "aufgabe": { "de": "<p>Drei Fragen zum Modell in Power BI.</p>" },
    "fragen": [
      { "frage": { "de": "Warum gilt für den Kurs Import statt DirectQuery?" },
        "optionen": [ { "de": "Import rechnet aus dem Speicher; DirectQuery schickt je Bild Abfragen an die Datenbank, die nur zwanzig Sitzungen der Rolle hält" }, { "de": "DirectQuery kann keine PostgreSQL-Datenbank lesen" }, { "de": "Import ist die einzige Möglichkeit, Beziehungen anzulegen" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Beide Modi lesen PostgreSQL und beide kennen Beziehungen. Der Unterschied ist, wo gerechnet wird — und ein Hörsaal mit DirectQuery-Berichten belegt die zwanzig Sitzungen in Minuten." } },
      { "frage": { "de": "Nach dem Laden steht in einem Balkendiagramm „Umsatz je Filiale“ in jeder Filiale derselbe Wert. Was fehlt?" },
        "optionen": [ { "de": "Die Beziehung zwischen fact_orders und dim_branch" }, { "de": "Ein Filter auf das Jahr 2025" }, { "de": "Die Materialisierung der Sicht" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Ohne Beziehung kann die Dimension die Fakten nicht filtern; jede Zeile zeigt die Gesamtsumme. Das ist das Bild, an dem man eine fehlende Beziehung erkennt." } },
      { "frage": { "de": "Welche Angaben werden beim ersten Laden zu Beziehungen?" },
        "optionen": [ { "de": "Die Fremdschlüssel der Datenbank — 13 in burgermetrics" }, { "de": "Alle Spalten mit gleichem Namen, auch ohne Fremdschlüssel" }, { "de": "Nur die Beziehungen, die man von Hand anlegt" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Die Option „Beziehungen aus Datenquellen beim ersten Laden importieren“ spiegelt die Fremdschlüssel. dim_weather und dim_time_slot haben keinen und brauchen Handarbeit." } }
    ],
    "rueckmeldung": { "de": "Import, Beziehungen aus Fremdschlüsseln, Measures statt Spalten — drei Entscheidungen, die den Bericht tragen." } },

  { "id": "W04-04", "typ": "zuordnen",
    "titel": { "de": "DAX-Ausdruck und Zweck" },
    "aufgabe": { "de": "<p>Ordnen Sie jeden Ausdruck seinem Zweck zu.</p>" },
    "ziele": [ { "id": "summe", "text": { "de": "Summe einer Spalte" } }, { "id": "zaehlen", "text": { "de": "Zeilen zählen" } }, { "id": "teilen", "text": { "de": "Quotient ohne Fehler bei null" } }, { "id": "mittel", "text": { "de": "Mittelwert einer Spalte" } }, { "id": "filter", "text": { "de": "Measure unter geändertem Filter" } } ],
    "paare": [
      { "begriff": { "de": "SUM(fact_orders[net_total])" }, "ziel": "summe" },
      { "begriff": { "de": "COUNTROWS(fact_orders)" }, "ziel": "zaehlen" },
      { "begriff": { "de": "DIVIDE([Umsatz], [Bestellungen])" }, "ziel": "teilen" },
      { "begriff": { "de": "AVERAGE(fact_reviews[stars])" }, "ziel": "mittel" },
      { "begriff": { "de": "CALCULATE([Umsatz], dim_date[year] = 2025)" }, "ziel": "filter" },
      { "begriff": { "de": "COUNT(fact_reviews[review_id])" }, "ziel": "zaehlen" }
    ],
    "rueckmeldung": { "de": "DIVIDE statt „/“ verhindert den Fehler bei null Bestellungen; CALCULATE ändert den Filterkontext — das Werkzeug hinter jeder Kennzahl „für 2025“." } },

  { "id": "W04-05", "typ": "checkliste",
    "titel": { "de": "Der Bericht in Power BI Desktop" },
    "aufgabe": { "de": "<p>In Power BI Desktop (Windows; Update August 2026 oder neuer) gegen die Datenbank der Fallstudie. Jeder Schritt endet mit einer Prüfung.</p>" },
    "schritte": [
      { "text": { "de": "Start → Daten abrufen → PostgreSQL-Datenbank; Server <code>supabase.butscher.cloud:5433</code>, Datenbank <code>postgres</code>, Modus Import; Warnung zur unverschlüsselten Verbindung mit OK bestätigt." } },
      { "text": { "de": "Authentifizierung Datenbank mit <code>studi_daba</code> / <code>thws</code>; der Navigator zeigt die Ordner <code>burgermetrics</code> und <code>wawi</code>." } },
      { "text": { "de": "Aus <code>burgermetrics</code> geladen: <code>dim_branch</code>, <code>dim_date</code>, <code>dim_product</code>, <code>dim_customer</code>, <code>fact_orders</code>, <code>fact_order_items</code>, <code>fact_reviews</code> — <code>obt_orders</code> nicht." } },
      { "text": { "de": "Modellansicht: <code>fact_orders</code> hat Linien zu <code>dim_branch</code>, <code>dim_date</code>, <code>dim_customer</code>; zwischen <code>fact_reviews</code> und <code>fact_orders</code>/<code>dim_date</code> ist eine Beziehung gestrichelt (inaktiv) — die direkte zum Datum bleibt aktiv." } },
      { "text": { "de": "Measures angelegt: <code>Umsatz</code>, <code>Bestellungen</code>, <code>Bestellwert</code>, <code>Ø Sterne</code> (Vorlage <code>powerbi-measures.dax</code>)." } },
      { "text": { "de": "Kachel mit <code>Umsatz</code> und Filter <code>dim_date[year] = 2025</code> zeigt <code>2.994.771,13 €</code>; Kachel <code>Bestellungen</code> zeigt <code>136.557</code>." } },
      { "text": { "de": "Balkendiagramm Umsatz je <code>branch_name</code>: acht verschieden hohe Balken, BM Europastern vorn — keine gleichen Werte in jeder Zeile." } }
    ],
    "rueckmeldung": { "de": "Der letzte Schritt ist die Probe auf die Beziehungen. Stimmen 2.994.771,13 € und 136.557, liest der Bericht dieselben Zahlen wie das Dashboard und die Notebooks." } }
]
```

---

### Task 7: Lab 05 — Tableau

**Files:** Create `web/lab/lab-05-tableau.html`, `web/lab/data/uebungen/lab-05.json`, `web/lab/vorlagen/tableau-berechnete-felder.txt`. Muster-Lab: `WInf-SP/lab-13-tableau.html` + `lab-13.json` (auf BurgerMetrics übertragen). `regal`-Block wie in Task 6, `spielplaetze.frei` mit `"variante": "tableau"`.

**Abschnitte:** `warum` — Tableau als zweites Werkzeug auf derselben Sicht; Ergebnis muss dasselbe sein. `begriffe` — Dimension und Measure (blau/grün), diskret und stetig, Live gegen Extract (`.hyper`: schneller, offline, Funktionen), Level of Detail. `verbinden` — Connect → To a Server → PostgreSQL: Server, Port 5433, Database, Username/Password, „Require SSL“ aus; Treiber erforderlich (Tableau verweist auf den Download); Tableau Desktop 2026.2 (27.08.2026); Public Edition kennt keine Datenbank (Dateien, Google Drive, OData; 15 Mio. Zeilen je Arbeitsmappe) → Weg über die CSV aus `notebooks/export/`; Studentenlizenz seit 01.02.2025 eingestellt (Stand 09/2026); Nachbildung 1: Data-Source-Seite mit Live/Extract-Schalter und den Tabellen `fact_orders` + `dim_branch`. `regal` — Columns/Rows/Marks/Filters; Nachbildung 2: Arbeitsblatt mit Regalen; Regel: Dimension auf Columns + Measure auf Rows = Balken, geordnete Dimension = Linie. `berechnen` — Calculated Fields: `[Bestellwert] = SUM([Net Total]) / COUNT([Order Id])`, `[Ø Sterne] = AVG([Stars])`, LOD `{ FIXED [Branch Name] : SUM([Net Total]) }`; Vorlage `tableau-berechnete-felder.txt`; Initial SQL `SET search_path TO burgermetrics, wawi`. `dashboard` — zwei Blätter, ein Filter (Jahr), Titel als Aussage. `stolper` — Live-Verbindung mit `studi_daba`: `ERROR:  cannot execute CREATE TABLE in a read-only transaction` — Tableau legt für manche Filter und Extrakte temporäre Tabellen an; die Rolle erlaubt das nicht; Abhilfe: Extract erzeugen oder den Filter als Datenquellenfilter setzen (Stand 09/2026, Meldung wörtlich aus PostgreSQL; ob Tableau sie zeigt, hängt von Version und Vorgang ab); Summe je Zeile gleich = fehlende Beziehung; Dimension auf Rows ergibt Tabelle statt Balken; `SUM(Order Id)` als Falle. `simulator` — `<div data-regal="frei" data-variante="tableau"></div>`. `uebungen`, `zusammenfassung`.

**Übungen (`lab-05.json`):**

```json
[
  { "id": "W05-01", "typ": "regal", "variante": "tableau",
    "titel": { "de": "Umsatz je Monat als Linie" },
    "aufgabe": { "de": "<p>Legen Sie <strong>Monat</strong> auf Columns und <strong>SUM(Umsatz)</strong> auf Rows. Weil der Monat geordnet ist, entsteht eine Linie.</p>" },
    "ziel": { "spalten": ["monat"], "zeilen": ["SUM:umsatz"] },
    "loesungBelegung": { "spalten": ["monat"], "zeilen": [ { "feld": "umsatz", "agg": "SUM" } ], "farbe": null, "filter": {} },
    "rueckmeldung": { "de": "Eine geordnete Dimension (Monat, Stunde) auf Columns ergibt eine Linie — in Tableau eine stetige Achse. Bei Filialen wäre es ein Balken: dort gibt es keine Reihenfolge." } },

  { "id": "W05-02", "typ": "regal", "variante": "tableau",
    "titel": { "de": "Zufriedenheit je Filiale im Sommer" },
    "aufgabe": { "de": "<p>Legen Sie <strong>Filiale</strong> auf Rows und <strong>AVG(Zufriedenheit)</strong> auf Columns — waagerechte Balken — und filtern Sie auf <strong>Saison = Summer</strong>.</p>" },
    "ziel": { "zeilen": ["filiale"], "spalten": ["AVG:zufriedenheit"], "filter": { "saison": ["Summer"] } },
    "loesungBelegung": { "spalten": [ { "feld": "zufriedenheit", "agg": "AVG" } ], "zeilen": ["filiale"], "farbe": null, "filter": { "saison": ["Summer"] } },
    "rueckmeldung": { "de": "AVG statt SUM: Zufriedenheit ist ein Wert je bewerteter Bestellung, keine Summe. Nur 451 der 2.000 Bestellungen tragen eine Bewertung — AVG ignoriert die Lücken, SUM würde sie verschweigen." } },

  { "id": "W05-03", "typ": "quiz",
    "titel": { "de": "Live, Extract, Public" },
    "aufgabe": { "de": "<p>Drei Fragen zur Verbindung.</p>" },
    "fragen": [
      { "frage": { "de": "Was speichert ein Extract?" },
        "optionen": [ { "de": "Einen Auszug der Daten als .hyper-Datei, der ohne Datenbank funktioniert" }, { "de": "Nur die Verbindungsdaten" }, { "de": "Das Dashboard als Bild" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Ein Extract ist eine Kopie mit Verfallsdatum: schneller, offline, mit Funktionen, die die Quelle nicht hat — und veraltet ab dem Moment, in dem er geschrieben ist." } },
      { "frage": { "de": "Wie kommt Tableau Desktop Public Edition an die Daten der Fallstudie?" },
        "optionen": [ { "de": "Über die CSV-Dateien aus notebooks/export/ — die Public Edition kennt keine Datenbankverbindung" }, { "de": "Über den PostgreSQL-Connector mit studi_daba" }, { "de": "Gar nicht" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Die Public Edition liest Dateien, Google Drive und OData, bis 15 Millionen Zeilen je Arbeitsmappe. Notebook 00 exportiert vier Sichten als CSV und Parquet." } },
      { "frage": { "de": "Eine Live-Verbindung mit studi_daba meldet „cannot execute CREATE TABLE in a read-only transaction“. Was ist die Ursache?" },
        "optionen": [ { "de": "Tableau will eine temporäre Tabelle anlegen; die Rolle darf nicht schreiben" }, { "de": "Das Kennwort ist falsch" }, { "de": "Die Datenbank ist voll" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Die Meldung stammt von PostgreSQL: Die Transaktion der Rolle ist nur lesend. Ein Extract oder ein Datenquellenfilter umgeht den Vorgang." } }
    ],
    "rueckmeldung": { "de": "Live fragt, Extract kopiert, Public liest Dateien — und die Rolle bleibt in allen drei Fällen nur lesend." } },

  { "id": "W05-04", "typ": "reihenfolge",
    "titel": { "de": "Vom Connector zum Dashboard" },
    "aufgabe": { "de": "<p>Bringen Sie die Schritte in die Reihenfolge, in der ein Dashboard entsteht.</p>" },
    "eintraege": [
      { "id": "verbinden", "text": { "de": "Connect → PostgreSQL, Server, Port 5433, studi_daba" } },
      { "id": "extract", "text": { "de": "Extract erzeugen (.hyper) — oder Live behalten" } },
      { "id": "blatt1", "text": { "de": "Blatt 1: Monat auf Columns, SUM(Net Total) auf Rows" } },
      { "id": "blatt2", "text": { "de": "Blatt 2: Branch Name auf Rows, SUM(Net Total) auf Columns" } },
      { "id": "dashboard", "text": { "de": "Dashboard aus beiden Blättern, Filter Jahr als Steuerung" } },
      { "id": "titel", "text": { "de": "Titel als Aussage formulieren und speichern" } }
    ],
    "richtig": ["verbinden", "extract", "blatt1", "blatt2", "dashboard", "titel"],
    "start": ["titel", "dashboard", "blatt2", "blatt1", "extract", "verbinden"],
    "rueckmeldung": { "de": "Erst die Datenquelle, dann die Blätter, dann das Dashboard — und der Titel zuletzt, weil er die Antwort nennt, nicht die Frage." } },

  { "id": "W05-05", "typ": "checkliste",
    "titel": { "de": "Ein Dashboard in Tableau Desktop oder Public Edition" },
    "aufgabe": { "de": "<p>Mit Tableau Desktop (Connector) oder der Public Edition (CSV aus <code>notebooks/export/</code>). Jeder Schritt endet mit einer Prüfung.</p>" },
    "schritte": [
      { "text": { "de": "Datenquelle angebunden: PostgreSQL mit <code>studi_daba</code> (Desktop) oder <code>v_umsatz_monat.csv</code> und <code>v_filiale.csv</code> aus <code>notebooks/export/</code> (Public Edition)." } },
      { "text": { "de": "Bei Live-Verbindung: Initial SQL <code>SET search_path TO burgermetrics, wawi</code> gesetzt, damit Sichten ohne Präfix gefunden werden." } },
      { "text": { "de": "Blatt „Umsatz je Monat“: Monat (stetig) auf Columns, SUM(Umsatz) auf Rows — eine Linie über 109 Monate." } },
      { "text": { "de": "Blatt „Umsatz je Filiale“: Filiale auf Rows, SUM(Umsatz) auf Columns — acht Balken, sortiert absteigend." } },
      { "text": { "de": "Berechnetes Feld <code>Bestellwert</code> = SUM([Umsatz]) / SUM([Bestellungen]) angelegt (Vorlage <code>tableau-berechnete-felder.txt</code>)." } },
      { "text": { "de": "Dashboard mit beiden Blättern; Jahr als Filter, der beide Blätter steuert; Titel nennt die Aussage." } },
      { "text": { "de": "Kontrollzahl: Umsatz 2025 im Dashboard = <code>2.994.771,13 €</code>." } }
    ],
    "rueckmeldung": { "de": "Wenn die Kontrollzahl stimmt, liest Tableau dieselbe Sicht wie Power BI und das Dashboard der Fallstudie — das Werkzeug ist austauschbar, die Definition nicht." } }
]
```

---

### Task 8: Lab 06 — Python und Colab

**Files:** Create `web/lab/lab-06-python.html`, `web/lab/data/uebungen/lab-06.json`, `web/lab/vorlagen/notebook-verbindungszelle.py`, `web/lab/vorlagen/verbindung-sqlalchemy.py`. Muster-Lab: `WInf-SP/lab-04-colab.html` + `lab-04.json` (Runtime, Reihenfolge, Geheimnisse — auf BurgerMetrics übertragen). Quelle für die Zellen: `notebooks/quellen/gemeinsam.py` und `notebooks/00_zugang_und_daten.ipynb` (Colab-Link, pip-Zelle, Verbindungszelle, `zahl()`).

**Abschnitte:** `warum` — ein Notebook ist Lehrmaterial nur, wenn es von oben nach unten durchläuft; die neun Notebooks der Fallstudie tun das (`notebooks/pruefe_notebooks.sh`). `runtime` — Colab: Runtime, Sitzung, „Runtime → Restart“, Zustand geht verloren; pip-Zelle mit `%pip install -q …` und der Meldung „Note: you may need to restart the kernel“; Nachbildung 1: Colab-Notebook mit Zellen `[1]`/`[2]` (`.zelle`/`.ausgabe`). `verbindung` — die Verbindungszelle (B01: `VERBINDUNG = "postgresql+psycopg2://studi_daba:thws@supabase.butscher.cloud:5433/postgres"`, `create_engine`, `lade_sql(sql)` mit `pd.read_sql`, `lade_csv(name)` über `media.githubusercontent.com/media/swrobuts/BurgerMetrics/main/dataset/`), Vorlagen `notebook-verbindungszelle.py` und `verbindung-sqlalchemy.py` (dasselbe für ein lokales Skript mit `.env`). `pandas` — `read_sql` liefert DataFrames; die Datenbank aggregiert, Python zeigt: eine Sicht mit zehn Zeilen kommt in Millisekunden, 2,95 Mio. Positionen holt niemand nach Colab; B02 (`lade_sql("SELECT jahr, bestellungen, umsatz FROM v_kennzahlen_jahr ORDER BY jahr")`, `tail(3)` → 2024 133.307 · 2.841.074,88, 2025 136.557 · 2.994.771,13, 2026 31.080 · 698.673,81). `dash` — die Dash-App inline (Notebook 00, `DASH_STARTEN = True` in Colab; lokal `python dash/app.py` → `http://127.0.0.1:8050`), vier Karten aus vier Sichten. `geheim` — Zugangsdaten nie ins Repository: das Demo-Konto ist die bewusste Ausnahme (öffentlich, nur lesend); eigene Konten in Colab-Secrets (`from google.colab import userdata`), lokal `.env` + `.gitignore`; B03 (`.env`-Zeile, `os.environ`, `.gitignore`-Eintrag). `stolper` — wörtlich: `Note: you may need to restart the kernel to use updated packages.` (Colab nach pip), `OperationalError: … could not connect to server` bei Tippfehler im Host, `canceling statement due to statement timeout` nach zehn Minuten, LFS-Zeiger statt Daten bei `raw.githubusercontent.com`, `TypeError`/`NotImplementedError` beim `register()` von pandas-3-Textspalten in DuckDB 1.4 (Helfer `fuer_duckdb()`). `uebungen`, `zusammenfassung`. Keine Datenbankübung auf dieser Seite (kein `data-datenbank`).

**Übungen (`lab-06.json`):**

```json
[
  { "id": "W06-01", "typ": "quiz",
    "titel": { "de": "Runtime und Reihenfolge" },
    "aufgabe": { "de": "<p>Drei Fragen zu Colab.</p>" },
    "fragen": [
      { "frage": { "de": "Nach „Runtime → Restart runtime“ sind Variablen und installierte Pakete …" },
        "optionen": [ { "de": "weg — Zellen werden von oben neu ausgeführt" }, { "de": "erhalten, nur die Ausgaben verschwinden" }, { "de": "in Google Drive gespeichert" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Die Runtime ist eine Sitzung; ein Neustart löscht ihren Zustand. Deshalb steht die pip-Zelle oben und die Verbindungszelle direkt darunter." } },
      { "frage": { "de": "Warum steht in jedem Notebook der Fallstudie dieselbe Verbindungszelle?" },
        "optionen": [ { "de": "Damit jedes Notebook allein und von oben nach unten läuft" }, { "de": "Weil Colab nur eine Verbindung je Notebook erlaubt" }, { "de": "Weil pandas sonst keine Datenbank lesen kann" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Ein Notebook, das eine Zelle aus einem anderen braucht, läuft nirgends reproduzierbar. lade_sql() und lade_csv() sind je Notebook definiert." } },
      { "frage": { "de": "Was tut lade_sql(\"SELECT … FROM v_kennzahlen_jahr\") in Colab?" },
        "optionen": [ { "de": "Die Datenbank rechnet, pandas erhält zehn fertige Zeilen als DataFrame" }, { "de": "Colab lädt fact_orders und rechnet selbst" }, { "de": "Die Sicht wird nach Colab kopiert" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "read_sql schickt die Abfrage an PostgreSQL und nimmt das Ergebnis entgegen. Große Tabellen bleiben, wo sie sind." } }
    ],
    "rueckmeldung": { "de": "Von oben nach unten, jede Zelle mit Zweck, die Datenbank rechnet — so bleiben die Notebooks in Colab wie lokal lauffähig." } },

  { "id": "W06-02", "typ": "quiz",
    "titel": { "de": "Zugangsdaten" },
    "aufgabe": { "de": "<p>Zwei Fragen zu Geheimnissen.</p>" },
    "fragen": [
      { "frage": { "de": "Warum darf studi_daba/thws im Notebook stehen?" },
        "optionen": [ { "de": "Das Konto ist absichtlich öffentlich, nur lesend, der Bestand synthetisch" }, { "de": "Weil GitHub Zugangsdaten automatisch verbirgt" }, { "de": "Weil Colab-Notebooks privat sind" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Die Ausnahme gilt nur für dieses Demo-Konto. Jedes eigene Konto gehört in Colab-Secrets oder eine .env-Datei, die in .gitignore steht." } },
      { "frage": { "de": "Wo liegt ein eigenes Datenbankkennwort in Colab richtig?" },
        "optionen": [ { "de": "Im Secrets-Panel, gelesen mit userdata.get()" }, { "de": "In einer Codezelle als Zeichenkette" }, { "de": "Im Dateinamen des Notebooks" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Secrets bleiben beim Konto und wandern nicht mit dem Notebook nach GitHub. Eine Zeichenkette in der Zelle steht nach dem ersten Commit für immer in der Historie." } }
    ],
    "rueckmeldung": { "de": "Ein Kennwort im Repository lässt sich nicht zurückholen — nur ändern. Das Demo-Konto ist die eine Ausnahme, und sie ist als solche dokumentiert." } },

  { "id": "W06-03", "typ": "zuordnen",
    "titel": { "de": "Zelle und Zweck" },
    "aufgabe": { "de": "<p>Ordnen Sie jede Zelle der Fallstudien-Notebooks ihrem Zweck zu.</p>" },
    "ziele": [ { "id": "pakete", "text": { "de": "Pakete bereitstellen" } }, { "id": "verbindung", "text": { "de": "Verbindung und Ladehelfer" } }, { "id": "ausgabe", "text": { "de": "deutsche Zahlen in Ausgaben" } }, { "id": "analyse", "text": { "de": "Daten holen und auswerten" } } ],
    "paare": [
      { "begriff": { "de": "%pip install -q sqlalchemy psycopg2-binary duckdb …" }, "ziel": "pakete" },
      { "begriff": { "de": "engine = create_engine(VERBINDUNG)" }, "ziel": "verbindung" },
      { "begriff": { "de": "def lade_csv(name): … media.githubusercontent.com …" }, "ziel": "verbindung" },
      { "begriff": { "de": "def zahl(wert, nachkommastellen=0): …" }, "ziel": "ausgabe" },
      { "begriff": { "de": "jahre = lade_sql(\"SELECT … FROM v_kennzahlen_jahr\")" }, "ziel": "analyse" },
      { "begriff": { "de": "con.register(\"dim_branch\", fuer_duckdb(filialen))" }, "ziel": "analyse" }
    ],
    "rueckmeldung": { "de": "Vier Kopfzellen, dann die Analyse — wer ein Notebook gelesen hat, findet sich in allen neun zurecht." } },

  { "id": "W06-04", "typ": "reihenfolge",
    "titel": { "de": "Ein Notebook von oben nach unten" },
    "aufgabe": { "de": "<p>Bringen Sie die Zellen eines Fallstudien-Notebooks in die Reihenfolge, in der sie laufen müssen.</p>" },
    "eintraege": [
      { "id": "pip", "text": { "de": "%pip install -q … (in Colab)" } },
      { "id": "verbindung", "text": { "de": "VERBINDUNG, create_engine, lade_sql, lade_csv" } },
      { "id": "zahl", "text": { "de": "def zahl(wert, nachkommastellen=0)" } },
      { "id": "daten", "text": { "de": "daten = lade_sql(\"SELECT …\")" } },
      { "id": "ergebnis", "text": { "de": "print(f\"Umsatz 2025: {zahl(umsatz)} €\")" } }
    ],
    "richtig": ["pip", "verbindung", "zahl", "daten", "ergebnis"],
    "start": ["ergebnis", "daten", "zahl", "verbindung", "pip"],
    "rueckmeldung": { "de": "Pakete vor Importen, Verbindung vor Daten, Helfer vor Ausgaben. Nach einem Neustart der Runtime beginnt man wieder oben." } },

  { "id": "W06-05", "typ": "checkliste",
    "titel": { "de": "Notebook 00 in Colab ausführen" },
    "aufgabe": { "de": "<p>Öffnen Sie <code>notebooks/00_zugang_und_daten.ipynb</code> über den Colab-Link im Repository und arbeiten Sie die Liste ab.</p>" },
    "schritte": [
      { "text": { "de": "Notebook in Colab geöffnet (Link „In Colab öffnen“ im Kopf oder über <code>colab.research.google.com/github/swrobuts/BurgerMetrics/blob/main/notebooks/00_zugang_und_daten.ipynb</code>)." } },
      { "text": { "de": "pip-Zelle ausgeführt; die Meldung <code>Note: you may need to restart the kernel</code> gelesen und die Runtime neu gestartet." } },
      { "text": { "de": "Verbindungszelle ausgeführt — ohne Fehler; danach zeigt die Tabellenübersicht <code>burgermetrics 14</code>, <code>wawi 16</code> Tabellen und <code>38</code> materialisierte Sichten." } },
      { "text": { "de": "Die DuckDB-Zelle liefert die acht Filialtypen; <code>lade_csv(\"dim_branch\")</code> hat eine echte CSV geladen, keinen LFS-Zeiger." } },
      { "text": { "de": "Die Export-Zelle hat <code>export/</code> mit vier Sichten als CSV und Parquet gefüllt (163 Zeilen zusammen)." } },
      { "text": { "de": "<code>DASH_STARTEN = True</code> gesetzt und die Dash-Zelle ausgeführt: Die vier Karten erscheinen unter der Zelle." } }
    ],
    "rueckmeldung": { "de": "Wenn die Dash-Zelle läuft, hat Colab die Datenbank auf Port 5433 erreicht — derselbe Weg, den Power BI und Tableau nehmen." } }
]
```

---

### Task 9: Lab 07 — Data Mining

**Files:** Create `web/lab/lab-07-datamining.html`, `web/lab/data/uebungen/lab-07.json`. Muster-Lab: `WInf-SP/lab-10-etl.html` (Aufbau mit Schrittfolge). Quellen: die `## Ergebnis`-Abschnitte der Notebooks 02–07 (`notebooks/0N_*.ipynb`) und der Abschnitt „Fakten für die Labs“.

**Abschnitte:** `warum` — Data Mining als Frage → Verfahren → Kennzahl → Befund; sechs Verfahren, sechs Notebooks; jeder Befund braucht eine Gegenprobe. `crispdm` — die sechs Schritte (Business Understanding, Data Understanding, Data Preparation, Modeling, Evaluation, Deployment) und wo sie in den Notebooks stehen (Fragestellung, Daten, Vorgehen, Ergebnis, Was offen bleibt). `rfm` — Notebook 02: RFM je Kunde aus `fact_orders` (Recency, Frequency, Monetary, Stichtag 31.03.2026), Quintile, Segmente = `v_rfm_kunde`; K-Means: Silhouette bevorzugt k = 2, gewählt k = 4 (Entscheidung, keine Messung), Cluster 3 (6.084 Kunden, 11,1 Tage, 36,1 Bestellungen, 698,0 €) und Cluster 2 (1.910, 337,9 Tage); B01 (RFM-Abfrage). `warenkorb` — Notebook 03: Apriori (`mlxtend`) auf Q1 2025; Support, Konfidenz, Lift; Nuggets → BBQ-Sauce Lift 11,23 (8,97 gesamt), Fries–Bier 1,00; Fallstrick: Support ohne Lift, Apriori findet Kombinationen, keine Ursachen. `prognose` — Notebook 04: STL, lineare Regression, Gradient Boosting, Backtesting zwölf Monate; MAE 172,4 / 169,0 gegen 286,6 €; Basiseffekt (Jan–Mär 2026 1.343,4 € je Tag gegen 1.336,7 €). `zufriedenheit` — Notebook 06: 142.317 bewertete Bestellungen (selbstselektiert), Baum Tiefe 3, Random Forest, 50,6 % gegen Basisrate 50,4 %, Recall 98/3/0. `ausreisser` — Notebook 07: z-Score 79, IQR 213, Isolation Forest 178 (Vorgabe contamination 0,01), 15 stärkste gemeinsam; Kiliani 56 Filialtage. `ehrlich` — belegt / entschieden / widerlegt (Temperatur 41,64 €/°C ohne Monatskontrolle, p = 0,171 mit; Heimspiel −251,50 € gegen Gegenprobe; TF-IDF 100 % auf Generatortexten); der Bestand ist synthetisch. `spielplatz` (Datenbankband, Konsole `data-start="SELECT customer_id, count(*) AS bestellungen, round(sum(net_total), 2) AS umsatz FROM fact_orders GROUP BY customer_id ORDER BY umsatz DESC;"`), `uebungen`, `zusammenfassung`.

**Übungen (`lab-07.json`):**

```json
[
  { "id": "W07-01", "typ": "zuordnen",
    "titel": { "de": "Frage und Verfahren" },
    "aufgabe": { "de": "<p>Ordnen Sie jede Frage dem Verfahren zu, das sie beantwortet.</p>" },
    "ziele": [ { "id": "rfm", "text": { "de": "RFM und K-Means" } }, { "id": "apriori", "text": { "de": "Warenkorbanalyse (Apriori)" } }, { "id": "prognose", "text": { "de": "Regression / Gradient Boosting" } }, { "id": "klassifikation", "text": { "de": "Entscheidungsbaum / Random Forest" } }, { "id": "ausreisser", "text": { "de": "z-Score, IQR, Isolation Forest" } }, { "id": "sentiment", "text": { "de": "Sentiment-Analyse" } } ],
    "paare": [
      { "begriff": { "de": "Welche Kunden sind wertvoll, welche verloren?" }, "ziel": "rfm" },
      { "begriff": { "de": "Welche Produkte werden zusammen gekauft — und ist das mehr als Zufall?" }, "ziel": "apriori" },
      { "begriff": { "de": "Wie hoch ist der Tagesumsatz einer Filiale morgen?" }, "ziel": "prognose" },
      { "begriff": { "de": "Was unterscheidet zufriedene von unzufriedenen Bestellungen?" }, "ziel": "klassifikation" },
      { "begriff": { "de": "Welche Tage fallen aus dem Rahmen?" }, "ziel": "ausreisser" },
      { "begriff": { "de": "Ist diese Rezension positiv oder negativ?" }, "ziel": "sentiment" },
      { "begriff": { "de": "Lassen sich Kunden ohne Vorgabe in Gruppen teilen?" }, "ziel": "rfm" }
    ],
    "rueckmeldung": { "de": "Die Frage kommt zuerst; das Verfahren folgt ihr. Notebook 02 bis 08 der Fallstudie tragen je eine dieser Fragen im Abschnitt Fragestellung." } },

  { "id": "W07-02", "typ": "quiz",
    "titel": { "de": "Lift lesen" },
    "aufgabe": { "de": "<p>Zwei Fragen zur Warenkorbanalyse.</p>" },
    "fragen": [
      { "frage": { "de": "Chicken Nuggets 6pc → BBQ-Sauce hat Lift 11,23. Was heißt das?" },
        "optionen": [ { "de": "BBQ-Sauce liegt 11-mal so oft im Korb wie erwartet, wenn Nuggets drin sind" }, { "de": "11,23 Prozent aller Körbe enthalten beide" }, { "de": "Nuggets werden 11-mal häufiger verkauft als BBQ-Sauce" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Lift = Konfidenz geteilt durch die Basisrate des Ziels. Der Anteil beider im Korb ist der Support, die Verkaufshäufigkeit sagt der Lift nicht." } },
      { "frage": { "de": "Medium Fries und Bier haben über ein Prozent Support und Lift 1,00. Was folgt?" },
        "optionen": [ { "de": "Kein Zusammenhang: Sie kommen so oft zusammen vor wie unabhängig voneinander" }, { "de": "Ein starkes Bündel, weil der Support hoch ist" }, { "de": "Ein Fehler in den Daten" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Hoher Support allein zeigt nur, dass beide häufig sind. association_rules behält Regeln erst ab Lift 1 — deshalb fehlen acht solcher Paare in der Regelliste." } }
    ],
    "rueckmeldung": { "de": "Support sagt, wie häufig; Konfidenz, wie sicher; Lift, ob es mehr als Zufall ist. Apriori findet Kombinationen, keine Ursachen." } },

  { "id": "W07-03", "typ": "quiz",
    "titel": { "de": "Entscheidung oder Messung" },
    "aufgabe": { "de": "<p>Drei Fragen zur ehrlichen Interpretation.</p>" },
    "fragen": [
      { "frage": { "de": "Die Silhouette bevorzugt k = 2, das Notebook wählt k = 4. Was ist das?" },
        "optionen": [ { "de": "Eine Entscheidung: vier Gruppen lassen sich noch beschreiben" }, { "de": "Ein Messfehler der Silhouette" }, { "de": "Ein Beleg, dass K-Means nicht funktioniert" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Elbow und Silhouette geben Hinweise; wie viele Gruppen das Geschäft ansprechen kann, entscheidet das Geschäft. Das Notebook sagt das ausdrücklich." } },
      { "frage": { "de": "Beide Zufriedenheitsmodelle treffen 50,6 Prozent; die häufigste Klasse allein 50,4 Prozent. Was zeigt das?" },
        "optionen": [ { "de": "Die Modelle sagen fast immer „mittel“ voraus — die äußeren Urteile treffen sie nicht" }, { "de": "Die Modelle sind gut, weil über 50 Prozent" }, { "de": "Die Daten sind fehlerhaft" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Eine Trefferquote gilt nur gegen die Basisrate. Recall 98 Prozent für „mittel“, 3 für „niedrig“, 0 für „hoch“ zeigt, wo das Modell versagt." } },
      { "frage": { "de": "Der Isolation Forest markiert 178 Tage. Warum ist das kein Befund?" },
        "optionen": [ { "de": "contamination = 0,01 legt die 178 als Vorgabe fest" }, { "de": "Weil 178 zu wenig sind" }, { "de": "Weil z-Score und IQR mehr finden" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Der Parameter bestimmt den Anteil, nicht die Daten. Belegt ist nur, was alle drei Verfahren gemeinsam finden — die 15 stärksten Ausschläge." } }
    ],
    "rueckmeldung": { "de": "Belegt, entschieden, widerlegt: Wer die drei auseinanderhält, bleibt überprüfbar. Der Bestand ist synthetisch — Effekte sind eingebaut oder Zufall." } },

  { "id": "W07-04", "typ": "sql",
    "titel": { "de": "Die Grundlage von RFM" },
    "aufgabe": { "de": "<p>Je Kunde: das Datum der letzten Bestellung (<code>letzte_bestellung</code>), die Zahl der Bestellungen (<code>bestellungen</code>) und der Umsatz (<code>round(sum(net_total), 2)</code> als <code>umsatz</code>) aus <code>fact_orders</code>, absteigend nach Umsatz, bei Gleichstand nach <code>customer_id</code>.</p>" },
    "start": "SELECT customer_id\nFROM fact_orders\n",
    "loesung": "SELECT customer_id, max(date) AS letzte_bestellung, count(*) AS bestellungen,\n       round(sum(net_total), 2) AS umsatz\nFROM fact_orders\nGROUP BY customer_id\nORDER BY umsatz DESC, customer_id",
    "sortiert": true,
    "hinweis": { "de": "<p>Recency ist <code>max(date)</code> (Tage seit dem Stichtag rechnet das Notebook), Frequency <code>count(*)</code>, Monetary <code>sum(net_total)</code>. Gruppieren nach <code>customer_id</code>.</p>" },
    "rueckmeldung": { "de": "Im Browser hat jeder der 19 Kunden eine Bestellung; im Bestand sind es 24.992 Kunden mit bis zu 36 Bestellungen je Jahr. Aus diesen drei Spalten entstehen Quintile, Segmente und die Sicht v_rfm_kunde." } },

  { "id": "W07-05", "typ": "reihenfolge",
    "titel": { "de": "CRISP-DM" },
    "aufgabe": { "de": "<p>Bringen Sie die sechs Schritte des Vorgehensmodells in ihre Reihenfolge.</p>" },
    "eintraege": [
      { "id": "business", "text": { "de": "Business Understanding — welche Entscheidung hängt an der Antwort?" } },
      { "id": "data", "text": { "de": "Data Understanding — welche Tabellen, welcher Grain, welche Lücken?" } },
      { "id": "prep", "text": { "de": "Data Preparation — Aggregation in SQL, Merkmale, Splits" } },
      { "id": "modeling", "text": { "de": "Modeling — Verfahren wählen und anwenden" } },
      { "id": "evaluation", "text": { "de": "Evaluation — Kennzahl gegen Basisrate, Gegenprobe" } },
      { "id": "deployment", "text": { "de": "Deployment — Sicht, Dashboard, Notebook mit Ausgaben" } }
    ],
    "richtig": ["business", "data", "prep", "modeling", "evaluation", "deployment"],
    "start": ["modeling", "deployment", "data", "evaluation", "business", "prep"],
    "rueckmeldung": { "de": "Die Notebooks folgen derselben Ordnung: Fragestellung, Daten, Vorgehen, Ergebnis, Was offen bleibt. Evaluation ohne Gegenprobe ist keine." } }
]
```

Prüfung: W07-04 → 19 Zeilen, erste `8315 | 2022-10-02 | 1 | 21.20`.

---

### Task 10: Lab 08 — Externe Daten und Sentiment

**Files:** Create `web/lab/lab-08-extern.html`, `web/lab/data/uebungen/lab-08.json`, `web/lab/vorlagen/open-meteo.py`. Muster-Lab: `WInf-SP/lab-05-json.html` + `lab-05.json` (JSON-Übung und JSON-Werkbank). Quellen: `notebooks/05_wetter_und_ereignisse.ipynb` (Zelle mit `hole_wetter()`), `notebooks/08_sentiment_rezensionen.ipynb`, `notebooks/daten_extern/README.md`, `db/aufbau/0021_rezensionen.sql` (Bremse: 20 je Sitzung in zehn Minuten, 600 je Stunde, Text 5–500 Zeichen).

**Abschnitte:** `datum` — das Datum als Schlüssel: `dim_date` (3.377 Tage) auf der einen, die Antwort der Quelle auf der anderen Seite; fünf Quellen (Open-Meteo, Paket `holidays`, OpenHolidays API, OpenLigaDB, Destatis-VPI) als CSV unter `notebooks/daten_extern/` (ohne LFS, Fallback über `raw.githubusercontent.com`). `openmeteo` — ein Aufruf: B01 (`requests.get("https://archive-api.open-meteo.com/v1/archive", params={latitude 49.79, longitude 9.95, start_date, end_date, daily "temperature_2m_max,temperature_2m_min,precipitation_sum", timezone "Europe/Berlin"})`, Antwortaufbau `{"latitude": …, "daily": {"time": […], "temperature_2m_max": […]}}` mit gleich langen Listen, ERA5 0,25°, 5 Tage Verzug, 3.304 Tage), Vorlage `open-meteo.py`; Nachbildung 1: JSON-Antwort als `.code`-Block mit Callouts. `lizenz` — Open-Meteo CC BY 4.0 („Weather data by Open-Meteo.com“, Grenzen 10.000/Tag), OpenHolidays und OpenLigaDB ODbL (Weitergabe unter gleicher Lizenz), Destatis DL-DE BY 2.0 („Datenquelle: Statistisches Bundesamt (Destatis), Genesis-Online, Abrufdatum; Datenlizenz by-2-0“), `holidays` MIT; Stand 09/2026. `rezension` — der Weg einer Rezension: Shop (Knopf „Bewerten“) → `wawi.rezension_anlegen()` (Sterne 1–5, Text 5–500 Zeichen, 20 je Sitzung in zehn Minuten, 600 je Stunde; Bremse erreicht den Browser als HTTP 503) → `wawi.rezension` (`quelle = 'shop'`) → sichtbar in `wawi.v_rezension_letzte` und im Ø am Produkt (`wawi.v_rezension_produkt`) → Übernahme durch den Betreiber mit `uebernahme_aus_wawi()` nach `fact_reviews` (`source = 'shop'`); `uebungsrezensionen_loeschen()` räumt Übungsrezensionen weg (nur Betreiber). `sentiment` — Notebook 08: Wortliste 71,6 %, TF-IDF 100,0 % (Generatortexte), BERT 94,2 %; Anteil positiv fällt mit der Bestelldauer (78,63 % bis 5 min, 41,67 % über 15 min), Kanal (68,61 % Counter, 82,70 % App); offen: echte Shop-Rezensionen. `stolper` — `HTTP 429 Too Many Requests` (ferien-api.de, deshalb OpenHolidays), Verzug fünf Tage (die letzten Tage fehlen), Zeitzone (`timezone=Europe/Berlin`, sonst UTC-Tage), Datum als Text gegen Datum als `date` beim Join, 503 der Bremse im Shop nach 20 Rezensionen. `spielplatz` — Datenbankband, JSON-Werkbank (`data-json-konsole` mit einer kleinen Open-Meteo-Antwort als `data-start`), SQL-Konsole (`data-start="SELECT * FROM v_rezension_letzte ORDER BY erstellt_am DESC;"`). `uebungen`, `zusammenfassung` (mit Verweis auf das Deck und die Notebooks als Wege weiter).

**Übungen (`lab-08.json`):**

```json
[
  { "id": "W08-01", "typ": "json",
    "titel": { "de": "Eine Open-Meteo-Antwort reparieren" },
    "aufgabe": { "de": "<p>Die Antwort unten hat drei Syntaxfehler und einen Sachfehler: einfache Anführungszeichen, ein Komma zu viel, ein fehlendes Komma — und <code>temperature_2m_max</code> hat weniger Werte als <code>time</code>. Machen Sie daraus gültiges JSON mit drei Tagen und drei Werten.</p>" },
    "start": "{\n  'latitude': 49.79,\n  \"longitude\": 9.95\n  \"timezone\": \"Europe/Berlin\",\n  \"daily\": {\n    \"time\": [\"2025-07-01\", \"2025-07-02\", \"2025-07-03\"],\n    \"temperature_2m_max\": [31.2, 33.8],\n  }\n}",
    "loesung": "{\n  \"latitude\": 49.79,\n  \"longitude\": 9.95,\n  \"timezone\": \"Europe/Berlin\",\n  \"daily\": {\n    \"time\": [\"2025-07-01\", \"2025-07-02\", \"2025-07-03\"],\n    \"temperature_2m_max\": [31.2, 33.8, 29.4]\n  }\n}",
    "regeln": [
      { "pfad": "/latitude", "typ": "number" },
      { "pfad": "/longitude", "typ": "number" },
      { "pfad": "/daily", "typ": "object", "schluessel": ["time", "temperature_2m_max"] },
      { "pfad": "/daily/time", "typ": "array", "laenge": 3, "jedes": [ { "pfad": "", "typ": "string", "muster": "^\\d{4}-\\d{2}-\\d{2}$" } ] },
      { "pfad": "/daily/temperature_2m_max", "typ": "array", "laenge": 3, "jedes": [ { "pfad": "", "typ": "number" } ], "text": { "de": "temperature_2m_max braucht genau einen Wert je Tag in time — drei Tage, drei Zahlen." } }
    ],
    "hinweis": { "de": "<p>JSON kennt nur doppelte Anführungszeichen; nach dem letzten Element steht kein Komma; zwischen zwei Feldern muss eines stehen. Die Listen unter <code>daily</code> sind parallel: gleicher Index, gleicher Tag.</p>" },
    "rueckmeldung": { "de": "Genau so baut hole_wetter() in Notebook 05 den DataFrame: pd.DataFrame({\"tag\": d[\"time\"], \"tmax\": d[\"temperature_2m_max\"], …}) — parallele Listen werden zu Spalten. Ungleich lange Listen würden dort mit ValueError scheitern." } },

  { "id": "W08-02", "typ": "sql",
    "titel": { "de": "Über das Datum verknüpfen: Umsatz je Saison" },
    "aufgabe": { "de": "<p>Verknüpfen Sie <code>fact_orders</code> über <code>date</code> mit <code>dim_date</code> und berechnen Sie je <code>season</code> die Zahl der Bestellungen und den Umsatz (<code>round(sum(net_total), 2)</code>), absteigend nach Umsatz.</p>" },
    "start": "SELECT d.season\nFROM fact_orders o\nJOIN dim_date d USING (date)\n",
    "loesung": "SELECT d.season, count(*) AS bestellungen, round(sum(o.net_total), 2) AS umsatz\nFROM fact_orders o\nJOIN dim_date d USING (date)\nGROUP BY d.season\nORDER BY umsatz DESC",
    "sortiert": true,
    "hinweis": { "de": "<p><code>USING (date)</code> verbindet über die gleichnamige Spalte. Externe Quellen hängen genauso: eine Tabelle mit einer Datumsspalte, ein Join darüber.</p>" },
    "rueckmeldung": { "de": "Die Saison steht in dim_date, das Wetter in dim_weather, Feiertage und Heimspiele in den CSV-Dateien — alle über das Datum. Wer das Datum als Text lädt, bekommt keinen Treffer: erst in date wandeln." } },

  { "id": "W08-03", "typ": "sql",
    "titel": { "de": "Sterne je Produkt aus der Sicht" },
    "aufgabe": { "de": "<p>Aus <code>burgermetrics.v_rezension_produkt</code>: je Produkt mit mindestens einer Rezension <code>product_name</code>, <code>anzahl</code>, <code>sterne_mittel</code> und <code>anteil_positiv_pct</code>, absteigend nach <code>anzahl</code>, bei Gleichstand nach <code>product_name</code>.</p>" },
    "start": "SELECT product_name\nFROM burgermetrics.v_rezension_produkt\n",
    "loesung": "SELECT product_name, anzahl, sterne_mittel, anteil_positiv_pct\nFROM burgermetrics.v_rezension_produkt\nWHERE anzahl > 0\nORDER BY anzahl DESC, product_name",
    "sortiert": true,
    "hinweis": { "de": "<p>Das Schema muss davorstehen (Lab 01); <code>WHERE anzahl > 0</code> lässt Produkte ohne Rezension weg.</p>" },
    "rueckmeldung": { "de": "Dieselbe Sicht füllt die vierte Karte der Dash-App. Im Bestand hat sie 57 Zeilen mit 10.000 Rezensionen — und jede Shop-Rezension kommt nach dem nächsten ETL-Lauf hinzu." } },

  { "id": "W08-04", "typ": "checkliste",
    "titel": { "de": "Vom Shop in die Datenbank" },
    "aufgabe": { "de": "<p>Schreiben Sie im Online-Shop der Fallstudie eine Rezension und finden Sie sie in der Datenbank wieder. Sie brauchen den Shop (<code>swrobuts.github.io/BurgerMetrics/shop.html</code>) und eine Verbindung aus Lab 01.</p>" },
    "schritte": [
      { "text": { "de": "Im Shop auf einer Produktkarte <code>Bewerten</code> gewählt; das Formular zeigt den aktuellen Stand (Ø Sterne, Anzahl) des Produkts." } },
      { "text": { "de": "Sterne gewählt, einen Text mit 5 bis 500 Zeichen geschrieben, Filiale gewählt, gesendet — die Meldung nennt die neue Nummer (<code>Gespeichert als wawi.rezension #…</code>)." } },
      { "text": { "de": "Der Ø am Produkt hat sich sofort geändert (die Sicht <code>wawi.v_rezension_produkt</code> rechnet live)." } },
      { "text": { "de": "In der Datenbank: <code>SELECT * FROM wawi.v_rezension_letzte ORDER BY erstellt_am DESC LIMIT 3;</code> zeigt die Rezension mit <code>quelle = 'shop'</code>." } },
      { "text": { "de": "<code>SELECT count(*) FROM burgermetrics.fact_reviews WHERE source = 'shop';</code> zählt sie noch nicht — die Übernahme (<code>uebernahme_aus_wawi()</code>) macht der Betreiber bewusst." } },
      { "text": { "de": "Zwanzig Rezensionen in zehn Minuten aus derselben Sitzung: Der Shop meldet einen Fehler (HTTP 503, Bremse der Datenbank) — die 21. kommt nicht durch." } }
    ],
    "rueckmeldung": { "de": "Der Weg Shop → wawi.rezension → Sicht ist derselbe wie bei Bestellungen. Übungsrezensionen räumt der Betreiber mit uebungsrezensionen_loeschen() weg; der kuratierte Bestand bleibt unverändert." } },

  { "id": "W08-05", "typ": "quiz",
    "titel": { "de": "Lizenz, Verzug, Sentiment" },
    "aufgabe": { "de": "<p>Drei Fragen zu externen Daten.</p>" },
    "fragen": [
      { "frage": { "de": "Was verlangt CC BY 4.0 von einem Notebook, das Open-Meteo-Daten nutzt?" },
        "optionen": [ { "de": "Die Nennung der Quelle — etwa „Weather data by Open-Meteo.com“" }, { "de": "Eine Gebühr ab dem ersten Aufruf" }, { "de": "Nichts, weil die Daten frei sind" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Frei heißt nicht anonym: Alle fünf Quellen der Fallstudie binden die Nutzung an die Nennung; ODbL verlangt zusätzlich die Weitergabe abgeleiteter Datenbanken unter gleicher Lizenz." } },
      { "frage": { "de": "Warum fehlen in einer Open-Meteo-Archivantwort die letzten Tage?" },
        "optionen": [ { "de": "Die Reanalyse ERA5 liegt mit rund fünf Tagen Verzug vor" }, { "de": "Weil der Aufruf ohne Schlüssel gekürzt wird" }, { "de": "Weil die Zeitzone falsch war" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Archivdaten sind Reanalysen, keine Live-Messungen. Für den Bestand bis 31.03.2026 spielt der Verzug keine Rolle." } },
      { "frage": { "de": "TF-IDF trifft 100 Prozent der Rezensionen, BERT 94,2 Prozent. Welches Ergebnis ist belastbarer?" },
        "optionen": [ { "de": "BERT: Es hat die Satzbausteine des Generators nie gesehen" }, { "de": "TF-IDF: 100 Prozent ist das Maximum" }, { "de": "Beide gleich" } ],
        "richtig": [0], "mehrfach": false,
        "erklaerung": { "de": "Die Rezensionen sind simuliert; TF-IDF lernt die Bausteine, nicht die Sprache. 100 Prozent sind ein Warnsignal — echte Shop-Rezensionen sind die eigentliche Prüfung." } }
    ],
    "rueckmeldung": { "de": "Datum als Schlüssel, Lizenz als Pflicht, Gegenprobe als Regel — und die erste echte Rezension aus dem Shop ist der erste Text, an dem sich Notebook 08 bewähren muss." } }
]
```

Prüfung: W08-02 → `Spring | 9 | 96.95`, `Autumn | 9 | 91.86`, `Winter | 1 | 12.04`; W08-03 → 11 Zeilen, erste `Beyond Burger | 2 | 4.50 | 100.0`; W08-01: `node -e` mit `pruefeJson` aus `assets/jsonpruefung.js` — `loesung` ohne Befund, `start` mit Parsefehler (der Abnahmelauf prüft beides).

---

### Task 11: Abnahme, Hinweisdatei, Spec, PR

**Files:**
- Create: `/Users/robert/Library/CloudStorage/OneDrive-Persönlich/Vorlesungen/Lernumgebungen/BM-Lab.md` (außerhalb des Repos)
- Modify: `docs/superpowers/specs/2026-09-12-bm-analyse-lernumgebung-design.md` (§11 Stand-Absatz Phase 6), `web/lab/README.md` (Abnahmezahlen)

- [ ] **Step 1: Abnahmelauf**

```bash
cd "/Users/robert/Library/CloudStorage/OneDrive-Persönlich/Vorlesungen/Datenbasierte Fallstudien/BurgerMetrics/BurgerMetrics_Website/web/lab"
node tools/verify.mjs 2>/dev/null | tail -8
for f in data/uebungen/lab-0*.json; do /Users/robert/miniforge3/bin/python3 -c "import json,sys; d=json.load(open('$f')); print('$f', len(d['uebungen']), sorted({u['typ'] for u in d['uebungen']}))"; done
grep -c 'lang="en"' lab-0*.html index.html; grep -c '"en"' data/uebungen/*.json
du -sh . assets/pglite
```

Erwartet: `0 Fehler`, Zusicherungen > 0; Übungen 6/5/5/5/5/5/5/5 = 41; keine `en`-Treffer; Gesamtgröße rund 21 MB.

- [ ] **Step 2: Sichtprüfung im Browser**

`cd web && python3 -m http.server 8731 &`; mit dem Playwright-MCP jede der neun Seiten öffnen (`/lab/`, `/lab/lab-01-zugang.html` … `/lab/lab-08-extern.html`): Datenbankband erreicht „bereit“ (Labs 01, 02, 03, 07, 08), keine Konsolenfehler, alle Übungsboxen vorhanden, Seitennavigation springt zu den Abschnitten, Regal-Simulator zeichnet (Lab 04, 05), JSON-Werkbank prüft (Lab 08); je Seite ein Bildschirmfoto nach `web/lab/tools/sichtpruefung/` **nicht** ins Repository — Bildschirmfotos in den Bericht (Scratchpad) legen. Auf `/lab/` den Fortschritt einer gelösten Übung sehen (nach einer gelösten SQL-Übung in Lab 01 zurück zur Übersicht: „1 von 41“). Server beenden.

- [ ] **Step 3: Hinweisdatei außerhalb des Repos**

```bash
cat > "/Users/robert/Library/CloudStorage/OneDrive-Persönlich/Vorlesungen/Lernumgebungen/BM-Lab.md" <<'MD'
# BM-Lab

Lernumgebung zur Fallstudie BurgerMetrics (Modul Datenbasierte Fallstudien). Liegt im Repository `swrobuts/BurgerMetrics` unter `web/lab/` (lokal: `Vorlesungen/Datenbasierte Fallstudien/BurgerMetrics/BurgerMetrics_Website/web/lab/`).
Veröffentlicht unter https://swrobuts.github.io/BurgerMetrics/lab/ — Aufbau und Abnahmelauf in `web/lab/README.md`.
MD
```

- [ ] **Step 4: Spec §11 fortschreiben**

Nach dem Absatz „**Stand 13. September 2026 (Phase 5):** …“ anfügen:

```markdown
**Stand <Datum> (Phase 6):** BM-Lab abgenommen — `web/lab/` mit acht Labs und 41 Übungen (6/5/5/5/5/5/5/5), Laufzeit `assets/bm.js`/`bm.css` aus WInf-SP (nur Deutsch, `bm:*`-Schlüssel, ohne Terminal-, Deploy- und SQLite-Pfade), PGlite mit den Schemata `wawi` und `burgermetrics` aus den Mini-Skripten plus `data/bm_sichten.sql`; `node web/lab/tools/verify.mjs` ohne Befund (prüft Deutsch-Pflicht, Struktur, Lösbarkeit und führt jede SQL-Lösung gegen die Browser-Datenbank aus); jede Seite im Browser gesehen; Pages liefert `web/lab/` nach dem Merge. Abweichungen: `dataset/burgermetrics_mini.sql` schreibt Booleans jetzt als TRUE/FALSE (PostgreSQL lehnte 0/1 ab; DuckDB läuft weiter); Regal-Daten aus `obt_orders` (2.000 Bestellungen 2025) mit den Feldern Monat, Wochentag, Stunde, Filiale, Kanal, Zahlart, Loyalty-Stufe, Saison (keine Kategorie, weil `obt_orders` je Bestellung keine trägt); Lab 03 hat fünf Übungen (vier SQL, ein Quiz); Kachel auf `web/index.html`, `README.md` und Doku folgen in Phase 7; die Stolpersteine zu Tableau und Nur-Lese-Transaktionen (§13) stehen in Lab 05 mit der PostgreSQL-Meldung, ohne Nachstellung in Tableau.
```

- [ ] **Step 5: Commit und PR**

```bash
cd "/Users/robert/Library/CloudStorage/OneDrive-Persönlich/Vorlesungen/Datenbasierte Fallstudien/BurgerMetrics/BurgerMetrics_Website"
git -c core.fileMode=false add docs/superpowers/specs/2026-09-12-bm-analyse-lernumgebung-design.md web/lab/README.md
git -c core.fileMode=false commit -m "lab, spec: Abnahmestand Phase 6 (BM-Lab)" -m "Co-Authored-By: <Modell> <noreply@anthropic.com>"
git push -u origin bm-analyse
gh pr create --base main --head bm-analyse --title "Phase 6: BM-Lab unter web/lab/" --body-file /tmp/pr_phase6.md
```

`/tmp/pr_phase6.md`: was das Lab ist (acht Labs, 41 Übungen, PGlite mit zwei Schemata, Regal-Simulator), Größe des Pakets (rund 21 MB, davon PGlite 19 MB), Abnahmezahlen aus Schritt 1, die Abweichungen aus dem Spec-Absatz, Hinweis, dass Startseiten-Kachel und README-Verweise in Phase 7 folgen, Trailer „🤖 Generated with [Claude Code](https://claude.com/claude-code)“. Kein Merge, kein Auto-Merge — Roberts Entscheidung. Nach dem Merge: `gh run watch` bis der Pages-Lauf grün ist, dann `curl -s -o /dev/null -w "%{http_code}\n" https://swrobuts.github.io/BurgerMetrics/lab/` → 200 und Aufruf im Browser (Datenbankband „bereit“ auf Lab 01).

---

## Selbstprüfung des Plans

**Spec-Abdeckung (§9.1):** alle Dateien der Aufbau-Tabelle haben einen Task (Übersicht: T2; acht Labs: T3–T10; `bm.css`/`bm.js`: T2; `pruefung.js`, `jsonpruefung.js`, `regal.js`, `pglite/`: T1/T2; `data/*`: T1; `data/uebungen/*`: T3–T10; `vorlagen/`: T3–T10; `tools/verify.mjs`, `tools/sql.mjs`: T1/T2; `README.md`: T2/T11); Terminal/Deploy/SQLite entfallen (T2); `data-datenbank="postgres"` überall (Schablone). **§9.2:** Übungstypen je Lab wie in der Tabelle (Lab 03: vier SQL mit Kontrolle — die Fan Trap ist ein SELECT — plus Quiz; Lab 07 sql = RFM-Grundlage; Lab 08 json = Open-Meteo, sql ×2, Checkliste Shop → Datenbank, Quiz), alle Lösungen gegen PGlite geprüft. **§9.3:** Veröffentlichung über den Merge (T11), lokaler Start, Abnahme mit `verify.mjs` und Sichtprüfung. **§11 BM-Lab:** `verify.mjs` ohne Befund, SQL-Lösungen geprüft, Pages erreichbar; Verweise in beide Richtungen: Lab → Startseite/Shop/Dashboard/Notebooks (T2); Startseite → Lab folgt in Phase 7 (§10, §12). **§13:** Tableau/Nur-Lese-Transaktionen als Stolperstein in Lab 05 (T7). **§2.3:** Palette in `bm.css` (T2).

**Platzhalter:** keine; der Spec-Absatz in T11 trägt `<Datum>` als das Datum der Abnahme (vom Ausführenden einzusetzen), `<Modell>` in Commit-Trailern ist das ausführende Modell.

**Namenskonsistenz:** `neueDatenbank()`, `fuehreAus()`, `SAAT` (T1) ↔ Import in `verify.mjs` (T2); `LABS`-Dateinamen `lab-01-zugang.html` … `lab-08-extern.html` (T2) ↔ Task-Dateien; Übungs-IDs `W0N-0k`; `regal.felder`-IDs (`monat, wochentag, stunde, filiale, kanal, zahlart, loyalty, saison, order_id, umsatz, positionen, zufriedenheit`) ↔ Spalten aus `gen_daten.py` (T1) ↔ Ziele in T6/T7; Vorlagen-Dateinamen in T3–T10 ↔ Dateistruktur.
