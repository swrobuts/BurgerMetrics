# Übungsblatt: Data Warehouse mit MotherDuck

**Datensatz:** BurgerMetrics — eine fiktive Burger-Restaurant-Kette mit 8 Filialen
**Zeitraum:** 2017–2026 · 754.513 Bestellungen · 2,95 Mio. Bestellpositionen
**Ziel:** Sternschema verstehen, Daten abfragen, OLAP-Konzepte einüben

Alle Queries laufen direkt in der MotherDuck-Web-UI in der Datenbank `burger_metrics`. Vor dem Start einmal:

```sql
USE burger_metrics;
```

---

## Vorbereitung: die Datenbank anlegen

Steht die Datenbank `burger_metrics` bereits bereit, kann dieser Abschnitt übersprungen werden. Andernfalls erzeugt sie das mitgelieferte Ladeskript aus den CSV-Dateien.

```bash
pip install duckdb

# Zugangstoken von app.motherduck.com, einmalig in der Sitzung setzen
export motherduck_token="<Token>"

cd dataset
python load_duckdb.py --motherduck
```

Das Skript legt die Datenbank an, lädt alle 13 Tabellen und prüft jede Zeilenzahl gegen den Sollwert. Weicht eine ab, wird sie einzeln gemeldet.

**Ohne MotherDuck-Konto** funktioniert dasselbe Übungsblatt auf einer lokalen Datei — sämtliche Abfragen laufen unverändert, nur `USE burger_metrics;` entfällt:

```bash
python load_duckdb.py --lokal        # erzeugt burger_metrics.duckdb
duckdb burger_metrics.duckdb         # oder in DBeaver öffnen
```

Für einen schnellen Durchlauf ohne die 176 MB große One Big Table: `--klein` ergänzen. Block E lässt sich dann allerdings nicht bearbeiten, weil dort `obt_orders` gebraucht wird.

---

## Block A — Daten erkunden (≈ 15 Min)

### A1. Welche Tabellen gibt es?

```sql
SHOW TABLES;
```

### A2. Wie sieht eine Faktentabelle aus?

```sql
SELECT * FROM fact_orders LIMIT 10;
```

**Frage:** Welche Spalten sind Schlüssel auf andere Tabellen? Welche sind Kennzahlen?

### A3. Wie viele Datensätze enthält jede Tabelle?

```sql
SELECT 'fact_orders'      AS tabelle, COUNT(*) AS anzahl FROM fact_orders
UNION ALL
SELECT 'fact_order_items',           COUNT(*) FROM fact_order_items
UNION ALL
SELECT 'dim_customer',               COUNT(*) FROM dim_customer
UNION ALL
SELECT 'dim_product',                COUNT(*) FROM dim_product
UNION ALL
SELECT 'dim_branch',                 COUNT(*) FROM dim_branch;
```

### A4. Wann wurde die erste und letzte Bestellung erfasst?

```sql
SELECT MIN(date) AS erste_bestellung,
       MAX(date) AS letzte_bestellung
FROM fact_orders;
```

---

## Block B — Erste Aggregationen (≈ 15 Min)

### B1. Wie viele Bestellungen pro Jahr?

```sql
SELECT YEAR(date) AS jahr,
       COUNT(*)   AS bestellungen
FROM fact_orders
GROUP BY jahr
ORDER BY jahr;
```

### B2. Was ist der durchschnittliche Bestellwert?

```sql
SELECT ROUND(AVG(net_total), 2) AS durchschnitt_eur,
       ROUND(MIN(net_total), 2) AS minimum_eur,
       ROUND(MAX(net_total), 2) AS maximum_eur
FROM fact_orders;
```

### B3. Welche Bestellkanäle gibt es und wie häufig?

```sql
SELECT order_channel,
       COUNT(*) AS anzahl
FROM fact_orders
GROUP BY order_channel
ORDER BY anzahl DESC;
```

**Diskussion:** Warum eignen sich die Spalten in `fact_orders` zum Gruppieren — und was wäre eleganter?

---

## Block C — Joins über zwei Tabellen (≈ 20 Min)

### C1. Umsatz pro Filiale

```sql
SELECT b.branch_name,
       b.city,
       COUNT(*)                AS bestellungen,
       ROUND(SUM(f.net_total)) AS umsatz_eur
FROM fact_orders f
JOIN dim_branch  b ON f.branch_id = b.branch_id
GROUP BY b.branch_name, b.city
ORDER BY umsatz_eur DESC;
```

### C2. Welche Zahlungsarten werden genutzt?

```sql
SELECT p.payment_type,
       COUNT(*)                AS bestellungen,
       ROUND(SUM(f.net_total)) AS umsatz_eur
FROM fact_orders        f
JOIN dim_payment_method p ON f.payment_id = p.payment_id
GROUP BY p.payment_type
ORDER BY bestellungen DESC;
```

### C3. Top-10-Produkte nach verkaufter Menge

```sql
SELECT p.product_name,
       p.category,
       SUM(fi.quantity)          AS verkauft,
       ROUND(SUM(fi.line_total)) AS umsatz_eur
FROM fact_order_items fi
JOIN dim_product      p ON fi.product_id = p.product_id
GROUP BY p.product_name, p.category
ORDER BY verkauft DESC
LIMIT 10;
```

---

## Block D — Sternschema mit drei Tabellen (≈ 20 Min)

### D1. Umsatz pro Filiale, pro Jahr

```sql
SELECT b.branch_name,
       d.year,
       ROUND(SUM(f.net_total)) AS umsatz_eur
FROM fact_orders f
JOIN dim_branch  b ON f.branch_id = b.branch_id
JOIN dim_date    d ON f.date      = d.date
GROUP BY b.branch_name, d.year
ORDER BY b.branch_name, d.year;
```

### D2. Verkäufe Wochenende vs. Werktag

```sql
SELECT CASE WHEN d.is_weekend THEN 'Wochenende' ELSE 'Werktag' END AS tagtyp,
       COUNT(*)                AS bestellungen,
       ROUND(AVG(f.net_total), 2) AS durchschnitt_eur
FROM fact_orders f
JOIN dim_date    d ON f.date = d.date
GROUP BY tagtyp;
```

### D3. Welche Produktkategorie verkauft sich am besten?

```sql
SELECT p.category,
       SUM(fi.quantity)          AS verkauft,
       ROUND(SUM(fi.line_total)) AS umsatz_eur
FROM fact_order_items fi
JOIN fact_orders      f ON fi.order_id   = f.order_id
JOIN dim_product      p ON fi.product_id = p.product_id
GROUP BY p.category
ORDER BY umsatz_eur DESC;
```

---

## Block E — Sternschema vs. One-Big-Table (≈ 15 Min)

Dieselbe fachliche Frage, einmal mit Joins, einmal aus der denormalisierten Tabelle `obt_orders`. Beobachten Sie unten rechts in der MotherDuck-UI die **Laufzeit** beider Queries.

### E1. Sternschema-Variante

```sql
SELECT b.branch_name,
       d.year,
       d.quarter,
       ROUND(SUM(f.net_total)) AS umsatz_eur
FROM fact_orders f
JOIN dim_branch  b ON f.branch_id = b.branch_id
JOIN dim_date    d ON f.date      = d.date
GROUP BY b.branch_name, d.year, d.quarter
ORDER BY b.branch_name, d.year, d.quarter;
```

### E2. OBT-Variante

```sql
SELECT branch_name,
       year,
       quarter,
       ROUND(SUM(net_total)) AS umsatz_eur
FROM obt_orders
GROUP BY branch_name, year, quarter
ORDER BY branch_name, year, quarter;
```

**Diskussionsfragen:**
- Welche Variante ist schneller? Warum?
- Welche ist wartbarer, wenn sich z. B. die Filial-Adresse ändert?
- Wann lohnt sich ein OBT, wann nicht?

---

## Block F — Auffälligkeiten im Schema (≈ 5 Min)

### F1. Wie viele Bestellungen sind einer Promotion zugeordnet?

```sql
SELECT pr.promo_name,
       COUNT(*) AS bestellungen
FROM fact_orders   f
JOIN dim_promotion pr ON f.promo_id = pr.promo_id
GROUP BY pr.promo_name
ORDER BY bestellungen DESC;
```

### F2. Welche Filiale hat die meisten Mitarbeiter?

```sql
SELECT b.branch_name,
       COUNT(*) AS mitarbeiter
FROM dim_employee e
JOIN dim_branch   b ON e.branch_id = b.branch_id
GROUP BY b.branch_name
ORDER BY mitarbeiter DESC;
```

**Frage:** Warum lässt sich die Frage „Welcher Mitarbeiter hat den meisten Umsatz erwirtschaftet?" mit diesem Schema **nicht** beantworten?

### F3. Versuchen Sie, einen Lieferanten mit einer Bestellung in Verbindung zu bringen.

```sql
-- Versuch: Welche Lieferanten gibt es überhaupt?
SELECT * FROM dim_supplier;

-- Frage: Wo taucht supplier_id in den Faktentabellen oder in dim_product auf?
DESCRIBE fact_orders;
DESCRIBE fact_order_items;
DESCRIBE dim_product;
```

**Diskussion:** `dim_supplier` ist eine **Orphan Dimension** — sie ist im Schema vorhanden, aber an keine Faktentabelle und keine andere Dimension angebunden. Was wäre in einem produktiven DWH zu tun?

---

## Hausaufgabe (optional)

Beantworten Sie folgende Fragen mit jeweils einer SQL-Abfrage:

1. In welcher Stunde des Tages wird im Durchschnitt am meisten Umsatz gemacht?
2. Wie viele unterschiedliche Kunden hatte die Filiale „BM Hauptbahnhof" in 2025?
3. Welcher Tag der Woche ist umsatzstärksten?
4. Verkauft sich die Produktkategorie „Burger" an Regentagen anders als an Sonnentagen?

Für Frage 4: Hinweis auf `dim_weather`.

---

*Stand: SoSe 2026 · Dataset: github.com/swrobuts/BurgerMetrics*
