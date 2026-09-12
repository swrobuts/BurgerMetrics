# Phase 4: Notebooks und Dash — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Neun ausgeführte Jupyter-Notebooks (`notebooks/00_…` bis `08_…`) führen Studierende vom Zugang mit dem Demo-Konto über das analytische Datenmodell zu Data-Mining-Analysen auf den BurgerMetrics-Daten, dazu eine Dash-App mit vier Karten; `notebooks/pruefe_notebooks.sh` führt alle Notebooks gegen die Datenbank aus und ist die Abnahme.

**Architecture:** Jedes Notebook wird aus einem kurzen Bauskript unter `notebooks/quellen/` erzeugt (Zellen als Python-Strings, geschrieben mit `nbformat`) und anschließend mit `jupyter nbconvert --execute --inplace` ausgeführt; eingecheckt werden Bauskript **und** ausgeführtes Notebook (GitHub zeigt die Ausgaben). Die Bauskripte teilen sich `gemeinsam.py` (Kopf mit Colab-Link, pip-Zelle, Verbindungszelle, Schreiben). Große Tabellen kommen per SQL-Aggregation aus der Datenbank (Rolle `studi_daba`), Dimensionen zur Demonstration per Git-LFS-URL. Externe Quellen werden einmal geholt und als CSV unter `notebooks/daten_extern/` versioniert. Die Dash-App ist eine Datei mit vier Datenfunktionen, einem Layout und einem Callback; `dash/test_app.py` prüft die Datenfunktionen gegen die Datenbank.

**Tech Stack:** Python 3.12, pandas 3, SQLAlchemy 2 + psycopg2, DuckDB, scikit-learn 1.8, mlxtend, statsmodels, holidays, transformers/torch (nur Notebook 08, Stichprobe), matplotlib, Plotly Dash 3, nbformat/nbconvert, pytest.

**Spec:** `docs/superpowers/specs/2026-09-12-bm-analyse-lernumgebung-design.md`, Abschnitte 6 (Notebooks, 6.1–6.3), 7 (externe Datenquellen), 11 (Abnahme, Zeilen „Notebooks", „Dash", „Übergabe je Phase") und 12.

## Global Constraints

- Nur Deutsch; sachlicher Ton, ganze Sätze, keine Bilder, keine Pointen, keine Personifizierung — auch in `print()`-Ausgaben. Echte Umlaute (ü, ö, ä, ß) in Markdown, Kommentaren und Ausgaben; Bezeichner ASCII (`lade_sql`, `umsatz_je_tag`).
- Jedes Notebook beginnt mit denselben Abschnitten in dieser Reihenfolge: **Fragestellung · Daten · Vorgehen · Ergebnis · Was offen bleibt** (Markdown-Überschriften `## …`). Davor der Kopf aus `gemeinsam.kopf()`: Titel mit „In Colab öffnen"-Link, pip-Zelle, Verbindungszelle (wörtlich wie in Spec 6.1; `lade_sql(sql)` und `lade_csv(name)`).
- Code für Anfänger: kurze Funktionen, deutsche Bezeichner, ein Kommentar je Funktion, keine verketteten Einzeiler, Ergebnisse als DataFrame anzeigen (letzte Zeile der Zelle) statt drucken; wo gedruckt wird, ganze Sätze.
- Große Tabellen (`fact_orders`, `fact_order_items`, `obt_orders`) nie komplett laden: Aggregation in SQL oder eine begrenzte Auswahl (z. B. ein Quartal). `lade_csv` nur für Dimensionen und zur Demonstration.
- Diagramme mit matplotlib: Standardfarben, beschriftete Achsen mit Einheit, Titel als Aussage, Nullpunkt bei Länge und Fläche; keine Wortwolken; Diagrammgröße `figsize=(9, 4)` bis `(9, 6)`.
- Ausführung: `jupyter nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 <Datei>` muss ohne Fehler durchlaufen; Laufzeit je Notebook unter zehn Minuten (Notebook 08 mit BERT unter 15). Keine Zelle schreibt in die Datenbank (die Rolle ist nur lesend); keine Zelle braucht ein Geheimnis.
- Verbindung wörtlich: `postgresql+psycopg2://studi_daba:thws@supabase.butscher.cloud:5433/postgres`; Suchpfad der Rolle ist `wawi, burgermetrics`, daher Tabellen in SQL ohne Schemapräfix, außer wo beide Schemata denselben Namen hätten (dann `burgermetrics.…`).
- Externe Quellen (Spec 7, geprüft am 13.09.2026): Open-Meteo Archive (ohne Schlüssel, CC BY 4.0), Feiertage Bayern über das Paket `holidays`, Schulferien Bayern über `openholidaysapi.org` (ohne Schlüssel; `ferien-api.de` antwortete mit HTTP 429 und wird nicht verwendet), Würzburger Kickers über OpenLigaDB (`bl2` 2016, `bl3` 2017–2019, `bl2` 2020, `bl3` 2021; Regionalliga-Bayern-Saisons dort nicht abgedeckt — wird im Notebook benannt), Verbraucherpreisindex als kuratierte CSV (Destatis, 2020 = 100). Jede Antwort landet als CSV in `notebooks/daten_extern/`; Notebooks lesen zuerst die Datei und rufen die API nur, wenn sie fehlt oder `AKTUALISIEREN = True`.
- Dash-App: eine Datei `dash/app.py`, rund 150 Zeilen, Verbindung aus `DATABASE_URL` mit Vorgabe `studi_daba`, Start `python dash/app.py` → `http://127.0.0.1:8050`; vier Karten: Kennzahlkacheln, Umsatz je Monat mit Filialfilter, Kanalanteile je Jahr, Ø Sterne je Produkt.
- Abweichungen von der Spec, im Plan festgelegt: (1) Kennzahlkacheln nehmen Umsatz, Bestellungen und Ø Bestellwert 2025 aus `v_kennzahlen_jahr` und die Zufriedenheit aus `v_kennzahl_einzeln` (`kennung = 'zufriedenheit_2025'`), weil `v_kennzahl_einzeln` keine Umsatzkennzahl führt; (2) der Filialfilter für „Umsatz je Monat" rechnet in SQL über `fact_orders`, weil `v_umsatz_monat` keine Filialspalte hat (ohne Filter kommt die Linie aus `v_umsatz_monat`); (3) Schulferien über OpenHolidays statt ferien-api.de.
- Tests: `python3 -m pytest dash/test_app.py -q` (gegen die Datenbank), `python3 notebooks/quellen/pruefe_ausgaben.py <Notebook>` (kein Fehler, keine leere Codezelle ohne Ausgabe, alle Pflichtabschnitte vorhanden), zum Schluss `bash notebooks/pruefe_notebooks.sh`.
- Commits: `git -c core.fileMode=false add …` / `commit`, Nachricht deutsch, Trailer `Co-Authored-By: <ausführendes Modell> <noreply@anthropic.com>`. Ausgeführte Notebooks werden mitcommittet (keine LFS-Regel für `*.ipynb`; Bilder als PNG-Base64 im JSON, je Notebook unter 2 MB). Arbeit auf Branch `bm-analyse` (steht auf `main`, cd8f43b); am Ende ein PR auf `main`, Merge nur nach Rückfrage bei Robert.
- Umgebung des Ausführenden: `/Users/robert/miniforge3/bin/python3` (3.12) mit pandas 3.0, sqlalchemy, psycopg2, duckdb, scikit-learn 1.8, statsmodels, dash, plotly, matplotlib, nbformat, nbconvert, ipykernel, transformers 5, torch 2.12; **fehlen und werden in Task 1 installiert:** `mlxtend`, `holidays`.

---

## Dateistruktur

| Datei | Verantwortung |
|---|---|
| `notebooks/quellen/gemeinsam.py` (neu) | `kopf()`, `md()`, `code()`, `schreiben()`; die Verbindungszelle als Konstante |
| `notebooks/quellen/bau_00.py` … `bau_08.py` (neu) | je ein Bauskript, das die Zellen definiert und das Notebook schreibt |
| `notebooks/quellen/alle_bauen.py` (neu) | ruft alle Bauskripte |
| `notebooks/quellen/pruefe_ausgaben.py` (neu) | prüft ein ausgeführtes Notebook: keine Fehlerausgabe, Pflichtabschnitte, jede Codezelle ausgeführt |
| `notebooks/00_zugang_und_daten.ipynb` … `08_sentiment_rezensionen.ipynb` (neu) | die ausgeführten Notebooks |
| `notebooks/requirements.txt`, `notebooks/README.md`, `notebooks/pruefe_notebooks.sh` (neu) | Umgebung, Anleitung, Abnahme |
| `notebooks/daten_extern/*.csv` (neu, aus Notebook 05) | Wetter (Open-Meteo), Schulferien, Kickers-Heimspiele, VPI |
| `dash/app.py`, `dash/requirements.txt`, `dash/README.md`, `dash/test_app.py` (neu) | Dash-App mit Test |
| `.gitignore` (ändern) | `notebooks/.ipynb_checkpoints/`, `dash/__pycache__/` |

Zeilenangaben sind Stand cd8f43b. Wo ein Schritt sagt „Zelle X", ist die Reihenfolge im Bauskript gemeint.

---

### Task 1: Grundlage — gemeinsam.py, Prüfskripte, README und Notebook 00

**Files:**
- Create: `notebooks/quellen/gemeinsam.py`, `notebooks/quellen/pruefe_ausgaben.py`, `notebooks/quellen/alle_bauen.py`, `notebooks/quellen/bau_00.py`, `notebooks/requirements.txt`, `notebooks/README.md`, `notebooks/pruefe_notebooks.sh`
- Modify: `.gitignore` (zwei Zeilen)
- Produces: `notebooks/00_zugang_und_daten.ipynb` (ausgeführt)

**Interfaces:**
- Produces (für alle weiteren Tasks): `gemeinsam.kopf(nummer, titel, dateiname) -> list[cell]`, `gemeinsam.md(text) -> cell`, `gemeinsam.code(text) -> cell`, `gemeinsam.schreiben(dateiname, zellen)`; `pruefe_ausgaben.py <ipynb>` (Exit 0/1); `pruefe_notebooks.sh`.

- [ ] **Step 1: Pakete und .gitignore**

```bash
python3 -m pip install -q mlxtend holidays
python3 -c "import mlxtend, holidays; print(mlxtend.__version__, holidays.__version__)"
printf '\n# Notebooks und Dash\nnotebooks/.ipynb_checkpoints/\ndash/__pycache__/\n' >> .gitignore
```

- [ ] **Step 2: `notebooks/quellen/gemeinsam.py`**

```python
"""gemeinsam.py — Bausteine, die alle Notebooks der Fallstudie teilen.

Jedes Notebook entsteht aus einem Bauskript (bau_NN.py): Die Zellen stehen dort als
Python-Strings, dieses Modul schreibt sie mit nbformat als .ipynb. So bleibt der
Quelltext lesbar im Diff, und die ausgeführte Fassung mit Ausgaben liegt daneben.
"""
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

REPO = "swrobuts/BurgerMetrics"
ORDNER = Path(__file__).resolve().parent.parent   # notebooks/

PAKETE = "sqlalchemy psycopg2-binary duckdb scikit-learn mlxtend statsmodels holidays dash"

VERBINDUNG = '''import pandas as pd
from sqlalchemy import create_engine

VERBINDUNG = "postgresql+psycopg2://studi_daba:thws@supabase.butscher.cloud:5433/postgres"
engine = create_engine(VERBINDUNG)

def lade_sql(sql):
    # Führt eine Abfrage aus und gibt das Ergebnis als DataFrame zurück
    return pd.read_sql(sql, engine)

def lade_csv(name):
    # Liest eine CSV-Datei des Datensatzes direkt aus GitHub (Git LFS)
    url = f"https://media.githubusercontent.com/media/swrobuts/BurgerMetrics/main/dataset/{name}.csv"
    return pd.read_csv(url)'''


def md(text):
    """Eine Markdown-Zelle; führende und schließende Leerzeilen fallen weg."""
    return new_markdown_cell(text.strip())


def code(text):
    """Eine Codezelle; führende und schließende Leerzeilen fallen weg."""
    return new_code_cell(text.strip())


def kopf(nummer, titel, dateiname, pakete=PAKETE):
    """Die drei Kopfzellen: Titel mit Colab-Link, pip-Zelle, Verbindungszelle."""
    colab = f"https://colab.research.google.com/github/{REPO}/blob/main/notebooks/{dateiname}"
    titelzelle = (f"# {nummer} {titel}\n\n"
                  f"[![In Colab öffnen](https://colab.research.google.com/assets/colab-badge.svg)]({colab})\n\n"
                  "Fallstudie BurgerMetrics · Datenbasierte Fallstudien (THWS). "
                  "Die Datenbank ist mit dem Demo-Konto `studi_daba` lesend erreichbar; "
                  "nichts in diesem Notebook schreibt in die Datenbank.")
    pipzelle = (f"# In Colab einmal ausführen; lokal genügt notebooks/requirements.txt\n"
                f"%pip install -q {pakete}")
    return [md(titelzelle), code(pipzelle), code(VERBINDUNG)]


def schreiben(dateiname, zellen):
    """Schreibt die Zellen als Notebook nach notebooks/<dateiname>."""
    metadaten = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                 "language_info": {"name": "python"}}
    nb = new_notebook(cells=zellen, metadata=metadaten)
    ziel = ORDNER / dateiname
    nbformat.write(nb, ziel)
    print(f"geschrieben: {ziel.name} mit {len(zellen)} Zellen")
```

- [ ] **Step 3: `notebooks/quellen/pruefe_ausgaben.py`**

```python
#!/usr/bin/env python3
"""pruefe_ausgaben.py — prüft ein ausgeführtes Notebook.

    python3 notebooks/quellen/pruefe_ausgaben.py notebooks/00_zugang_und_daten.ipynb

Befunde: eine Codezelle ohne Ausführungsnummer (nie gelaufen), eine Ausgabe vom Typ
error, ein fehlender Pflichtabschnitt. Exit 1 bei mindestens einem Befund.
"""
import sys

import nbformat

PFLICHT = ["## Fragestellung", "## Daten", "## Vorgehen", "## Ergebnis", "## Was offen bleibt"]


def befunde(pfad):
    """Sammelt alle Befunde eines Notebooks als Liste von Sätzen."""
    nb = nbformat.read(pfad, as_version=4)
    liste = []
    markdown = "\n".join(z.source for z in nb.cells if z.cell_type == "markdown")
    for abschnitt in PFLICHT:
        if abschnitt not in markdown:
            liste.append(f"Abschnitt fehlt: {abschnitt}")
    for nummer, zelle in enumerate(nb.cells, 1):
        if zelle.cell_type != "code":
            continue
        if zelle.execution_count is None:
            liste.append(f"Zelle {nummer} wurde nicht ausgeführt")
        for ausgabe in zelle.outputs:
            if ausgabe.output_type == "error":
                liste.append(f"Zelle {nummer} endet mit {ausgabe.ename}: {ausgabe.evalue[:120]}")
    return liste


if __name__ == "__main__":
    fehler = 0
    for pfad in sys.argv[1:]:
        liste = befunde(pfad)
        print(f"{pfad}: {len(liste)} Befund(e)")
        for satz in liste:
            print("  -", satz)
        fehler += len(liste)
    sys.exit(1 if fehler else 0)
```

- [ ] **Step 4: `notebooks/quellen/alle_bauen.py`, `notebooks/pruefe_notebooks.sh`, `notebooks/requirements.txt`**

```python
#!/usr/bin/env python3
"""alle_bauen.py — erzeugt alle Notebooks neu aus ihren Bauskripten (ohne Ausführung)."""
import runpy
from pathlib import Path

HIER = Path(__file__).resolve().parent
for skript in sorted(HIER.glob("bau_0*.py")):
    print("==", skript.name)
    runpy.run_path(str(skript), run_name="__main__")
```

```bash
#!/usr/bin/env bash
# pruefe_notebooks.sh — führt alle Notebooks gegen die Datenbank aus und speichert die
# Ausgaben im Notebook. Das ist die Abnahme der Phase: Läuft eines nicht durch, bricht
# das Skript ab. Danach prüft pruefe_ausgaben.py jedes Notebook auf Fehlerausgaben.
set -euo pipefail
cd "$(dirname "$0")"
for nb in 0*.ipynb; do
  echo "== $nb"
  jupyter nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 "$nb"
done
python3 quellen/pruefe_ausgaben.py 0*.ipynb
echo "Alle Notebooks ausgeführt und geprüft."
```

`notebooks/requirements.txt`:

```
pandas>=2.2
sqlalchemy>=2.0
psycopg2-binary>=2.9
duckdb>=1.0
scikit-learn>=1.5
mlxtend>=0.23
statsmodels>=0.14
holidays>=0.50
matplotlib>=3.8
dash>=2.17
plotly>=5.22
requests>=2.31
pyarrow>=15
nbformat>=5.10
nbconvert>=7.16
ipykernel>=6.29
transformers>=4.40
torch>=2.2
```

`chmod +x notebooks/pruefe_notebooks.sh`.

- [ ] **Step 5: `notebooks/README.md`**

```markdown
# Notebooks zur Fallstudie BurgerMetrics

Neun Notebooks, jedes für sich lauffähig — in Google Colab (Link am Kopf jedes Notebooks)
oder lokal. Alle lesen die Datenbank mit dem Demo-Konto `studi_daba` (nur lesend) und
brauchen kein Geheimnis.

| Notebook | Inhalt |
|---|---|
| `00_zugang_und_daten` | Verbindung, Schemata und Sichten, CSV per Git LFS, DuckDB, Export für Power BI und Tableau, Grenzen der Rolle, Dash inline |
| `01_analytisches_datenmodell` | Frage → Grain → Dimensionen → Fakten → Sicht; Fan Trap; Abgleich mit `burgermetrics`; Rezensionen als neue Faktentabelle |
| `02_rfm_und_kundensegmente` | RFM mit Quintilen und Zweitschlüssel, Vergleich mit `v_rfm_kunde`, K-Means |
| `03_warenkorbanalyse` | Apriori mit `mlxtend`, Support, Konfidenz, Lift, Richtung der Regel |
| `04_nachfrageprognose` | STL, Merkmale aus Kalender und Wetter, Regression und Gradient Boosting, Backtesting |
| `05_wetter_und_ereignisse` | Regression auf Wetter und Ereignisse; externe Quellen: Open-Meteo, Feiertage, Schulferien, Kickers, VPI |
| `06_zufriedenheit_erklaeren` | Entscheidungsbaum und Random Forest auf `satisfaction_score` |
| `07_ausreisser_tagesumsatz` | z-Score, IQR, Isolation Forest; Treffer erklären |
| `08_sentiment_rezensionen` | Wortliste, TF-IDF + logistische Regression, deutsches BERT-Modell, Sentiment gegen Kanal und Produkt |

## Lokal ausführen

```bash
python3 -m pip install -r notebooks/requirements.txt
jupyter lab notebooks/
```

## Neu bauen und abnehmen

Die Notebooks entstehen aus Bauskripten unter `quellen/` (Zellen als Python-Strings,
geschrieben mit `nbformat`). Wer ein Notebook ändert, ändert das Bauskript, baut neu und
führt aus:

```bash
python3 notebooks/quellen/bau_03.py          # ein Notebook neu schreiben
python3 notebooks/quellen/alle_bauen.py      # alle
bash notebooks/pruefe_notebooks.sh           # alle ausführen und prüfen (rund 20 Minuten)
```

`pruefe_notebooks.sh` ist die Abnahme: Jedes Notebook läuft mit `jupyter nbconvert --execute`
gegen die Datenbank, die Ausgaben werden gespeichert und eingecheckt, `quellen/pruefe_ausgaben.py`
meldet Fehlerausgaben und fehlende Abschnitte.

## Externe Daten

`daten_extern/` enthält die einmal geholten Antworten der externen Quellen (Open-Meteo,
OpenHolidays, OpenLigaDB) und den kuratierten Verbraucherpreisindex. Notebook 05 liest zuerst
diese Dateien und ruft die Anbieter nur, wenn eine Datei fehlt oder `AKTUALISIEREN = True`
gesetzt ist. Quellen und Stand stehen im Notebook.
```

- [ ] **Step 6: `notebooks/quellen/bau_00.py`**

```python
#!/usr/bin/env python3
"""bau_00.py — schreibt notebooks/00_zugang_und_daten.ipynb."""
from gemeinsam import code, kopf, md, schreiben

ZELLEN = kopf("00", "Zugang und Daten", "00_zugang_und_daten.ipynb") + [
md("""
## Fragestellung

Wie erreichen wir die Daten der Fallstudie — in der Datenbank, als CSV und lokal in DuckDB —
und wie bereiten wir sie für Power BI, Tableau und eine eigene Dash-App auf?

## Daten

Die Datenbank ist eine PostgreSQL-Instanz mit zwei Schemata: `wawi` ist das operative Modell
in dritter Normalform (Kasse und Shop schreiben hinein), `burgermetrics` das Auswertungsmodell
als Galaxy-Schema mit materialisierten Sichten `v_*`. Dieselben Daten liegen als CSV-Dateien
im Repository (Git LFS).

## Vorgehen

Erst die Verbindung und ihre Grenzen, dann die Schemata über `information_schema`, dann die
drei Wege zu den Daten: SQL, CSV per LFS-URL und DuckDB. Zum Schluss ein Export für Power BI
und Tableau sowie eine kleine Dash-App direkt im Notebook.
"""),
md("### Verbindung prüfen"),
code("""
lade_sql("SELECT current_user, current_setting('search_path') AS suchpfad, "
         "current_setting('default_transaction_read_only') AS nur_lesen")
"""),
md("""
Die Rolle `studi_daba` sieht beide Schemata über den Suchpfad `wawi, burgermetrics`, arbeitet
nur lesend und darf höchstens zehn Minuten je Abfrage rechnen. Tabellen mit gleichem Namen in
beiden Schemata gibt es nicht; wer sicher gehen will, schreibt den Schemanamen davor.

### Schemata und Sichten
"""),
code("""
tabellen = lade_sql(\"\"\"
    SELECT table_schema AS schema, table_type AS art, count(*) AS anzahl
    FROM information_schema.tables
    WHERE table_schema IN ('wawi', 'burgermetrics')
    GROUP BY table_schema, table_type
    ORDER BY table_schema, table_type
\"\"\")
tabellen
"""),
code("""
# Materialisierte Sichten stehen nicht in information_schema, sondern in pg_matviews
sichten = lade_sql(\"\"\"
    SELECT schemaname AS schema, matviewname AS sicht
    FROM pg_matviews
    WHERE schemaname = 'burgermetrics'
    ORDER BY matviewname
\"\"\")
print(f"Das Schema burgermetrics hat {len(sichten)} materialisierte Sichten.")
sichten.head(40)
"""),
md("### Erste Kennzahlen aus der Semantikschicht"),
code("""
kennzahlen = lade_sql("SELECT jahr, bestellungen, umsatz, aov FROM v_kennzahlen_jahr ORDER BY jahr")
kennzahlen
"""),
code("""
import matplotlib.pyplot as plt

abb, achse = plt.subplots(figsize=(9, 4))
achse.bar(kennzahlen["jahr"], kennzahlen["umsatz"] / 1_000_000)
achse.set_xlabel("Jahr")
achse.set_ylabel("Umsatz in Mio. €")
achse.set_title("2017 und 2026 sind Rumpfjahre: Der Betrieb begann im März 2017, die Daten enden im März 2026")
achse.set_ylim(0)
plt.show()
"""),
md("""
### CSV per Git LFS

Die Dimensionstabellen sind klein und lassen sich direkt aus GitHub lesen. Die großen
Faktentabellen (`fact_orders` mit 754.513 Zeilen, `fact_order_items` mit 2,95 Millionen)
holen wir aus der Datenbank — das schont das LFS-Kontingent und ist schneller.
"""),
code("""
produkte = lade_csv("dim_product")
print(f"dim_product.csv hat {len(produkte)} Zeilen und {produkte.shape[1]} Spalten.")
produkte.head()
"""),
md("""
### DuckDB: SQL auf CSV-Dateien

DuckDB fragt CSV- und Parquet-Dateien direkt ab, ohne Server. Hier laden wir zwei
Dimensionen über die LFS-URLs und rechnen eine Kennzahl; `dataset/load_duckdb.py` im
Repository baut auf diesem Weg den ganzen Datensatz als lokale Datenbank.
"""),
code("""
import duckdb

filialen = lade_csv("dim_branch")
con = duckdb.connect()
con.register("dim_branch", filialen)
con.register("dim_product", produkte)
con.sql(\"\"\"
    SELECT branch_type AS filialtyp, count(*) AS filialen, round(avg(monthly_rent_eur)) AS miete_mittel
    FROM dim_branch
    GROUP BY branch_type
    ORDER BY filialen DESC
\"\"\").df()
"""),
md("""
### Export für Power BI und Tableau

Beide Werkzeuge verbinden sich direkt mit PostgreSQL (Host `supabase.butscher.cloud`, Port
5433, Datenbank `postgres`, Benutzer `studi_daba`, Kennwort `thws`). Wer lieber Dateien
importiert, exportiert Sichten als Parquet oder CSV. Parquet behält die Datentypen und ist
kleiner; CSV liest jedes Werkzeug.
"""),
code("""
from pathlib import Path

export = Path("export")
export.mkdir(exist_ok=True)

def exportiere(sicht):
    # Liest eine Sicht und schreibt sie als Parquet und CSV in den Ordner export/
    daten = lade_sql(f"SELECT * FROM {sicht}")
    daten.to_parquet(export / f"{sicht}.parquet", index=False)
    daten.to_csv(export / f"{sicht}.csv", index=False)
    return len(daten)

zeilen = {sicht: exportiere(sicht) for sicht in ["v_kennzahlen_jahr", "v_filiale", "v_kanal_jahr", "v_umsatz_monat"]}
pd.DataFrame({"sicht": zeilen.keys(), "zeilen": zeilen.values()})
"""),
md("""
### Grenzen der Rolle

Die Rolle kann nicht schreiben. Der Versuch endet mit einer Fehlermeldung der Datenbank —
und genau so soll es sein: Die Übungen verändern den Bestand nicht.
"""),
code("""
from sqlalchemy import text

try:
    with engine.connect() as verbindung:
        verbindung.execute(text("UPDATE dim_branch SET branch_name = 'Test' WHERE branch_id = 1"))
except Exception as fehler:
    print("Die Datenbank lehnt ab:", str(fehler).splitlines()[0])
"""),
md("""
## Ergebnis

Drei Wege führen zu den Daten: SQL gegen die Datenbank (für alles Große), CSV per LFS-URL
(für Dimensionen und zum Nachvollziehen) und DuckDB (für SQL ohne Server). Die
Semantikschicht `v_*` liefert Kennzahlen, die im Dashboard, in Power BI und in den Notebooks
identisch sind, weil sie nur einmal definiert sind.

### Dash-App im Notebook

Die App aus `dash/app.py` lässt sich auch im Notebook starten. Die Zelle unten ist auf
`DASH_STARTEN = False` gesetzt, damit die Abnahme ohne offenen Port durchläuft; in Colab auf
`True` stellen, dann erscheint die App unter der Zelle.
"""),
code("""
DASH_STARTEN = False

from dash import Dash, dcc, html, Input, Output
import plotly.express as px

umsatz_monat = lade_sql("SELECT monat, umsatz FROM v_umsatz_monat ORDER BY monat")
filialliste = lade_sql("SELECT branch_id, branch_name FROM v_filiale ORDER BY branch_id")

def umsatz_je_filiale(branch_id):
    # Monatsumsatz einer Filiale aus fact_orders; None heißt alle Filialen
    if branch_id is None:
        return umsatz_monat
    return lade_sql(f\"\"\"
        SELECT to_char(date, 'YYYY-MM') AS monat, sum(net_total) AS umsatz
        FROM fact_orders WHERE branch_id = {int(branch_id)}
        GROUP BY 1 ORDER BY 1\"\"\")

app = Dash(__name__)
app.layout = html.Div([
    html.H3("Umsatz je Monat"),
    dcc.Dropdown(id="filiale", options=[{"label": "Alle Filialen", "value": "alle"}]
                 + [{"label": z.branch_name, "value": int(z.branch_id)} for z in filialliste.itertuples()],
                 value="alle", clearable=False),
    dcc.Graph(id="linie"),
])

@app.callback(Output("linie", "figure"), Input("filiale", "value"))
def zeichne(wahl):
    # Zeichnet die Linie neu, sobald die Filiale wechselt
    daten = umsatz_je_filiale(None if wahl == "alle" else wahl)
    return px.line(daten, x="monat", y="umsatz", labels={"monat": "Monat", "umsatz": "Umsatz in €"})

if DASH_STARTEN:
    app.run(jupyter_mode="inline", port=8050)
else:
    print("Dash-App gebaut; zum Starten DASH_STARTEN = True setzen.")
"""),
md("""
## Was offen bleibt

Der Export hier umfasst vier Sichten; Power BI und Tableau kommen mit der direkten
Verbindung ohne Export aus. Wer die CSV-Dateien lieber lokal hat, klont das Repository mit
Git LFS — die Anleitung steht in `dataset/README.md`.
"""),
]

schreiben("00_zugang_und_daten.ipynb", ZELLEN)
```

- [ ] **Step 7: Bauen, ausführen, prüfen**

```bash
python3 notebooks/quellen/bau_00.py
jupyter nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 notebooks/00_zugang_und_daten.ipynb
python3 notebooks/quellen/pruefe_ausgaben.py notebooks/00_zugang_und_daten.ipynb
ls notebooks/export 2>/dev/null && rm -rf notebooks/export
```
Expected: `geschrieben: 00_zugang_und_daten.ipynb mit 21 Zellen`; nbconvert ohne Fehler; `0 Befund(e)`. Der Ordner `notebooks/export/` entsteht beim Ausführen und wird nicht eingecheckt (`echo 'notebooks/export/' >> .gitignore`).

- [ ] **Step 8: Commit**

```bash
git -c core.fileMode=false add .gitignore notebooks/
git -c core.fileMode=false commit -m "notebooks: Grundlage (gemeinsam.py, Prüfskripte, README) und 00 Zugang und Daten, ausgeführt" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 2: Notebook 01 — Analytisches Datenmodell

**Files:**
- Create: `notebooks/quellen/bau_01.py`
- Produces: `notebooks/01_analytisches_datenmodell.ipynb` (ausgeführt)

**Interfaces:**
- Consumes: `gemeinsam.kopf/md/code/schreiben` (Task 1); Tabellen `wawi.kundenbestellung`, `bestellposition`, `rechnung`, `artikel`, `artikelunterkategorie`, `artikelkategorie`, `filiale`, `filialtyp`; `burgermetrics.fact_orders`, `fact_reviews`, `dim_product`.
- Produces: nichts für andere Tasks.

- [ ] **Step 1: `notebooks/quellen/bau_01.py`**

```python
#!/usr/bin/env python3
"""bau_01.py — schreibt notebooks/01_analytisches_datenmodell.ipynb."""
from gemeinsam import code, kopf, md, schreiben

ZELLEN = kopf("01", "Analytisches Datenmodell", "01_analytisches_datenmodell.ipynb") + [
md("""
## Fragestellung

Wie wird aus dem operativen Modell in dritter Normalform (`wawi`) ein analytisches Modell,
mit dem sich Fragen wie „Umsatz je Filiale und Jahr" ohne Umwege beantworten lassen — und
was geht schief, wenn man Tabellen mit unterschiedlichem Grain naiv verbindet?

## Daten

Ein Auszug aus `wawi` für das Jahr 2025: Bestellungen, Positionen und Rechnungen, dazu die
Stammdaten Artikel (drei Tabellen), Filialen und Filialtypen. Der Auszug kommt per SQL in
DataFrames und von dort in DuckDB, wo wir das analytische Modell Schritt für Schritt bauen.

## Vorgehen

Frage → Grain → Dimensionen → Fakten → Sicht. Am Ende vergleichen wir das Ergebnis mit dem
fertigen Schema `burgermetrics` und sehen uns an, wie die Rezensionen als dritte Faktentabelle
hineinpassen.
"""),
md("### Auszug aus dem operativen Modell"),
code("""
JAHR = 2025
VON, BIS = f"{JAHR}-01-01", f"{JAHR + 1}-01-01"

bestellungen = lade_sql(f\"\"\"
    SELECT bestellung_id, bestelldatum, filiale_id, kunde_id, zahlungsart_id, promotion_id,
           bestellkanal, artikel_anzahl, brutto_gesamt, rabatt_betrag, netto_gesamt,
           bestelldauer_min, zufriedenheit
    FROM kundenbestellung
    WHERE bestelldatum >= '{VON}' AND bestelldatum < '{BIS}'\"\"\")
positionen = lade_sql(f\"\"\"
    SELECT p.position_id, p.bestellung_id, p.artikel_id, p.menge, p.einzelpreis, p.positionsbetrag
    FROM bestellposition p
    JOIN kundenbestellung b USING (bestellung_id)
    WHERE b.bestelldatum >= '{VON}' AND b.bestelldatum < '{BIS}'\"\"\")
rechnungen = lade_sql(f\"\"\"
    SELECT r.rechnung_id, r.bestellung_id, r.rechnungsdatum, r.zahlbetrag, r.mwst_satz, r.mwst_betrag
    FROM rechnung r
    JOIN kundenbestellung b USING (bestellung_id)
    WHERE b.bestelldatum >= '{VON}' AND b.bestelldatum < '{BIS}'\"\"\")
artikel = lade_sql("SELECT artikel_id, name, unterkategorie_id, vegetarisch, vegan, kalorien, listenpreis FROM artikel")
unterkategorien = lade_sql("SELECT unterkategorie_id, name AS unterkategorie, kategorie_id FROM artikelunterkategorie")
kategorien = lade_sql("SELECT kategorie_id, name AS kategorie FROM artikelkategorie")
filialen = lade_sql("SELECT f.filiale_id, f.name, f.stadtteil, f.eroeffnet_am, t.name AS filialtyp FROM filiale f JOIN filialtyp t USING (filialtyp_id)")

pd.DataFrame({"tabelle": ["kundenbestellung", "bestellposition", "rechnung", "artikel", "filiale"],
              "zeilen": [len(bestellungen), len(positionen), len(rechnungen), len(artikel), len(filialen)]})
"""),
md("""
### Schritt 1: Die Frage und ihr Grain

„Umsatz je Filiale und Jahr" — die kleinste Einheit, die wir dafür zählen, ist **eine
Bestellung** (der Grain). Die Positionen einer Bestellung sind feiner; sie brauchen wir für
Fragen nach Produkten, nicht für den Umsatz je Filiale.

### Schritt 2: Dimensionen

Eine Dimension fasst zusammen, wonach wir gruppieren und filtern. `dim_product` entsteht aus
drei normalisierten Tabellen — Artikel, Unterkategorie, Kategorie — als eine breite Tabelle
mit einer Zeile je Artikel. `dim_branch` kommt aus Filiale und Filialtyp.
"""),
code("""
import duckdb

con = duckdb.connect()
for name, tabelle in {"kundenbestellung": bestellungen, "bestellposition": positionen, "rechnung": rechnungen,
                      "artikel": artikel, "artikelunterkategorie": unterkategorien,
                      "artikelkategorie": kategorien, "filiale": filialen}.items():
    con.register(name, tabelle)

con.sql(\"\"\"
    CREATE TABLE dim_product AS
    SELECT a.artikel_id AS product_id, a.name AS product_name, k.kategorie AS category,
           u.unterkategorie AS subcategory, a.vegetarisch AS is_vegetarian, a.vegan AS is_vegan,
           a.kalorien AS calories, a.listenpreis AS unit_price
    FROM artikel a
    JOIN artikelunterkategorie u USING (unterkategorie_id)
    JOIN artikelkategorie k USING (kategorie_id)
\"\"\")
con.sql(\"\"\"
    CREATE TABLE dim_branch AS
    SELECT filiale_id AS branch_id, name AS branch_name, stadtteil AS district,
           filialtyp AS branch_type, eroeffnet_am AS opening_date
    FROM filiale
\"\"\")
con.sql("SELECT category, count(*) AS produkte FROM dim_product GROUP BY category ORDER BY produkte DESC").df()
"""),
md("""
### Schritt 3: Fakten

`fact_orders` hat eine Zeile je Bestellung mit den Kennzahlen auf diesem Grain (Beträge, Dauer,
Zufriedenheit) und den Schlüsseln zu den Dimensionen. `fact_order_items` hat eine Zeile je
Position — ein zweiter Grain, eine zweite Faktentabelle. Beide teilen sich die Dimensionen:
Das ist die Galaxy (Fact Constellation).
"""),
code("""
con.sql(\"\"\"
    CREATE TABLE fact_orders AS
    SELECT bestellung_id AS order_id, bestelldatum AS date, filiale_id AS branch_id, kunde_id AS customer_id,
           zahlungsart_id AS payment_id, promotion_id AS promo_id, bestellkanal AS order_channel,
           artikel_anzahl AS item_count, brutto_gesamt AS gross_total, rabatt_betrag AS discount_amount,
           netto_gesamt AS net_total, bestelldauer_min AS order_duration_min, zufriedenheit AS satisfaction_score
    FROM kundenbestellung
\"\"\")
con.sql(\"\"\"
    CREATE TABLE fact_order_items AS
    SELECT position_id AS order_item_id, bestellung_id AS order_id, artikel_id AS product_id,
           menge AS quantity, einzelpreis AS unit_price, positionsbetrag AS line_total
    FROM bestellposition
\"\"\")
con.sql("SELECT 'fact_orders' AS tabelle, count(*) AS zeilen FROM fact_orders UNION ALL SELECT 'fact_order_items', count(*) FROM fact_order_items").df()
"""),
md("### Schritt 4: Die Sicht, die die Frage beantwortet"),
code("""
con.sql(\"\"\"
    CREATE VIEW v_umsatz_filiale_jahr AS
    SELECT b.branch_name, year(o.date) AS jahr, count(*) AS bestellungen, round(sum(o.net_total), 2) AS umsatz
    FROM fact_orders o
    JOIN dim_branch b USING (branch_id)
    GROUP BY b.branch_name, year(o.date)
\"\"\")
umsatz_filiale = con.sql("SELECT * FROM v_umsatz_filiale_jahr ORDER BY umsatz DESC").df()
umsatz_filiale
"""),
md("""
### Die Fan Trap: derselbe Betrag, viele Male gezählt

Wer den Umsatz aus der Bestellung nimmt, aber die Positionen dazujoint, zählt jeden
Bestellbetrag so oft, wie die Bestellung Positionen hat. Das Ergebnis sieht plausibel aus und
ist um ein Vielfaches zu hoch.
"""),
code("""
richtig = con.sql("SELECT sum(net_total) FROM fact_orders").fetchone()[0]
falsch = con.sql(\"\"\"
    SELECT sum(o.net_total)
    FROM fact_orders o
    JOIN fact_order_items i USING (order_id)
\"\"\").fetchone()[0]
print(f"Umsatz {JAHR} aus fact_orders: {richtig:,.0f} €.".replace(",", "."))
print(f"Derselbe Umsatz nach einem Join auf die Positionen: {falsch:,.0f} € — das {falsch / richtig:.1f}-Fache.".replace(",", "."))
print("Der Faktor ist die mittlere Zahl der Positionen je Bestellung: Jede Bestellung wird so oft gezählt.")
"""),
md("""
Die Regel: Kennzahlen immer auf dem Grain aggregieren, auf dem sie entstehen. Umsatz je
Bestellung aus `fact_orders`, Mengen je Produkt aus `fact_order_items` — und beides erst danach
über die gemeinsamen Dimensionen zusammenführen.

### Abgleich mit dem fertigen Schema `burgermetrics`

Das Schema in der Datenbank ist auf demselben Weg entstanden (`db/aufbau/0019`). Die Zahlen
müssen übereinstimmen.
"""),
code("""
vergleich = lade_sql(f\"\"\"
    SELECT b.branch_name, count(*) AS bestellungen_db, round(sum(o.net_total), 2) AS umsatz_db
    FROM burgermetrics.fact_orders o
    JOIN burgermetrics.dim_branch b USING (branch_id)
    WHERE o.date >= '{VON}' AND o.date < '{BIS}'
    GROUP BY b.branch_name\"\"\")
abgleich = umsatz_filiale.merge(vergleich, on="branch_name")
abgleich["differenz"] = (abgleich["umsatz"] - abgleich["umsatz_db"]).round(2)
abgleich[["branch_name", "bestellungen", "bestellungen_db", "umsatz", "umsatz_db", "differenz"]]
"""),
md("""
### Rezensionen als dritte Faktentabelle

Seit September 2026 gibt es `fact_reviews`: eine Zeile je Rezension, mit Schlüsseln zu
Produkt, Kunde, Filiale, Datum und — als Besonderheit — zur Bestellung, aus der sie stammt.
Der Grain ist neu (eine Rezension), die Dimensionen sind dieselben. Genau das macht das
Galaxy-Schema aus: Eine neue Frage bekommt eine neue Faktentabelle, nicht ein neues Modell.
"""),
code("""
lade_sql(\"\"\"
    SELECT p.category, count(*) AS rezensionen, round(avg(r.stars), 2) AS sterne_mittel,
           round(100.0 * avg(CASE WHEN r.stars >= 4 THEN 1 ELSE 0 END), 1) AS anteil_positiv_pct
    FROM fact_reviews r
    JOIN dim_product p USING (product_id)
    GROUP BY p.category
    ORDER BY rezensionen DESC\"\"\")
"""),
md("""
## Ergebnis

Aus sieben normalisierten Tabellen wurden zwei Dimensionen, zwei Faktentabellen und eine
Sicht; die Sicht beantwortet die Frage in einer Abfrage, und ihre Zahlen stimmen mit dem
fertigen Schema überein. Die Fan Trap zeigt, warum der Grain die wichtigste Entscheidung im
Modell ist.

## Was offen bleibt

Der Auszug umfasst ein Jahr; `db/aufbau/0019_wawi_zu_burgermetrics.sql` macht denselben
Schritt für den ganzen Bestand als ETL in der Datenbank. Die Dimensionen `dim_date` und
`dim_customer` haben wir übersprungen — sie entstehen nach demselben Muster.
"""),
]

schreiben("01_analytisches_datenmodell.ipynb", ZELLEN)
```

- [ ] **Step 2: Bauen, ausführen, prüfen**

```bash
python3 notebooks/quellen/bau_01.py
jupyter nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 notebooks/01_analytisches_datenmodell.ipynb
python3 notebooks/quellen/pruefe_ausgaben.py notebooks/01_analytisches_datenmodell.ipynb
```
Expected: 17 Zellen, keine Fehler, `0 Befund(e)`; im Abgleich ist `differenz` überall 0.00; der Fan-Trap-Faktor liegt bei rund 3,9.

- [ ] **Step 3: Commit**

```bash
git -c core.fileMode=false add notebooks/quellen/bau_01.py notebooks/01_analytisches_datenmodell.ipynb
git -c core.fileMode=false commit -m "notebooks: 01 Analytisches Datenmodell — Grain, Dimensionen, Fakten, Fan Trap, Abgleich" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 3: Notebook 02 — RFM und Kundensegmente

**Files:**
- Create: `notebooks/quellen/bau_02.py`
- Produces: `notebooks/02_rfm_und_kundensegmente.ipynb`

**Interfaces:**
- Consumes: `gemeinsam` (Task 1); `fact_orders`, `v_rfm_kunde` (Spalten `customer_id, recency_tage, frequenz, monetaer, r_wert, f_wert, m_wert, segment`; Stichtag 2026-03-31; `ntile(5)` mit `customer_id` als Zweitschlüssel; `r_wert = 6 - ntile`).

- [ ] **Step 1: `notebooks/quellen/bau_02.py`**

```python
#!/usr/bin/env python3
"""bau_02.py — schreibt notebooks/02_rfm_und_kundensegmente.ipynb."""
from gemeinsam import code, kopf, md, schreiben

ZELLEN = kopf("02", "RFM und Kundensegmente", "02_rfm_und_kundensegmente.ipynb") + [
md("""
## Fragestellung

Welche Kunden sind wertvoll, welche verloren — und lassen sich die Kunden ohne Vorgaben in
Gruppen teilen, die sich sinnvoll beschreiben lassen?

## Daten

`fact_orders` (754.513 Bestellungen von 24.992 Kunden), aggregiert je Kunde: Tage seit der
letzten Bestellung (Recency), Zahl der Bestellungen (Frequency) und Umsatz (Monetary) zum
Stichtag 31.03.2026. Zum Vergleich die Sicht `v_rfm_kunde` der Semantikschicht.

## Vorgehen

RFM-Werte je Kunde in SQL berechnen, jede Größe in Quintile teilen (mit `customer_id` als
Zweitschlüssel, damit Gleichstände reproduzierbar zugeordnet werden), Segmente nach festen
Regeln bilden und mit der Sicht abgleichen. Danach K-Means auf standardisierten Werten,
Elbow-Kurve und Silhouette zur Wahl von k, Beschreibung der Cluster.
"""),
code("""
STICHTAG = "2026-03-31"
basis = lade_sql(f\"\"\"
    SELECT customer_id,
           DATE '{STICHTAG}' - max(date) AS recency_tage,
           count(*)                       AS frequenz,
           sum(net_total)                 AS monetaer
    FROM fact_orders
    GROUP BY customer_id
    ORDER BY customer_id\"\"\")
print(f"{len(basis)} Kunden mit mindestens einer Bestellung.")
basis.describe().round(1)
"""),
md("""
### Quintile mit Zweitschlüssel

`ntile(5)` in PostgreSQL füllt fünf gleich große Fächer und gibt die ersten Fächer eine Zeile
mehr, wenn die Zahl nicht teilbar ist. Bei Gleichständen entscheidet die Reihenfolge — deshalb
sortieren wir zusätzlich nach `customer_id`. So kommt in Python dasselbe heraus wie in der
Datenbank.
"""),
code("""
import numpy as np

def fachgroessen(n, k=5):
    # Fachgrößen wie ntile(k): die ersten (n mod k) Fächer bekommen eine Zeile mehr
    basisgroesse, rest = divmod(n, k)
    return [basisgroesse + 1 if i < rest else basisgroesse for i in range(k)]

def quintil(daten, spalte):
    # Sortiert aufsteigend nach der Spalte, bei Gleichstand nach customer_id, und vergibt die Fachnummer 1 bis 5
    reihenfolge = daten.sort_values([spalte, "customer_id"]).index
    faecher = np.repeat(np.arange(1, 6), fachgroessen(len(daten)))
    return pd.Series(faecher, index=reihenfolge).reindex(daten.index)

rfm = basis.copy()
rfm["r_wert"] = 6 - quintil(rfm, "recency_tage")   # wenige Tage = hoher Wert
rfm["f_wert"] = quintil(rfm, "frequenz")
rfm["m_wert"] = quintil(rfm, "monetaer")
rfm[["r_wert", "f_wert", "m_wert"]].apply(pd.Series.value_counts).sort_index()
"""),
md("### Segmente nach festen Regeln"),
code("""
def segment(zeile):
    # Dieselben Regeln wie in v_rfm_kunde (db/aufbau/0009): Recency und Frequency entscheiden
    r, f = zeile["r_wert"], zeile["f_wert"]
    if r >= 4 and f >= 4:
        return "Champions"
    if r >= 3 and f >= 3:
        return "Loyal"
    if r >= 4 and f >= 2:
        return "Potenzial"
    if r >= 4:
        return "Neukunden"
    if r == 3:
        return "Schläfer"
    if r == 2:
        return "Abwanderungsgefahr"
    return "Verloren"

rfm["segment"] = rfm.apply(segment, axis=1)
uebersicht = rfm.groupby("segment").agg(kunden=("customer_id", "count"), recency_tage=("recency_tage", "mean"),
                                        frequenz=("frequenz", "mean"), umsatz=("monetaer", "sum")).round(1)
uebersicht.sort_values("kunden", ascending=False)
"""),
md("### Abgleich mit `v_rfm_kunde`"),
code("""
sicht = lade_sql("SELECT customer_id, r_wert, f_wert, m_wert, segment FROM v_rfm_kunde")
abgleich = rfm.merge(sicht, on="customer_id", suffixes=("", "_db"))
gleich = {spalte: (abgleich[spalte] == abgleich[f"{spalte}_db"]).mean() * 100
          for spalte in ["r_wert", "f_wert", "m_wert", "segment"]}
pd.DataFrame({"spalte": gleich.keys(), "uebereinstimmung_pct": [round(v, 2) for v in gleich.values()]})
"""),
md("""
Die Übereinstimmung liegt bei 100 Prozent: Der Zweitschlüssel macht die Quintile
reproduzierbar, in SQL wie in Python.

### K-Means: Gruppen ohne Vorgabe

RFM-Segmente folgen Regeln, die jemand festgelegt hat. K-Means sucht Gruppen in den Daten
selbst. Frequency und Monetary sind schief verteilt; wir logarithmieren sie und
standardisieren alle drei Größen, damit keine die Distanz dominiert.
"""),
code("""
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

merkmale = pd.DataFrame({
    "recency": rfm["recency_tage"],
    "frequenz_log": np.log1p(rfm["frequenz"]),
    "monetaer_log": np.log1p(rfm["monetaer"]),
})
X = StandardScaler().fit_transform(merkmale)

stichprobe = np.random.default_rng(2026).choice(len(X), 5000, replace=False)
bewertung = []
for k in range(2, 9):
    modell = KMeans(n_clusters=k, n_init=10, random_state=2026).fit(X)
    bewertung.append({"k": k, "inertia": modell.inertia_,
                      "silhouette": silhouette_score(X[stichprobe], modell.labels_[stichprobe])})
bewertung = pd.DataFrame(bewertung)
bewertung.round(3)
"""),
code("""
import matplotlib.pyplot as plt

abb, (links, rechts) = plt.subplots(1, 2, figsize=(9, 4))
links.plot(bewertung["k"], bewertung["inertia"], marker="o")
links.set_xlabel("k (Zahl der Cluster)")
links.set_ylabel("Inertia (Summe der quadrierten Abstände)")
links.set_title("Elbow: der Knick liegt bei k = 3 bis 4")
links.set_ylim(0)
rechts.plot(bewertung["k"], bewertung["silhouette"], marker="o")
rechts.set_xlabel("k (Zahl der Cluster)")
rechts.set_ylabel("Silhouette (Stichprobe 5.000)")
rechts.set_title("Silhouette: höher ist besser")
rechts.set_ylim(0)
plt.tight_layout()
plt.show()
"""),
code("""
K = 4
kmeans = KMeans(n_clusters=K, n_init=10, random_state=2026).fit(X)
rfm["cluster"] = kmeans.labels_
beschreibung = rfm.groupby("cluster").agg(kunden=("customer_id", "count"), recency_tage=("recency_tage", "mean"),
                                          frequenz=("frequenz", "mean"), monetaer=("monetaer", "mean")).round(1)
beschreibung
"""),
code("""
# Wie verteilen sich die RFM-Segmente auf die Cluster? Zeilen: Segment, Spalten: Cluster.
pd.crosstab(rfm["segment"], rfm["cluster"])
"""),
md("""
## Ergebnis

Die RFM-Segmente aus Python und aus der Datenbank stimmen überein; die Regeln lassen sich
also überall gleich anwenden. K-Means mit vier Clustern trennt die Kunden vor allem nach
Recency und Frequency — die Kreuztabelle zeigt, dass die Cluster die Regelsegmente grob
nachbilden, aber die Grenzen anders ziehen: Cluster kennen kein „Champion", nur Nähe im Raum.

## Was offen bleibt

Die Wahl von k ist eine Entscheidung, keine Messung: Elbow und Silhouette geben Hinweise, das
Geschäft entscheidet, wie viele Gruppen es ansprechen kann. Die Kundendaten sind synthetisch
und gleichverteilt über die Stadtteile — echte Segmente hätten mehr Struktur.
"""),
]

schreiben("02_rfm_und_kundensegmente.ipynb", ZELLEN)
```

- [ ] **Step 2: Bauen, ausführen, prüfen**

```bash
python3 notebooks/quellen/bau_02.py
jupyter nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 notebooks/02_rfm_und_kundensegmente.ipynb
python3 notebooks/quellen/pruefe_ausgaben.py notebooks/02_rfm_und_kundensegmente.ipynb
```
Expected: keine Fehler; `uebereinstimmung_pct` = 100.0 in allen vier Zeilen (sonst stimmt `quintil()` nicht mit `ntile` überein — dann `fachgroessen` und die Sortierung prüfen, nicht die Zahl anpassen). Laufzeit unter drei Minuten (K-Means mit n_init=10 auf 25.000 Zeilen).

- [ ] **Step 3: Commit**

```bash
git -c core.fileMode=false add notebooks/quellen/bau_02.py notebooks/02_rfm_und_kundensegmente.ipynb
git -c core.fileMode=false commit -m "notebooks: 02 RFM und Kundensegmente — Quintile mit Zweitschlüssel, Abgleich, K-Means" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 4: Notebook 03 — Warenkorbanalyse

**Files:**
- Create: `notebooks/quellen/bau_03.py`
- Produces: `notebooks/03_warenkorbanalyse.ipynb`

**Interfaces:**
- Consumes: `gemeinsam` (Task 1); `fact_orders`, `fact_order_items`, `dim_product`, `v_warenkorb_regeln` (Spalten `produkt_a, produkt_b, gemeinsam, support_pct, konfidenz_pct, lift`); mlxtend 0.25 (`association_rules(df, num_itemsets=…, metric=…, min_threshold=…)`).

- [ ] **Step 1: `notebooks/quellen/bau_03.py`**

```python
#!/usr/bin/env python3
"""bau_03.py — schreibt notebooks/03_warenkorbanalyse.ipynb."""
from gemeinsam import code, kopf, md, schreiben

ZELLEN = kopf("03", "Warenkorbanalyse", "03_warenkorbanalyse.ipynb") + [
md("""
## Fragestellung

Welche Produkte werden zusammen gekauft — und welche dieser Paare sind mehr als Zufall?

## Daten

Warenkörbe aus `fact_order_items` mit Produktnamen aus `dim_product`, beschränkt auf das erste
Quartal 2025 (rund 31.000 Bestellungen, 120.000 Positionen). Zum Vergleich die Sicht
`v_warenkorb_regeln`, die über den ganzen Bestand rechnet.

## Vorgehen

Warenkörbe in eine Tabelle Bestellung × Produkt (wahr/falsch) bringen, mit Apriori
(`mlxtend`) häufige Kombinationen finden, Regeln mit Support, Konfidenz und Lift ableiten,
die Richtung einer Regel prüfen und die Ergebnisse gegen die Sicht halten.
"""),
code("""
koerbe = lade_sql(\"\"\"
    SELECT o.order_id, p.product_name
    FROM fact_orders o
    JOIN fact_order_items i USING (order_id)
    JOIN dim_product p USING (product_id)
    WHERE o.date >= '2025-01-01' AND o.date < '2025-04-01'\"\"\")
tabelle = pd.crosstab(koerbe["order_id"], koerbe["product_name"]).astype(bool)
print(f"{tabelle.shape[0]} Warenkörbe, {tabelle.shape[1]} Produkte; "
      f"im Mittel {tabelle.sum(axis=1).mean():.2f} verschiedene Produkte je Korb.")
tabelle.iloc[:5, :6]
"""),
md("""
### Häufige Kombinationen mit Apriori

Der Support ist der Anteil der Körbe, die eine Kombination enthalten. Wir fordern mindestens
ein Prozent — darunter sind die Regeln zu selten, um zu tragen.
"""),
code("""
from mlxtend.frequent_patterns import apriori, association_rules

haeufig = apriori(tabelle, min_support=0.01, use_colnames=True)
haeufig["produkte"] = haeufig["itemsets"].apply(len)
print(f"{len(haeufig)} häufige Kombinationen, davon {int((haeufig['produkte'] >= 2).sum())} mit zwei oder mehr Produkten.")
haeufig[haeufig["produkte"] >= 2].sort_values("support", ascending=False).head(10)
"""),
md("""
### Regeln: Support, Konfidenz, Lift

Konfidenz ist der Anteil der Körbe mit A, die auch B enthalten. Lift setzt das ins Verhältnis
zur Häufigkeit von B insgesamt: Lift 1 heißt „B kommt mit A nicht öfter vor als sonst", Lift 2
heißt doppelt so oft.
"""),
code("""
regeln = association_rules(haeufig, num_itemsets=len(tabelle), metric="lift", min_threshold=1.0)
regeln["A"] = regeln["antecedents"].apply(lambda s: ", ".join(sorted(s)))
regeln["B"] = regeln["consequents"].apply(lambda s: ", ".join(sorted(s)))
paare = regeln[(regeln["antecedents"].apply(len) == 1) & (regeln["consequents"].apply(len) == 1)]
spalten = ["A", "B", "support", "confidence", "lift"]
paare.sort_values("lift", ascending=False)[spalten].head(12).round(3)
"""),
md("""
### Die Richtung einer Regel

Eine Regel A → B hat denselben Support und denselben Lift wie B → A, aber nicht dieselbe
Konfidenz: Sie hängt davon ab, wie häufig A allein ist. Für die Empfehlung an der Kasse zählt
die Konfidenz — also die Richtung.
"""),
code("""
def beide_richtungen(a, b):
    # Konfidenz für A → B und B → A nebeneinander
    hin = paare[(paare["A"] == a) & (paare["B"] == b)]["confidence"]
    zurueck = paare[(paare["A"] == b) & (paare["B"] == a)]["confidence"]
    return {"A": a, "B": b, "konfidenz_A_B": float(hin.iloc[0]) if len(hin) else None,
            "konfidenz_B_A": float(zurueck.iloc[0]) if len(zurueck) else None}

beste = paare.sort_values("lift", ascending=False).drop_duplicates("support").head(6)
pd.DataFrame([beide_richtungen(z.A, z.B) for z in beste.itertuples()]).round(3)
"""),
md("### Vergleich mit der Semantikschicht (ganzer Bestand)"),
code("""
sicht = lade_sql("SELECT produkt_a, produkt_b, support_pct, konfidenz_pct, lift FROM v_warenkorb_regeln")

def paar(a, b):
    # Ein Paar unabhängig von der Richtung, damit sich beide Tabellen zusammenführen lassen
    return " | ".join(sorted([a, b]))

sicht["paar"] = [paar(a, b) for a, b in zip(sicht["produkt_a"], sicht["produkt_b"])]
paare_q1 = paare.assign(paar=[paar(a, b) for a, b in zip(paare["A"], paare["B"])])
paare_q1 = paare_q1.groupby("paar", as_index=False).agg(lift_q1_2025=("lift", "first"), support_q1_2025=("support", "first"))
vergleich = sicht.merge(paare_q1, on="paar", how="left")
vergleich["support_q1_2025"] = (vergleich["support_q1_2025"] * 100).round(2)
vergleich[["produkt_a", "produkt_b", "support_pct", "support_q1_2025", "lift", "lift_q1_2025"]].round(2)
"""),
code("""
import matplotlib.pyplot as plt

abb, achse = plt.subplots(figsize=(6, 6))
achse.scatter(vergleich["lift"], vergleich["lift_q1_2025"])
achse.plot([0.9, 3.5], [0.9, 3.5], linestyle="--")
achse.set_xlabel("Lift im ganzen Bestand (v_warenkorb_regeln)")
achse.set_ylabel("Lift im ersten Quartal 2025 (Apriori)")
achse.set_title("Ein Quartal reicht: Die Lifts liegen nahe der Diagonale")
achse.set_xlim(0.9, 3.5)
achse.set_ylim(0.9, 3.5)
plt.show()
"""),
md("""
## Ergebnis

Die stärksten Regeln verbinden Frühstücksprodukte mit Kaffee und Burger mit Pommes; ihre
Lifts liegen deutlich über 1 und stimmen zwischen Quartal und Gesamtbestand überein. Ein Lift
von 1,03 — wie bei Burger und Bier in der Sicht — ist kein Signal: Bier kommt mit Burger
praktisch so oft vor wie ohne.

## Was offen bleibt

Apriori findet Kombinationen, keine Ursachen: Dass Pommes zum Burger gehören, wusste die
Speisekarte schon. Interessant werden Regeln, die nicht auf der Hand liegen — dafür braucht es
mehr Produkte, als diese Karte hat, oder feinere Merkmale wie Tageszeit und Kanal.
"""),
]

schreiben("03_warenkorbanalyse.ipynb", ZELLEN)
```

- [ ] **Step 2: Bauen, ausführen, prüfen**

```bash
python3 notebooks/quellen/bau_03.py
jupyter nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 notebooks/03_warenkorbanalyse.ipynb
python3 notebooks/quellen/pruefe_ausgaben.py notebooks/03_warenkorbanalyse.ipynb
```
Expected: keine Fehler; Apriori liefert mehrere Dutzend Kombinationen; der Vergleich hat für die meisten Sichtzeilen einen Wert in `lift_q1_2025` (Zeilen ohne Treffer haben Support unter 1 % im Quartal — das ist in Ordnung). Bleibt `paare` leer, `min_support` auf 0.005 senken und im Text nennen.

- [ ] **Step 3: Commit**

```bash
git -c core.fileMode=false add notebooks/quellen/bau_03.py notebooks/03_warenkorbanalyse.ipynb
git -c core.fileMode=false commit -m "notebooks: 03 Warenkorbanalyse — Apriori, Support, Konfidenz, Lift, Richtung, Vergleich mit der Sicht" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 5: Notebook 04 — Nachfrageprognose

**Files:**
- Create: `notebooks/quellen/bau_04.py`
- Produces: `notebooks/04_nachfrageprognose.ipynb`

**Interfaces:**
- Consumes: `gemeinsam` (Task 1); `fact_orders`, `dim_date` (`date, year, month, day_of_week, day_name, is_weekend, is_holiday, special_event`), `dim_weather` (`date, temperature_celsius, precipitation_mm, condition`), `dim_branch` (`branch_id, branch_name, opening_date`).

- [ ] **Step 1: `notebooks/quellen/bau_04.py`**

```python
#!/usr/bin/env python3
"""bau_04.py — schreibt notebooks/04_nachfrageprognose.ipynb."""
from gemeinsam import code, kopf, md, schreiben

ZELLEN = kopf("04", "Nachfrageprognose", "04_nachfrageprognose.ipynb") + [
md("""
## Fragestellung

Wie gut lässt sich der Tagesumsatz einer Filiale aus Kalender und Wetter vorhersagen — und
wie prüft man das ehrlich?

## Daten

Tagesumsatz je Filiale aus `fact_orders` (aggregiert in SQL), Merkmale aus `dim_date`
(Wochentag, Monat, Wochenende, Feiertag, Ereignis) und `dim_weather` (Temperatur,
Niederschlag). Beispielfiliale ist BM Europastern (`branch_id = 1`), die älteste mit der
längsten Reihe.

## Vorgehen

Zerlegung der Reihe in Trend, Wochenmuster und Rest (STL), dann zwei Modelle — lineare
Regression und Gradient Boosting — trainiert bis März 2025 und geprüft auf den letzten
zwölf Monaten (Backtesting). Bewertet wird mit MAE und MAPE. Zum Schluss der Basiseffekt bei
Rumpfjahren.
"""),
code("""
FILIALE = 1
tage = lade_sql(f\"\"\"
    SELECT o.date AS tag, sum(o.net_total) AS umsatz, count(*) AS bestellungen,
           d.year AS jahr, d.month AS monat, d.day_of_week AS wochentag, d.is_weekend AS wochenende,
           d.is_holiday AS feiertag, d.special_event AS ereignis,
           w.temperature_celsius AS temperatur, w.precipitation_mm AS niederschlag
    FROM fact_orders o
    JOIN dim_date d ON d.date = o.date
    LEFT JOIN dim_weather w ON w.date = o.date
    WHERE o.branch_id = {FILIALE}
    GROUP BY o.date, d.year, d.month, d.day_of_week, d.is_weekend, d.is_holiday, d.special_event,
             w.temperature_celsius, w.precipitation_mm
    ORDER BY o.date\"\"\")
tage["tag"] = pd.to_datetime(tage["tag"])
tage = tage.set_index("tag").asfreq("D")
print(f"{len(tage)} Tage von {tage.index.min().date()} bis {tage.index.max().date()}, "
      f"davon {int(tage['umsatz'].isna().sum())} ohne Bestellung.")
tage["umsatz"] = tage["umsatz"].fillna(0)
tage["bestellungen"] = tage["bestellungen"].fillna(0)
tage[["umsatz", "bestellungen", "temperatur", "niederschlag"]].describe().round(1)
"""),
md("### Zerlegung: Trend, Wochenmuster, Rest"),
code("""
from statsmodels.tsa.seasonal import STL
import matplotlib.pyplot as plt

zerlegung = STL(tage["umsatz"], period=7, robust=True).fit()
abb, achsen = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
achsen[0].plot(zerlegung.trend)
achsen[0].set_ylabel("Trend in €")
achsen[0].set_title("Der Trend trägt das Wachstum, das Wochenmuster wiederholt sich, der Rest ist Rauschen")
achsen[1].plot(zerlegung.seasonal.iloc[-56:])
achsen[1].set_ylabel("Wochenmuster in €")
achsen[2].plot(zerlegung.resid)
achsen[2].set_ylabel("Rest in €")
achsen[2].set_xlabel("Tag")
plt.tight_layout()
plt.show()
"""),
md("""
### Merkmale und Backtesting

Wir trainieren auf allen Tagen bis zum 31. März 2025 und prüfen auf den zwölf Monaten danach —
Daten, die das Modell beim Lernen nie gesehen hat. Merkmale: Wochentag und Monat als
Kategorien, Wochenende, Feiertag, Ereignis, Temperatur, Niederschlag und eine laufende
Tagesnummer für den Trend.
"""),
code("""
import numpy as np

merkmale = pd.DataFrame({
    "tag_nr": np.arange(len(tage)),
    "wochenende": tage["wochenende"].fillna(False).astype(int),
    "feiertag": tage["feiertag"].fillna(False).astype(int),
    "ereignis": tage["ereignis"].notna().astype(int),
    "temperatur": tage["temperatur"].ffill().bfill(),
    "niederschlag": tage["niederschlag"].fillna(0),
}, index=tage.index)
merkmale = merkmale.join(pd.get_dummies(tage.index.dayofweek, prefix="wt", dtype=int).set_index(tage.index))
merkmale = merkmale.join(pd.get_dummies(tage.index.month, prefix="monat", dtype=int).set_index(tage.index))

TRENNUNG = "2025-04-01"
lern = merkmale.index < TRENNUNG
X_lern, X_test = merkmale[lern], merkmale[~lern]
y_lern, y_test = tage["umsatz"][lern], tage["umsatz"][~lern]
print(f"Lernen: {lern.sum()} Tage, Prüfen: {(~lern).sum()} Tage, {merkmale.shape[1]} Merkmale.")
"""),
code("""
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

def bewerte(name, modell):
    # Trainiert das Modell auf dem Lernzeitraum und misst den Fehler auf dem Prüfzeitraum
    modell.fit(X_lern, y_lern)
    vorhersage = modell.predict(X_test)
    return {"modell": name,
            "MAE in €": mean_absolute_error(y_test, vorhersage),
            "MAPE in %": mean_absolute_percentage_error(y_test, vorhersage) * 100,
            "vorhersage": vorhersage}

ergebnisse = [bewerte("Lineare Regression", LinearRegression()),
              bewerte("Gradient Boosting", GradientBoostingRegressor(n_estimators=300, max_depth=3,
                                                                       learning_rate=0.05, random_state=2026))]
mittelwert = np.full(len(y_test), y_lern.iloc[-365:].mean())
ergebnisse.append({"modell": "Mittelwert der letzten 365 Lerntage", "MAE in €": mean_absolute_error(y_test, mittelwert),
                   "MAPE in %": mean_absolute_percentage_error(y_test, mittelwert) * 100, "vorhersage": mittelwert})
pd.DataFrame([{k: v for k, v in e.items() if k != "vorhersage"} for e in ergebnisse]).round(1)
"""),
code("""
abb, achse = plt.subplots(figsize=(9, 4))
achse.plot(y_test.index, y_test, label="Ist")
for e in ergebnisse[:2]:
    achse.plot(y_test.index, e["vorhersage"], label=e["modell"], alpha=0.8)
achse.set_xlabel("Tag")
achse.set_ylabel("Tagesumsatz in €")
achse.set_title("Backtesting April 2025 bis März 2026: Beide Modelle treffen das Wochenmuster, Ausreißer nicht")
achse.set_ylim(0)
achse.legend()
plt.show()
"""),
md("""
### Basiseffekt bei Rumpfjahren

Wer Jahresumsätze vergleicht, sieht 2017 und 2026 als Einbruch. Beide Jahre sind unvollständig:
2017 beginnt am 15. März, 2026 endet am 31. März. Der Umsatz je Tag zeigt das echte Bild.
"""),
code("""
jahre = tage.groupby(tage.index.year).agg(tage=("umsatz", "size"), umsatz=("umsatz", "sum"))
jahre.index.name = "jahr"
jahre["umsatz_je_tag"] = jahre["umsatz"] / jahre["tage"]
jahre["veraenderung_je_tag_pct"] = jahre["umsatz_je_tag"].pct_change() * 100
jahre.round(1)
"""),
md("""
## Ergebnis

Gradient Boosting schlägt die lineare Regression und beide schlagen den naiven Mittelwert; der
MAPE bleibt zweistellig, weil einzelne Tage (Ereignisse, Feiertage) weit vom Muster abweichen.
Der Trend und das Wochenmuster erklären den größten Teil der Varianz — das Wetter wenig, wie
Notebook 05 zeigt.

## Was offen bleibt

Ein echtes Prognosemodell würde die Vergangenheit der Reihe selbst als Merkmal nutzen (Lags,
gleitende Mittel) und die Prüfung über mehrere Zeitfenster wiederholen (rollierendes
Backtesting). Beides ist hier bewusst weggelassen, damit der Unterschied zwischen erklärenden
Merkmalen und Autokorrelation sichtbar bleibt.
"""),
]

schreiben("04_nachfrageprognose.ipynb", ZELLEN)
```

- [ ] **Step 2: Bauen, ausführen, prüfen**

```bash
python3 notebooks/quellen/bau_04.py
jupyter nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 notebooks/04_nachfrageprognose.ipynb
python3 notebooks/quellen/pruefe_ausgaben.py notebooks/04_nachfrageprognose.ipynb
```
Expected: keine Fehler; Tabelle mit drei Modellen, Gradient Boosting mit dem kleinsten MAE; Laufzeit unter zwei Minuten.

- [ ] **Step 3: Commit**

```bash
git -c core.fileMode=false add notebooks/quellen/bau_04.py notebooks/04_nachfrageprognose.ipynb
git -c core.fileMode=false commit -m "notebooks: 04 Nachfrageprognose — STL, Merkmale, Regression und Gradient Boosting, Backtesting, Basiseffekt" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 6: Notebook 05 — Wetter und Ereignisse, externe Quellen

**Files:**
- Create: `notebooks/quellen/bau_05.py`, `notebooks/daten_extern/vpi_jahr.csv`, `notebooks/daten_extern/README.md`
- Produces: `notebooks/05_wetter_und_ereignisse.ipynb`; beim Ausführen entstehen `notebooks/daten_extern/wetter_open_meteo.csv`, `schulferien_bayern.csv`, `kickers_heimspiele.csv` (werden mitcommittet)

**Interfaces:**
- Consumes: `gemeinsam` (Task 1); `fact_orders`, `dim_date`, `dim_weather`, `v_kennzahlen_jahr`; Pakete `requests`, `holidays`, `statsmodels`.
- Produces: die drei CSV-Dateien (Spalten siehe Code) für spätere Phasen (BM-Lab, Deck).

- [ ] **Step 1: Kuratierter Verbraucherpreisindex**

`notebooks/daten_extern/vpi_jahr.csv` (Destatis, Verbraucherpreisindex für Deutschland, Basis 2020 = 100; 2021–2025 aus der Tabelle „Verbraucherpreisindizes Gesamtindex und 12 Abteilungen", Stand 10.09.2026; 2017–2020 aus der langen Reihe Basis 2015 = 100 (Statistischer Bericht, erschienen 17.01.2023: 102,0 · 103,8 · 105,3 · 105,8) umbasiert auf 2020 = 100; 2026 = Wert 2025, weil das Jahr nicht abgeschlossen ist):

```csv
jahr,vpi_2020_100,quelle
2017,96.4,Destatis lange Reihe (2015=100: 102.0) umbasiert
2018,98.1,Destatis lange Reihe (2015=100: 103.8) umbasiert
2019,99.5,Destatis lange Reihe (2015=100: 105.3) umbasiert
2020,100.0,Destatis lange Reihe (2015=100: 105.8) umbasiert
2021,103.1,Destatis Tabelle 61111 Jahresdurchschnitt Stand 2026-09-10
2022,110.2,Destatis Tabelle 61111 Jahresdurchschnitt Stand 2026-09-10
2023,116.7,Destatis Tabelle 61111 Jahresdurchschnitt Stand 2026-09-10
2024,119.3,Destatis Tabelle 61111 Jahresdurchschnitt Stand 2026-09-10
2025,121.9,Destatis Tabelle 61111 Jahresdurchschnitt Stand 2026-09-10
2026,121.9,vorläufig: Wert 2025 (Jahr nicht abgeschlossen)
```

`notebooks/daten_extern/README.md`:

```markdown
# Externe Daten (einmal geholt, versioniert)

| Datei | Quelle | Stand | Lizenz |
|---|---|---|---|
| `wetter_open_meteo.csv` | Open-Meteo Historical Weather API, Würzburg 49,79 N / 9,95 O, täglich `temperature_2m_max/min`, `precipitation_sum` | 13.09.2026 | Daten CC BY 4.0, API für nicht-kommerzielle Nutzung kostenfrei |
| `schulferien_bayern.csv` | OpenHolidays API (`openholidaysapi.org/SchoolHolidays`, DE-BY) | 13.09.2026 | frei (Open Data der Länder) |
| `kickers_heimspiele.csv` | OpenLigaDB (`api.openligadb.de`), Würzburger Kickers: 2. Bundesliga 2016/17 und 2020/21, 3. Liga 2017/18 bis 2019/20 und 2021/22; Regionalliga Bayern 2022/23 bis 2025/26 dort nicht abgedeckt | 13.09.2026 | frei |
| `vpi_jahr.csv` | Destatis, Verbraucherpreisindex Deutschland, 2020 = 100 (Herkunft je Zeile in der Spalte `quelle`) | 10.09.2026 | Datenlizenz Deutschland 2.0 |

Notebook 05 liest zuerst diese Dateien; nur wenn eine fehlt oder dort `AKTUALISIEREN = True`
gesetzt ist, ruft es die Anbieter erneut. Feiertage kommen aus dem Python-Paket `holidays`
(MIT) und brauchen keine Datei.
```

- [ ] **Step 2: `notebooks/quellen/bau_05.py`**

```python
#!/usr/bin/env python3
"""bau_05.py — schreibt notebooks/05_wetter_und_ereignisse.ipynb."""
from gemeinsam import code, kopf, md, schreiben

ZELLEN = kopf("05", "Wetter und Ereignisse", "05_wetter_und_ereignisse.ipynb") + [
md("""
## Fragestellung

Wie stark hängt der Tagesumsatz von Wetter, Wochentag, Feiertagen und Ereignissen ab — und
was ändert sich, wenn wir statt des eingebauten Wetters gemessene Daten von außen nehmen?

## Daten

Tagesumsatz aller Filialen aus `fact_orders`, Kalender aus `dim_date`, Wetter aus
`dim_weather`. Dazu fünf externe Quellen: Open-Meteo (gemessenes Wetter), Feiertage Bayern
(Paket `holidays`), Schulferien Bayern (OpenHolidays API), Heimspiele der Würzburger Kickers
(OpenLigaDB) und der Verbraucherpreisindex (Destatis, kuratierte CSV). Jede API-Antwort wird
einmal geholt und unter `daten_extern/` versioniert.

## Vorgehen

Erst eine Regression des Tagesumsatzes auf die eingebauten Merkmale, dann die externen
Quellen holen, über das Datum verknüpfen und die Fragen stellen, die nur sie beantworten:
Stimmt `dim_weather` mit dem gemessenen Wetter überein? Zählen Ferien und Heimspiele? Wie
sieht der Umsatz real statt nominal aus?
"""),
code("""
tage = lade_sql(\"\"\"
    SELECT o.date AS tag, sum(o.net_total) AS umsatz, count(*) AS bestellungen,
           d.year AS jahr, d.day_name AS wochentag, d.is_holiday AS feiertag, d.holiday_name AS feiertagsname,
           d.special_event AS ereignis, w.temperature_celsius AS temperatur, w.precipitation_mm AS niederschlag,
           w.condition AS wetterlage
    FROM fact_orders o
    JOIN dim_date d ON d.date = o.date
    LEFT JOIN dim_weather w ON w.date = o.date
    GROUP BY o.date, d.year, d.day_name, d.is_holiday, d.holiday_name, d.special_event,
             w.temperature_celsius, w.precipitation_mm, w.condition
    ORDER BY o.date\"\"\")
tage["tag"] = pd.to_datetime(tage["tag"])
tage["feiertag"] = tage["feiertag"].astype(int)
tage["ereignis"] = tage["ereignis"].fillna("keines")
print(f"{len(tage)} Tage, {tage['tag'].min().date()} bis {tage['tag'].max().date()}.")
tage.head()
"""),
md("""
### Regression auf die eingebauten Merkmale

Eine lineare Regression mit `statsmodels` — die Jahre als Kategorie fangen das Wachstum ab,
damit Wetter und Kalender nicht den Trend erklären müssen.
"""),
code("""
import statsmodels.formula.api as smf

modell = smf.ols("umsatz ~ temperatur + niederschlag + C(wochentag) + feiertag + C(ereignis) + C(jahr)", data=tage).fit()
koeffizienten = pd.DataFrame({"koeffizient": modell.params, "p_wert": modell.pvalues}).round(3)
print(f"R² = {modell.rsquared:.3f} auf {int(modell.nobs)} Tagen.")
koeffizienten.loc[[z for z in koeffizienten.index if not z.startswith("C(jahr)")]]
"""),
md("""
Wochentage und Ereignisse tragen; Kiliani liegt mehrere Tausend Euro über einem gewöhnlichen
Tag. Temperatur und Niederschlag haben kleine Koeffizienten — das eingebaute Wetter erklärt
wenig.

### Externe Quellen holen (oder aus der Datei lesen)
"""),
code("""
import requests
from pathlib import Path

DATEN = Path("daten_extern")
AKTUALISIEREN = False   # True: Anbieter erneut abrufen und die CSV-Dateien überschreiben

def hole_oder_lies(name, holen):
    # Liest daten_extern/<name>.csv, wenn vorhanden; sonst ruft die Quelle und speichert die Antwort
    pfad = DATEN / f"{name}.csv"
    if pfad.exists() and not AKTUALISIEREN:
        return pd.read_csv(pfad)
    daten = holen()
    DATEN.mkdir(exist_ok=True)
    daten.to_csv(pfad, index=False)
    print(f"{name}: {len(daten)} Zeilen von der Quelle geholt und gespeichert.")
    return daten

def hole_wetter():
    # Open-Meteo Archive: Tageswerte für Würzburg über den ganzen Zeitraum, ohne Schlüssel
    antwort = requests.get("https://archive-api.open-meteo.com/v1/archive", timeout=60, params={
        "latitude": 49.79, "longitude": 9.95, "start_date": "2017-03-15", "end_date": "2026-03-31",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum", "timezone": "Europe/Berlin"})
    antwort.raise_for_status()
    d = antwort.json()["daily"]
    return pd.DataFrame({"tag": d["time"], "tmax": d["temperature_2m_max"],
                         "tmin": d["temperature_2m_min"], "niederschlag_mm": d["precipitation_sum"]})

def hole_schulferien():
    # OpenHolidays API erlaubt höchstens 1095 Tage je Anfrage, deshalb in Blöcken
    zeilen = []
    for von, bis in [("2017-01-01", "2019-12-31"), ("2020-01-01", "2022-12-31"),
                     ("2023-01-01", "2025-12-31"), ("2026-01-01", "2026-12-31")]:
        antwort = requests.get("https://openholidaysapi.org/SchoolHolidays", timeout=60, params={
            "countryIsoCode": "DE", "subdivisionCode": "DE-BY", "validFrom": von, "validTo": bis, "languageIsoCode": "DE"})
        antwort.raise_for_status()
        for ferien in antwort.json():
            zeilen.append({"von": ferien["startDate"], "bis": ferien["endDate"], "name": ferien["name"][0]["text"]})
    return pd.DataFrame(zeilen).drop_duplicates()

def hole_kickers():
    # OpenLigaDB: Heimspiele der Würzburger Kickers in den Saisons, die die Datenbank abdeckt
    saisons = [("bl2", 2016), ("bl3", 2017), ("bl3", 2018), ("bl3", 2019), ("bl2", 2020), ("bl3", 2021)]
    zeilen = []
    for liga, saison in saisons:
        antwort = requests.get(f"https://api.openligadb.de/getmatchdata/{liga}/{saison}", timeout=60)
        antwort.raise_for_status()
        for spiel in antwort.json():
            if "rzburg" in spiel["team1"]["teamName"]:
                zeilen.append({"tag": spiel["matchDateTime"][:10], "liga": liga, "saison": saison,
                               "gegner": spiel["team2"]["teamName"]})
    return pd.DataFrame(zeilen)

wetter = hole_oder_lies("wetter_open_meteo", hole_wetter)
schulferien = hole_oder_lies("schulferien_bayern", hole_schulferien)
kickers = hole_oder_lies("kickers_heimspiele", hole_kickers)
vpi = pd.read_csv(DATEN / "vpi_jahr.csv")   # kuratiert, siehe daten_extern/README.md
pd.DataFrame({"quelle": ["Open-Meteo", "Schulferien", "Kickers-Heimspiele", "VPI"],
              "zeilen": [len(wetter), len(schulferien), len(kickers), len(vpi)]})
"""),
md("""
Feiertage kommen aus dem Paket `holidays`; ein Vergleich mit `dim_date.is_holiday` zeigt,
wo die Fallstudie und das Paket verschieden zählen.
"""),
code("""
import holidays

bayern = holidays.country_holidays("DE", subdiv="BY", years=range(2017, 2027))
tage["feiertag_paket"] = tage["tag"].dt.date.map(lambda t: int(t in bayern))
unterschied = tage[tage["feiertag"] != tage["feiertag_paket"]][["tag", "feiertagsname", "feiertag", "feiertag_paket"]]
print(f"{len(unterschied)} Tage zählen dim_date und das Paket verschieden:")
unterschied.groupby("feiertagsname", dropna=False).size().rename("tage").reset_index()
"""),
md("""
Mariä Himmelfahrt ist in Bayern nur in überwiegend katholischen Gemeinden Feiertag — in
Würzburg ja, im Paket standardmäßig nein. `dim_date` folgt Würzburg.

### Verknüpfen über das Datum
"""),
code("""
wetter["tag"] = pd.to_datetime(wetter["tag"])
ferientage = set()
for zeile in schulferien.itertuples():
    ferientage.update(pd.date_range(zeile.von, zeile.bis))
kickers["tag"] = pd.to_datetime(kickers["tag"])

daten = tage.merge(wetter, on="tag", how="left")
daten["ferien"] = daten["tag"].isin(ferientage).astype(int)
daten["heimspiel"] = daten["tag"].isin(set(kickers["tag"])).astype(int)
daten = daten.merge(vpi[["jahr", "vpi_2020_100"]], on="jahr", how="left")
daten[["tag", "umsatz", "temperatur", "tmax", "niederschlag", "niederschlag_mm", "ferien", "heimspiel", "vpi_2020_100"]].head()
"""),
md("### Stimmt das eingebaute Wetter mit dem gemessenen überein?"),
code("""
import matplotlib.pyplot as plt

r_temp = daten["temperatur"].corr(daten["tmax"])
r_regen = daten["niederschlag"].corr(daten["niederschlag_mm"])
print(f"Korrelation Temperatur (dim_weather) mit Tageshöchsttemperatur (Open-Meteo): r = {r_temp:.3f}")
print(f"Korrelation Niederschlag (dim_weather) mit gemessenem Niederschlag: r = {r_regen:.3f}")

abb, achse = plt.subplots(figsize=(9, 4))
monat = daten.set_index("tag")[["temperatur", "tmax"]].resample("MS").mean()
achse.plot(monat.index, monat["temperatur"], label="dim_weather (synthetisch)")
achse.plot(monat.index, monat["tmax"], label="Open-Meteo (gemessen, Tageshöchstwert)")
achse.set_xlabel("Monat")
achse.set_ylabel("Temperatur in °C, Monatsmittel")
achse.set_title("Das eingebaute Wetter folgt der Jahreszeit, nicht dem gemessenen Tag")
achse.legend()
plt.show()
"""),
md("""
Der Bestand ist synthetisch: Sein Wetter hat den richtigen Jahresgang, aber keinen Bezug zum
tatsächlichen Wetter eines Tages. Das ist kein Fehler des Datensatzes, aber eine Grenze, die
man kennen muss, bevor man Wettereffekte interpretiert.

### Regression mit den externen Merkmalen
"""),
code("""
modell_extern = smf.ols("umsatz ~ tmax + niederschlag_mm + C(wochentag) + feiertag + ferien + heimspiel + C(ereignis) + C(jahr)",
                        data=daten).fit()
print(f"R² eingebaut: {modell.rsquared:.3f}, R² extern: {modell_extern.rsquared:.3f}")
pd.DataFrame({"koeffizient": modell_extern.params, "p_wert": modell_extern.pvalues}).loc[
    ["tmax", "niederschlag_mm", "feiertag", "ferien", "heimspiel"]].round(3)
"""),
md("""
Ferien und Heimspiele haben keinen messbaren Effekt — der Generator kannte sie nicht. Genau
das ist der Befund: Externe Merkmale helfen nur, wenn die Zielgröße sie enthält. Bei echten
Kassendaten wäre der Test derselbe, das Ergebnis vermutlich ein anderes.

### Umsatz real statt nominal
"""),
code("""
jahre = lade_sql("SELECT jahr, umsatz FROM v_kennzahlen_jahr ORDER BY jahr").merge(vpi[["jahr", "vpi_2020_100"]], on="jahr")
jahre["umsatz_real_2020"] = jahre["umsatz"] / jahre["vpi_2020_100"] * 100
jahre["nominal_pct"] = jahre["umsatz"].pct_change() * 100
jahre["real_pct"] = jahre["umsatz_real_2020"].pct_change() * 100
jahre.round(1)
"""),
md("""
## Ergebnis

Wochentag und Ereignisse erklären den Tagesumsatz, das Wetter kaum — weder das eingebaute
noch das gemessene, weil der Bestand synthetisch ist und das Wetter nur der Jahreszeit folgt.
Ferien und Heimspiele bringen nichts, aus demselben Grund. Der Verbraucherpreisindex zeigt,
dass ein Teil des nominalen Wachstums seit 2021 Preissteigerung ist.

## Was offen bleibt

Die Kickers-Daten decken die Regionalliga-Saisons ab 2022 nicht ab; wer sie braucht, pflegt
eine CSV von Hand nach. Der VPI ist ein Jahreswert — für Monatsreihen liefert Destatis
Monatsindizes über GENESIS-Online (Konto erforderlich).
"""),
]

schreiben("05_wetter_und_ereignisse.ipynb", ZELLEN)
```

- [ ] **Step 3: Bauen, ausführen, prüfen**

```bash
python3 notebooks/quellen/bau_05.py
jupyter nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 notebooks/05_wetter_und_ereignisse.ipynb
python3 notebooks/quellen/pruefe_ausgaben.py notebooks/05_wetter_und_ereignisse.ipynb
ls -la notebooks/daten_extern/
```
Expected: keine Fehler; drei neue CSV-Dateien (`wetter_open_meteo.csv` 3.304 Zeilen, `schulferien_bayern.csv` rund 70, `kickers_heimspiele.csv` 110); Korrelation Temperatur nahe null (|r| < 0,15); der Unterschied bei den Feiertagen nennt Mariä Himmelfahrt. Ein zweiter Lauf holt nichts mehr von den Anbietern (keine „geholt und gespeichert"-Zeile).

- [ ] **Step 4: Commit**

```bash
git -c core.fileMode=false add notebooks/quellen/bau_05.py notebooks/05_wetter_und_ereignisse.ipynb notebooks/daten_extern/
git -c core.fileMode=false commit -m "notebooks: 05 Wetter und Ereignisse — Regression, Open-Meteo, Feiertage, Schulferien, Kickers, VPI (daten_extern versioniert)" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 7: Notebook 06 — Zufriedenheit erklären

**Files:**
- Create: `notebooks/quellen/bau_06.py`
- Produces: `notebooks/06_zufriedenheit_erklaeren.ipynb`

**Interfaces:**
- Consumes: `gemeinsam` (Task 1); `fact_orders` (142.317 Zeilen mit `satisfaction_score`), `dim_date`, `dim_branch`.

- [ ] **Step 1: `notebooks/quellen/bau_06.py`**

```python
#!/usr/bin/env python3
"""bau_06.py — schreibt notebooks/06_zufriedenheit_erklaeren.ipynb."""
from gemeinsam import code, kopf, md, schreiben

ZELLEN = kopf("06", "Zufriedenheit erklären", "06_zufriedenheit_erklaeren.ipynb") + [
md("""
## Fragestellung

Was unterscheidet zufriedene von unzufriedenen Bestellungen — Kanal, Wartezeit, Filiale,
Uhrzeit oder Wochentag?

## Daten

Die 142.317 Bestellungen mit `satisfaction_score` (18,9 Prozent aller Bestellungen — eine
selbstselektierte Stichprobe, siehe `dataset/README.md`), dazu Kanal, Bestelldauer, Filiale,
Stunde und Wochentag.

## Vorgehen

Die Zufriedenheit in drei Klassen teilen (niedrig unter 3,5, mittel, hoch ab 4,2), einen
Entscheidungsbaum mit Tiefe 3 zeichnen, einen Random Forest auf einem Prüfdatensatz bewerten
und die Merkmalswichtigkeit lesen.
"""),
code("""
daten = lade_sql(\"\"\"
    SELECT o.satisfaction_score AS zufriedenheit, o.order_channel AS kanal, o.order_duration_min AS dauer_min,
           b.branch_name AS filiale, o.hour AS stunde, d.day_of_week AS wochentag, d.is_weekend AS wochenende
    FROM fact_orders o
    JOIN dim_date d ON d.date = o.date
    JOIN dim_branch b ON b.branch_id = o.branch_id
    WHERE o.satisfaction_score IS NOT NULL\"\"\")

def klasse(wert):
    # Drei Klassen mit festen Grenzen, damit die Klassen über Notebooks hinweg gleich bleiben
    if wert < 3.5:
        return "niedrig"
    if wert < 4.2:
        return "mittel"
    return "hoch"

daten["klasse"] = daten["zufriedenheit"].apply(klasse)
daten["wochenende"] = daten["wochenende"].astype(int)
daten["klasse"].value_counts().rename("bestellungen").to_frame()
"""),
md("### Merkmale vorbereiten"),
code("""
from sklearn.model_selection import train_test_split

X = pd.get_dummies(daten[["kanal", "dauer_min", "filiale", "stunde", "wochentag", "wochenende"]],
                   columns=["kanal", "filiale"], dtype=int)
y = daten["klasse"]
X_lern, X_test, y_lern, y_test = train_test_split(X, y, test_size=0.25, random_state=2026, stratify=y)
print(f"{X_lern.shape[0]} Bestellungen zum Lernen, {X_test.shape[0]} zum Prüfen, {X.shape[1]} Merkmale.")
"""),
md("### Ein Entscheidungsbaum mit Tiefe 3"),
code("""
from sklearn.tree import DecisionTreeClassifier, plot_tree
import matplotlib.pyplot as plt

baum = DecisionTreeClassifier(max_depth=3, random_state=2026).fit(X_lern, y_lern)
print(f"Trefferquote des Baums auf dem Prüfdatensatz: {baum.score(X_test, y_test) * 100:.1f} Prozent.")
abb, achse = plt.subplots(figsize=(16, 8))
plot_tree(baum, feature_names=list(X.columns), class_names=list(baum.classes_), filled=False, rounded=True, fontsize=9, ax=achse)
achse.set_title("Die erste Trennung ist die Bestelldauer — nichts anderes zählt annähernd so viel")
plt.show()
"""),
md("### Random Forest"),
code("""
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, classification_report

wald = RandomForestClassifier(n_estimators=200, max_depth=8, n_jobs=-1, random_state=2026).fit(X_lern, y_lern)
vorhersage = wald.predict(X_test)
print(f"Trefferquote des Random Forest: {wald.score(X_test, y_test) * 100:.1f} Prozent.")
print(classification_report(y_test, vorhersage, digits=3))
pd.DataFrame(confusion_matrix(y_test, vorhersage, labels=wald.classes_),
             index=[f"ist {k}" for k in wald.classes_], columns=[f"vorhergesagt {k}" for k in wald.classes_])
"""),
code("""
wichtigkeit = pd.Series(wald.feature_importances_, index=X.columns).sort_values(ascending=True).tail(12)
abb, achse = plt.subplots(figsize=(9, 5))
achse.barh(wichtigkeit.index, wichtigkeit.values)
achse.set_xlabel("Merkmalswichtigkeit (Anteil an der Verringerung der Unreinheit)")
achse.set_title("Die Bestelldauer erklärt die Zufriedenheit fast allein")
achse.set_xlim(0)
plt.tight_layout()
plt.show()
"""),
code("""
# Zur Einordnung: mittlere Zufriedenheit je Dauerklasse
daten["dauer_klasse"] = pd.cut(daten["dauer_min"], bins=[0, 5, 10, 15, 20, 60], labels=["bis 5", "6–10", "11–15", "16–20", "über 20"])
daten.groupby("dauer_klasse", observed=True).agg(bestellungen=("zufriedenheit", "size"), zufriedenheit=("zufriedenheit", "mean")).round(2)
"""),
md("""
## Ergebnis

Beide Modelle finden dasselbe: Die Bestelldauer trennt die Klassen, alles andere trägt wenig
bei. Der Random Forest ist etwas treffsicherer als der Baum, aber die Klasse „mittel" bleibt
schwer — sie liegt zwischen den beiden anderen, ohne eigenes Muster.

## Was offen bleibt

Die Merkmalswichtigkeit sagt, welche Merkmale das Modell nutzt, nicht, was die Zufriedenheit
verursacht. Und die Stichprobe ist selbstselektiert: Wer bewertet, ist nicht zufällig gewählt.
Beides gehört in jede Interpretation.
"""),
]

schreiben("06_zufriedenheit_erklaeren.ipynb", ZELLEN)
```

- [ ] **Step 2: Bauen, ausführen, prüfen**

```bash
python3 notebooks/quellen/bau_06.py
jupyter nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 notebooks/06_zufriedenheit_erklaeren.ipynb
python3 notebooks/quellen/pruefe_ausgaben.py notebooks/06_zufriedenheit_erklaeren.ipynb
```
Expected: keine Fehler; `dauer_min` an der Spitze der Wichtigkeit; Laufzeit unter drei Minuten.

- [ ] **Step 3: Commit**

```bash
git -c core.fileMode=false add notebooks/quellen/bau_06.py notebooks/06_zufriedenheit_erklaeren.ipynb
git -c core.fileMode=false commit -m "notebooks: 06 Zufriedenheit erklären — Klassen, Entscheidungsbaum, Random Forest, Merkmalswichtigkeit" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 8: Notebook 07 — Ausreißer im Tagesumsatz

**Files:**
- Create: `notebooks/quellen/bau_07.py`
- Produces: `notebooks/07_ausreisser_tagesumsatz.ipynb`

**Interfaces:**
- Consumes: `gemeinsam` (Task 1); `fact_orders`, `dim_date`, `dim_branch` (`opening_date`).

- [ ] **Step 1: `notebooks/quellen/bau_07.py`**

```python
#!/usr/bin/env python3
"""bau_07.py — schreibt notebooks/07_ausreisser_tagesumsatz.ipynb."""
from gemeinsam import code, kopf, md, schreiben

ZELLEN = kopf("07", "Ausreißer im Tagesumsatz", "07_ausreisser_tagesumsatz.ipynb") + [
md("""
## Fragestellung

Welche Tage fallen im Umsatz einer Filiale aus dem Rahmen — und lassen sie sich erklären?

## Daten

Tagesumsatz und Bestellungen je Filiale aus `fact_orders` (17.744 Filialtage), Kalender aus
`dim_date` (Feiertag, Ereignis), Eröffnungsdatum aus `dim_branch`.

## Vorgehen

Drei Verfahren nebeneinander: z-Score je Filiale, Interquartilsabstand (IQR) je Filiale und
Isolation Forest über Umsatz, Bestellungen und Wochentag. Die Treffer werden mit Kalender und
Eröffnung erklärt — was übrig bleibt, ist der eigentliche Befund.
"""),
code("""
tage = lade_sql(\"\"\"
    SELECT o.date AS tag, b.branch_name AS filiale, b.opening_date AS eroeffnet, sum(o.net_total) AS umsatz,
           count(*) AS bestellungen, d.day_of_week AS wochentag, d.is_weekend AS wochenende,
           d.holiday_name AS feiertag, d.special_event AS ereignis
    FROM fact_orders o
    JOIN dim_date d ON d.date = o.date
    JOIN dim_branch b ON b.branch_id = o.branch_id
    GROUP BY o.date, b.branch_name, b.opening_date, d.day_of_week, d.is_weekend, d.holiday_name, d.special_event
    ORDER BY b.branch_name, o.date\"\"\")
tage["tag"] = pd.to_datetime(tage["tag"])
tage["eroeffnet"] = pd.to_datetime(tage["eroeffnet"])
tage["tage_seit_eroeffnung"] = (tage["tag"] - tage["eroeffnet"]).dt.days
print(f"{len(tage)} Filialtage für {tage['filiale'].nunique()} Filialen.")
tage.head()
"""),
md("### z-Score je Filiale"),
code("""
def z_score(spalte):
    # Abstand vom Filialmittel in Standardabweichungen — je Filiale, weil die Größen verschieden sind
    return (spalte - spalte.mean()) / spalte.std()

tage["z"] = tage.groupby("filiale")["umsatz"].transform(z_score)
tage["ausreisser_z"] = tage["z"].abs() > 3
print(f"{int(tage['ausreisser_z'].sum())} Filialtage liegen mehr als drei Standardabweichungen vom Filialmittel entfernt.")
"""),
md("### Interquartilsabstand (IQR) je Filiale"),
code("""
def iqr_grenzen(gruppe):
    # Tukeys Regel: alles außerhalb von 1,5 IQR unter Q1 oder über Q3 gilt als Ausreißer
    q1, q3 = gruppe["umsatz"].quantile([0.25, 0.75])
    iqr = q3 - q1
    return (gruppe["umsatz"] < q1 - 1.5 * iqr) | (gruppe["umsatz"] > q3 + 1.5 * iqr)

tage["ausreisser_iqr"] = tage.groupby("filiale", group_keys=False).apply(iqr_grenzen, include_groups=False)
print(f"{int(tage['ausreisser_iqr'].sum())} Filialtage nach der IQR-Regel.")
"""),
md("### Isolation Forest"),
code("""
from sklearn.ensemble import IsolationForest

merkmale = pd.DataFrame({
    "umsatz_relativ": tage["umsatz"] / tage.groupby("filiale")["umsatz"].transform("median"),
    "bestellungen_relativ": tage["bestellungen"] / tage.groupby("filiale")["bestellungen"].transform("median"),
    "wochentag": tage["wochentag"],
})
wald = IsolationForest(contamination=0.01, random_state=2026).fit(merkmale)
tage["ausreisser_forest"] = wald.predict(merkmale) == -1
tage["anomalie_wert"] = -wald.score_samples(merkmale)
pd.DataFrame({"verfahren": ["z-Score", "IQR", "Isolation Forest"],
              "treffer": [int(tage["ausreisser_z"].sum()), int(tage["ausreisser_iqr"].sum()), int(tage["ausreisser_forest"].sum())]})
"""),
md("### Treffer erklären"),
code("""
def erklaerung(zeile):
    # Eine Erklärung aus Kalender und Eröffnung; bleibt keine, ist der Tag ein echter Befund
    if zeile["tage_seit_eroeffnung"] <= 14:
        return "Eröffnungsphase"
    if pd.notna(zeile["ereignis"]):
        return zeile["ereignis"]
    if pd.notna(zeile["feiertag"]):
        return zeile["feiertag"]
    if zeile["wochenende"]:
        return "Wochenende"
    return "unerklärt"

treffer = tage[tage["ausreisser_forest"]].copy()
treffer["erklaerung"] = treffer.apply(erklaerung, axis=1)
treffer["erklaerung"].value_counts().rename("filialtage").to_frame()
"""),
code("""
treffer.sort_values("anomalie_wert", ascending=False)[["tag", "filiale", "umsatz", "bestellungen", "z", "erklaerung"]].head(15).round(2)
"""),
code("""
import matplotlib.pyplot as plt

FILIALE = "BM Europastern"
reihe = tage[tage["filiale"] == FILIALE].set_index("tag")
markiert = reihe[reihe["ausreisser_forest"]]
abb, achse = plt.subplots(figsize=(9, 4))
achse.plot(reihe.index, reihe["umsatz"], linewidth=0.6, label="Tagesumsatz")
achse.scatter(markiert.index, markiert["umsatz"], color="tab:red", s=18, zorder=3, label="Isolation Forest")
achse.set_xlabel("Tag")
achse.set_ylabel("Tagesumsatz in €")
achse.set_title(f"{FILIALE}: Die markierten Tage sind Feste, Feiertage und die Eröffnung")
achse.set_ylim(0)
achse.legend()
plt.show()
"""),
md("""
## Ergebnis

Die drei Verfahren markieren überwiegend dieselben Tage: Kiliani und die Sommerfeste nach oben,
Weihnachten und Eröffnungstage nach unten. Was der Isolation Forest zusätzlich findet, sind
Tage mit ungewöhnlichem Verhältnis von Umsatz zu Bestellungen — die sieht der z-Score nicht.

## Was offen bleibt

„Unerklärt" heißt: nicht aus dem Kalender erklärbar. Im synthetischen Bestand ist das
Rauschen; in echten Daten wäre es der Anfang einer Nachfrage bei der Filiale.
"""),
]

schreiben("07_ausreisser_tagesumsatz.ipynb", ZELLEN)
```

- [ ] **Step 2: Bauen, ausführen, prüfen**

```bash
python3 notebooks/quellen/bau_07.py
jupyter nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 notebooks/07_ausreisser_tagesumsatz.ipynb
python3 notebooks/quellen/pruefe_ausgaben.py notebooks/07_ausreisser_tagesumsatz.ipynb
```
Expected: keine Fehler; rund 177 Treffer des Isolation Forest (1 Prozent von 17.744); die Erklärungstabelle nennt Kiliani, Eröffnungsphase und Weihnachtstage.

- [ ] **Step 3: Commit**

```bash
git -c core.fileMode=false add notebooks/quellen/bau_07.py notebooks/07_ausreisser_tagesumsatz.ipynb
git -c core.fileMode=false commit -m "notebooks: 07 Ausreißer im Tagesumsatz — z-Score, IQR, Isolation Forest, Treffer erklärt" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 9: Notebook 08 — Sentiment der Rezensionen

**Files:**
- Create: `notebooks/quellen/bau_08.py`
- Produces: `notebooks/08_sentiment_rezensionen.ipynb`

**Interfaces:**
- Consumes: `gemeinsam` (Task 1); `fact_reviews` (10.000 Zeilen, `stars`, `review_text`, `order_id`, `product_id`, `branch_id`), `fact_orders` (`order_channel`, `order_duration_min`), `dim_product`, `dim_branch`; `transformers` (Modell `oliverguhr/german-sentiment-bert`, Labels `positive`/`negative`/`neutral`; Laden rund 40 s, 500 Texte rund 20 s auf CPU).
- Vorab gemessen (13.09.2026, lokale CSV): Wortliste rund 76 Prozent Trefferquote mit 2.371 unentschiedenen Texten; TF-IDF + logistische Regression 100 Prozent — die Texte stammen aus einem Generator mit festen Bausteinen, das Notebook benennt das; BERT rund 93 Prozent auf einer Stichprobe.

- [ ] **Step 1: `notebooks/quellen/bau_08.py`**

```python
#!/usr/bin/env python3
"""bau_08.py — schreibt notebooks/08_sentiment_rezensionen.ipynb."""
from gemeinsam import PAKETE, code, kopf, md, schreiben

ZELLEN = kopf("08", "Sentiment der Rezensionen", "08_sentiment_rezensionen.ipynb", pakete=PAKETE + " transformers torch") + [
md("""
## Fragestellung

Lässt sich aus dem Text einer Rezension lesen, ob sie positiv oder negativ ist — und was
sagt das Sentiment über Kanal, Wartezeit, Filiale und Produkt?

## Daten

`fact_reviews`: 10.000 deutsche Rezensionen mit Sternen (1 bis 5), jede an eine bewertete
Bestellung gehängt. Die Texte sind simuliert (Generator mit Satzbausteinen, danach sprachlich
geglättet, siehe `dataset/README.md`). Polarität: 1–2 Sterne negativ, 4–5 positiv; die
3-Sterne-Texte bleiben als „unentschieden" außen vor.

## Vorgehen

Vorverarbeitung (Kleinschreibung, Umlaute, Stoppwörter), eine Wortliste als Grundlinie,
dann TF-IDF mit logistischer Regression und einer Konfusionsmatrix, zum Vergleich ein
vortrainiertes deutsches BERT-Modell auf einer Stichprobe. Zum Schluss das Sentiment gegen
Kanal, Bestelldauer, Filiale und Produkt.
"""),
code("""
rezensionen = lade_sql(\"\"\"
    SELECT r.review_id, r.stars, r.review_text, r.order_id, p.product_name, p.category, b.branch_name,
           o.order_channel, o.order_duration_min
    FROM fact_reviews r
    JOIN dim_product p USING (product_id)
    JOIN dim_branch b USING (branch_id)
    JOIN fact_orders o USING (order_id)\"\"\")
print(f"{len(rezensionen)} Rezensionen.")
rezensionen["stars"].value_counts().sort_index().rename("anzahl").to_frame().T
"""),
md("""
### Vorverarbeitung

Kleinschreibung, Umlaute in einheitlicher Schreibweise (ae, oe, ue, ss — ein Teil der Texte
ist so geschrieben), alles außer Buchstaben entfernen, Stoppwörter streichen.
"""),
code("""
import re

STOPPWOERTER = set(\"\"\"der die das und oder aber ein eine einen einem einer ich wir es war waren ist sind hat hatte
haben mit von zu im in am an auf fuer den dem des nicht auch noch sehr so wie bei nach aus als dass sich mir uns
man mal dann wieder einfach ganz hier dort dieser diese dieses zum zur ueber um bis was wenn wer\"\"\".split())

def normalisiere(text):
    # Einheitliche Schreibweise: klein, Umlaute als ae/oe/ue/ss, nur Buchstaben und Leerzeichen
    text = text.lower()
    for umlaut, ersatz in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(umlaut, ersatz)
    return re.sub(r"[^a-z\\s]", " ", text)

def ohne_stoppwoerter(text):
    # Entfernt Stoppwörter, damit Zählungen die inhaltlichen Wörter treffen
    return " ".join(wort for wort in text.split() if wort not in STOPPWOERTER)

rezensionen["text_norm"] = rezensionen["review_text"].map(normalisiere).map(ohne_stoppwoerter)
polar = rezensionen[rezensionen["stars"] != 3].copy()
polar["positiv"] = (polar["stars"] >= 4).astype(int)
polar[["stars", "review_text", "text_norm"]].head(3)
"""),
md("### Grundlinie: eine Wortliste"),
code("""
POSITIV = set(\"\"\"gelungen lecker frisch schnell freundlich empfehlen perfekt zufrieden begeistert gut gerne wunderbar
hervorragend richtig angenehm knusprig saftig ausgezeichnet toll super klasse ueberzeugt ueberzeugend gepasst\"\"\".split())
NEGATIV = set(\"\"\"kalt lauwarm matschig lange warten enttaeuscht enttaeuschend schlecht nie teuer fettig wenig leider zaeh
trocken falsch fehlte schal aergerlich unfreundlich vergessen aergert katastrophal schlechter\"\"\".split())

def wortliste(text):
    # Positive Wörter zählen minus negative; das Vorzeichen ist die Polarität
    woerter = text.split()
    return sum(w in POSITIV for w in woerter) - sum(w in NEGATIV for w in woerter)

polar["score"] = polar["text_norm"].map(wortliste)
polar["wortliste_positiv"] = (polar["score"] > 0).astype(int)
treffer = (polar["wortliste_positiv"] == polar["positiv"]).mean() * 100
unentschieden = (polar["score"] == 0).mean() * 100
print(f"Die Wortliste trifft {treffer:.1f} Prozent; {unentschieden:.1f} Prozent der Texte enthalten kein Wort der Liste "
      f"und zählen als negativ.")
pd.crosstab(polar["positiv"].map({0: "ist negativ", 1: "ist positiv"}),
            polar["wortliste_positiv"].map({0: "Wortliste negativ", 1: "Wortliste positiv"}))
"""),
md("### TF-IDF und logistische Regression"),
code("""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report

X_lern, X_test, y_lern, y_test = train_test_split(polar["text_norm"], polar["positiv"], test_size=0.25,
                                                  random_state=2026, stratify=polar["positiv"])
vektor = TfidfVectorizer(ngram_range=(1, 2), min_df=3)
modell = LogisticRegression(max_iter=1000).fit(vektor.fit_transform(X_lern), y_lern)
vorhersage = modell.predict(vektor.transform(X_test))
print(classification_report(y_test, vorhersage, target_names=["negativ", "positiv"], digits=3))
pd.DataFrame(confusion_matrix(y_test, vorhersage), index=["ist negativ", "ist positiv"],
             columns=["vorhergesagt negativ", "vorhergesagt positiv"])
"""),
code("""
# Welche Wörter tragen am stärksten? Die größten und kleinsten Koeffizienten.
gewichte = pd.Series(modell.coef_[0], index=vektor.get_feature_names_out())
pd.DataFrame({"positiv": gewichte.nlargest(10).index, "negativ": gewichte.nsmallest(10).index})
"""),
md("""
Die Trefferquote liegt bei nahezu 100 Prozent — zu gut, um wahr zu sein, und das ist der
Punkt: Die Texte stammen aus einem Generator mit festen Bausteinen, und die Glättung hat die
Wortwahl nur begrenzt verändert. Ein Modell, das die Bausteine lernt, kennt die Antwort. Bei
echten Rezensionen liegen solche Modelle typischerweise zwischen 85 und 92 Prozent.

### Was macht das Modell mit den 3-Sterne-Texten?
"""),
code("""
mittlere = rezensionen[rezensionen["stars"] == 3]
wahrscheinlichkeit = modell.predict_proba(vektor.transform(mittlere["text_norm"]))[:, 1]
print(f"{len(mittlere)} Texte mit drei Sternen: {(wahrscheinlichkeit >= 0.5).mean() * 100:.1f} Prozent würden als positiv "
      f"eingeordnet, die mittlere Wahrscheinlichkeit liegt bei {wahrscheinlichkeit.mean():.2f}.")
pd.Series(wahrscheinlichkeit).describe().round(2).to_frame("p_positiv").T
"""),
md("""
### Vergleich: vortrainiertes deutsches BERT-Modell

`oliverguhr/german-sentiment-bert` hat diese Texte nie gesehen. Auf einer Stichprobe von 500
Texten aus dem Prüfdatensatz zeigt sich, wie ein allgemeines Modell ohne Bausteinwissen
abschneidet. Das Modell antwortet mit `positive`, `negative` oder `neutral`; `neutral` zählt
als Fehler, weil die Texte eine Polarität haben.
"""),
code("""
from transformers import pipeline

klassifikator = pipeline("text-classification", model="oliverguhr/german-sentiment-bert", truncation=True)
stichprobe = polar.loc[X_test.index].sample(500, random_state=2026)
antworten = klassifikator(stichprobe["review_text"].tolist(), batch_size=16)
stichprobe["bert"] = [antwort["label"] for antwort in antworten]
stichprobe["bert_positiv"] = (stichprobe["bert"] == "positive").astype(int)
stichprobe["lr_positiv"] = modell.predict(vektor.transform(stichprobe["text_norm"]))
bert_treffer = ((stichprobe["bert"] == "positive") & (stichprobe["positiv"] == 1)
                | (stichprobe["bert"] == "negative") & (stichprobe["positiv"] == 0)).mean() * 100
lr_treffer = (stichprobe["lr_positiv"] == stichprobe["positiv"]).mean() * 100
print(f"Auf denselben 500 Texten: BERT {bert_treffer:.1f} Prozent, TF-IDF mit logistischer Regression {lr_treffer:.1f} Prozent.")
pd.crosstab(stichprobe["positiv"].map({0: "ist negativ", 1: "ist positiv"}), stichprobe["bert"])
"""),
md("### Sentiment gegen Kanal, Bestelldauer, Filiale und Produkt"),
code("""
# Vorhersage für alle 10.000 Texte mit dem TF-IDF-Modell (Wahrscheinlichkeit für „positiv")
rezensionen["p_positiv"] = modell.predict_proba(vektor.transform(rezensionen["text_norm"]))[:, 1]
rezensionen["dauer_klasse"] = pd.cut(rezensionen["order_duration_min"], bins=[0, 5, 10, 15, 60],
                                     labels=["bis 5 min", "6–10 min", "11–15 min", "über 15 min"])

def anteil_positiv(spalte):
    # Anteil positiv vorhergesagter Texte und mittlere Sterne je Ausprägung
    return (rezensionen.groupby(spalte, observed=True)
            .agg(rezensionen=("review_id", "size"), anteil_positiv_pct=("p_positiv", lambda p: (p >= 0.5).mean() * 100),
                 sterne_mittel=("stars", "mean")).round(2))

anteil_positiv("order_channel")
"""),
code("""
anteil_positiv("dauer_klasse")
"""),
code("""
anteil_positiv("branch_name").sort_values("anteil_positiv_pct", ascending=False)
"""),
code("""
anteil_positiv("category").sort_values("anteil_positiv_pct", ascending=False)
"""),
code("""
import matplotlib.pyplot as plt

produkte = anteil_positiv("product_name").sort_values("anteil_positiv_pct")
abb, achse = plt.subplots(figsize=(9, 6))
achse.barh(produkte.index[-15:], produkte["anteil_positiv_pct"].iloc[-15:])
achse.set_xlabel("Anteil positiver Rezensionen in %")
achse.set_xlim(0, 100)
achse.set_title("Die Produkte mit dem höchsten Anteil positiver Rezensionen")
plt.tight_layout()
plt.show()
"""),
md("""
## Ergebnis

Die Wortliste trifft rund drei Viertel, TF-IDF mit logistischer Regression fast alles — weil
die Texte simuliert sind und das Modell die Bausteine lernt. BERT, das die Bausteine nicht
kennt, liegt bei rund 90 Prozent und ist damit der realistischere Maßstab. Der Anteil
positiver Rezensionen fällt mit der Bestelldauer und unterscheidet sich zwischen den Kanälen —
genau wie die Sterne, aus denen der Generator die Texte gebaut hat.

## Was offen bleibt

Echte Rezensionen aus dem Shop (`source = 'shop'`) fehlen noch im Bestand; sobald sie da
sind, wird das Modell an Texten geprüft, die kein Generator geschrieben hat. Die Stoppwortliste
ist kurz und die Wortliste klein — beides ließe sich aus den Koeffizienten des Modells
erweitern.
"""),
]

schreiben("08_sentiment_rezensionen.ipynb", ZELLEN)
```

- [ ] **Step 2: Bauen, ausführen, prüfen**

```bash
python3 notebooks/quellen/bau_08.py
jupyter nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 notebooks/08_sentiment_rezensionen.ipynb
python3 notebooks/quellen/pruefe_ausgaben.py notebooks/08_sentiment_rezensionen.ipynb
```
Expected: keine Fehler; BERT-Trefferquote zwischen 85 und 97 Prozent; Laufzeit unter fünf Minuten (Modell liegt im Hugging-Face-Cache). Erscheinen Fortschrittsbalken von `transformers` in den Ausgaben, ist das in Ordnung.

- [ ] **Step 3: Commit**

```bash
git -c core.fileMode=false add notebooks/quellen/bau_08.py notebooks/08_sentiment_rezensionen.ipynb
git -c core.fileMode=false commit -m "notebooks: 08 Sentiment der Rezensionen — Wortliste, TF-IDF mit logistischer Regression, BERT-Vergleich, Sentiment je Kanal und Produkt" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 10: Dash-App mit Test

**Files:**
- Create: `dash/app.py`, `dash/requirements.txt`, `dash/README.md`, `dash/test_app.py`

**Interfaces:**
- Consumes: Sichten `v_kennzahlen_jahr` (`jahr, bestellungen, umsatz, aov`), `v_kennzahl_einzeln` (`kennung, wert`), `v_umsatz_monat` (`monat, umsatz`), `v_filiale` (`branch_id, branch_name`), `v_kanal_jahr` (`jahr, kanal, anteil_pct`), `v_rezension_produkt` (`product_name, category, anzahl, sterne_mittel`); `fact_orders` für den Filialfilter.
- Produces: `lade_kennzahlen() -> dict`, `lade_umsatz_monat(branch_id: int | None) -> DataFrame[monat, umsatz]`, `lade_filialen() -> DataFrame`, `lade_kanaele() -> DataFrame`, `lade_rezensionen() -> DataFrame`, `baue_app() -> Dash`.

- [ ] **Step 1: Test schreiben — `dash/test_app.py`**

```python
"""Prüft die Datenfunktionen der Dash-App gegen die Datenbank und den Aufbau der App."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import app  # noqa: E402


def test_kennzahlen_vier_kacheln():
    kacheln = app.lade_kennzahlen()
    assert list(kacheln) == ["Umsatz 2025", "Bestellungen 2025", "Ø Bestellwert 2025", "Zufriedenheit 2025"]
    assert kacheln["Bestellungen 2025"] == "136.557"
    assert kacheln["Zufriedenheit 2025"].startswith("3,8")


def test_umsatz_monat_ohne_und_mit_filiale():
    alle = app.lade_umsatz_monat(None)
    eine = app.lade_umsatz_monat(1)
    assert list(alle.columns) == ["monat", "umsatz"] and list(eine.columns) == ["monat", "umsatz"]
    assert alle["monat"].iloc[0] == "2017-03" and alle["monat"].iloc[-1] == "2026-03"
    assert len(alle) == 109 and len(eine) == 109
    assert eine["umsatz"].sum() < alle["umsatz"].sum()


def test_filialen_und_kanaele():
    filialen = app.lade_filialen()
    assert len(filialen) == 8 and filialen["branch_id"].iloc[0] == 1
    kanaele = app.lade_kanaele()
    assert set(kanaele["kanal"]) == {"App Order", "Counter", "Drive-Through", "Kiosk"}
    assert abs(kanaele[kanaele["jahr"] == 2025]["anteil_pct"].sum() - 100) < 0.5


def test_rezensionen_je_produkt():
    daten = app.lade_rezensionen()
    assert len(daten) >= 50 and daten["anzahl"].sum() == 10000
    assert daten["sterne_mittel"].between(1, 5).all()


def test_app_hat_vier_karten():
    dash_app = app.baue_app()
    ids = [k.id for k in dash_app.layout.children if getattr(k, "id", None)]
    assert ids == ["kacheln", "karte-umsatz", "karte-kanaele", "karte-rezensionen"]
    assert "linie-umsatz.figure" in dash_app.callback_map
```

- [ ] **Step 2: Test laufen lassen — muss scheitern**

Run: `python3 -m pytest dash/test_app.py -q`
Expected: `ModuleNotFoundError: No module named 'app'` (Sammelfehler).

- [ ] **Step 3: `dash/app.py`**

```python
#!/usr/bin/env python3
"""app.py — Dash-App zur Fallstudie BurgerMetrics: vier Karten aus der Semantikschicht.

    python3 dash/app.py            # http://127.0.0.1:8050

Verbindung aus der Umgebungsvariable DATABASE_URL; ohne sie das Demo-Konto studi_daba
(nur lesend). Jede Karte liest genau eine Sicht — dieselben Zahlen wie das Dashboard,
weil beide dieselbe Definition benutzen.
"""
import os

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html
from sqlalchemy import create_engine

DATABASE_URL = os.environ.get("DATABASE_URL",
                              "postgresql+psycopg2://studi_daba:thws@supabase.butscher.cloud:5433/postgres")
engine = create_engine(DATABASE_URL)


def lade_sql(sql):
    """Führt eine Abfrage aus und gibt das Ergebnis als DataFrame zurück."""
    return pd.read_sql(sql, engine)


def zahl(wert, nachkommastellen=0):
    """Formatiert eine Zahl deutsch: Punkt als Tausendertrenner, Komma als Dezimaltrenner."""
    text = f"{wert:,.{nachkommastellen}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def lade_kennzahlen():
    """Die vier Kacheln: drei Werte für 2025 aus v_kennzahlen_jahr, die Zufriedenheit aus v_kennzahl_einzeln."""
    jahr = lade_sql("SELECT bestellungen, umsatz, aov FROM v_kennzahlen_jahr WHERE jahr = 2025").iloc[0]
    zufriedenheit = lade_sql("SELECT wert FROM v_kennzahl_einzeln WHERE kennung = 'zufriedenheit_2025'").iloc[0, 0]
    return {
        "Umsatz 2025": zahl(jahr["umsatz"] / 1_000_000, 2) + " Mio. €",
        "Bestellungen 2025": zahl(jahr["bestellungen"]),
        "Ø Bestellwert 2025": zahl(jahr["aov"], 2) + " €",
        "Zufriedenheit 2025": zahl(zufriedenheit, 2) + " von 5",
    }


def lade_umsatz_monat(branch_id):
    """Umsatz je Monat: ohne Filiale aus der Sicht, mit Filiale aus fact_orders gerechnet."""
    if branch_id is None:
        return lade_sql("SELECT monat, umsatz FROM v_umsatz_monat ORDER BY monat")
    return lade_sql(f"""
        SELECT to_char(date, 'YYYY-MM') AS monat, sum(net_total) AS umsatz
        FROM fact_orders WHERE branch_id = {int(branch_id)}
        GROUP BY 1 ORDER BY 1""")


def lade_filialen():
    """Filialen für die Auswahl."""
    return lade_sql("SELECT branch_id, branch_name FROM v_filiale ORDER BY branch_id")


def lade_kanaele():
    """Kanalanteile je Jahr."""
    return lade_sql("SELECT jahr, kanal, anteil_pct FROM v_kanal_jahr ORDER BY jahr, kanal")


def lade_rezensionen():
    """Ø Sterne je Produkt aus der materialisierten Sicht, nur Produkte mit Rezensionen."""
    return lade_sql("""
        SELECT product_name, category, anzahl, sterne_mittel
        FROM v_rezension_produkt WHERE anzahl > 0
        ORDER BY sterne_mittel DESC, anzahl DESC""")


def kachel(titel, wert):
    """Eine Kennzahlkachel."""
    return html.Div([html.Div(titel, className="kachel-titel"), html.Div(wert, className="kachel-wert")], className="kachel")


def figur_umsatz(branch_id):
    """Linie Umsatz je Monat, wahlweise für eine Filiale."""
    daten = lade_umsatz_monat(branch_id)
    figur = px.line(daten, x="monat", y="umsatz", labels={"monat": "Monat", "umsatz": "Umsatz in €"})
    figur.update_layout(margin=dict(l=40, r=20, t=20, b=40), yaxis_rangemode="tozero")
    return figur


def figur_kanaele():
    """Gestapelte Balken: Anteil der Kanäle je Jahr."""
    figur = px.bar(lade_kanaele(), x="jahr", y="anteil_pct", color="kanal",
                   labels={"jahr": "Jahr", "anteil_pct": "Anteil in %", "kanal": "Kanal"})
    figur.update_layout(margin=dict(l=40, r=20, t=20, b=40), barmode="stack")
    return figur


def figur_rezensionen():
    """Balken: Ø Sterne je Produkt, die zwanzig meistbewerteten Produkte."""
    daten = lade_rezensionen().sort_values("anzahl", ascending=False).head(20).sort_values("sterne_mittel")
    figur = px.bar(daten, x="sterne_mittel", y="product_name", orientation="h", color="category",
                   hover_data=["anzahl"], labels={"sterne_mittel": "Ø Sterne", "product_name": "Produkt", "category": "Kategorie"})
    figur.update_layout(margin=dict(l=40, r=20, t=20, b=40), xaxis_range=[0, 5], height=560)
    return figur


def baue_app():
    """Baut Layout und Callback; getrennt von app.run, damit der Test die App prüfen kann."""
    dash_app = Dash(__name__, title="BurgerMetrics — Dash")
    filialen = lade_filialen()
    kennzahlen = lade_kennzahlen()
    dash_app.layout = html.Div([
        html.H1("BurgerMetrics — vier Karten aus der Semantikschicht"),
        html.Div([kachel(t, w) for t, w in kennzahlen.items()], id="kacheln", className="kacheln"),
        html.Div([
            html.H2("Umsatz je Monat"),
            dcc.Dropdown(id="filiale", clearable=False, value="alle",
                         options=[{"label": "Alle Filialen", "value": "alle"}]
                         + [{"label": z.branch_name, "value": int(z.branch_id)} for z in filialen.itertuples()]),
            dcc.Graph(id="linie-umsatz"),
        ], id="karte-umsatz", className="karte"),
        html.Div([html.H2("Kanalanteile je Jahr"), dcc.Graph(figure=figur_kanaele())], id="karte-kanaele", className="karte"),
        html.Div([html.H2("Ø Sterne je Produkt (die 20 meistbewerteten)"), dcc.Graph(figure=figur_rezensionen())],
                 id="karte-rezensionen", className="karte"),
        html.P("Quelle: Sichten v_kennzahlen_jahr, v_kennzahl_einzeln, v_umsatz_monat, v_kanal_jahr, v_rezension_produkt; "
               "Filialfilter über fact_orders.", className="quelle"),
    ], className="seite")

    @dash_app.callback(Output("linie-umsatz", "figure"), Input("filiale", "value"))
    def zeichne_umsatz(wahl):
        # Zeichnet die Linie neu, sobald die Filiale wechselt
        return figur_umsatz(None if wahl == "alle" else wahl)

    return dash_app


if __name__ == "__main__":
    baue_app().run(debug=False, port=8050)
```

- [ ] **Step 4: `dash/assets/stil.css`** (Dash lädt `assets/` automatisch), `dash/requirements.txt`, `dash/README.md`

```css
/* stil.css — schlichte Karten, Orange als Leitfarbe der Analyse-Materialien */
body { font-family: system-ui, sans-serif; margin: 0; background: #FDF1E7; color: #1C1917; }
.seite { max-width: 1100px; margin: 0 auto; padding: 24px; }
h1 { font-size: 1.5rem; color: #7C2D12; }
h2 { font-size: 1.1rem; margin: 0 0 8px; color: #9A3412; }
.kacheln { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.kachel { background: #fff; border-radius: 8px; padding: 14px 16px; border-left: 4px solid #C2410C; }
.kachel-titel { font-size: .8rem; color: #57534E; }
.kachel-wert { font-size: 1.4rem; font-weight: 600; }
.karte { background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 20px; }
.quelle { font-size: .8rem; color: #57534E; }
@media (max-width: 700px) { .kacheln { grid-template-columns: repeat(2, 1fr); } }
```

`dash/requirements.txt`:

```
dash>=2.17
plotly>=5.22
pandas>=2.2
sqlalchemy>=2.0
psycopg2-binary>=2.9
pytest>=8
```

`dash/README.md`:

```markdown
# Dash-App zur Fallstudie BurgerMetrics

Eine Datei, vier Karten: Kennzahlkacheln (Umsatz, Bestellungen, Ø Bestellwert, Zufriedenheit
2025), Umsatz je Monat mit Filialfilter, Kanalanteile je Jahr, Ø Sterne je Produkt. Jede Karte
liest eine Sicht der Semantikschicht — dieselben Zahlen wie das Dashboard.

```bash
python3 -m pip install -r dash/requirements.txt
python3 dash/app.py            # http://127.0.0.1:8050
```

Die Verbindung kommt aus `DATABASE_URL`; ohne die Variable nutzt die App das Demo-Konto
`studi_daba` (nur lesend). In Colab läuft dieselbe App als letzte Zelle von
`notebooks/00_zugang_und_daten.ipynb` mit `app.run(jupyter_mode="inline")`.

Test gegen die Datenbank: `python3 -m pytest dash/test_app.py -q` (fünf Tests).
```

- [ ] **Step 5: Test laufen lassen — muss bestehen; App starten und Bildschirmfoto**

```bash
python3 -m pytest dash/test_app.py -q
```
Expected: `5 passed`. Dann `python3 dash/app.py` im Hintergrund starten, `http://127.0.0.1:8050` im Browser (Playwright-MCP oder Browser-Pane) öffnen: vier Kacheln, Linie, gestapelte Balken, Balken der Produkte; Filialwahl „BM Sanderring" zeichnet die Linie neu (kleinere Werte). Bildschirmfoto als `dash/bildschirmfoto.png` speichern (Playwright `browser_take_screenshot` mit `filename`, volle Seite) — es wird im Deck (Phase 5) gebraucht. App beenden.

- [ ] **Step 6: Commit**

```bash
git -c core.fileMode=false add dash/
git -c core.fileMode=false commit -m "dash: App mit vier Karten aus der Semantikschicht, Test gegen die Datenbank, README, Bildschirmfoto" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 11: Abnahme, Spec-Notiz, Pull Request

**Files:**
- Modify: `docs/superpowers/specs/2026-09-12-bm-analyse-lernumgebung-design.md` (Abschnitt 11, Stand-Absätze), `README.md` (eine Zeile, siehe Step 2)

- [ ] **Step 1: Alle Notebooks in einem Lauf (Spec 11, Zeile „Notebooks")**

```bash
bash notebooks/pruefe_notebooks.sh 2>&1 | tail -15
python3 -m pytest dash/test_app.py -q
python3 -m pytest dataset/tests -q
git status --short
```
Expected: neun Notebooks ohne Fehler, `0 Befund(e)` je Notebook, `5 passed`, `29 passed`; `git status` zeigt nur die neu ausgeführten Notebooks (Ausführungszähler, Zeitstempel der Ausgaben) — diese committen: `git -c core.fileMode=false add notebooks/*.ipynb && git -c core.fileMode=false commit -m "notebooks: Abnahmelauf pruefe_notebooks.sh, alle neun ausgeführt" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"`.

- [ ] **Step 2: Verweise und Spec**

`README.md` (Repo-Wurzel): in der Übersicht der Ordner eine Zeile für `notebooks/` („neun ausgeführte Notebooks, Zugang bis Sentiment-Analyse; `notebooks/README.md`") und eine für `dash/` („Dash-App mit vier Karten; `dash/README.md`") — an der Stelle, wo `dataset/` und `db/` beschrieben sind (`grep -n "dataset/" README.md`), im Stil der Nachbarzeilen. Keine weiteren README-Änderungen (Phase 7).

Spec Abschnitt 11, nach dem Absatz „**Stand 12. September 2026 (Phase 3):** …" ergänzen:

```markdown
**Stand 13. September 2026 (Phase 4):** Notebooks und Dash abgenommen — `pruefe_notebooks.sh` führt alle neun gegen die Datenbank aus, die Ausgaben sind eingecheckt; Dash-App mit vier Karten und Test. Abweichungen: Kennzahlkacheln aus `v_kennzahlen_jahr` plus Zufriedenheit aus `v_kennzahl_einzeln`; Filialfilter über `fact_orders`; Schulferien über OpenHolidays statt ferien-api.de (HTTP 429); Kickers-Heimspiele nur für die Saisons mit OpenLigaDB-Abdeckung (2016/17 bis 2021/22); VPI als kuratierte CSV mit Quellenangabe. Von der Übergabe je Phase ist „Notebooks mit Ausgaben auf GitHub" erfüllt, sobald der PR auf `main` ist.
```

```bash
git -c core.fileMode=false add README.md docs/superpowers/specs/2026-09-12-bm-analyse-lernumgebung-design.md
git -c core.fileMode=false commit -m "spec, README: Abnahmestand Phase 4 vermerkt, Verweise auf notebooks/ und dash/" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

- [ ] **Step 3: Push und PR**

```bash
git push origin bm-analyse
gh pr create --base main --head bm-analyse --title "Phase 4: Notebooks und Dash" --body-file - <<'EOF'
## Was
- `notebooks/00`–`08`: neun ausgeführte Notebooks (Zugang und Daten, analytisches Datenmodell, RFM, Warenkorb, Nachfrageprognose, Wetter und Ereignisse mit externen Quellen, Zufriedenheit, Ausreißer, Sentiment) — gebaut aus `notebooks/quellen/bau_NN.py`, ausgeführt mit `notebooks/pruefe_notebooks.sh`
- `notebooks/daten_extern/`: Open-Meteo, Schulferien (OpenHolidays), Kickers-Heimspiele (OpenLigaDB), Verbraucherpreisindex (Destatis, kuratiert) — mit Quellen und Stand
- `dash/app.py`: vier Karten aus der Semantikschicht, `dash/test_app.py` gegen die Datenbank, Bildschirmfoto für das Deck

## Abnahme
- `pruefe_notebooks.sh`: alle neun ohne Fehler, `pruefe_ausgaben.py` 0 Befunde
- `pytest dash/test_app.py` 5 passed; `pytest dataset/tests` 29 passed
- Colab-Links am Kopf jedes Notebooks zeigen auf `main`

Spec: docs/superpowers/specs/2026-09-12-bm-analyse-lernumgebung-design.md · Plan: docs/superpowers/plans/2026-09-13-phase-4-notebooks-und-dash.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
```

- [ ] **Step 4: Merge nur nach Rückfrage bei Robert**

Nach seiner Zusage: `gh pr merge <Nummer> --merge --delete-branch=false`, `main` per `--ff-only` ziehen, `bm-analyse` nachziehen. Danach ein Colab-Link stichprobenartig öffnen (`https://colab.research.google.com/github/swrobuts/BurgerMetrics/blob/main/notebooks/00_zugang_und_daten.ipynb` lädt das Notebook) und die GitHub-Ansicht eines Notebooks mit Diagramm prüfen.

---

## Selbstprüfung des Plans (durchgeführt)

- **Spec-Abdeckung:** 6.1 Konventionen (Abschnitte, Verbindungszelle, Anfängercode, matplotlib, Colab-Link, pip-Zelle, requirements, Ausführung und Prüfskript) → Task 1 und Global Constraints; 6.2 die neun Notebooks → Tasks 1–9 mit den jeweils genannten Inhalten (00: Verbindung, Schemata, Suchpfad, Kennzahlen, CSV per LFS, DuckDB, Export, Grenzen der Rolle, Dash inline; 01: Frage → Grain → Dimensionen → Fakten → Sicht, Fan Trap, Abgleich, Rezensionen; 02: RFM, Quintile mit Zweitschlüssel, Vergleich mit `v_rfm_kunde`, K-Means mit Elbow und Silhouette; 03: Apriori, Support/Konfidenz/Lift, Richtung, Vergleich mit `v_warenkorb_regeln`; 04: STL, Merkmale, Regression und Gradient Boosting, Backtesting zwölf Monate, MAE/MAPE, Basiseffekt; 05: Regression auf `dim_weather`/`special_event`, dann Open-Meteo, Feiertage, Schulferien, Kickers, VPI, Vergleich synthetisch/gemessen; 06: Klassen, Baum Tiefe 3, Random Forest, Merkmalswichtigkeit; 07: z-Score, IQR, Isolation Forest, Treffer erklären; 08: Vorverarbeitung, Wortliste, TF-IDF + logistische Regression, Konfusionsmatrix, BERT-Stichprobe, Sentiment gegen Kanal/Dauer/Filiale/Produkt); 6.3 Dash → Task 10 und die Colab-Zelle in Task 1; 7 externe Quellen → Task 6 mit den geprüften Zugängen; 11 Abnahme → Task 11; „Übergabe je Phase" (Notebooks mit Ausgaben auf GitHub) → Task 11 Step 4.
- **Placeholder-Scan:** keine „TBD", keine Beschreibungen ohne Code; alle Zellinhalte stehen im Plan. Die Abweichungen von der Spec sind in den Global Constraints benannt.
- **Schnittstellen:** `gemeinsam.kopf(nummer, titel, dateiname, pakete=PAKETE)` in Task 1 definiert, in Task 9 mit `pakete=` genutzt; `VERBINDUNG` liefert `lade_sql`/`lade_csv`, die alle Notebooks verwenden; Sichten- und Spaltennamen (`v_rfm_kunde`, `v_warenkorb_regeln`, `v_kennzahl_einzeln`, `v_rezension_produkt` mit `anzahl`/`sterne_mittel`) gegen die Datenbank geprüft (13.09.2026); Dash-Funktionen in `app.py` und `test_app.py` gleichnamig (`lade_kennzahlen`, `lade_umsatz_monat`, `lade_filialen`, `lade_kanaele`, `lade_rezensionen`, `baue_app`); Element-IDs `kacheln`, `karte-umsatz`, `karte-kanaele`, `karte-rezensionen`, `linie-umsatz`, `filiale` in Layout, Callback und Test identisch.
