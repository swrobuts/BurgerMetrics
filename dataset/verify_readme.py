#!/usr/bin/env python3
"""
verify_readme.py — Rechnet jede Zahl aus README.md gegen die CSV-Dateien nach.

Der Datensatz lebt davon, dass die dokumentierten Muster stimmen: Studierende
suchen genau nach ihnen. Eine README, die einen älteren Datenstand beschreibt,
schickt sie hinter Mustern her, die es nicht gibt. Dieses Skript macht die
Dokumentation überprüfbar statt nur behauptet.

Verwendung:
    python verify_readme.py          # Exit-Code 0 = alles bestätigt, 1 = Abweichung

Voraussetzungen: Python 3.8+, pandas, alle CSVs im selben Verzeichnis.
Laufzeit: rund 1 Minute (liest die 86-MB-Positionsdatei).

Nach jeder Änderung an den Daten oder an README.md hier erneut durchlaufen.
"""

import sys
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
ENCODING = "utf-8-sig"

_ergebnisse = []


def lade(name, **kwargs):
    return pd.read_csv(BASE / name, encoding=ENCODING, **kwargs)


def pruefe(label, berechnet, readme_wert, toleranz=0.005):
    """Vergleicht einen berechneten Wert mit der Angabe in README.md.

    toleranz ist relativ; 0 erzwingt exakte Gleichheit (für Zählungen).
    """
    berechnet, readme_wert = float(berechnet), float(readme_wert)
    grenze = toleranz * max(abs(readme_wert), 1e-9)
    bestanden = abs(berechnet - readme_wert) <= grenze
    _ergebnisse.append(bestanden)
    status = "OK    " if bestanden else "ABWEICHUNG"
    print(f"  {status}  {label}: README={readme_wert:g}  berechnet={berechnet:.4g}")


def main():
    print("Lade Daten...")
    fo = lade("fact_orders.csv")
    fi = lade("fact_order_items.csv")
    dd = lade("dim_date.csv", keep_default_na=False)
    br = lade("dim_branch.csv")
    cu = lade("dim_customer.csv", keep_default_na=False)
    pr = lade("dim_product.csv")
    pm = lade("dim_payment_method.csv")

    print("\n--- Umfang ---")
    pruefe("Bestellungen", len(fo), 754_513, 0)
    pruefe("Bestellpositionen", len(fi), 2_950_082, 0)
    pruefe("Kunden", len(cu), 25_000, 0)
    pruefe("Produkte", len(pr), 57, 0)
    pruefe("Kalendertage", len(dd), 3_377, 0)
    pruefe("Promotions", len(lade("dim_promotion.csv")), 13, 0)
    pruefe("Mitarbeiter", len(lade("dim_employee.csv")), 188, 0)
    pruefe("Umsatz (Mio. EUR)", fo.net_total.sum() / 1e6, 14.52, 0.002)
    pruefe("Bestellwert (EUR)", fo.net_total.mean(), 19.25, 0.002)
    pruefe("Bewertete Bestellungen (%)", fo.satisfaction_score.notna().mean() * 100, 18.9, 0.02)
    pruefe("Promotions-Anteil (%)", (fo.promo_id != 0).mean() * 100, 8.2, 0.02)
    pruefe("Bestellungen mit Promotion", (fo.promo_id != 0).sum(), 62_023, 0)

    f = fo.merge(dd[["date", "day_name", "special_event", "month", "is_weekend"]], on="date", how="left")

    print("\n--- Zeitliche Muster ---")
    tag = f.groupby("day_name").agg(b=("order_id", "count"), t=("date", "nunique"))
    tag["pro_tag"] = tag.b / tag.t
    pruefe("Samstag (Bestellungen/Tag)", tag.loc["Saturday", "pro_tag"], 278, 0.01)
    pruefe("Dienstag (Bestellungen/Tag)", tag.loc["Tuesday", "pro_tag"], 195, 0.01)
    pruefe("Samstag vs. Dienstag (%)", (tag.loc["Saturday", "pro_tag"] / tag.loc["Tuesday", "pro_tag"] - 1) * 100, 43, 0.05)
    stunde = f.groupby("hour").order_id.count()
    pruefe("Bestellungen 12 Uhr", stunde[12], 121_331, 0)
    pruefe("Bestellungen 13 Uhr", stunde[13], 104_250, 0)

    basis = f[f.special_event == ""].groupby("date").order_id.count().mean()
    pruefe("Basis ohne Event (Bestellungen/Tag)", basis, 221, 0.01)
    for event, erwartet in [("Kiliani", 34), ("Weihnachtsmarkt", 5)]:
        mittel = f[f.special_event == event].groupby("date").order_id.count().mean()
        pruefe(f"Event {event} (%)", (mittel / basis - 1) * 100, erwartet, 0.10)

    uni = f[f.branch_id == 3].groupby("month").order_id.count() / dd.groupby("month").date.nunique()
    pruefe("Sanderring August (Bestellungen/Tag)", uni[8], 18.4, 0.02)
    pruefe("Sanderring August vs. Jahresmittel (%)", (uni[8] / uni.mean() - 1) * 100, -31, 0.06)

    print("\n--- Standort und Kanal ---")
    fb = f.merge(br[["branch_id", "has_drive_through"]], on="branch_id")
    dt = fb.groupby("has_drive_through").agg(aov=("net_total", "mean"), items=("item_count", "mean"))
    pruefe("Bestellwert mit Drive-Through", dt.loc[True, "aov"], 19.53)
    pruefe("Bestellwert ohne Drive-Through", dt.loc[False, "aov"], 18.82)
    pruefe("Artikel mit Drive-Through", dt.loc[True, "items"], 4.64, 0.01)
    pruefe("Artikel ohne Drive-Through", dt.loc[False, "items"], 4.34, 0.01)

    miete = br.set_index("branch_id")[["monthly_rent_eur"]].join(f.groupby("branch_id").net_total.sum().rename("umsatz"))
    pruefe("Korrelation Miete~Umsatz", miete.monthly_rent_eur.corr(miete.umsatz), 0.68, 0.02)
    kanal = pd.crosstab(f.branch_id, f.order_channel, normalize="index") * 100
    pruefe("Europastern Drive-Through (%)", kanal.loc[1, "Drive-Through"], 53.6, 0.01)
    aov_filiale = f.groupby("branch_id").net_total.mean()
    pruefe("Bestellwert Hauptbahnhof", aov_filiale[2], 17.80)
    pruefe("Bestellwert Zellerau", aov_filiale[8], 21.05)
    wochenende = f.groupby("branch_id").is_weekend.mean() * 100
    pruefe("Wochenendanteil Sanderring (%)", wochenende[3], 23, 0.05)
    pruefe("Wochenendanteil Mainfrankenpark (%)", wochenende[6], 42, 0.05)

    print("\n--- Kunden und Zahlung ---")
    fo["jahr"] = fo.date.str[:4].astype(int)
    zahlart = dict(zip(pm.payment_id, pm.payment_type))
    for jahr, typ, erwartet in [(2018, "Cash", 48.6), (2025, "Cash", 20.4),
                                (2018, "Mobile Payment", 0.9), (2025, "Mobile Payment", 12.2),
                                (2025, "EC Card", 40.3)]:
        anteil = (fo[fo.jahr == jahr].payment_id.map(zahlart).value_counts(normalize=True) * 100).get(typ, 0)
        pruefe(f"{typ} {jahr} (%)", anteil, erwartet, 0.02)

    fc = fo.merge(cu[["customer_id", "loyalty_tier", "has_app"]], on="customer_id", how="left")
    loy = fc.groupby("loyalty_tier").agg(umsatz=("net_total", "sum"), kunden=("customer_id", "nunique"),
                                         best=("order_id", "count"), aov=("net_total", "mean"))
    pruefe("Gold: Bestellungen/Kopf", loy.loc["Gold", "best"] / loy.loc["Gold", "kunden"], 33.8, 0.01)
    pruefe("Ohne Programm: Bestellungen/Kopf", loy.loc["None", "best"] / loy.loc["None", "kunden"], 30.4, 0.01)
    pruefe("Gold: EUR/Kopf", loy.loc["Gold", "umsatz"] / loy.loc["Gold", "kunden"], 627, 0.01)
    pruefe("Ohne Programm: EUR/Kopf", loy.loc["None", "umsatz"] / loy.loc["None", "kunden"], 590, 0.01)
    pruefe("Gold: Bestellwert", loy.loc["Gold", "aov"], 18.56)
    pruefe("Ohne Programm: Bestellwert", loy.loc["None", "aov"], 19.40)

    app = fc.groupby("has_app").agg(aov=("net_total", "mean"), best=("order_id", "count"), kunden=("customer_id", "nunique"))
    pruefe("App-Nutzer: Bestellwert", app.loc[True, "aov"], 19.04)
    pruefe("Ohne App: Bestellwert", app.loc[False, "aov"], 19.41)
    pruefe("App-Nutzer: Bestellungen/Kopf", app.loc[True, "best"] / app.loc[True, "kunden"], 29.2, 0.01)
    pruefe("Ohne App: Bestellungen/Kopf", app.loc[False, "best"] / app.loc[False, "kunden"], 31.0, 0.01)

    app_filiale = fo.merge(cu[["customer_id", "has_app"]], on="customer_id").groupby("branch_id").has_app.mean() * 100
    pruefe("App-Quote je Filiale: Minimum (%)", app_filiale.min(), 43, 0.03)
    pruefe("App-Quote je Filiale: Maximum (%)", app_filiale.max(), 45, 0.03)
    bezirk = cu.home_district.value_counts()
    pruefe("Kunden je Bezirk: Minimum", bezirk.min(), 2_023, 0.001)
    pruefe("Kunden je Bezirk: Maximum", bezirk.max(), 2_185, 0.001)

    print("\n--- Wartezeit und Zufriedenheit ---")
    z = fo.dropna(subset=["satisfaction_score"])
    klassen = z.groupby(pd.cut(z.order_duration_min, [0, 5, 10, 15, 20, 100]), observed=True).satisfaction_score.agg(["mean", "size"])
    pruefe("Zufriedenheit 0-5 Min.", klassen.iloc[0]["mean"], 3.83)
    pruefe("Zufriedenheit 10-15 Min.", klassen.iloc[2]["mean"], 3.69)
    pruefe("Zufriedenheit 15-20 Min.", klassen.iloc[3]["mean"], 3.47)
    pruefe("Fallzahl 15-20 Min.", klassen.iloc[3]["size"], 282, 0)
    pruefe("Fallzahl ueber 20 Min.", klassen.iloc[4]["size"], 2, 0)
    pruefe("Korrelation Dauer~Zufriedenheit", z.order_duration_min.corr(z.satisfaction_score), -0.061, 0.05)

    print("\n--- Saisonalitaet ---")
    it = (fi.merge(pr[["product_id", "product_name", "category", "subcategory"]], on="product_id", how="left")
            .merge(fo[["order_id", "date"]], on="order_id")
            .merge(dd[["date", "season"]], on="date"))
    tage = dd.groupby("season").date.nunique()
    je_saison = lambda maske: it[maske].groupby("season").quantity.sum() / tage
    eis = je_saison(it.subcategory.isin(["Ice Cream", "Sundae"]))
    kalt = je_saison(it.subcategory.isin(["Soft Drink", "Water", "Juice", "Milkshake"]))
    heiss = je_saison(it.subcategory == "Hot Drink")
    pruefe("Eis Sommer/Winter", eis["Summer"] / eis["Winter"], 2.78, 0.01)
    pruefe("Kaltgetraenke Sommer/Winter", kalt["Summer"] / kalt["Winter"], 1.50, 0.01)
    pruefe("Heissgetraenke Winter (Stueck/Tag)", heiss["Winter"], 114.1, 0.01)
    pruefe("Heissgetraenke Sommer (Stueck/Tag)", heiss["Summer"], 74.5, 0.01)
    pruefe("Heissgetraenke Winter/Sommer", heiss["Winter"] / heiss["Summer"], 1.53, 0.01)

    print("\n--- Warenkorb ---")
    # Explizite Produktlisten statt LIKE-Mustern: '%Cola%' trifft auch
    # 'Milkshake Chocolate', '%BBQ%' auch den Burger 'BBQ Smokehouse'.
    n = fo.order_id.nunique()
    korb = it.groupby("order_id").product_name.apply(set)
    kategorien = it.groupby("order_id").category.apply(set)
    enthaelt = lambda namen: korb.apply(lambda b: bool(b & set(namen)))

    cola = enthaelt(["Cola 0.3l", "Cola 0.5l"])
    fries = enthaelt(["Small Fries", "Medium Fries", "Large Fries", "Loaded Fries", "Sweet Potato Fries"])
    nuggets = enthaelt(["Chicken Nuggets 6pc", "Chicken Nuggets 9pc"])
    bbq = enthaelt(["BBQ Sauce"])
    coffee = enthaelt(["Coffee"])
    beer = enthaelt(["Beer 0.3l"])
    burger = kategorien.apply(lambda c: "Burger" in c)
    breakfast = kategorien.apply(lambda c: "Breakfast" in c)

    anteil = lambda m: m.sum() / n * 100
    lift = lambda a, b: ((a & b).sum() / n) / ((a.sum() / n) * (b.sum() / n))

    for label, maske, erwartet in [("Burger", burger, 59.6), ("Fries", fries, 51.1), ("Cola", cola, 41.6),
                                   ("BBQ-Sauce", bbq, 4.6), ("Coffee", coffee, 16.9), ("Beer", beer, 12.3)]:
        pruefe(f"Anteil {label} (%)", anteil(maske), erwartet, 0.02)

    pruefe("Support Burger+Fries+Cola (%)", anteil(burger & fries & cola), 29.2)
    pruefe("Support Nuggets+BBQ (%)", anteil(nuggets & bbq), 2.7, 0.02)
    pruefe("Konfidenz Nuggets->BBQ (%)", (nuggets & bbq).sum() / nuggets.sum() * 100, 40.9)
    pruefe("Support Breakfast+Coffee (%)", anteil(breakfast & coffee), 4.1, 0.02)
    pruefe("Konfidenz Breakfast->Coffee (%)", (breakfast & coffee).sum() / breakfast.sum() * 100, 60.8)
    pruefe("Support Burger+Beer (%)", anteil(burger & beer), 7.6, 0.02)
    pruefe("Konfidenz Burger->Beer (%)", (burger & beer).sum() / burger.sum() * 100, 12.7)
    pruefe("Lift Nuggets->BBQ", lift(nuggets, bbq), 8.93, 0.01)
    pruefe("Lift Breakfast->Coffee", lift(breakfast, coffee), 3.59, 0.01)
    pruefe("Lift Burger->Beer", lift(burger, beer), 1.03, 0.01)
    pruefe("Lift Burger+Fries+Cola",
           ((burger & fries & cola).sum() / n) / ((burger.sum() / n) * (fries.sum() / n) * (cola.sum() / n)),
           2.30, 0.01)

    bestanden = sum(_ergebnisse)
    gesamt = len(_ergebnisse)
    print(f"\n==> {bestanden} von {gesamt} Angaben bestaetigt, {gesamt - bestanden} abweichend")
    return 0 if bestanden == gesamt else 1


if __name__ == "__main__":
    sys.exit(main())
