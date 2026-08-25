#!/usr/bin/env python3
"""
generate_obt.py — Erzeugt die denormalisierte One Big Table (obt_orders.csv)
aus den Star-Schema-CSVs des BurgerMetrics-Datasets.

Fachlicher Hintergrund
----------------------
Die OBT beantwortet dieselben Fragen wie das Galaxy-Schema, aber ohne JOINs:
jede Zeile ist eine Bestellung, angereichert um die beschreibenden Attribute
ihrer Dimensionen. Das ist der klassische Trade-off aus der BI-Vorlesung —
Abfragekomfort und Lesegeschwindigkeit gegen Redundanz und Pflegeaufwand.

Die Granularität bleibt die der Bestellung (order grain), NICHT die der
Bestellposition. `fact_order_items` wird deshalb bewusst nicht eingebunden:
ein Join auf Positionsebene würde jede Bestellung vervielfachen und sämtliche
Umsatzsummen aufblähen. Wer Produktanalysen braucht, arbeitet direkt auf
`fact_order_items` × `dim_product`.

Verwendung
----------
    python generate_obt.py                 # schreibt obt_orders.csv
    python generate_obt.py /pfad/out.csv   # alternatives Ziel

Voraussetzungen
---------------
    - Python 3.8+
    - pandas (pip install pandas)
    - Alle CSV-Dateien im selben Verzeichnis wie dieses Skript

Ausgabe
-------
    obt_orders.csv — 754.513 Zeilen, 41 Spalten, ~185 MB

Hinweis zum Einlesen
--------------------
Alle Dateien werden als Text eingelesen (`dtype=str`, `keep_default_na=False`).
Das ist Absicht, kein Schludern: Die Spalte `loyalty_tier` enthält den
Literal-String "None" für Kunden ohne Loyalty-Programm. Mit den
pandas-Standardeinstellungen würde daraus ein fehlender Wert (NaN) und beim
Schreiben ein leeres Feld — die Information ginge still verloren. Ebenso
bleiben `discount_pct` als "15" statt "15.0" und `net_total` als "8.8" statt
"8.800000000000001" erhalten. Für eine reine Denormalisierung ist der
Texttransport verlustfrei; typisiert wird erst im auswertenden Werkzeug.
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Encoding der Quelldateien: UTF-8 mit BOM (Excel-kompatibel)
ENCODING = "utf-8-sig"

# Welche Attribute je Dimension in die OBT wandern und über welchen
# Fremdschlüssel sie an fact_orders hängen. Die Reihenfolge dieser Liste
# bestimmt die Spaltenreihenfolge der Ausgabe.
DIMENSIONS = [
    ("dim_branch.csv", "branch_id", [
        "branch_name", "district", "branch_type", "has_drive_through", "opening_date",
    ]),
    ("dim_customer.csv", "customer_id", [
        "age_group", "gender", "has_app", "loyalty_tier", "home_district",
    ]),
    ("dim_payment_method.csv", "payment_id", [
        "payment_type",
    ]),
    ("dim_promotion.csv", "promo_id", [
        "promo_name", "promo_type", "discount_pct",
    ]),
    ("dim_date.csv", "date", [
        "year", "quarter", "month", "month_name", "day_name",
        "is_weekend", "is_holiday", "special_event", "season",
    ]),
    ("dim_weather.csv", "date", [
        "temperature_celsius", "condition",
    ]),
]


def read_csv(path):
    """Liest eine CSV verlustfrei als Text ein (siehe Modul-Docstring)."""
    return pd.read_csv(path, encoding=ENCODING, dtype=str, keep_default_na=False)


def main(out_path=None):
    base = Path(__file__).parent
    out_path = Path(out_path) if out_path else base / "obt_orders.csv"

    print("Lade fact_orders.csv (754.513 Zeilen)...")
    obt = read_csv(base / "fact_orders.csv")
    fact_rows = len(obt)

    for filename, key, columns in DIMENSIONS:
        print(f"Verknüpfe {filename} über {key}...")
        dim = read_csv(base / filename)

        missing = [c for c in [key] + columns if c not in dim.columns]
        if missing:
            raise SystemExit(f"FEHLER: {filename} fehlen die Spalten: {', '.join(missing)}")

        # Dimensionsschlüssel müssen eindeutig sein, sonst vervielfacht der
        # LEFT JOIN die Faktenzeilen — der klassische Fan-Trap.
        if dim[key].duplicated().any():
            raise SystemExit(f"FEHLER: {filename} hat mehrdeutige Schlüssel in '{key}'")

        obt = obt.merge(dim[[key] + columns], on=key, how="left")

        if len(obt) != fact_rows:
            raise SystemExit(
                f"FEHLER: Join mit {filename} hat die Zeilenzahl verändert "
                f"({fact_rows} → {len(obt)})"
            )

    # Nicht getroffene Fremdschlüssel tauchen als NaN auf. Da alles als Text
    # gelesen wurde, ist NaN ein sicheres Zeichen für referenzielle Lücken —
    # im sauberen Sternschema darf es keine geben.
    luecken = obt.isna().any()
    if luecken.any():
        betroffen = ", ".join(luecken[luecken].index)
        print(f"WARNUNG: Fremdschlüssel ohne Treffer in: {betroffen}")
        obt = obt.fillna("")

    print(f"Schreibe {len(obt):,} Zeilen × {len(obt.columns)} Spalten nach {out_path.name}...")
    obt.to_csv(out_path, index=False, encoding=ENCODING, lineterminator="\n")

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Fertig! {out_path.name} ({size_mb:.0f} MB, {len(obt):,} Zeilen, {len(obt.columns)} Spalten)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
