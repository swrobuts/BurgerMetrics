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

def fuer_duckdb(daten):
    # DuckDB 1.4 kennt pandas' neuen Standard-Stringtyp "str" (ab pandas 3) noch nicht
    spalten = {s: object for s in daten.columns if daten[s].dtype == "str"}
    return daten.astype(spalten) if spalten else daten

filialen = fuer_duckdb(lade_csv("dim_branch"))
con = duckdb.connect()
con.register("dim_branch", filialen)
con.register("dim_product", fuer_duckdb(produkte))
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
