# BurgerMetrics

Eine Fallstudie für Datenbanken und Business Intelligence: erfundene
Fast-Food-Kette, acht Filialen in Würzburg, neun Jahre Geschäft,
754.513 Bestellungen. Erfunden heißt nicht beliebig — der Bestand ist so
gebaut, dass jede Kennzahl nachrechenbar ist und die typischen
Auswertungsfallen tatsächlich zuschnappen.

Das Repository enthält alles, was zwischen einem Satz über das Geschäft und
einer Zahl im Dashboard liegt: die Rohdaten, das operative Modell, das
Auswertungsmodell, die Semantikschicht und das Dashboard selbst.

**Live:** <https://swrobuts.github.io/BurgerMetrics/>

---

## Klonen

Die CSV-Dateien liegen in Git LFS und sind zusammen rund 315 MB groß. Ohne
LFS bekommen Sie nur Textzeiger statt Daten.

```bash
git lfs install
git clone https://github.com/swrobuts/BurgerMetrics.git
cd BurgerMetrics
```

Prüfen, ob es geklappt hat — die Datei muss groß sein, nicht 133 Byte:

```bash
ls -lh dataset/fact_orders.csv
```

Steht dort `version https://git-lfs.github.com/spec/v1`, fehlte LFS beim
Klonen. Dann `git lfs install` nachholen und `git lfs pull` ausführen.

---

## Was wo liegt

| Verzeichnis | Inhalt |
|---|---|
| `dataset/` | die 15 CSV-Dateien, ein Ladeskript für DuckDB, ein Übungsblatt und `burgermetrics_mini.sql` — dieselbe Struktur in 13 KB zum Mitlesen |
| `db/` | der Aufbau der Datenbank: Schema, Fakten, Semantikschicht, Sicherheit — als nummerierte SQL-Dateien in der Reihenfolge, in der sie laufen |
| `notebooks/` | neun ausgeführte Notebooks, vom Zugang mit dem Demo-Konto bis zur Sentiment-Analyse; `notebooks/README.md` |
| `dash/` | Dash-App mit vier Karten aus der Semantikschicht; `dash/README.md` |
| `web/` | Online-Shop, Kassensystem, BI-Dashboard und unter `web/lab/` die Lernumgebung BM-Lab |
| `web/lab/` | Lernumgebung BM-Lab: acht Labs mit 41 Übungen im Browser, PostgreSQL per PGlite; `web/lab/README.md` |
| `powerbi/` | das Power-BI-Projekt (PBIP) zu Lab 04: Modell, Measures, Bericht und Dashboard als Textdateien, ohne Daten; `powerbi/README.md` |
| `tableau/` | die Tableau-Arbeitsmappe zu Lab 05: Datenquelle, Parameter, 28 Calculated Fields, zehn Blätter und das Kennzahlen-Dashboard als `.twb`, ohne Daten; `tableau/README.md` |
| `docs/` | die ausführliche Dokumentation zu Modell, Kennzahlen und Betrieb |
| `mcp/` | ein MCP-Server über beide Schemata für den Betreiber — Claude Desktop oder Claude Code als Fenster auf die Datenbank |

---

## Zwei Wege, damit zu arbeiten

### Der kleine Weg: DuckDB auf den CSV-Dateien

Kein Server, keine Zugangsdaten, zwei Minuten. Gut, um das Modell zu
verstehen und SQL zu üben.

```bash
pip install duckdb
python3 dataset/load_duckdb.py --lokal
```

Das Skript prüft die geladenen Zeilenzahlen gegen die Sollwerte aus
`dataset/README.md` und legt `dataset/burger_metrics.duckdb` an. Darin rechnen
Sie die Aufgaben aus `dataset/uebungsblatt.md`.

Beim erneuten Laden werden nur die ausgewählten Datensatztabellen ersetzt;
eigene Übungstabellen bleiben erhalten. Der Import läuft in einer Transaktion:
Fehlt eine Zeile oder schlägt das Einlesen fehl, wird der gesamte Import
zurückgerollt und das Skript endet mit einem Fehlerstatus.

Die erste Probe:

```sql
SELECT count(*) FROM fact_orders;                   -- 754.513
SELECT round(sum(net_total), 2) FROM fact_orders;   -- 14.522.378,70
```

### Der große Weg: PostgreSQL mit Semantikschicht

So läuft das Dashboard. Die Anleitung steht in [`db/README.md`](db/README.md):
Schema anlegen, CSVs laden, Sichten bauen, materialisieren. Sie brauchen eine
eigene PostgreSQL-Instanz und tragen deren Adresse in
`web/js/konfiguration.js` ein.

### Notebooks und Dash

Neun ausgeführte Notebooks (`notebooks/00` bis `08`) behandeln Zugang und
Daten, das analytische Datenmodell, RFM und Kundensegmente, Warenkorb,
Nachfrageprognose, Wetter und Ereignisse, Zufriedenheit, Ausreißer und
Sentiment. Jedes läuft mit dem Demo-Konto `studi_daba` lokal oder in Google
Colab (`notebooks/README.md`). Große Tabellen liest jedes Notebook aus der
Datenbank; `lade_csv()` dient nur den Dimensionen, um das Bandbreitenbudget
von Git LFS zu schonen. Die Dash-App `dash/app.py` zeigt vier Karten aus der
Semantikschicht — dieselben Zahlen wie das Dashboard (`dash/README.md`).

### Lernumgebung

Die Lernumgebung **BM-Lab** steht unter
<https://swrobuts.github.io/BurgerMetrics/lab/>. Acht Labs mit 41 Übungen
führen vom Zugang zur Datenbank über die Daten und das analytische
Datenmodell zu Power BI, Tableau und Python bis zu Data Mining und externen
Daten. Die SQL-Übungen laufen gegen eine echte PostgreSQL-Datenbank im
Browser (PGlite) mit einem Miniaturbestand in beiden Schemata `wawi` und
`burgermetrics`, dazu ein Shelf-Simulator nach dem Vorbild von Power BI
(Field Wells) und Tableau (Shelves). Aufbau und Abnahmelauf stehen in [`web/lab/README.md`](web/lab/README.md).

---

## Die Kette

Das Projekt ist als eine Linie gebaut, und jede Station ist im Repository
nachvollziehbar:

1. **Fachlichkeit** — sechs Sätze über das Geschäft
2. **ER-Modell** — Entitäten, Beziehungen, Kardinalitäten
3. **Normalisierung** — bis zur dritten Normalform, `dataset/wawi_mini.sql`; im Betrieb das Schema `wawi`, `db/aufbau/0016`
4. **Anwendungen** — Shop und Kasse lesen und schreiben in denselben operativen Kern, `web/`; seit `0021` nimmt der Shop auch Rezensionen entgegen (`wawi.rezension`)
5. **Auswertungsmodell** — Galaxy-Schema mit drei Faktentabellen (`fact_orders`, `fact_order_items`, `fact_reviews`), `db/aufbau/`; der ETL-Schritt von `wawi` dorthin ist `db/aufbau/0019`, erweitert um Rezensionen in `0021`
6. **Kennzahlen** — die Semantikschicht als SQL-Sichten
7. **Dashboard** — `web/dashboard.html`

Der Nachweis, dass Schritt 3 und Schritt 5 zusammenpassen, liegt bei:
`dataset/wawi_zu_analytisch.sql` erzeugt aus dem operativen Ausschnitt
dieselben Tabellen wie `dataset/burgermetrics_mini.sql` — acht von acht
zeilengleich.

---

## Eine Eigenschaft, die zum Lernstoff gehört

Im Quelltext von `web/dashboard.html` steht **keine einzige Geschäftszahl**.
Weder in den Kacheln noch in den Tabellen noch in den Deutungstexten. Die
Seite lädt beim Aufruf 34 Sichten aus der Datenbank und baut daraus alles,
was sie zeigt.

Das war nicht immer so. In der ersten Fassung standen die Zahlen fest im
HTML — und beim Umbau fiel auf, dass über sechzig Aussagen darin sich nicht
mehr nachrechnen ließen. Der Befund steht in [`db/README.md`](db/README.md)
und ist der Grund, warum es diese Trennung gibt: Eine Zahl im HTML altert,
ohne dass es jemand merkt.

---

## Herkunft der Daten

Vollständig erzeugt, keine echten Personen, keine echten Umsätze. Wetterdaten
und Kalender sind plausibel konstruiert, nicht gemessen. Der Datensatz darf
für Lehre und Übung frei verwendet werden.
