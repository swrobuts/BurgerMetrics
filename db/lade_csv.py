#!/usr/bin/env python3
"""lade_csv.py — laedt dataset/*.csv per COPY in das Schema burgermetrics.

Verbindung aus Umgebungsvariablen PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD.
Reihenfolge respektiert die Fremdschluessel; jede Tabelle wird vor dem Laden
geleert (TRUNCATE ... CASCADE nur ueber die Ladereihenfolge, kein Datenverlust
ausserhalb des Schemas). obt_orders wird NICHT geladen, sondern in
0003_obt.sql aus dem Galaxy-Schema erzeugt — derselbe Weg wie im Deck.

    python3 db/lade_csv.py [dataset-Verzeichnis]
"""
import os, sys, time
import psycopg2
from pathlib import Path


def lade_env():
    """Liest .env im Projektstamm, ohne die Shell zu bemuehen."""
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for zeile in env.read_text().splitlines():
            zeile = zeile.strip()
            if zeile and not zeile.startswith("#") and "=" in zeile:
                k, _, v = zeile.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


lade_env()

BASIS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "dataset"
REIHENFOLGE = ["dim_branch", "dim_customer", "dim_date", "dim_payment_method",
               "dim_product", "dim_promotion", "dim_supplier", "dim_time_slot",
               "dim_weather", "dim_employee", "fact_orders", "fact_order_items"]

con = psycopg2.connect(host=os.environ["PGHOST"], port=os.environ["PGPORT"],
                       dbname=os.environ["PGDATABASE"], user=os.environ["PGUSER"],
                       password=os.environ["PGPASSWORD"])
con.autocommit = False
cur = con.cursor()
cur.execute("SET search_path TO burgermetrics")

# Leeren in umgekehrter Reihenfolge (Fremdschluessel)
for t in reversed(REIHENFOLGE):
    cur.execute(f"TRUNCATE TABLE {t} CASCADE")

for t in REIHENFOLGE:
    pfad = BASIS / f"{t}.csv"
    start = time.time()
    with open(pfad, encoding="utf-8") as f:
        cur.copy_expert(
            f"COPY {t} FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')", f)
    cur.execute(f"SELECT count(*) FROM {t}")
    n = cur.fetchone()[0]
    print(f"  {t:<22} {n:>9,} Zeilen  {time.time()-start:6.1f}s".replace(",", "."))

con.commit()
con.close()
print("Fertig — eine Transaktion, alles oder nichts.")
