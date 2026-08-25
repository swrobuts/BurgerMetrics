# BurgerMetrics GmbH — BI-Musterdatensatz

## Unternehmensszenario

**BurgerMetrics GmbH** ist eine fiktive Burger-Kette mit 8 Filialen in Würzburg. Die Kette positioniert sich als modernes Quick-Service-Restaurant mit digitaler Bestellinfrastruktur (App, Kiosk, Drive-Through) und einem Loyalitätsprogramm. Die Daten simulieren den Export aus einem integrierten Warenwirtschaftssystem (ERP), der für analytische Zwecke aufzubereiten ist.

**Zeitraum:** 15. März 2017 – 31. März 2026
**Umfang:** 754.513 Bestellungen · 2.950.082 Bestellpositionen · 25.000 Kunden · 14,52 Mio. € Nettoumsatz
**Durchschnittlicher Bestellwert:** 19,25 €

> Alle Zahlen in diesem Dokument wurden am 25. August 2026 aus den CSV-Dateien nachgerechnet. Siehe [Prüfstand](#prüfstand) am Ende.

---

## Datenmodell

### Galaxy-Schema (Fact Constellation)

Das Modell hat **zwei Faktentabellen auf unterschiedlicher Granularität**, die sich Dimensionen teilen. Dieser Aufbau heißt Galaxy-Schema oder Fact Constellation — nicht Star Schema. Ein Star Schema hat definitionsgemäß genau eine Faktentabelle.

```
   dim_date ─────┐                    ┌───── dim_payment_method
   dim_weather ──┤                    ├───── dim_promotion
                 │                    │
   dim_branch ───┼──▶ fact_orders ◀───┼───── dim_customer
                        │  (Bestellung)
                        │  754.513 Zeilen
                        │
                        │ order_id
                        ▼
                   fact_order_items ◀──────── dim_product
                      (Position)
                      2.950.082 Zeilen

   dim_time_slot   (über hour an fact_orders anschließbar, aber nicht verknüpft)
   dim_employee    (hängt an dim_branch, hat keinen Bezug zu den Fakten)
   dim_supplier    (Orphan Dimension — an nichts angebunden)
```

Die beiden Fakten unterscheiden sich in der **Granularität** (grain): `fact_orders` hat eine Zeile je Bestellung, `fact_order_items` eine Zeile je Bestellposition. Diese Unterscheidung ist die wichtigste Modellierungsentscheidung im Datensatz — wer die beiden Ebenen in einem Join vermischt, vervielfacht Bestellungen und bläht jede Umsatzsumme auf (Fan Trap).

### Dateien

| Datei | Typ | Zeilen | Beschreibung |
|-------|-----|--------|-------------|
| `dim_branch.csv` | Dimension | 8 | Filialen mit Geo-Koordinaten, Größe, Ausstattung, Miete |
| `dim_product.csv` | Dimension | 57 | Produkte mit Kategorien, Preisen, Nährwerten, Allergenen |
| `dim_customer.csv` | Dimension | 25.000 | Kundenprofile mit App-Status, Loyalty-Tier, Heimatbezirk |
| `dim_payment_method.csv` | Dimension | 4 | Zahlungsarten (Cash, EC Card, Credit Card, Mobile Payment) |
| `dim_promotion.csv` | Dimension | 13 | Aktionen und Rabatte, inkl. `promo_id = 0` für „No Promotion" |
| `dim_date.csv` | Dimension | 3.377 | Kalenderdimension mit Feiertagen, Events, Saison |
| `dim_time_slot.csv` | Dimension | 18 | Tageszeit-Zuordnung (Breakfast, Lunch, Dinner, …) |
| `dim_employee.csv` | Dimension | 188 | Mitarbeiter mit Rollen und Stundenlöhnen |
| `dim_supplier.csv` | Dimension | 8 | Lieferanten (**Orphan Dimension**, siehe unten) |
| `dim_weather.csv` | Dimension | 3.377 | Tägliche Wetterdaten für Würzburg |
| `fact_orders.csv` | Fakt | 754.513 | Bestellungen (Kopf) |
| `fact_order_items.csv` | Fakt | 2.950.082 | Bestellpositionen (Detail) |
| `obt_orders.csv` | OBT | 754.513 | One Big Table, denormalisiert auf Bestellebene (41 Spalten) |

### Schlüsselbeziehungen

```
fact_orders.branch_id      → dim_branch.branch_id
fact_orders.customer_id    → dim_customer.customer_id
fact_orders.payment_id     → dim_payment_method.payment_id
fact_orders.promo_id       → dim_promotion.promo_id      (0 = keine Promotion)
fact_orders.date           → dim_date.date
fact_order_items.order_id  → fact_orders.order_id
fact_order_items.product_id→ dim_product.product_id
dim_employee.branch_id     → dim_branch.branch_id
dim_weather.date           → dim_date.date
```

### Bewusst eingebaute Modellierungsschwächen

Drei Dimensionen sind **absichtlich** nicht sauber angebunden. Sie sind Diskussionsmaterial, keine Fehler:

- **`dim_supplier` ist eine Orphan Dimension.** Es gibt keinen `supplier_id`-Fremdschlüssel — weder in den Faktentabellen noch in `dim_product`. Die Tabelle ist im Schema vorhanden, aber an nichts angebunden. Frage an die Studierenden: Wie käme man an eine Lieferantenanalyse, und was müsste im Quellsystem dafür passieren?
- **`dim_employee` hängt nur an `dim_branch`.** Es gibt keine `employee_id` in `fact_orders`. Deshalb lässt sich „Welcher Mitarbeiter hat den meisten Umsatz erwirtschaftet?" mit diesem Schema **nicht** beantworten — nur „Welche Filiale hat wie viele Mitarbeiter?". Ein klassisches Beispiel dafür, dass die Frage am Grain scheitert, nicht am SQL.
- **`dim_time_slot` ist anschließbar, aber nicht angeschlossen.** `fact_orders.hour` und `dim_time_slot.hour` passen zusammen, ein Join ist also möglich. Genutzt wird die Dimension im Datensatz aber nirgends — die OBT enthält `hour`, nicht `time_slot`.

---

## Die 8 Filialen

Achtung beim Nachschlagen: Die `branch_id` folgt der **Eröffnungsreihenfolge**, nicht dem Alphabet und nicht der Umsatzhöhe.

| ID | Filiale | Typ | Eröffnet | Miete/Mon. | Drive-Thr. | Bestellungen | Umsatz |
|----|---------|-----|----------|-----------:|:----------:|-------------:|-------:|
| 1 | BM Europastern | Highway | 2017-03-15 | 6.800 € | ja | 182.120 | 3,39 Mio. € |
| 2 | BM Hauptbahnhof | City Center | 2018-06-01 | 8.500 € | nein | 123.929 | 2,21 Mio. € |
| 3 | BM Sanderring | University | 2019-02-01 | 5.200 € | nein | 89.366 | 1,68 Mio. € |
| 4 | BM Heuchelhof | Residential | 2019-09-01 | 4.800 € | ja | 100.783 | 2,03 Mio. € |
| 5 | BM Lengfeld | Commercial | 2020-08-01 | 5.500 € | ja | 72.218 | 1,36 Mio. € |
| 6 | BM Mainfrankenpark | Shopping | 2021-04-01 | 7.200 € | ja | 102.631 | 2,16 Mio. € |
| 7 | BM Grombühl | Hospital | 2022-01-15 | 4.500 € | nein | 47.734 | 0,94 Mio. € |
| 8 | BM Zellerau | Mixed | 2023-03-01 | 4.000 € | nein | 35.732 | 0,75 Mio. € |

Die absoluten Umsätze sind stark von der Betriebsdauer geprägt — Europastern läuft neun Jahre, Zellerau drei. Für einen fairen Standortvergleich muss auf Umsatz **pro Betriebsjahr** oder **pro Sitzplatz** normiert werden. Das ist eine der lohnendsten Übungsaufgaben am Datensatz.

---

## Eingeimpfte Muster

Diese Muster sind in den Daten nachweisbar. Die Zahlen sind nachgerechnet — wer beim Analysieren deutlich andere Werte erhält, hat vermutlich einen Join auf der falschen Granularität.

### Zeitliche Muster

| # | Muster | Befund |
|---|--------|--------|
| 1 | **Wochentage** | Samstag liegt mit 278 Bestellungen/Tag an erster, Dienstag mit 195 an letzter Stelle (+43 %). Reihenfolge: Sa > Fr > So > Do > Mi > Mo > Di. |
| 2 | **Tageszeit** | Klarer Mittagspeak: 12 Uhr (121.331) und 13 Uhr (104.250) liegen vorn, gefolgt von einem Abendpeak um 18–19 Uhr. Randzeiten 23 Uhr und 6 Uhr liegen bei rund 6.000–12.000. |
| 3 | **Saisonalität** | Eis (Ice Cream + Sundae) steigt im Sommer auf das **2,78-fache** des Winterwerts (58,5 vs. 21,0 Stück/Tag), Kaltgetränke auf das **1,50-fache** (431,6 vs. 287,1). Gegenläufig dazu die Heißgetränke: **114,1 im Winter gegenüber 74,5 im Sommer** (Faktor 1,53) und nur 65,5 im Frühling. |
| 4 | **Events** | Kiliani **+34 %** gegenüber eventfreien Tagen (297 vs. 221 Bestellungen/Tag), Weinfest +27 %, Mainfranken Messe +24 %, Mozartfest +24 %. Der Weihnachtsmarkt fällt mit **+5 %** deutlich schwächer aus als die Sommerevents. |
| 5 | **Sommerloch am Uni-Standort** | BM Sanderring geht im August auf 18,4 Bestellungen/Tag zurück — **−31 %** gegenüber dem eigenen Jahresmittel. Juli ist mit 20,5 ebenfalls schwach, Juni mit 34,7 der stärkste Monat. |

### Standort- und Kanalmuster

| # | Muster | Befund |
|---|--------|--------|
| 6 | **Kanalmix je Standort** | Der Standorteffekt mit der größten Spannweite, und er ist baulich bedingt: Europastern wickelt **53,6 %** über Drive-Through ab, die vier Filialen ohne Drive-Through zwangsläufig 0 %. Dort verschiebt sich das Volumen auf Counter (68–73 %) und Kiosk (21–23 %). |
| 7 | **Drive-Through und Warenkorb** | Filialen mit Drive-Through haben einen höheren Bestellwert (19,53 € vs. 18,82 €) und mehr Artikel je Bestellung (4,64 vs. 4,34). Der Effekt ist real, aber klein — für eine belastbare Aussage muss gegen den Standorttyp kontrolliert werden. |
| 8 | **Miete vs. Umsatz** | Positiv, aber weit von einem Automatismus entfernt (Korrelation **0,68**). Der Hauptbahnhof zahlt mit 8.500 € die höchste Miete und erreicht nur den zweithöchsten Umsatz sowie den **niedrigsten** Bestellwert aller Filialen (17,80 €). |
| 9 | **Bestellwert je Standort** | Spannweite 17,80 € (Hauptbahnhof) bis 21,05 € (Zellerau). Die jüngeren, kleineren Standorte erzielen die höheren Bestellwerte. |
| 10 | **Wochenendanteil** | Reicht von 23 % (Sanderring, Uni) bis 42 % (Mainfrankenpark, Shopping) — der Standorttyp wirkt hier deutlich. |

### Kunden- und Zahlungsmuster

| # | Muster | Befund |
|---|--------|--------|
| 11 | **Bargeld-Rückgang** | Der Trend mit der größten Veränderung im Datensatz: Cash fällt von **48,6 % (2018) auf 20,4 % (2025)**. |
| 12 | **Mobile Payment** | Wächst von **0,9 % (2018) auf 12,2 % (2025)**. EC Card hat mit 40,3 % (2025) den größten Anteil. |
| 13 | **Loyalty-Tiers** | Gold-Kunden bestellen **häufiger** (33,8 Bestellungen/Kopf vs. 30,4 ohne Programm) und geben insgesamt mehr aus (627 € vs. 590 € pro Kopf) — haben aber den **niedrigsten Bestellwert** (18,56 € vs. 19,40 €). Ein lehrreicher Fall: Frequenz und Bonhöhe zeigen in entgegengesetzte Richtungen. |
| 14 | **Promotions** | Nur **8,2 %** aller Bestellungen sind einer Aktion zugeordnet (62.023 von 754.513). `promo_id = 0` bedeutet „keine Promotion" und macht die übrigen 91,8 % aus — ein Klassiker für falsch gezählte Kennzahlen. |

### Warenkorbmuster (Association Rules)

| # | Regel | Support | Konfidenz | Lift |
|---|-------|--------:|----------:|-----:|
| 15 | **Burger + Fries + Cola** | 29,2 % | — | **2,30** |
| 16 | **Nuggets → BBQ-Sauce** | 2,7 % | 40,9 % | **8,93** |
| 17 | **Breakfast → Coffee** | 4,1 % | 60,8 % | **3,59** |
| 18 | **Burger → Bier** | 7,6 % | 12,7 % | **1,03** |

Einzelhäufigkeiten zum Nachrechnen: Burger 59,6 % · Fries 51,1 % · Cola 41,6 % · Nuggets 6,7 % · BBQ-Sauce 4,6 % · Breakfast 6,7 % · Coffee 16,9 % · Beer 12,3 %.

Regel 18 eignet sich besonders als Lehrbeispiel, weil sie den Unterschied zwischen Konfidenz und Lift sichtbar macht: Bier taucht in 12,7 % der Burger-Bestellungen auf — das klingt nach einem Muster, entspricht aber fast exakt dem Bier-Anteil über alle Bestellungen (12,3 %). Der **Lift von 1,03** zeigt, dass beide Produkte praktisch unabhängig sind. Wer nur auf Support und Konfidenz schaut, findet hier eine Regel, die keine ist. Umgekehrt hat Regel 16 den kleinsten Support, aber mit Lift 8,93 den mit Abstand stärksten Zusammenhang.

> **Fallstrick bei der Produktauswahl:** Ein `LIKE '%Cola%'` trifft auch *Milkshake **Chocolate***, *Hot **Chocolate*** und *Cookie **Chocolate***; ein `LIKE '%BBQ%'` trifft neben der *BBQ Sauce* auch den Burger *BBQ Smokehouse*. Die Werte oben beruhen auf expliziten Produktlisten. Ein unsauberer Filter verschiebt die Konfidenz hier um mehrere Prozentpunkte.

### Anomalien und Fallstricke

| # | Muster | Befund |
|---|--------|--------|
| 19 | **Bewertungs-Bias** | Nur **18,9 %** der Bestellungen haben einen `satisfaction_score`. Wer Zufriedenheit auswertet, arbeitet mit einer selbstselektierten Stichprobe. |
| 20 | **Wartezeit vs. Zufriedenheit** | Der Zusammenhang ist **schwach** (Korrelation −0,061). Bis 15 Minuten fällt die Zufriedenheit von 3,83 auf 3,69, im Bereich 15–20 Minuten auf 3,47 — aber dieser Bereich umfasst nur 282 Bestellungen, jenseits von 20 Minuten liegen **2**. Wer daraus eine Kurve zeichnet, illustriert vor allem, wie dünn besetzte Randklassen Scheinmuster erzeugen. |
| 21 | **Keine Kundensegmente nach Standort** | Kundenherkunft (`home_district`) ist über alle 12 Würzburger Bezirke **gleichverteilt** (2.023 bis 2.185 Kunden je Bezirk), und die App-Nutzung liegt in **allen** Filialen bei 43–45 %. Ein Clustering nach Kundenprofil je Standort findet nichts — was die Standorte unterscheidet, sind Kanalmix, Bestellwert und Wochenendanteil, nicht die Kundschaft. |

---

## Infrastruktur-Empfehlungen

### A) Kommerzielle Cloud-Lösungen (kostenfreie Tiers)

| Lösung | Free Tier | Eignung | Besonderheit |
|--------|-----------|---------|-------------|
| **MotherDuck** | Free Tier | Data Warehouse, SQL-Analyse | DuckDB in der Cloud, Web-UI ohne Setup — **Grundlage des Übungsblatts** |
| **Google BigQuery** | 1 TB Queries/Monat, 10 GB Storage | Data Warehouse, SQL-Analyse | Serverless, Standard-SQL, Anbindung an Looker Studio |
| **Snowflake** | 30 Tage Trial, 400 $ Credits | Data Warehouse, Multi-Cloud | Trennung von Storage/Compute, Time Travel |
| **Microsoft Fabric / Power BI** | Power BI Desktop kostenlos, Fabric Trial 60 Tage | Full-Stack BI | DirectLake, Copilot, DAX + M |
| **Databricks Community Edition** | kostenlos | Data Engineering + ML | Notebooks, Spark, MLflow |
| **Google Looker Studio** | vollständig kostenlos | Dashboarding | Direkte BigQuery-Anbindung |
| **Tableau Public** | kostenlos (Daten öffentlich) | Visualisierung, Lehre | Public Galleries |

### B) Open-Source-Lösungen (Self-Hosted)

| Lösung | Kategorie | Eignung |
|--------|-----------|---------|
| **PostgreSQL** (z. B. via Supabase) | RDBMS / DWH | Galaxy-Schema, SQL-Analysen |
| **DuckDB** | Embedded Analytical DB | Lokale Analyse, liest CSVs direkt, kein Server nötig |
| **Apache Doris** | MPP Analytical DB | OLAP-Queries, Aggregationen |
| **ClickHouse** | Columnar OLAP DB | Echtzeit-Analytik, Zeitreihen |
| **Apache Superset** | BI / Dashboarding | Dashboards, SQL Lab, Docker-Deploy |
| **Metabase** | BI / Dashboarding | Self-Service BI, einsteigerfreundlich |
| **MinIO** | Object Storage | Data-Lake-Layer, S3-kompatibel |

### C) Digitale Souveränität — Lehrpunkte

- **Datenhoheit:** Alle Daten bleiben auf eigener Infrastruktur (EU/DE-hosted)
- **Vendor Lock-in:** BigQuery (proprietär) vs. PostgreSQL (portabel)
- **DSGVO:** Personenbezogene Daten in deutscher Infrastruktur
- **TCO-Analyse:** Cloud-Kosten vs. Self-Hosting-Aufwand
- **Exit-Strategie:** Datenportabilität zwischen Systemen

### D) Python Analytics Stack

```
pandas          → Datenaufbereitung, ETL
duckdb          → SQL direkt in Python auf CSVs
plotly / dash   → Interaktive Dashboards
scikit-learn    → Clustering, Classification
mlxtend         → Apriori / FP-Growth (Warenkorbanalyse)
folium          → Geo-Visualisierung der Filialen
streamlit       → Schnelle Dashboard-Prototypen
```

---

## Übungen und Use Cases

### Grundlagen (OLAP / Multidimensional)
1. **Cube-Operationen:** Drill-Down (Jahr → Quartal → Monat → Tag), Roll-Up, Slice & Dice
2. **Pivot-Tabellen:** Umsatz nach Filiale × Jahr, Zahlungsart × Kanal
3. **Galaxy-Schema in SQL:** JOINs über beide Faktentabellen und die geteilten Dimensionen
4. **Grain-Falle:** Warum liefert ein Join von `fact_orders` auf `fact_order_items` falsche Umsatzsummen?
5. **OBT vs. Galaxy-Schema:** Laufzeit- und Wartbarkeitsvergleich

### Fortgeschritten (Data Mining)
6. **Warenkorbanalyse:** Apriori auf `fact_order_items`, Lift statt Support als Kriterium (siehe Regel 18)
7. **Kundensegmentierung:** RFM-Analyse, K-Means auf Bestellverhalten
8. **Umsatzprognose:** Zeitreihenanalyse mit saisonaler Zerlegung
9. **Standortanalyse:** Normierung auf Betriebsjahre und Sitzplätze
10. **Anomalie-Erkennung:** Ungewöhnliche Umsatztage identifizieren

### BI-Prozess End-to-End
11. **ETL-Pipeline:** CSV → Staging → Galaxy-Schema in PostgreSQL
12. **Dashboard-Design:** KPI-Dashboard in Power BI / Superset / Dash
13. **Datenqualität:** Orphan Dimensions aufspüren und dokumentieren
14. **Reporting:** Automatisierte Monatsberichte mit Python

---

## Schnellstart

### DuckDB (lokal, ohne Setup)

```python
import duckdb

con = duckdb.connect()

# Umsatz pro Filiale und Jahr
con.execute("""
    SELECT b.branch_name,
           d.year,
           ROUND(SUM(o.net_total)) AS umsatz_eur
    FROM 'fact_orders.csv' o
    JOIN 'dim_branch.csv'  b ON o.branch_id = b.branch_id
    JOIN 'dim_date.csv'    d ON o.date      = d.date
    GROUP BY b.branch_name, d.year
    ORDER BY b.branch_name, d.year
""").df()
```

### PostgreSQL

PostgreSQL kann CSVs nicht direkt lesen — Tabellen müssen angelegt und befüllt werden:

```sql
CREATE TABLE dim_branch (
    branch_id        INTEGER PRIMARY KEY,
    branch_name      TEXT NOT NULL,
    address          TEXT,
    district         TEXT,
    city             TEXT,
    postal_code      TEXT,
    latitude         NUMERIC(8,5),
    longitude        NUMERIC(8,5),
    size_sqm         INTEGER,
    seats_indoor     INTEGER,
    seats_outdoor    INTEGER,
    has_drive_through BOOLEAN,
    has_playground   BOOLEAN,
    parking_spots    INTEGER,
    opening_date     DATE,
    monthly_rent_eur NUMERIC(10,2),
    branch_type      TEXT
);
```

Import im `psql`-Client (die Dateien sind UTF-8 mit BOM):

```
\copy dim_branch FROM 'dim_branch.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
```

### Power BI

1. Daten abrufen → CSV-Dateien laden
2. Beziehungen im Modell-View konfigurieren — beide Faktentabellen mit den geteilten Dimensionen verbinden
3. DAX-Measures erstellen, z. B. `Total Revenue = SUM(fact_orders[net_total])`
4. Visualisierungen erstellen

### One Big Table neu erzeugen

```bash
python generate_obt.py
```

Erzeugt `obt_orders.csv` aus den Star-Schema-CSVs (754.513 Zeilen × 41 Spalten, ~185 MB, Laufzeit rund 10 Sekunden). Das Ergebnis ist byte-identisch zur mitgelieferten Datei.

---

## Prüfstand

Sämtliche Kennzahlen, Zeilenzahlen und Muster in diesem Dokument wurden am **25. August 2026** mit pandas direkt aus den CSV-Dateien nachgerechnet — **79 Angaben, alle bestätigt**.

Das ist nachvollziehbar und wiederholbar:

```bash
python verify_readme.py     # Exit-Code 0 = alle Angaben bestätigt
```

Das Skript prüft jede Zahl dieses Dokuments gegen die CSVs und meldet Abweichungen einzeln. Nach jeder Änderung an den Daten sollte es erneut durchlaufen.

Die Vorgängerfassung beschrieb einen älteren, kleineren Datenstand: Kalenderjahr 2024 statt 2017–2026, 106.720 statt 754.513 Bestellungen, 12.000 statt 25.000 Kunden, 50 statt 57 Produkte, 366 statt 3.377 Kalendertage. Sie bezeichnete das Modell außerdem als Star Schema, obwohl es mit zwei Faktentabellen ein Galaxy-Schema ist, und nummerierte die Filialen abweichend von der tatsächlichen `branch_id`.

Bei der Prüfung fielen zusätzlich drei Aussagen durch, die sich in den Daten **nicht** bestätigen ließen:

- *„Filialcluster: unterschiedliche Kundenprofile pro Standort"* — die Kundenherkunft ist über alle Bezirke gleichverteilt.
- *„Uni-Filiale mit hoher App-Nutzung"* — die App-Quote liegt in allen acht Filialen bei 43–45 %.
- *„App-Nutzer bestellen häufiger"* — sie bestellen etwas **seltener** (29,2 vs. 31,0 Bestellungen pro Kopf) und mit geringerem Bestellwert (19,04 € vs. 19,41 €).

Mehrere quantitative Angaben waren der Größenordnung nach zu korrigieren, darunter der Anteil bewerteter Bestellungen (30 % → 18,9 %), der Mobile-Payment-Verlauf (17 → 25 % statt tatsächlich 0,9 → 12,2 %) und der Weihnachtsmarkt-Effekt (+15 % → +5 %).

Weitere Prüfberichte liegen unter [`../docs/`](../docs/).
