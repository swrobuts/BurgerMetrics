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

Dieses Repository und <https://github.com/swrobuts/burger> haben denselben
Inhalt. `burger` ist die ältere Adresse und wird mitgeführt, damit
bestehende Verweise nicht ins Leere laufen; hier liegen zusätzlich die
Quellen der Foliensammlung unter `slides/`.

---

## Klonen

Die CSV-Dateien liegen in Git LFS und sind zusammen rund 311 MB groß. Ohne
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
| `dataset/` | die 13 CSV-Dateien, ein Ladeskript für DuckDB, ein Übungsblatt und `burgermetrics_mini.sql` — dieselbe Struktur in 13 KB zum Mitlesen |
| `db/` | der Aufbau der Datenbank: Schema, Fakten, Semantikschicht, Sicherheit — als nummerierte SQL-Dateien in der Reihenfolge, in der sie laufen |
| `web/` | Online-Shop, Kassensystem und BI-Dashboard |
| `docs/` | die ausführliche Dokumentation zu Modell, Kennzahlen und Betrieb |
| `slides/` | das Bauskript der Foliensammlung, die Mermaid-Quellen und die Bildschirmfotos |

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
Sie die Aufgaben aus `dataset/uebungsblatt.md`. Die erste Probe:

```sql
SELECT count(*) FROM fact_orders;                   -- 754.513
SELECT round(sum(net_total), 2) FROM fact_orders;   -- 14.522.378,70
```

### Der große Weg: PostgreSQL mit Semantikschicht

So läuft das Dashboard. Die Anleitung steht in [`db/README.md`](db/README.md):
Schema anlegen, CSVs laden, Sichten bauen, materialisieren. Sie brauchen eine
eigene PostgreSQL-Instanz und tragen deren Adresse in
`web/js/konfiguration.js` ein.

---

## Die Kette

Das Projekt ist als eine Linie gebaut, und jede Station ist im Repository
nachvollziehbar:

1. **Fachlichkeit** — sechs Sätze über das Geschäft
2. **ER-Modell** — Entitäten, Beziehungen, Kardinalitäten
3. **Normalisierung** — bis zur dritten Normalform, `dataset/wawi_mini.sql`
4. **Anwendungen** — Shop und Kasse auf demselben Kern, `web/`
5. **Auswertungsmodell** — Galaxy-Schema mit zwei Faktentabellen, `db/aufbau/`
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
Seite lädt beim Aufruf 33 Sichten aus der Datenbank und baut daraus alles,
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
