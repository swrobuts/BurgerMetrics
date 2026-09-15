#!/usr/bin/env python3
"""lade_csv.py — laedt dataset/*.csv per COPY in das Schema burgermetrics.

Verbindung aus Umgebungsvariablen PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD.
Reihenfolge respektiert die Fremdschluessel; jede Tabelle wird vor dem Laden
geleert (TRUNCATE ... CASCADE nur ueber die Ladereihenfolge, kein Datenverlust
ausserhalb des Schemas). obt_orders wird NICHT geladen, sondern in
0003_obt.sql aus dem Galaxy-Schema erzeugt — derselbe Weg wie im Deck.

    python3 db/lade_csv.py [dataset-Verzeichnis]
    python3 db/lade_csv.py --nur fact_reviews     # nur eine Tabelle leeren und laden
"""
import argparse, os, sys, time
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

con = psycopg2.connect(host=os.environ["PGHOST"], port=os.environ["PGPORT"],
                       dbname=os.environ["PGDATABASE"], user=os.environ["PGUSER"],
                       password=os.environ["PGPASSWORD"], sslmode="verify-full")
con.autocommit = False
cur = con.cursor()
cur.execute("SET search_path TO burgermetrics")


def vorhanden(tabelle):
    """Sagt, ob die Tabelle im Schema burgermetrics schon angelegt ist."""
    cur.execute("SELECT to_regclass(%s) IS NOT NULL", (f"burgermetrics.{tabelle}",))
    return cur.fetchone()[0]


# fact_reviews entsteht erst mit 0021 — beim Erstaufbau fehlt die Tabelle noch.
fehlend = [t for t in TABELLEN if not vorhanden(t)]
if fehlend and ARGS.nur:
    sys.exit(f"FEHLER: Tabelle(n) fehlen noch: {', '.join(fehlend)} — erst das Aufbauskript ausführen (fact_reviews: 0021)")
for t in fehlend:
    print(f"  {t:<22} übersprungen — Tabelle fehlt noch (0021 legt sie an)")
TABELLEN = [t for t in TABELLEN if t not in fehlend]

# Leeren in einem Schritt. Der Volllauf darf per CASCADE auch Abhängiges leeren,
# eine Auswahl (--nur) nicht: Sonst verschwinden still Tabellen, die gar nicht neu
# geladen werden. PostgreSQL bricht dann mit einer klaren Meldung ab, und man nennt
# die abhängigen Tabellen einfach mit (--nur fact_orders fact_order_items fact_reviews).
kaskade = "" if ARGS.nur else " CASCADE"
cur.execute("TRUNCATE TABLE " + ", ".join(TABELLEN) + kaskade)

for t in TABELLEN:
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
