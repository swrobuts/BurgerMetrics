# duckdb-laden.py — zwei CSV-Dateien des Datensatzes BurgerMetrics in eine
# DuckDB-Datei laden und dieselbe Abfrage stellen, die in Lab 02 (Übung W02-01)
# gegen PostgreSQL läuft. Kopiervorlage zu Lab 02, Befehlskarte B03.
#
# Voraussetzungen: ein Klon mit Git LFS (Lab 02, B01) und das Paket duckdb
#   python3 -m pip install duckdb
# Aufruf aus dem Wurzelverzeichnis des Klons:
#   python3 duckdb-laden.py
# Legt die Datei burger_metrics.duckdb im aktuellen Ordner an. Stand 09/2026.

import duckdb

# Eine Datei, kein Server: connect() öffnet die Datei oder legt sie neu an
con = duckdb.connect("burger_metrics.duckdb")

# Zwei Tabellen aus den CSV-Dateien; read_csv erkennt Spaltennamen und Typen
# OR REPLACE ersetzt eine vorhandene Tabelle, damit das Skript mehrfach läuft;
# das ist DuckDB-Syntax — PostgreSQL kennt OR REPLACE bei Tabellen nicht (dort CREATE TABLE ... AS)
con.sql("CREATE OR REPLACE TABLE fact_orders AS SELECT * FROM read_csv('dataset/fact_orders.csv')")
con.sql("CREATE OR REPLACE TABLE dim_branch AS SELECT * FROM read_csv('dataset/dim_branch.csv')")

# Die Abfrage aus Übung W02-01 — Standard-SQL, wortgleich in PostgreSQL
# Über den vollständigen Datensatz sind es acht Filialen, im Miniaturbestand fünf
abfrage = """
SELECT b.branch_name, count(*) AS bestellungen, round(sum(o.net_total), 2) AS umsatz
FROM fact_orders o
JOIN dim_branch b USING (branch_id)
GROUP BY b.branch_name
ORDER BY umsatz DESC
"""
print(con.sql(abfrage))

# Verbindung schließen; die Datei bleibt und lässt sich mit connect() wieder öffnen
con.close()
