#!/usr/bin/env python3
"""
generate_obt.py — Erzeugt die denormalisierte One-Big-Table (obt_orders.csv)
aus den Star-Schema-CSVs des BurgerMetrics-Datasets.

Verwendung:
    python generate_obt.py

Voraussetzungen:
    - Python 3.8+
    - pandas (pip install pandas)
    - Alle CSV-Dateien im selben Verzeichnis wie dieses Skript

Ausgabe:
    obt_orders.csv (~185 MB, 754.513 Zeilen)
"""

import os
import sys
import pandas as pd
from pathlib import Path

def main():
    base = Path(__file__).parent

    print("Lade Dimensionstabellen...")
    dim_branch = pd.read_csv(base / "dim_branch.csv", encoding="utf-8-sig")
    dim_customer = pd.read_csv(base / "dim_customer.csv", encoding="utf-8-sig")
    dim_date = pd.read_csv(base / "dim_date.csv", encoding="utf-8-sig")
    dim_product = pd.read_csv(base / "dim_product.csv", encoding="utf-8-sig")
    dim_payment = pd.read_csv(base / "dim_payment_method.csv", encoding="utf-8-sig")
    dim_promotion = pd.read_csv(base / "dim_promotion.csv", encoding="utf-8-sig")
    dim_employee = pd.read_csv(base / "dim_employee.csv", encoding="utf-8-sig")
    dim_time_slot = pd.read_csv(base / "dim_time_slot.csv", encoding="utf-8-sig")
    dim_weather = pd.read_csv(base / "dim_weather.csv", encoding="utf-8-sig")

    print("Lade fact_orders.csv (754.513 Zeilen)...")
    fact_orders = pd.read_csv(base / "fact_orders.csv", encoding="utf-8-sig")

    print("Lade fact_order_items.csv (~2,95 Mio. Zeilen)...")
    fact_items = pd.read_csv(base / "fact_order_items.csv", encoding="utf-8-sig")

    # --- Joins aufbauen ---
    print("Verknüpfe Dimensionstabellen...")

    # 1. Order Items mit Produktdaten anreichern
    items_enriched = fact_items.merge(
        dim_product, on="product_id", how="left", suffixes=("", "_prod")
    )

    # 2. Items auf Order-Ebene aggregieren (für OBT brauchen wir eine Zeile pro Order)
    #    → Produktliste als kommaseparierter String
    item_agg = items_enriched.groupby("order_id").agg(
        products=("product_name", lambda x: ", ".join(x)),
        categories=("category", lambda x: ", ".join(x.unique())),
        total_items=("quantity", "sum"),
        has_vegetarian=("is_vegetarian", "max"),
        has_vegan=("is_vegan", "max"),
    ).reset_index()

    # 3. Fact Orders mit Dimensionen joinen
    obt = fact_orders.copy()

    # Date-Dimension (über date-Spalte → date_id generieren)
    obt["date_id"] = pd.to_datetime(obt["date"]).dt.strftime("%Y%m%d").astype(int)
    obt = obt.merge(dim_date, on="date_id", how="left", suffixes=("", "_dim"))

    # Branch
    obt = obt.merge(
        dim_branch[["branch_id", "branch_name", "district", "branch_type",
                     "has_drive_through", "seats_indoor", "seats_outdoor"]],
        on="branch_id", how="left"
    )

    # Customer
    obt = obt.merge(
        dim_customer[["customer_id", "age_group", "gender", "home_district",
                       "loyalty_tier", "has_app"]],
        on="customer_id", how="left"
    )

    # Payment
    obt = obt.merge(
        dim_payment[["payment_id", "payment_type"]],
        on="payment_id", how="left"
    )

    # Promotion
    obt = obt.merge(
        dim_promotion, on="promo_id", how="left", suffixes=("", "_promo")
    )

    # Weather (über date_id)
    if "date_id" in dim_weather.columns:
        obt = obt.merge(dim_weather, on="date_id", how="left", suffixes=("", "_weather"))

    # Item-Aggregation
    obt = obt.merge(item_agg, on="order_id", how="left")

    # --- Aufräumen ---
    # Doppelte/überflüssige Spalten entfernen
    drop_cols = [c for c in obt.columns if c.endswith("_dim") or c.endswith("_weather")]
    # date_dim duplicate
    if "date_dim" in obt.columns:
        drop_cols.append("date_dim")
    obt.drop(columns=drop_cols, errors="ignore", inplace=True)

    # --- Export ---
    out_path = base / "obt_orders.csv"
    print(f"Schreibe {len(obt):,} Zeilen nach {out_path.name}...")
    obt.to_csv(out_path, index=False, encoding="utf-8-sig")

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Fertig! {out_path.name} ({size_mb:.0f} MB, {len(obt):,} Zeilen, {len(obt.columns)} Spalten)")


if __name__ == "__main__":
    main()
