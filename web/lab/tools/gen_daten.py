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
