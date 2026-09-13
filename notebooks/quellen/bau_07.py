#!/usr/bin/env python3
"""bau_07.py — schreibt notebooks/07_ausreisser_tagesumsatz.ipynb."""
from gemeinsam import code, kopf, md, schreiben

ZELLEN = kopf("07", "Ausreißer im Tagesumsatz", "07_ausreisser_tagesumsatz.ipynb") + [
md("""
## Fragestellung

Welche Tage fallen im Umsatz einer Filiale aus dem Rahmen — und lassen sie sich erklären?

## Daten

Tagesumsatz und Bestellungen je Filiale aus `fact_orders` (17.744 Filialtage), Kalender aus
`dim_date` (Feiertag, Ereignis), Eröffnungsdatum aus `dim_branch`.

## Vorgehen

Drei Verfahren nebeneinander: z-Score je Filiale, Interquartilsabstand (IQR) je Filiale und
Isolation Forest über Umsatz, Bestellungen und Wochentag. Die Treffer werden mit Kalender und
Eröffnung erklärt — was übrig bleibt, ist der eigentliche Befund.
"""),
code("""
tage = lade_sql(\"\"\"
    SELECT o.date AS tag, b.branch_name AS filiale, b.opening_date AS eroeffnet, sum(o.net_total) AS umsatz,
           count(*) AS bestellungen, d.day_of_week AS wochentag, d.is_weekend AS wochenende,
           d.holiday_name AS feiertag, d.special_event AS ereignis
    FROM fact_orders o
    JOIN dim_date d ON d.date = o.date
    JOIN dim_branch b ON b.branch_id = o.branch_id
    GROUP BY o.date, b.branch_name, b.opening_date, d.day_of_week, d.is_weekend, d.holiday_name, d.special_event
    ORDER BY b.branch_name, o.date\"\"\")
tage["tag"] = pd.to_datetime(tage["tag"])
tage["eroeffnet"] = pd.to_datetime(tage["eroeffnet"])
tage["tage_seit_eroeffnung"] = (tage["tag"] - tage["eroeffnet"]).dt.days
print(f"{zahl(len(tage))} Filialtage für {zahl(tage['filiale'].nunique())} Filialen.")
tage.head()
"""),
md("### z-Score je Filiale"),
code("""
def z_score(spalte):
    # Abstand vom Filialmittel in Standardabweichungen — je Filiale, weil die Größen verschieden sind
    return (spalte - spalte.mean()) / spalte.std()

tage["z"] = tage.groupby("filiale")["umsatz"].transform(z_score)
tage["ausreisser_z"] = tage["z"].abs() > 3
print(f"{zahl(int(tage['ausreisser_z'].sum()))} Filialtage liegen mehr als drei Standardabweichungen vom Filialmittel entfernt.")
"""),
md("### Interquartilsabstand (IQR) je Filiale"),
code("""
def iqr_grenzen(gruppe):
    # Tukeys Regel: alles außerhalb von 1,5 IQR unter Q1 oder über Q3 gilt als Ausreißer
    q1, q3 = gruppe["umsatz"].quantile([0.25, 0.75])
    iqr = q3 - q1
    return (gruppe["umsatz"] < q1 - 1.5 * iqr) | (gruppe["umsatz"] > q3 + 1.5 * iqr)

tage["ausreisser_iqr"] = tage.groupby("filiale", group_keys=False).apply(iqr_grenzen, include_groups=False)
print(f"{zahl(int(tage['ausreisser_iqr'].sum()))} Filialtage nach der IQR-Regel.")
"""),
md("### Isolation Forest"),
code("""
from sklearn.ensemble import IsolationForest

merkmale = pd.DataFrame({
    "umsatz_relativ": tage["umsatz"] / tage.groupby("filiale")["umsatz"].transform("median"),
    "bestellungen_relativ": tage["bestellungen"] / tage.groupby("filiale")["bestellungen"].transform("median"),
    "wochentag": tage["wochentag"],
})
wald = IsolationForest(contamination=0.01, random_state=2026).fit(merkmale)
tage["ausreisser_forest"] = wald.predict(merkmale) == -1
tage["anomalie_wert"] = -wald.score_samples(merkmale)
pd.DataFrame({"verfahren": ["z-Score", "IQR", "Isolation Forest"],
              "treffer": [int(tage["ausreisser_z"].sum()), int(tage["ausreisser_iqr"].sum()), int(tage["ausreisser_forest"].sum())]})
"""),
md("### Treffer erklären"),
code("""
# Wie stark stimmen die drei Verfahren überein: alle drei Paare gekreuzt
print("z-Score gegen Isolation Forest, in Filialtagen:")
print(pd.crosstab(tage["ausreisser_z"], tage["ausreisser_forest"], rownames=["z-Score"], colnames=["Isolation Forest"]))
print()
print("IQR gegen Isolation Forest, in Filialtagen:")
print(pd.crosstab(tage["ausreisser_iqr"], tage["ausreisser_forest"], rownames=["IQR"], colnames=["Isolation Forest"]))
print()
print("z-Score gegen IQR, in Filialtagen:")
print(pd.crosstab(tage["ausreisser_z"], tage["ausreisser_iqr"], rownames=["z-Score"], colnames=["IQR"]))
print()
print(f"{zahl(int((tage['ausreisser_forest'] & ~tage['ausreisser_z'] & ~tage['ausreisser_iqr']).sum()))} Forest-Treffer tragen keine der beiden anderen Markierungen.")
"""),
code("""
def erklaerung(zeile):
    # Eine Erklärung aus Kalender und Eröffnung; bleibt keine, ist der Tag ein echter Befund
    if zeile["tage_seit_eroeffnung"] <= 14:
        return "Eröffnungsphase"
    if pd.notna(zeile["ereignis"]):
        return zeile["ereignis"]
    if pd.notna(zeile["feiertag"]):
        return zeile["feiertag"]
    if zeile["wochenende"]:
        return "Wochenende"
    return "unerklärt"

treffer = tage[tage["ausreisser_forest"]].copy()
treffer["erklaerung"] = treffer.apply(erklaerung, axis=1)
treffer.groupby("erklaerung").agg(filialtage=("erklaerung", "size"), mittlerer_z=("z", "mean"), z_min=("z", "min"), z_max=("z", "max")).sort_values("filialtage", ascending=False).round(2)
"""),
code("""
treffer.sort_values("anomalie_wert", ascending=False)[["tag", "filiale", "umsatz", "bestellungen", "z", "erklaerung", "ausreisser_z", "ausreisser_iqr"]].head(15).round({"umsatz": 2, "z": 2})
"""),
code("""
import matplotlib.pyplot as plt

FILIALE = "BM Europastern"
reihe = tage[tage["filiale"] == FILIALE].set_index("tag")
markiert = reihe[reihe["ausreisser_forest"]]
zaehlung = treffer[treffer["filiale"] == FILIALE]["erklaerung"].value_counts()
print(f"{FILIALE}: {zahl(len(markiert))} markierte Tage — " + ", ".join(f"{zahl(n)} {name}" for name, n in zaehlung.items()))
abb, achse = plt.subplots(figsize=(9, 4))
achse.plot(reihe.index, reihe["umsatz"], linewidth=0.6, label="Tagesumsatz")
achse.scatter(markiert.index, markiert["umsatz"], color="tab:red", s=18, zorder=3, label="Isolation Forest")
achse.set_xlabel("Tag")
achse.set_ylabel("Tagesumsatz in €")
achse.set_title(f"{FILIALE}: Die markierten Tage sind überwiegend Kiliani und Mozartfest")
achse.set_ylim(0)
achse.legend()
plt.show()
"""),
md("""
## Ergebnis

Die drei Verfahren überschneiden sich deutlich, aber nicht vollständig. Jeder der 79
z-Score-Ausreißer ist zugleich ein IQR-Ausreißer, und 59 von ihnen (75 Prozent) markiert auch
der Isolation Forest. Von den 213 IQR-Ausreißern markiert der Isolation Forest 105 (49 Prozent);
umgekehrt tragen 73 der 178 vom Isolation Forest markierten Tage (41 Prozent) keine der beiden
anderen Markierungen. Die 15 auffälligsten Treffer nach dem Isolation Forest sind dabei
durchweg auch z-Score- und IQR-Ausreißer — die stärksten Ausschläge finden alle drei Verfahren
gemeinsam; die nur vom Isolation Forest gefundenen Tage liegen entsprechend nicht unter den
auffälligsten Werten.

Die Erklärungstabelle zeigt eine klare Richtung: Kiliani (56 Filialtage, mittlerer z-Wert 3,25),
Mozartfest (26, 2,84), Weinfest (5, 2,57) und die Mainfranken Messe (2, 2,70) liegen durchweg
über dem Filialmittel — das sind die Sommerfeste. Nach unten fallen vor allem Ostermontag
(2, -2,27) und der Weihnachtsmarkt (8, -1,40); die 18 unerklärten Filialtage liegen im Mittel
ebenfalls darunter (-1,60). Der Wochenendeffekt ist mit 60 Filialtagen uneinheitlich (mittlerer
z-Wert 0,80, Spanne -2,41 bis 3,73): Wochenenden schlagen sowohl nach oben als auch nach unten
aus. Eine Eröffnungsphase kommt unter den Treffern nicht vor. Beim Plot für BM Europastern
bestätigt sich das Bild: 13 der 24 markierten Tage sind Kiliani, zwei weitere Mozartfest, der
Rest verteilt sich auf Wochenenden, einen Feiertag und drei unerklärte Tage.

## Was offen bleibt

„Unerklärt" heißt: nicht aus dem Kalender erklärbar. Im synthetischen Bestand ist das
Rauschen; in echten Daten wäre es der Anfang einer Nachfrage bei der Filiale.
"""),
]

schreiben("07_ausreisser_tagesumsatz.ipynb", ZELLEN)
