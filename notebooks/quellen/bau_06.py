#!/usr/bin/env python3
"""bau_06.py — schreibt notebooks/06_zufriedenheit_erklaeren.ipynb."""
from gemeinsam import code, kopf, md, schreiben

ZELLEN = kopf("06", "Zufriedenheit erklären", "06_zufriedenheit_erklaeren.ipynb") + [
md("""
## Fragestellung

Was unterscheidet zufriedene von unzufriedenen Bestellungen — Kanal, Wartezeit, Filiale,
Uhrzeit oder Wochentag?

## Daten

Die 142.317 Bestellungen mit `satisfaction_score` (18,9 Prozent aller Bestellungen — eine
selbstselektierte Stichprobe, siehe `dataset/README.md`), dazu Kanal, Bestelldauer, Filiale,
Stunde und Wochentag.

## Vorgehen

Die Zufriedenheit in drei Klassen teilen (niedrig unter 3,5, mittel, hoch ab 4,2), einen
Entscheidungsbaum mit Tiefe 3 zeichnen, einen Random Forest auf einem Prüfdatensatz bewerten
und die Merkmalswichtigkeit lesen.
"""),
code("""
daten = lade_sql(\"\"\"
    SELECT o.satisfaction_score AS zufriedenheit, o.order_channel AS kanal, o.order_duration_min AS dauer_min,
           b.branch_name AS filiale, o.hour AS stunde, d.day_of_week AS wochentag, d.is_weekend AS wochenende
    FROM fact_orders o
    JOIN dim_date d ON d.date = o.date
    JOIN dim_branch b ON b.branch_id = o.branch_id
    WHERE o.satisfaction_score IS NOT NULL\"\"\")

def klasse(wert):
    # Drei Klassen mit festen Grenzen, damit die Klassen über Notebooks hinweg gleich bleiben
    if wert < 3.5:
        return "niedrig"
    if wert < 4.2:
        return "mittel"
    return "hoch"

daten["klasse"] = daten["zufriedenheit"].apply(klasse)
daten["wochenende"] = daten["wochenende"].astype(int)
print(f'Wer immer „mittel" sagt, trifft {zahl(daten["klasse"].value_counts(normalize=True).iloc[0] * 100, 1)} Prozent der Bestellungen.')
daten["klasse"].value_counts().rename("bestellungen").to_frame()
"""),
md("### Merkmale vorbereiten"),
code("""
from sklearn.model_selection import train_test_split

X = pd.get_dummies(daten[["kanal", "dauer_min", "filiale", "stunde", "wochentag", "wochenende"]],
                   columns=["kanal", "filiale"], drop_first=True, dtype=int)
y = daten["klasse"]
X_lern, X_test, y_lern, y_test = train_test_split(X, y, test_size=0.25, random_state=2026, stratify=y)
print(f"{zahl(X_lern.shape[0])} Bestellungen zum Lernen, {zahl(X_test.shape[0])} zum Prüfen, {zahl(X.shape[1])} Merkmale.")
"""),
md("### Ein Entscheidungsbaum mit Tiefe 3"),
code("""
from sklearn.tree import DecisionTreeClassifier, plot_tree
import matplotlib.pyplot as plt

baum = DecisionTreeClassifier(max_depth=3, random_state=2026).fit(X_lern, y_lern)
print(f"Trefferquote des Baums auf dem Prüfdatensatz: {zahl(baum.score(X_test, y_test) * 100, 1)} Prozent.")
erste_trennung = X.columns[baum.tree_.feature[0]]
print(f'Die erste Trennung im Baum verläuft über das Merkmal „{erste_trennung}".')
abb, achse = plt.subplots(figsize=(16, 8))
plot_tree(baum, feature_names=list(X.columns), class_names=list(baum.classes_), filled=False, rounded=True, fontsize=9, ax=achse)
achse.set_title("Die erste Trennung ist die Bestelldauer — nichts anderes zählt annähernd so viel")
plt.show()
"""),
md("### Random Forest"),
code("""
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, classification_report

wald = RandomForestClassifier(n_estimators=200, max_depth=8, n_jobs=-1, random_state=2026).fit(X_lern, y_lern)
vorhersage = wald.predict(X_test)
print(f"Trefferquote des Random Forest: {zahl(wald.score(X_test, y_test) * 100, 1)} Prozent.")
print(classification_report(y_test, vorhersage, digits=3, zero_division=0))
pd.DataFrame(confusion_matrix(y_test, vorhersage, labels=wald.classes_),
             index=[f"ist {k}" for k in wald.classes_], columns=[f"vorhergesagt {k}" for k in wald.classes_])
"""),
code("""
wichtigkeit = pd.Series(wald.feature_importances_, index=X.columns).sort_values(ascending=True).tail(12)
print(f"Die Bestelldauer trägt {zahl(wichtigkeit.iloc[-1] * 100)} Prozent der Merkmalswichtigkeit, "
      f"die Uhrzeit {zahl(wichtigkeit.iloc[-2] * 100)} Prozent.")
abb, achse = plt.subplots(figsize=(9, 5))
achse.barh(wichtigkeit.index, wichtigkeit.values)
achse.set_xlabel("Merkmalswichtigkeit (Anteil an der Verringerung der Unreinheit)")
achse.set_title("Die Bestelldauer ist das wichtigste Merkmal, mit Abstand vor der Uhrzeit")
achse.set_xlim(0)
plt.tight_layout()
plt.show()
"""),
code("""
# Zur Einordnung: mittlere Zufriedenheit je Dauerklasse
daten["dauer_klasse"] = pd.cut(daten["dauer_min"], bins=[0, 5, 10, 15, 20, 60], labels=["bis 5", "6–10", "11–15", "16–20", "über 20"])
daten.groupby("dauer_klasse", observed=True).agg(bestellungen=("zufriedenheit", "size"), zufriedenheit=("zufriedenheit", "mean")).round(2)
"""),
md("""
## Ergebnis

Die Bestelldauer dominiert beide Modelle. Im gezeichneten Baum ändern die zusätzlichen
Verzweigungen nach Kanal, Uhrzeit und Wochentag die vorhergesagte Klasse in keinem Blatt: Bis
12,5 Minuten sagt der Baum durchgehend „mittel" voraus, darüber durchgehend „niedrig" — „hoch"
kommt in keinem Blatt vor. Im Random Forest trägt die Bestelldauer 36 Prozent der
Merkmalswichtigkeit, mit Abstand vor der Uhrzeit (24 Prozent); alle übrigen Merkmale liegen
einzeln darunter.

Die Trefferquote bleibt trotzdem schwach und ist für beide Modelle mit 50,6 Prozent praktisch
gleich — kaum mehr als die 50,4 Prozent, die „mittel" (die größte der drei Klassen) allein
erreicht. Der Klassifikationsbericht des Random Forest zeigt, woran das liegt: „mittel"
erreicht einen Recall von 98 Prozent, weil das Modell diese Klasse ganz überwiegend vorhersagt,
„niedrig" nur 3 Prozent, „hoch" wird kein einziges Mal vorhergesagt. Schwer sind damit nicht die
mittleren, sondern die beiden äußeren Urteile.

## Was offen bleibt

Die Merkmalswichtigkeit sagt, welche Merkmale das Modell nutzt, nicht, was die Zufriedenheit
verursacht. Und die Stichprobe ist selbstselektiert: Wer bewertet, ist nicht zufällig gewählt.
Beides gehört in jede Interpretation.
"""),
]

schreiben("06_zufriedenheit_erklaeren.ipynb", ZELLEN)
