# Notebooks zur Fallstudie BurgerMetrics

Neun Notebooks, jedes für sich lauffähig — in Google Colab (Link am Kopf jedes Notebooks)
oder lokal. Alle lesen die Datenbank mit dem Demo-Konto `studi_daba` (nur lesend) und
brauchen kein Geheimnis.

| Notebook | Inhalt |
|---|---|
| `00_zugang_und_daten` | Verbindung, Schemata und Sichten, CSV per Git LFS, DuckDB, Export für Power BI und Tableau, Grenzen der Rolle, Dash inline |
| `01_analytisches_datenmodell` | Frage → Grain → Dimensionen → Fakten → Sicht; Fan Trap; Abgleich mit `burgermetrics`; Rezensionen als neue Faktentabelle |
| `02_rfm_und_kundensegmente` | RFM mit Quintilen und Zweitschlüssel, Vergleich mit `v_rfm_kunde`, K-Means |
| `03_warenkorbanalyse` | Apriori mit `mlxtend`, Support, Konfidenz, Lift, Richtung der Regel |
| `04_nachfrageprognose` | STL, Merkmale aus Kalender und Wetter, Regression und Gradient Boosting, Backtesting |
| `05_wetter_und_ereignisse` | Regression auf Wetter und Ereignisse; externe Quellen: Open-Meteo, Feiertage, Schulferien, Kickers, VPI |
| `06_zufriedenheit_erklaeren` | Entscheidungsbaum und Random Forest auf `satisfaction_score` |
| `07_ausreisser_tagesumsatz` | z-Score, IQR, Isolation Forest; Treffer erklären |
| `08_sentiment_rezensionen` | Wortliste, TF-IDF + logistische Regression, deutsches BERT-Modell, Sentiment gegen Kanal und Produkt |

## Lokal ausführen

```bash
python3 -m pip install -r notebooks/requirements.txt
jupyter lab notebooks/
```

## Neu bauen und abnehmen

Die Notebooks entstehen aus Bauskripten unter `quellen/` (Zellen als Python-Strings,
geschrieben mit `nbformat`). Wer ein Notebook ändert, ändert das Bauskript, baut neu und
führt aus:

```bash
PYTHONPATH=notebooks/quellen python3 notebooks/quellen/bau_03.py          # ein Notebook neu schreiben
PYTHONPATH=notebooks/quellen python3 notebooks/quellen/alle_bauen.py      # alle
bash notebooks/pruefe_notebooks.sh           # alle ausführen und prüfen (rund 20 Minuten)
```

`pruefe_notebooks.sh` ist die Abnahme: Jedes Notebook läuft mit `jupyter nbconvert --execute`
gegen die Datenbank, die Ausgaben werden gespeichert und eingecheckt, `quellen/pruefe_ausgaben.py`
meldet Fehlerausgaben und fehlende Abschnitte.

## Externe Daten

`daten_extern/` enthält die einmal geholten Antworten der externen Quellen (Open-Meteo,
OpenHolidays, OpenLigaDB) und den kuratierten Verbraucherpreisindex, ohne Git LFS versioniert
(eigene `.gitattributes`, sonst lägen in Colab nur LFS-Zeigerdateien vor). Notebook 05 liest
zuerst diese Dateien, dann dieselben Dateien aus GitHub (`main`) und ruft die Anbieter nur, wenn
auch das scheitert oder `AKTUALISIEREN = True` gesetzt ist. Quellen und Stand stehen im Notebook.
