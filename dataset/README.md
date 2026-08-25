# BurgerMetrics GmbH - BI-Musterdatensatz

## Unternehmensszenario

**BurgerMetrics GmbH** ist eine fiktive Burger-Kette mit 8 Filialen in Würzburg. Die Kette positioniert sich als modernes Quick-Service-Restaurant mit digitaler Bestellinfrastruktur (App, Kiosk, Drive-Through) und einem Loyalitätsprogramm. Die Daten simulieren den Export aus einem integrierten Warenwirtschaftssystem (ERP), der für analytische Zwecke aufzubereiten ist.

**Zeitraum:** 1. Januar 2024 - 31. Dezember 2024
**Umfang:** ~107.000 Bestellungen, ~412.000 Einzelpositionen, 12.000 Kunden

---

## Datenmodell

### Star Schema (Dimensionales Modell)

```
                    dim_date
                       |
dim_branch --- fact_orders --- dim_customer
                       |
              dim_payment_method
                       |
                 dim_promotion
                       |
              fact_order_items --- dim_product
```

### Dateien

| Datei | Typ | Zeilen | Beschreibung |
|-------|-----|--------|-------------|
| `dim_branch.csv` | Dimension | 8 | Filialen mit Geo-Koordinaten, Größe, Ausstattung |
| `dim_product.csv` | Dimension | 50 | Produkte mit Kategorien, Preisen, Nährwerten, Allergenen |
| `dim_customer.csv` | Dimension | 12.000 | Kundenprofile mit App-Status, Loyalty-Tier |
| `dim_payment_method.csv` | Dimension | 4 | Zahlungsarten (Bar, EC, Kreditkarte, Mobile Payment) |
| `dim_promotion.csv` | Dimension | 11 | Aktionen und Rabatte (teils App-gebunden) |
| `dim_date.csv` | Dimension | 366 | Kalenderdimension mit Feiertagen, Schulferien, Saison |
| `dim_time_slot.csv` | Dimension | 18 | Tageszeit-Zuordnung (Breakfast, Lunch, Dinner, ...) |
| `dim_employee.csv` | Dimension | 188 | Mitarbeiter mit Rollen und Stundenlöhnen |
| `dim_supplier.csv` | Dimension | 8 | Lieferanten der Burger-Kette |
| `dim_weather.csv` | Dimension | 366 | Tägliche Wetterdaten für Würzburg |
| `fact_orders.csv` | Fakt | 106.720 | Bestellungen (Header) |
| `fact_order_items.csv` | Fakt | 411.982 | Bestellpositionen (Detail) |
| `obt_orders.csv` | OBT | 106.720 | One Big Table (denormalisiert) |

### Schlüsselbeziehungen

- `fact_orders.branch_id` → `dim_branch.branch_id`
- `fact_orders.customer_id` → `dim_customer.customer_id`
- `fact_orders.payment_id` → `dim_payment_method.payment_id`
- `fact_orders.promo_id` → `dim_promotion.promo_id`
- `fact_orders.date` → `dim_date.date`
- `fact_order_items.order_id` → `fact_orders.order_id`
- `fact_order_items.product_id` → `dim_product.product_id`
- `dim_employee.branch_id` → `dim_branch.branch_id`
- `dim_weather.date` → `dim_date.date`

---

## 8 Filialen - Standortprofile

| # | Filiale | Typ | Besonderheiten |
|---|---------|-----|---------------|
| 1 | BM Hauptbahnhof | City Center | Hoher Laufkundenanteil, Touristen, kein Drive-Through, höchste Miete |
| 2 | BM Sanderring | University | Studierendenaffin, hohe App-Nutzung, starker Veggie-Anteil, Einbruch in Semesterferien |
| 3 | BM Europastern | Highway | Höchstes Volumen, Drive-Through-Schwerpunkt, Familien, großer Parkplatz |
| 4 | BM Mainfrankenpark | Shopping | Weekend-Peaks, Familien, Spielplatz, Shopping-Publikum |
| 5 | BM Grombühl | Hospital | Kleiner Standort, Krankenhaus-Umfeld, Mittagspeak dominiert |
| 6 | BM Heuchelhof | Residential | Wohngebiet, Familien, Drive-Through, Spielplatz |
| 7 | BM Lengfeld | Commercial | Gewerbegebiet, Lunch-Peaks unter der Woche |
| 8 | BM Zellerau | Mixed | Neueste Filiale (2022), im Aufbau, niedrigstes Volumen |

---

## Eingeimpfte Muster (für Data Mining & BI-Analysen)

### Zeitliche Muster
1. **Saisonalität:** Eis/Kaltgetränke im Sommer +150%, Heißgetränke im Winter +150%
2. **Wochentags-Effekte:** Freitag/Samstag höheres Volumen, Montag/Dienstag niedriger
3. **Tageszeit:** Klare Breakfast-, Lunch-, Dinner-Peaks mit unterschiedlichen Produktpräferenzen
4. **Events:** Kiliani Volksfest (Juni/Juli) +25%, Weihnachtsmarkt +15%
5. **Schulferien:** Familien-Filialen steigen, Uni-Filiale bricht im Sommer ein (-45%)

### Standort-Muster (Geoanalyse)
6. **Filialcluster:** Unterschiedliche Kundenprofile pro Standort
7. **Drive-Through-Korrelation:** Standorte mit Drive-Through haben größere Warenkörbe
8. **Mietkosten vs. Umsatz:** Nicht-lineare Beziehung, City-Center = hohe Miete, aber nicht höchster Umsatz

### Kunden- & Zahlungsmuster
9. **App-Effekt:** App-Nutzer bestellen häufiger, höhere Zufriedenheit, weniger Barzahlung
10. **Loyalty-Tiers:** Gold-Kunden geben mehr aus, nutzen mehr Promotions
11. **Mobile Payment Trend:** Wächst über das Jahr von ~17% auf ~25%
12. **Cash-Rückgang:** Barzahlungsanteil sinkt im Jahresverlauf

### Warenkorbanalyse (Association Rules)
13. **Burger + Fries + Cola:** Häufigstes Combo-Muster (~35%)
14. **Nuggets → BBQ Sauce:** Starke Assoziation (40%)
15. **Breakfast + Coffee:** 50% Wahrscheinlichkeit
16. **Große Burger → Bier:** Abend-Assoziation (12%)

### Anomalien & Ausreißer
17. **Bewertungs-Bias:** Nur 30% der Bestellungen haben Ratings (Selbstselektion)
18. **Wartezeiteffekt:** Längere Wartezeit → niedrigere Zufriedenheit

---

## Infrastruktur-Empfehlungen

### A) Kommerzielle Cloud-Lösungen (kostenfreie Tiers)

| Lösung | Free Tier | Eignung | Besonderheit |
|--------|-----------|---------|-------------|
| **Google BigQuery** | 1 TB Queries/Monat, 10 GB Storage | Data Warehouse, SQL-Analyse | Serverless, Standard-SQL, Integration mit Looker Studio (kostenlos) |
| **Snowflake** | 30 Tage Trial, $400 Credits | Data Warehouse, Multi-Cloud | Separation von Storage/Compute, Time Travel, kostenlose Trial |
| **Microsoft Fabric / Power BI** | Power BI Desktop kostenlos, Fabric Trial 60 Tage | Full-Stack BI | DirectLake, Copilot-Integration, DAX + M, kostenlose Desktop-Version |
| **Databricks Community Edition** | Kostenloser Community-Zugang | Data Engineering + ML | Notebooks, Spark, MLflow, Unity Catalog |
| **AWS Free Tier (Redshift Serverless)** | 3 Monate, $300 Credits | Cloud DWH | Gute Integration mit AWS-Ökosystem |
| **Google Looker Studio** | Vollständig kostenlos | Dashboarding/Reporting | Direkte BigQuery-Anbindung, Sharing |
| **Tableau Public** | Kostenlos (Daten öffentlich) | Visualisierung, Lehre | Sehr gutes Lernwerkzeug, Public Galleries |

**Empfohlener kommerzieller Stack für den Kurs:**
- **Google BigQuery + Looker Studio** (komplett kostenlos nutzbar, SQL-basiert)
- **Power BI Desktop** (kostenlos, DAX + M-Sprache, starke Visualisierung)
- **Snowflake Trial** für Data Warehousing Konzepte

### B) Open-Source-Lösungen (Self-Hosted auf VPS)

| Lösung | Kategorie | Eignung | Anmerkung |
|--------|-----------|---------|-----------|
| **PostgreSQL** (via Supabase) | RDBMS / DWH | Star Schema, SQL-Analysen | Bereits auf deinem VPS, nutze CTAS für analytische Views |
| **Apache Doris** | MPP Analytical DB | OLAP-Queries, Aggregationen | Bereits auf deinem VPS, ideal für Multi-Dim-Analysen |
| **DuckDB** | Embedded Analytical DB | Lokale Analyse, Python-Integration | Kein Server nötig, direkt in Python/CLI, sehr schnell auf CSVs |
| **ClickHouse** | Columnar OLAP DB | Echtzeit-Analytik, große Datenmengen | Sehr performant, gut für Zeitreihen |
| **Apache Superset** | BI / Dashboarding | Dashboards, Charts, SQL Lab | Open-Source Tableau-Alternative, Docker-Deploy |
| **Metabase** | BI / Dashboarding | Self-Service BI, Fragen stellen | Einsteigerfreundlich, Docker-Deploy |
| **MinIO** | Object Storage | Data Lake Layer | S3-kompatibel, für Rohdaten-Ablage |

**Empfohlener Open-Source Stack:**
- **Supabase (PostgreSQL)** → Relationale Datenhaltung, Star Schema
- **Apache Doris** → OLAP-Analysen, Materialized Views
- **DuckDB** → Lokale Ad-hoc-Analyse in Python-Notebooks
- **Apache Superset** → Dashboarding (Docker auf VPS)

### C) Digitale Souveränität - Lehrpunkte

Der Open-Source-Stack ermöglicht die Diskussion wichtiger Konzepte:
- **Datenhoheit:** Alle Daten bleiben auf eigenem VPS (EU/DE-hosted)
- **Vendor Lock-in:** Vergleich BigQuery (proprietär) vs. PostgreSQL (portabel)
- **DSGVO:** Personenbezogene Daten (Kunden) bleiben in deutscher Infrastruktur
- **TCO-Analyse:** Cloud-Kosten vs. Self-Hosting-Aufwand
- **Exit-Strategie:** Datenportabilität zwischen Systemen

### D) Python Analytics Stack

```
pandas          → Datenaufbereitung, ETL
dash / plotly   → Interaktive Dashboards
scikit-learn    → Clustering, Classification, Association Rules
mlxtend         → Apriori / FP-Growth (Warenkorbanalyse)
folium          → Geo-Visualisierung der Filialen
duckdb          → SQL direkt in Python auf CSVs
streamlit       → Schnelle Dashboard-Prototypen
```

### E) KI & MCP Integration

- **MCP-Server für Datenanalyse:** Claude kann per MCP direkt auf PostgreSQL/Supabase zugreifen und SQL-Queries ausführen
- **Natural Language to SQL:** Studierende formulieren Fragen in natürlicher Sprache, KI generiert SQL
- **Automatische Insights:** KI erkennt Muster in Dashboards und erklärt Anomalien
- **Prompt Engineering für BI:** Studierende lernen, BI-Fragen so zu formulieren, dass KI aussagekräftige Analysen liefert

---

## Vorschläge für Übungen & Use Cases

### Grundlagen (OLAP / Multidimensional)
1. **Cube-Operationen:** Drill-Down (Jahr → Quartal → Monat → Woche → Tag), Roll-Up, Slice & Dice
2. **Pivot-Tabellen:** Umsatz nach Filiale × Monat, Zahlungsart × Kanal
3. **Star Schema in SQL:** JOINs über Dimensions- und Fakttabellen
4. **OBT vs. Star Schema:** Performance-Vergleich, Vor-/Nachteile

### Fortgeschritten (Data Mining)
5. **Warenkorbanalyse:** Apriori-Algorithmus auf `fact_order_items` → Häufige Itemsets, Assoziationsregeln
6. **Kundensegmentierung:** K-Means Clustering auf Basis von Bestellverhalten (RFM-Analyse)
7. **Churn Prediction:** Welche App-Nutzer werden inaktiv? (Classification)
8. **Umsatzprognose:** Zeitreihenanalyse mit saisonaler Zerlegung
9. **Geo-Analyse:** Einzugsgebiete der Filialen, Standort-Performance auf Karte
10. **Anomalie-Erkennung:** Ungewöhnliche Umsatztage identifizieren (Isolation Forest)

### BI-Prozess End-to-End
11. **ETL-Pipeline:** CSV → Staging → Star Schema in PostgreSQL
12. **Dashboard-Design:** KPI-Dashboard in Power BI / Superset / Dash
13. **Self-Service BI:** Metabase für Fachanwender konfigurieren
14. **Reporting:** Automatisierte Monatsberichte mit Python

### KI-Integration
15. **NL2SQL:** Natürliche Sprache → SQL-Queries via Claude MCP
16. **Automatische Interpretation:** KI erklärt Dashboard-Anomalien
17. **Augmented Analytics:** KI schlägt relevante Analysen vor

---

## Schnellstart

### Python (DuckDB)
```python
import duckdb

con = duckdb.connect()
con.execute("SELECT * FROM 'fact_orders.csv' LIMIT 5").df()

# Umsatz pro Filiale und Monat
con.execute("""
    SELECT b.branch_name, d.month_name,
           SUM(o.net_total) as revenue
    FROM 'fact_orders.csv' o
    JOIN 'dim_branch.csv' b ON o.branch_id = b.branch_id
    JOIN 'dim_date.csv' d ON o.date = d.date
    GROUP BY b.branch_name, d.month_name
    ORDER BY b.branch_name, MIN(d.month)
""").df()
```

### PostgreSQL (Supabase)
```sql
-- Tabellen anlegen und CSVs importieren (via psql \copy)
CREATE TABLE dim_branch AS SELECT * FROM read_csv('dim_branch.csv');
-- oder: \copy dim_branch FROM 'dim_branch.csv' CSV HEADER;
```

### Power BI
1. Daten abrufen → CSV-Dateien laden
2. Beziehungen im Modell-View konfigurieren (Star Schema)
3. DAX-Measures erstellen (z.B. `Total Revenue = SUM(fact_orders[net_total])`)
4. Visualisierungen erstellen
