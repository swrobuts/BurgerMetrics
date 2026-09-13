#!/usr/bin/env python3
"""bau_02.py — schreibt notebooks/02_rfm_und_kundensegmente.ipynb."""
from gemeinsam import code, kopf, md, schreiben

ZELLEN = kopf("02", "RFM und Kundensegmente", "02_rfm_und_kundensegmente.ipynb") + [
md("""
## Fragestellung

Welche Kunden sind wertvoll, welche verloren — und lassen sich die Kunden ohne Vorgaben in
Gruppen teilen, die sich sinnvoll beschreiben lassen?

## Daten

`fact_orders` (754.513 Bestellungen von 24.992 Kunden), aggregiert je Kunde: Tage seit der
letzten Bestellung (Recency), Zahl der Bestellungen (Frequency) und Umsatz (Monetary) zum
Stichtag 31.03.2026. Zum Vergleich die Sicht `v_rfm_kunde` der Semantikschicht.

## Vorgehen

RFM-Werte je Kunde in SQL berechnen, jede Größe in Quintile teilen (mit `customer_id` als
Zweitschlüssel, damit Gleichstände reproduzierbar zugeordnet werden), Segmente nach festen
Regeln bilden und mit der Sicht abgleichen. Danach K-Means auf standardisierten Werten,
Elbow-Kurve und Silhouette zur Wahl von k, Beschreibung der Cluster.
"""),
code("""
STICHTAG = "2026-03-31"
basis = lade_sql(f\"\"\"
    SELECT customer_id,
           DATE '{STICHTAG}' - max(date) AS recency_tage,
           count(*)                       AS frequenz,
           sum(net_total)                 AS monetaer
    FROM fact_orders
    GROUP BY customer_id
    ORDER BY customer_id\"\"\")
print(f"{zahl(len(basis))} Kunden mit mindestens einer Bestellung.")
basis.describe().round(1)
"""),
md("""
### Quintile mit Zweitschlüssel

`ntile(5)` in PostgreSQL füllt fünf gleich große Fächer und gibt die ersten Fächer eine Zeile
mehr, wenn die Zahl nicht teilbar ist. Bei Gleichständen entscheidet die Reihenfolge — deshalb
sortieren wir zusätzlich nach `customer_id`. So kommt in Python dasselbe heraus wie in der
Datenbank.
"""),
code("""
import numpy as np

def fachgroessen(n, k=5):
    # Fachgrößen wie ntile(k): die ersten (n mod k) Fächer bekommen eine Zeile mehr
    basisgroesse, rest = divmod(n, k)
    return [basisgroesse + 1 if i < rest else basisgroesse for i in range(k)]

def quintil(daten, spalte):
    # Sortiert aufsteigend nach der Spalte, bei Gleichstand nach customer_id, und vergibt die Fachnummer 1 bis 5
    reihenfolge = daten.sort_values([spalte, "customer_id"]).index
    faecher = np.repeat(np.arange(1, 6), fachgroessen(len(daten)))
    return pd.Series(faecher, index=reihenfolge).reindex(daten.index)

rfm = basis.copy()
rfm["r_wert"] = 6 - quintil(rfm, "recency_tage")   # wenige Tage = hoher Wert
rfm["f_wert"] = quintil(rfm, "frequenz")
rfm["m_wert"] = quintil(rfm, "monetaer")
rfm[["r_wert", "f_wert", "m_wert"]].apply(pd.Series.value_counts).sort_index()
"""),
md("### Segmente nach festen Regeln"),
code("""
def segment(zeile):
    # Dieselben Regeln wie in v_rfm_kunde (db/aufbau/0009): Recency und Frequency entscheiden
    r, f = zeile["r_wert"], zeile["f_wert"]
    if r >= 4 and f >= 4:
        return "Champions"
    if r >= 3 and f >= 3:
        return "Loyal"
    if r >= 4 and f >= 2:
        return "Potenzial"
    if r >= 4:
        return "Neukunden"
    if r == 3:
        return "Schläfer"
    if r == 2:
        return "Abwanderungsgefahr"
    return "Verloren"

rfm["segment"] = rfm.apply(segment, axis=1)
uebersicht = rfm.groupby("segment").agg(kunden=("customer_id", "count"), recency_tage=("recency_tage", "mean"),
                                        frequenz=("frequenz", "mean"), umsatz=("monetaer", "sum")).round(1)
uebersicht.sort_values("kunden", ascending=False)
"""),
md("### Abgleich mit `v_rfm_kunde`"),
code("""
sicht = lade_sql("SELECT customer_id, r_wert, f_wert, m_wert, segment FROM v_rfm_kunde")
abgleich = rfm.merge(sicht, on="customer_id", suffixes=("", "_db"))
gleich = {spalte: (abgleich[spalte] == abgleich[f"{spalte}_db"]).mean() * 100
          for spalte in ["r_wert", "f_wert", "m_wert", "segment"]}
pd.DataFrame({"spalte": gleich.keys(), "uebereinstimmung_pct": [round(v, 2) for v in gleich.values()]})
"""),
md("""
Die Übereinstimmung liegt bei 100 Prozent: Der Zweitschlüssel macht die Quintile
reproduzierbar, in SQL wie in Python.

### K-Means: Gruppen ohne Vorgabe

RFM-Segmente folgen Regeln, die jemand festgelegt hat. K-Means sucht Gruppen in den Daten
selbst. Alle drei Größen sind schief verteilt — Recency am stärksten (einzelne Kunden waren
seit Jahren nicht da). Wir logarithmieren alle drei und standardisieren sie, damit
keine Größe die Distanz allein bestimmt.
"""),
code("""
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

merkmale = pd.DataFrame({
    "recency_log": np.log1p(rfm["recency_tage"]),
    "frequenz_log": np.log1p(rfm["frequenz"]),
    "monetaer_log": np.log1p(rfm["monetaer"]),
})
X = StandardScaler().fit_transform(merkmale)

stichprobe = np.random.default_rng(2026).choice(len(X), 5000, replace=False)
bewertung = []
for k in range(2, 9):
    modell = KMeans(n_clusters=k, n_init=10, random_state=2026).fit(X)
    bewertung.append({"k": k, "inertia": modell.inertia_,
                      "silhouette": silhouette_score(X[stichprobe], modell.labels_[stichprobe])})
bewertung = pd.DataFrame(bewertung)
bewertung.round(3)
"""),
code("""
import matplotlib.pyplot as plt

abb, (links, rechts) = plt.subplots(1, 2, figsize=(9, 4))
links.plot(bewertung["k"], bewertung["inertia"], marker="o")
links.set_xlabel("k (Zahl der Cluster)")
links.set_ylabel("Inertia (Summe der quadrierten Abstände)")
links.set_title("Elbow: der Knick liegt bei k = 4")
links.set_ylim(0)
rechts.plot(bewertung["k"], bewertung["silhouette"], marker="o")
rechts.set_xlabel("k (Zahl der Cluster)")
rechts.set_ylabel("Silhouette (Stichprobe 5.000)")
rechts.set_title("Silhouette: am höchsten bei k = 2, ab k = 4 fallend")
rechts.set_ylim(0)
plt.tight_layout()
plt.show()
"""),
code("""
K = 4
kmeans = KMeans(n_clusters=K, n_init=10, random_state=2026).fit(X)
rfm["cluster"] = kmeans.labels_
beschreibung = rfm.groupby("cluster").agg(kunden=("customer_id", "count"), recency_tage=("recency_tage", "mean"),
                                          frequenz=("frequenz", "mean"), monetaer=("monetaer", "mean")).round(1)
beschreibung
"""),
code("""
# Wie verteilen sich die RFM-Segmente auf die Cluster? Zeilen: Segment, Spalten: Cluster.
pd.crosstab(rfm["segment"], rfm["cluster"])
"""),
md("""
## Ergebnis

Die RFM-Segmente aus Python und aus der Datenbank stimmen überein; die Regeln lassen sich
also überall gleich anwenden. Cluster 2 (1.910 Kunden) hat mit Abstand die höchste Recency
(im Mittel 337,9 Tage seit der letzten Bestellung) sowie die niedrigste Frequenz und den
niedrigsten Umsatz. Cluster 3 (6.084 Kunden) hat die niedrigste Recency (11,1 Tage) bei hoher
Frequenz (36,1) und hohem Umsatz (698,0 €). Cluster 1 (10.893 Kunden, die größte Gruppe)
ähnelt Cluster 3 bei Frequenz und Umsatz, hat aber eine deutlich höhere Recency (95,7 Tage).
Cluster 0 (6.105 Kunden) liegt bei allen drei Größen im Mittelfeld. Die Silhouette bevorzugt
k = 2; wir wählen k = 4, weil vier Gruppen sich noch beschreiben lassen — eine Entscheidung,
keine Messung.

## Was offen bleibt

Die Wahl von k ist eine Entscheidung, keine Messung: Elbow und Silhouette geben Hinweise, das
Geschäft entscheidet, wie viele Gruppen es ansprechen kann. Die Kundendaten sind synthetisch
und gleichverteilt über die Stadtteile — echte Segmente hätten mehr Struktur.
"""),
]

schreiben("02_rfm_und_kundensegmente.ipynb", ZELLEN)
