#!/usr/bin/env python3
"""bau_04.py — schreibt notebooks/04_nachfrageprognose.ipynb."""
from gemeinsam import code, kopf, md, schreiben

ZELLEN = kopf("04", "Nachfrageprognose", "04_nachfrageprognose.ipynb") + [
md("""
## Fragestellung

Wie gut lässt sich der Tagesumsatz einer Filiale aus Kalender und Wetter vorhersagen — und
wie prüft man das ehrlich?

## Daten

Tagesumsatz je Filiale aus `fact_orders` (aggregiert in SQL), Merkmale aus `dim_date`
(Wochentag, Monat, Wochenende, Feiertag, Ereignis) und `dim_weather` (Temperatur,
Niederschlag). Beispielfiliale ist BM Europastern (`branch_id = 1`), die älteste mit der
längsten Reihe.

## Vorgehen

Zerlegung der Reihe in Trend, Wochenmuster und Rest (STL), dann zwei Modelle — lineare
Regression und Gradient Boosting — trainiert bis März 2025 und geprüft auf den letzten
zwölf Monaten (Backtesting). Bewertet wird mit MAE und MAPE. Zum Schluss der Basiseffekt bei
Rumpfjahren.
"""),
code("""
FILIALE = 1
tage = lade_sql(f\"\"\"
    SELECT o.date AS tag, sum(o.net_total) AS umsatz, count(*) AS bestellungen,
           d.year AS jahr, d.month AS monat, d.day_of_week AS wochentag, d.is_weekend AS wochenende,
           d.is_holiday AS feiertag, d.special_event AS ereignis,
           w.temperature_celsius AS temperatur, w.precipitation_mm AS niederschlag
    FROM fact_orders o
    JOIN dim_date d ON d.date = o.date
    LEFT JOIN dim_weather w ON w.date = o.date
    WHERE o.branch_id = {FILIALE}
    GROUP BY o.date, d.year, d.month, d.day_of_week, d.is_weekend, d.is_holiday, d.special_event,
             w.temperature_celsius, w.precipitation_mm
    ORDER BY o.date\"\"\")
tage["tag"] = pd.to_datetime(tage["tag"])
tage = tage.set_index("tag").asfreq("D")
print(f"{zahl(len(tage))} Tage von {tage.index.min().date()} bis {tage.index.max().date()}, davon {zahl(int(tage['umsatz'].isna().sum()))} ohne Bestellung.")
tage["umsatz"] = tage["umsatz"].fillna(0)
tage["bestellungen"] = tage["bestellungen"].fillna(0)
tage[["umsatz", "bestellungen", "temperatur", "niederschlag"]].describe().round(1)
"""),
md("### Zerlegung: Trend, Wochenmuster, Rest"),
code("""
from statsmodels.tsa.seasonal import STL
import matplotlib.pyplot as plt

zerlegung = STL(tage["umsatz"], period=7, robust=True).fit()
abb, achsen = plt.subplots(3, 1, figsize=(9, 7))
achsen[0].plot(zerlegung.trend)
achsen[0].set_ylabel("Trend in €")
achsen[0].set_title("Der Trend trägt das Wachstum, das Wochenmuster wiederholt sich, der Rest ist Rauschen")
achsen[1].plot(zerlegung.seasonal.iloc[-56:])
achsen[1].set_ylabel("Wochenmuster in €")
achsen[1].set_xlim(zerlegung.seasonal.index[-56], zerlegung.seasonal.index[-1])
achsen[1].set_xlabel("die letzten acht Wochen")
achsen[2].plot(zerlegung.resid)
achsen[2].set_ylabel("Rest in €")
achsen[2].set_xlabel("Tag")
plt.tight_layout()
plt.show()
"""),
code("""
# Wie viel Varianz tragen die Komponenten? Anteile an der Varianz des Umsatzes.
varianz = tage["umsatz"].var()
pd.DataFrame({"komponente": ["Trend", "Wochenmuster", "Rest"],
              "varianzanteil_pct": [zerlegung.trend.var() / varianz * 100, zerlegung.seasonal.var() / varianz * 100,
                                    zerlegung.resid.var() / varianz * 100]}).round(1)
"""),
md("""
### Merkmale und Backtesting

Wir trainieren auf allen Tagen bis zum 31. März 2025 und prüfen auf den zwölf Monaten danach —
Daten, die das Modell beim Lernen nie gesehen hat. Merkmale: Wochentag und Monat als
Kategorien, Feiertag, Ereignis, Temperatur, Niederschlag und eine laufende
Tagesnummer für den Trend.
"""),
code("""
import numpy as np

merkmale = pd.DataFrame({
    "tag_nr": np.arange(len(tage)),
    "feiertag": tage["feiertag"].fillna(False).astype(int),
    "ereignis": tage["ereignis"].notna().astype(int),
    "temperatur": tage["temperatur"].ffill().bfill(),
    "niederschlag": tage["niederschlag"].fillna(0),
}, index=tage.index)
merkmale = merkmale.join(pd.get_dummies(tage.index.dayofweek, prefix="wt", drop_first=True, dtype=int).set_index(tage.index))
merkmale = merkmale.join(pd.get_dummies(tage.index.month, prefix="monat", drop_first=True, dtype=int).set_index(tage.index))

TRENNUNG = "2025-04-01"
lern = merkmale.index < TRENNUNG
X_lern, X_test = merkmale[lern], merkmale[~lern]
y_lern, y_test = tage["umsatz"][lern], tage["umsatz"][~lern]
print(f"Lernen: {zahl(int(lern.sum()))} Tage, Prüfen: {zahl(int((~lern).sum()))} Tage, {zahl(merkmale.shape[1])} Merkmale.")
"""),
code("""
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

def bewerte(name, modell):
    # Trainiert das Modell auf dem Lernzeitraum und misst den Fehler auf dem Prüfzeitraum
    modell.fit(X_lern, y_lern)
    vorhersage = modell.predict(X_test)
    return {"modell": name,
            "MAE in €": mean_absolute_error(y_test, vorhersage),
            "MAPE in %": mean_absolute_percentage_error(y_test, vorhersage) * 100,
            "vorhersage": vorhersage,
            "objekt": modell}

ergebnisse = [bewerte("Lineare Regression", LinearRegression()),
              bewerte("Gradient Boosting", GradientBoostingRegressor(n_estimators=300, max_depth=3,
                                                                       learning_rate=0.05, random_state=2026))]
mittelwert = np.full(len(y_test), y_lern.iloc[-365:].mean())
ergebnisse.append({"modell": "Mittelwert der letzten 365 Lerntage", "MAE in €": mean_absolute_error(y_test, mittelwert),
                   "MAPE in %": mean_absolute_percentage_error(y_test, mittelwert) * 100, "vorhersage": mittelwert})
pd.DataFrame([{k: v for k, v in e.items() if k not in ("vorhersage", "objekt")} for e in ergebnisse]).round(1)
"""),
code("""
# Welche Merkmale nutzt das Gradient Boosting? Die zehn wichtigsten.
gb = ergebnisse[1]["objekt"]
wichtigkeit = pd.Series(gb.feature_importances_, index=merkmale.columns).sort_values(ascending=False)
wichtigkeit.head(10).round(3).rename("wichtigkeit").to_frame()
"""),
code("""
abb, achse = plt.subplots(figsize=(9, 4))
achse.plot(y_test.index, y_test, label="Ist")
for e in ergebnisse[:2]:
    achse.plot(y_test.index, e["vorhersage"], label=e["modell"], alpha=0.8)
achse.set_xlabel("Tag")
achse.set_ylabel("Tagesumsatz in €")
achse.set_title("Backtesting April 2025 bis März 2026: Beide Modelle treffen das Wochenmuster, Ausreißer nicht")
achse.set_ylim(0)
achse.legend()
plt.show()
"""),
code("""
# Fehler des Gradient Boosting je Tagestyp im Prüfzeitraum
fehler = pd.DataFrame({"abs_fehler": (y_test - ergebnisse[1]["vorhersage"]).abs()}, index=y_test.index)
fehler["tagestyp"] = "gewöhnlich"
# Ein Tag, der Feiertag und Ereignis zugleich ist, zählt als Ereignis (letzte Zuweisung gewinnt)
fehler.loc[merkmale.loc[y_test.index, "feiertag"] == 1, "tagestyp"] = "Feiertag"
fehler.loc[merkmale.loc[y_test.index, "ereignis"] == 1, "tagestyp"] = "Ereignis"
fehler.groupby("tagestyp").agg(tage=("abs_fehler", "size"), mae=("abs_fehler", "mean")).round(1)
"""),
md("""
### Basiseffekt bei Rumpfjahren

Wer Jahresumsätze vergleicht, sieht 2017 und 2026 als Einbruch. Beide Jahre sind unvollständig:
2017 beginnt am 15. März, 2026 endet am 31. März. Der Umsatz je Tag zeigt das echte Bild.
"""),
code("""
jahre = tage.groupby(tage.index.year).agg(tage=("umsatz", "size"), umsatz=("umsatz", "sum"))
jahre.index.name = "jahr"
jahre["umsatz_je_tag"] = jahre["umsatz"] / jahre["tage"]
jahre["veraenderung_je_tag_pct"] = jahre["umsatz_je_tag"].pct_change() * 100
jahre.round(1)
"""),
code("""
# Gleicher Zeitraum in beiden Jahren: Januar bis März 2025 gegen Januar bis März 2026
q1 = tage[(tage.index.month <= 3) & (tage.index.year >= 2025)]
q1.groupby(q1.index.year).agg(tage=("umsatz", "size"), umsatz_je_tag=("umsatz", "mean")).round(1)
"""),
md("""
Der Rückgang je Tag in 2026 gegenüber dem Jahresmittel 2025 ist ein Jahreszeiteffekt: Das
erste Quartal ist im Jahresverlauf das umsatzschwächste. Im Vergleich Januar–März zu
Januar–März liegt 2026 mit 1.343,4 € je Tag sogar leicht über 2025 (1.336,7 €, +0,5 Prozent).
"""),
md("""
## Ergebnis

Gradient Boosting und lineare Regression liegen nah beieinander: Gradient Boosting hat den
niedrigeren mittleren Fehler in Euro (169,0 € gegenüber 172,4 €), die lineare Regression den
niedrigeren prozentualen Fehler (11,9 gegenüber 12,2 Prozent); beide schlagen den naiven
Mittelwert deutlich (286,6 €, 19,5 Prozent). An Feiertagen ist der Fehler des Gradient Boosting
mit 197,3 € je Tag am höchsten; an Ereignistagen liegt er mit 147,2 € am niedrigsten, sogar unter
dem Fehler an gewöhnlichen Tagen (172,1 €). Trend und Wochenmuster tragen zusammen rund 90
Prozent der Varianz des Umsatzes (66,8 plus 23,3 Prozent); in der Merkmalswichtigkeit des
Gradient Boosting liegt Temperatur bei 4,7 Prozent, Niederschlag erscheint nicht unter den zehn
wichtigsten Merkmalen. Notebook 05 untersucht den Wettereffekt genauer.

Der scheinbare Rückgang 2026 gegenüber dem Jahresmittel 2025 ist ein Basiseffekt der
Rumpfjahre: Verglichen wird ein volles Jahr 2025 mit dem ersten, umsatzschwächsten Quartal 2026;
im Vergleich je Tag über den gleichen Zeitraum (Januar–März) liegt 2026 leicht über 2025.

## Was offen bleibt

Ein echtes Prognosemodell würde die Vergangenheit der Reihe selbst als Merkmal nutzen (Lags,
gleitende Mittel) und die Prüfung über mehrere Zeitfenster wiederholen (rollierendes
Backtesting). Beides ist hier bewusst weggelassen, damit der Unterschied zwischen erklärenden
Merkmalen und Autokorrelation sichtbar bleibt.
"""),
]

schreiben("04_nachfrageprognose.ipynb", ZELLEN)
