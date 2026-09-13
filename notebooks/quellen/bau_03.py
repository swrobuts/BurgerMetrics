#!/usr/bin/env python3
"""bau_03.py — schreibt notebooks/03_warenkorbanalyse.ipynb."""
from gemeinsam import code, kopf, md, schreiben

ZELLEN = kopf("03", "Warenkorbanalyse", "03_warenkorbanalyse.ipynb") + [
md("""
## Fragestellung

Welche Produkte werden zusammen gekauft — und welche dieser Paare sind mehr als Zufall?

## Daten

Warenkörbe aus `fact_order_items` mit Produktnamen aus `dim_product`, beschränkt auf das erste
Quartal 2025 (rund 31.000 Bestellungen, 120.000 Positionen). Zum Vergleich die Sicht
`v_warenkorb_regeln`, die über den ganzen Bestand rechnet.

## Vorgehen

Warenkörbe in eine Tabelle Bestellung × Produkt (wahr/falsch) bringen, mit Apriori
(`mlxtend`) häufige Kombinationen finden, Regeln mit Support, Konfidenz und Lift ableiten,
die Richtung einer Regel prüfen und die Ergebnisse gegen die Sicht halten.
"""),
code("""
koerbe = lade_sql(\"\"\"
    SELECT o.order_id, p.product_name
    FROM fact_orders o
    JOIN fact_order_items i USING (order_id)
    JOIN dim_product p USING (product_id)
    WHERE o.date >= '2025-01-01' AND o.date < '2025-04-01'\"\"\")
tabelle = pd.crosstab(koerbe["order_id"], koerbe["product_name"]).astype(bool)
print(f"{zahl(tabelle.shape[0])} Warenkörbe, {zahl(tabelle.shape[1])} Produkte; im Mittel {zahl(tabelle.sum(axis=1).mean(), 2)} verschiedene Produkte je Korb.")
tabelle.iloc[:5, :6]
"""),
md("""
### Häufige Kombinationen mit Apriori

Der Support ist der Anteil der Körbe, die eine Kombination enthalten. Wir fordern mindestens
ein Prozent — darunter sind die Regeln zu selten, um zu tragen.
"""),
code("""
from mlxtend.frequent_patterns import apriori, association_rules

haeufig = apriori(tabelle, min_support=0.01, use_colnames=True)
haeufig["produkte"] = haeufig["itemsets"].apply(len)
print(f"{zahl(len(haeufig))} häufige Kombinationen, davon {zahl(int((haeufig['produkte'] >= 2).sum()))} mit zwei oder mehr Produkten.")
haeufig[haeufig["produkte"] >= 2].sort_values("support", ascending=False).head(10)
"""),
md("""
### Regeln: Support, Konfidenz, Lift

Konfidenz ist der Anteil der Körbe mit A, die auch B enthalten. Lift setzt das ins Verhältnis
zur Häufigkeit von B insgesamt: Lift 1 heißt „B kommt mit A nicht öfter vor als sonst", Lift 2
heißt doppelt so oft.
"""),
code("""
regeln = association_rules(haeufig, num_itemsets=len(tabelle), metric="lift", min_threshold=1.0)
regeln["A"] = regeln["antecedents"].apply(lambda s: ", ".join(sorted(s)))
regeln["B"] = regeln["consequents"].apply(lambda s: ", ".join(sorted(s)))
paare = regeln[(regeln["antecedents"].apply(len) == 1) & (regeln["consequents"].apply(len) == 1)]
spalten = ["A", "B", "support", "confidence", "lift"]
paare.sort_values("lift", ascending=False)[spalten].head(12).round(3)
"""),
md("""
### Die Richtung einer Regel

Eine Regel A → B hat denselben Support und denselben Lift wie B → A, aber nicht dieselbe
Konfidenz: Sie hängt davon ab, wie häufig A allein ist. Für die Empfehlung an der Kasse zählt
die Konfidenz — also die Richtung.
"""),
code("""
def beide_richtungen(a, b):
    # Konfidenz für A → B und B → A nebeneinander
    hin = paare[(paare["A"] == a) & (paare["B"] == b)]["confidence"]
    zurueck = paare[(paare["A"] == b) & (paare["B"] == a)]["confidence"]
    return {"A": a, "B": b, "konfidenz_A_B": float(hin.iloc[0]) if len(hin) else None,
            "konfidenz_B_A": float(zurueck.iloc[0]) if len(zurueck) else None}

beste = paare.sort_values("lift", ascending=False).drop_duplicates("support").head(6)
pd.DataFrame([beide_richtungen(z.A, z.B) for z in beste.itertuples()]).round(3)
"""),
md("### Vergleich mit der Semantikschicht (ganzer Bestand)"),
code("""
sicht = lade_sql("SELECT produkt_a, produkt_b, support_pct, konfidenz_pct, lift FROM v_warenkorb_regeln")

def paar(a, b):
    # Ein Paar unabhängig von der Richtung, damit sich beide Tabellen zusammenführen lassen
    return " | ".join(sorted([a, b]))

sicht["paar"] = [paar(a, b) for a, b in zip(sicht["produkt_a"], sicht["produkt_b"])]
paare_q1 = paare.assign(paar=[paar(a, b) for a, b in zip(paare["A"], paare["B"])])
paare_q1 = paare_q1.groupby("paar", as_index=False).agg(lift_q1_2025=("lift", "first"), support_q1_2025=("support", "first"))
vergleich = sicht.merge(paare_q1, on="paar", how="left")
vergleich["support_q1_2025"] = (vergleich["support_q1_2025"] * 100).round(2)
vergleich[["produkt_a", "produkt_b", "support_pct", "support_q1_2025", "lift", "lift_q1_2025"]].round(2)
"""),
md("### Die Paare ohne Signal: Lift nahe 1"),
code("""
def support_und_lift_q1(a, b):
    # Support und Lift eines Paares direkt aus der Korbtabelle des Quartals, ohne Schwellen
    zusammen = (tabelle[a] & tabelle[b]).mean()
    return pd.Series({"support_q1_pct": zusammen * 100,
                      "lift_q1": zusammen / (tabelle[a].mean() * tabelle[b].mean())})

nahe_eins = vergleich.assign(abstand=(vergleich["lift"] - 1).abs()).nsmallest(8, "abstand")
q1 = nahe_eins.apply(lambda z: support_und_lift_q1(z["produkt_a"], z["produkt_b"]), axis=1)
nahe_eins = nahe_eins.join(q1)
nahe_eins[["produkt_a", "produkt_b", "support_pct", "lift", "support_q1_pct", "lift_q1"]].round(2)
"""),
code("""
import matplotlib.pyplot as plt

abb, achse = plt.subplots(figsize=(6, 6))
achse.scatter(vergleich["lift"], vergleich["lift_q1_2025"])
grenze = max(vergleich["lift"].max(), vergleich["lift_q1_2025"].max()) * 1.05
untergrenze = min(vergleich["lift"].min(), vergleich["lift_q1_2025"].min()) * 0.95
achse.plot([untergrenze, grenze], [untergrenze, grenze], linestyle="--")
achse.set_xlabel("Lift im ganzen Bestand (v_warenkorb_regeln)")
achse.set_ylabel("Lift im ersten Quartal 2025 (Apriori)")
achse.set_title("Ein Quartal reicht für die meisten Paare; die stärksten liegen im Quartal höher")
achse.set_xlim(untergrenze, grenze)
achse.set_ylim(untergrenze, grenze)
plt.show()
"""),
md("""
## Ergebnis

Die stärksten Regeln verbinden Chicken Nuggets mit BBQ-Sauce und Burger mit Ketchup Extra, im
ersten Quartal wie im Gesamtbestand; ihre Lifts liegen deutlich über 1 und fallen im kleineren
Quartalsdatensatz noch etwas höher aus (11,23 statt 8,97 bei Chicken Nuggets 6pc und
BBQ-Sauce). Ein Lift nahe 1 — wie bei Medium Fries und Bier (1,00) und den sieben weiteren
Paaren mit dem geringsten Abstand zu 1 — ist dagegen kein Signal: Diese Produkte kommen
zusammen praktisch so oft vor wie unabhängig voneinander. Im ersten Quartal erreichen alle acht
Paare mehr als ein Prozent Support, aber ihr Lift liegt unter 1 (0,87 bis 0,98); deshalb fehlen
sie in `paare`: `association_rules` behält nur Regeln mit Lift ab 1.

## Was offen bleibt

Apriori findet Kombinationen, keine Ursachen: Dass Pommes zum Burger gehören, wusste die
Speisekarte schon. Interessant werden Regeln, die nicht auf der Hand liegen — dafür braucht es
mehr Produkte, als diese Karte hat, oder feinere Merkmale wie Tageszeit und Kanal.
"""),
]

schreiben("03_warenkorbanalyse.ipynb", ZELLEN)
