#!/usr/bin/env python3
"""
load_duckdb.py — Lädt den BurgerMetrics-Datensatz in eine DuckDB- oder
MotherDuck-Datenbank.

Hintergrund
-----------
Das Übungsblatt setzt eine Datenbank `burger_metrics` in der MotherDuck-Web-UI
voraus. Wie sie entsteht, war bisher nirgends dokumentiert. Dieses Skript
schließt die Lücke und deckt drei Wege ab:

    python load_duckdb.py --lokal            # burger_metrics.duckdb im Ordner
    python load_duckdb.py --motherduck       # MotherDuck, Datenbank burger_metrics
    python load_duckdb.py --lokal --klein    # nur Dimensionen + Fakten ohne OBT

Voraussetzungen
---------------
    pip install duckdb

Für MotherDuck zusätzlich ein Zugangstoken. Es wird NICHT im Skript hinterlegt,
sondern aus der Umgebung gelesen:

    export motherduck_token="<Token aus app.motherduck.com>"

Ohne gesetztes Token bricht der MotherDuck-Lauf mit einem Hinweis ab, statt
nach Zugangsdaten zu fragen.

Laufzeit und Größe
------------------
Lokal rund 30 Sekunden; die erzeugte Datei ist deutlich kleiner als die
Summe der CSV-Dateien, weil DuckDB spaltenweise und komprimiert speichert.
Der Upload nach MotherDuck dauert je nach Verbindung länger.

Warum nicht `read_csv_auto` auf einer URL?
------------------------------------------
Die CSV-Dateien liegen in Git LFS. Ein direkter Zugriff über eine Roh-URL
liefert je nach Zugriffsweg die LFS-Verweisdatei statt der Daten. Dieses
Skript liest deshalb die lokalen Dateien aus dem geklonten Repository.
"""

import argparse
import os
import sys
from pathlib import Path

BASE = Path(__file__).parent

# Tabellenname -> Datei. Reihenfolge: erst Dimensionen, dann Fakten, dann OBT.
TABELLEN = [
    ("dim_branch", "dim_branch.csv"),
    ("dim_customer", "dim_customer.csv"),
    ("dim_date", "dim_date.csv"),
    ("dim_employee", "dim_employee.csv"),
    ("dim_payment_method", "dim_payment_method.csv"),
    ("dim_product", "dim_product.csv"),
    ("dim_promotion", "dim_promotion.csv"),
    ("dim_supplier", "dim_supplier.csv"),
    ("dim_time_slot", "dim_time_slot.csv"),
    ("dim_weather", "dim_weather.csv"),
    ("fact_orders", "fact_orders.csv"),
    ("fact_order_items", "fact_order_items.csv"),
    ("obt_orders", "obt_orders.csv"),
]

# Sollwerte aus dataset/README.md. Das Skript prüft dagegen, damit ein
# unvollständiger Ladelauf sofort auffällt und nicht erst in der Übung.
SOLL = {
    "dim_branch": 8,
    "dim_customer": 25_000,
    "dim_date": 3_377,
    "dim_employee": 188,
    "dim_payment_method": 4,
    "dim_product": 57,
    "dim_promotion": 13,
    "dim_supplier": 8,
    "dim_time_slot": 18,
    "dim_weather": 3_377,
    "fact_orders": 754_513,
    "fact_order_items": 2_950_082,
    "obt_orders": 754_513,
}

DB_NAME = "burger_metrics"


def pointer_datei(pfad: Path) -> bool:
    """Erkennt eine Git-LFS-Verweisdatei, die versehentlich statt der Daten vorliegt."""
    try:
        with open(pfad, "rb") as f:
            return f.read(40).startswith(b"version https://git-lfs")
    except OSError:
        return False


def pruefe_dateien(tabellen):
    fehlend, pointer = [], []
    for _, datei in tabellen:
        p = BASE / datei
        if not p.exists():
            fehlend.append(datei)
        elif pointer_datei(p):
            pointer.append(datei)
    if fehlend:
        sys.exit(f"FEHLER: Diese Dateien fehlen: {', '.join(fehlend)}")
    if pointer:
        sys.exit(
            "FEHLER: Diese Dateien sind Git-LFS-Verweise, keine Daten:\n  "
            + ", ".join(pointer)
            + "\n\nAbhilfe:  git lfs install && git lfs pull"
        )


def main():
    ap = argparse.ArgumentParser(description="BurgerMetrics nach DuckDB oder MotherDuck laden")
    ziel = ap.add_mutually_exclusive_group(required=True)
    ziel.add_argument("--lokal", action="store_true", help="lokale Datei burger_metrics.duckdb")
    ziel.add_argument("--motherduck", action="store_true", help="MotherDuck-Datenbank burger_metrics")
    ap.add_argument("--klein", action="store_true",
                    help="ohne obt_orders (spart 176 MB und den größten Teil der Ladezeit)")
    ap.add_argument("--ausgabe", default=None, help="Pfad der lokalen Datei (Standard: burger_metrics.duckdb)")
    args = ap.parse_args()

    try:
        import duckdb
    except ImportError:
        sys.exit("FEHLER: duckdb fehlt.  Abhilfe:  pip install duckdb")

    tabellen = [t for t in TABELLEN if not (args.klein and t[0] == "obt_orders")]
    pruefe_dateien(tabellen)

    if args.motherduck:
        if not os.environ.get("motherduck_token"):
            sys.exit(
                "FEHLER: Umgebungsvariable motherduck_token ist nicht gesetzt.\n"
                "Token unter app.motherduck.com erzeugen, dann:\n"
                '  export motherduck_token="<Token>"'
            )
        print("Verbinde mit MotherDuck...")
        con = duckdb.connect("md:")
        con.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        con.execute(f"USE {DB_NAME}")
        ort = f"MotherDuck / {DB_NAME}"
    else:
        pfad = Path(args.ausgabe) if args.ausgabe else BASE / f"{DB_NAME}.duckdb"
        if pfad.exists():
            pfad.unlink()
        print(f"Erzeuge lokale Datenbank {pfad.name}...")
        con = duckdb.connect(str(pfad))
        ort = str(pfad)

    # Die CSV-Dateien sind UTF-8 mit BOM. DuckDB entfernt die Byte-Order-Mark
    # beim Einlesen nicht selbst, sie landete sonst im ersten Spaltennamen.
    for name, datei in tabellen:
        quelle = str((BASE / datei).resolve()).replace("'", "''")
        con.execute(f"""
            CREATE OR REPLACE TABLE {name} AS
            SELECT * FROM read_csv_auto('{quelle}', header = true, sample_size = -1)
        """)
        n = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        erwartet = SOLL.get(name)
        status = "OK  " if erwartet is None or n == erwartet else "ABWEICHUNG"
        print(f"  {status}  {name:<20} {n:>10,} Zeilen".replace(",", "."))
        if erwartet is not None and n != erwartet:
            print(f"        erwartet: {erwartet:,}".replace(",", "."))

    # Erste Spalte auf BOM-Reste prüfen — ein stiller Klassiker beim CSV-Import.
    spalten = con.execute("SELECT * FROM dim_branch LIMIT 0").description
    if spalten and spalten[0][0].startswith("﻿"):
        print("\nWARNUNG: Der erste Spaltenname enthält eine Byte-Order-Mark.")
        print("         Abfragen auf diese Spalte schlagen sonst fehl.")

    print(f"\nFertig. Datenbank: {ort}")
    print("\nErster Test:")
    print("  USE burger_metrics;")
    print("  SELECT COUNT(*) FROM fact_orders;        -- erwartet: 754.513")
    print("  SELECT ROUND(SUM(net_total), 2) FROM fact_orders;  -- erwartet: 14.522.378,70")

    con.close()


if __name__ == "__main__":
    main()
