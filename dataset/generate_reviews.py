#!/usr/bin/env python3
"""
generate_reviews.py — erzeugt 10.000 Rezensionen zu echten Bestellpositionen.

Fachlicher Hintergrund
----------------------
Jede Rezension hängt an einer bewerteten Bestellung (satisfaction_score ist
gesetzt) und an einem Produkt daraus. Die Sterne folgen einer latenten Größe
aus Zufriedenheit und Bestelldauer der Bestellung, einem Produktniveau und
Rauschen. So findet die Sentiment-Analyse später einen Zusammenhang, den man
nachrechnen kann. Der Text entsteht aus Satzbausteinen je Sternestufe
(rezension_bausteine.json); rund 15 Prozent sind umgangssprachlich.

Verwendung
----------
    python3 generate_reviews.py                    # schreibt fact_reviews_roh.csv
    python3 generate_reviews.py --anzahl 500       # kleiner Probelauf
    python3 generate_reviews.py --ausgabe /pfad/x.csv

Zwei Läufe mit demselben Seed liefern byte-identische Dateien. Der geglättete
Bestand fact_reviews.csv entsteht danach in glaettung/ (siehe README).
"""
import argparse
import json
from datetime import date, timedelta
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

BASIS = Path(__file__).resolve().parent
ENCODING = "utf-8-sig"
LETZTER_TAG = date(2026, 3, 31)           # Ende von dim_date
ANTEIL_UMGANGSSPRACHE = 0.15
# Feste Abweichung je Produkt von der mittleren Bewertung (0 = Durchschnitt).
PRODUKTNIVEAU = {
    "Truffle Deluxe": 0.4, "Smashed Burger": 0.3, "BBQ Smokehouse": 0.25, "Crispy Chicken Deluxe": 0.2,
    "Beyond Burger": 0.15, "Craft Lemonade": 0.2, "Fresh OJ": 0.15, "Sweet Potato Fries": 0.15,
    "Fish Burger": -0.3, "Kids Burger": -0.2, "Water 0.5l": -0.1, "Coleslaw": -0.2,
    "Hash Browns": -0.15, "Donut": -0.1, "Scrambled Eggs & Toast": -0.2, "Onion Rings": -0.1,
}
# Kumulierte Anteile der Sterne 1 bis 4 — die Schwellen liegen auf diesen
# Quantilen der latenten Größe, dadurch stimmt die Verteilung exakt.
STERNE_QUANTILE = [0.13, 0.22, 0.35, 0.62]
# Uhrzeit der Rezension: Stunden 7 bis 23 mit Abendspitze.
STUNDEN = list(range(7, 24))
STUNDEN_GEWICHT = [1, 1, 2, 2, 3, 4, 4, 3, 3, 3, 4, 5, 6, 6, 5, 4, 3]


def lade_kandidaten(basis):
    """Liest bewertete Bestellpositionen ohne Extras samt Gewicht aus den CSV-Dateien."""
    con = duckdb.connect()
    pfad = lambda name: str((basis / f"{name}.csv").resolve()).replace("'", "''")
    return con.execute(f"""
        SELECT o.order_id, o.date, o.branch_id, o.customer_id, o.order_channel,
               o.order_duration_min, o.satisfaction_score, o.promo_id,
               i.product_id, p.product_name, p.category, c.has_app, b.branch_name,
               (1 + (extract(year FROM o.date) - 2017) / 3.0)
               * CASE o.order_channel WHEN 'App Order' THEN 3 WHEN 'Kiosk' THEN 1.5 ELSE 1 END
               * CASE WHEN c.has_app THEN 2 ELSE 1 END AS gewicht
        FROM read_csv_auto('{pfad("fact_orders")}', header = true) o
        JOIN read_csv_auto('{pfad("fact_order_items")}', header = true) i USING (order_id)
        JOIN read_csv_auto('{pfad("dim_product")}', header = true) p USING (product_id)
        JOIN read_csv_auto('{pfad("dim_customer")}', header = true) c USING (customer_id)
        JOIN read_csv_auto('{pfad("dim_branch")}', header = true) b USING (branch_id)
        WHERE o.satisfaction_score IS NOT NULL AND p.category <> 'Extra'
        ORDER BY o.order_id, i.order_item_id
    """).df()


def ziehe_stichprobe(kandidaten, anzahl, rng):
    """Wählt gewichtet Bestellungen aus und je Bestellung eine Position."""
    je_bestellung = kandidaten.groupby("order_id").gewicht.first()
    gewichte = je_bestellung.values / je_bestellung.values.sum()
    gewaehlt = rng.choice(je_bestellung.index.values, size=anzahl, replace=False, p=gewichte)
    positionen_je_bestellung = kandidaten.groupby("order_id").indices
    zeilen = [rng.choice(positionen_je_bestellung[order_id]) for order_id in gewaehlt]
    return kandidaten.iloc[zeilen].reset_index(drop=True)


def berechne_sterne(stichprobe, rng):
    """Latente Größe aus Zufriedenheit, Dauer, Produktniveau und Rauschen; Quantile setzen die Schwellen."""
    median_dauer = stichprobe.order_duration_min.median()
    niveau = stichprobe.product_name.map(PRODUKTNIVEAU).fillna(0.0)
    z = (1.2 * (stichprobe.satisfaction_score - 3.8)
         - 0.03 * (stichprobe.order_duration_min - median_dauer)
         + niveau + rng.normal(0, 0.6, len(stichprobe)))
    schwellen = np.quantile(z, STERNE_QUANTILE)
    return pd.Series(1 + np.searchsorted(schwellen, z, side="right"), index=stichprobe.index)


def polaritaet(sterne):
    """Sterne 1–2 negativ, 3 neutral, 4–5 positiv."""
    if sterne <= 2:
        return "negativ"
    if sterne == 3:
        return "neutral"
    return "positiv"


def wartezeit_klasse(minuten):
    """Bestelldauer in drei Klassen für die Kontextsätze."""
    if minuten <= 4:
        return "kurz"
    if minuten <= 9:
        return "mittel"
    return "lang"


def kontextsatz(zeile, sterne, bausteine, rng):
    """Ein Satz zu Wartezeit, Kanal, Filiale oder Preis — passend zur Bestellung."""
    art = rng.choice(["wartezeit", "kanal", "filiale", "preis"], p=[0.4, 0.25, 0.2, 0.15])
    k = bausteine["kontext"]
    if art == "wartezeit":
        klasse = wartezeit_klasse(zeile.order_duration_min)
        if klasse == "lang":
            return rng.choice(k["wartezeit"]["lang"]["positiv" if sterne >= 4 else "negativ"])
        return rng.choice(k["wartezeit"][klasse])
    if art == "kanal":
        return rng.choice(k["kanal"][zeile.order_channel])
    if art == "filiale":
        return rng.choice(k["filiale"]).replace("{filiale}", zeile.branch_name)
    if zeile.promo_id != 0:
        return rng.choice(k["preis"]["mit_aktion"])
    return rng.choice(k["preis"][polaritaet(sterne)])


def umgangssprachlich(text, rng):
    """Kleinschreibung, ae/oe/ue statt Umlaute, gelegentlich mehrfache Satzzeichen."""
    text = text.lower()
    for alt, neu in [("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")]:
        text = text.replace(alt, neu)
    if rng.random() < 0.5:
        text = text.rstrip(".") + rng.choice(["!!", "...", "!"])
    return text


def erzeuge_text(zeile, sterne, bausteine, rng):
    """Einstieg, Produktsatz, optional Kontext und Schluss — ein bis vier Sätze."""
    stufe = str(sterne)
    saetze = [rng.choice(bausteine["einstieg"][stufe])]
    produkt = rng.choice(bausteine["produkt"][zeile.category][polaritaet(sterne)])
    saetze.append(produkt.replace("{produkt}", zeile.product_name))
    if rng.random() < 0.55:
        saetze.append(kontextsatz(zeile, sterne, bausteine, rng))
    if sterne != 3 and rng.random() < 0.35:
        saetze.append(rng.choice(bausteine["schluss"][stufe]))
    text = " ".join(saetze)
    if len(text) > 500:
        text = " ".join(saetze[:2])       # Einstieg und Produktsatz reichen immer unter 500 Zeichen
    if rng.random() < ANTEIL_UMGANGSSPRACHE:
        text = umgangssprachlich(text, rng)
    return text


def erzeuge_zeitpunkt(bestelldatum, rng):
    """Datum 0–3 Tage nach der Bestellung (höchstens Ende des Kalenders), Uhrzeit mit Abendspitze."""
    tag = min(pd.Timestamp(bestelldatum).date() + timedelta(days=int(rng.integers(0, 4))), LETZTER_TAG)
    stunde = rng.choice(STUNDEN, p=np.array(STUNDEN_GEWICHT) / sum(STUNDEN_GEWICHT))
    return tag.isoformat(), f"{stunde:02d}:{int(rng.integers(0, 60)):02d}:{int(rng.integers(0, 60)):02d}"


def erzeuge_rezensionen(kandidaten, bausteine, anzahl=10_000, seed=2026):
    """Der ganze Lauf: Stichprobe, Sterne, Texte, Zeitpunkte, Nummerierung."""
    rng = np.random.default_rng(seed)
    stichprobe = ziehe_stichprobe(kandidaten, anzahl, rng)
    sterne = berechne_sterne(stichprobe, rng)
    zeilen = []
    for i, zeile in stichprobe.iterrows():
        datum, uhrzeit = erzeuge_zeitpunkt(zeile.date, rng)
        zeilen.append({
            "date": datum, "time": uhrzeit,
            "customer_id": int(zeile.customer_id), "product_id": int(zeile.product_id),
            "branch_id": int(zeile.branch_id), "order_id": int(zeile.order_id),
            "stars": int(sterne[i]), "review_text": erzeuge_text(zeile, int(sterne[i]), bausteine, rng),
            "source": "simulation"})
    ergebnis = pd.DataFrame(zeilen).sort_values(["date", "time", "order_id"]).reset_index(drop=True)
    ergebnis.insert(0, "review_id", range(1, len(ergebnis) + 1))
    return ergebnis


def main():
    """Kommandozeile: Kandidaten laden, erzeugen, schreiben, Verteilung nennen."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--anzahl", type=int, default=10_000)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--ausgabe", default=str(BASIS / "fact_reviews_roh.csv"))
    args = ap.parse_args()

    bausteine = json.loads((BASIS / "rezension_bausteine.json").read_text(encoding="utf-8"))
    print("Lade bewertete Bestellpositionen ...")
    kandidaten = lade_kandidaten(BASIS)
    print(f"  {len(kandidaten):,} Kandidaten".replace(",", "."))
    ergebnis = erzeuge_rezensionen(kandidaten, bausteine, args.anzahl, args.seed)
    ergebnis.to_csv(args.ausgabe, index=False, encoding=ENCODING, lineterminator="\n")
    anteile = (ergebnis.stars.value_counts(normalize=True).sort_index() * 100).round(1)
    print(f"Geschrieben: {args.ausgabe} ({len(ergebnis):,} Zeilen)".replace(",", "."))
    print("Sterne-Anteile in Prozent:", anteile.to_dict())


if __name__ == "__main__":
    main()
