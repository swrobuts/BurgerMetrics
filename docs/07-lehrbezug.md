# 7 — Lehrbezug: DABA und BINT

BurgerMetrics ist als **Fallstudie zu DABA Kurseinheit 9** angelegt: „SQL — Analytische Funktionen, OLAP-Datenmodelle und Fallstudie". Dieses Kapitel ordnet die Bestandteile des Projekts den Lerngegenständen zu und benennt, wo das Projekt über die Kurseinheit hinausgeht.

Die verbindliche Kursdatenwelt in BINT ist Superstore. BurgerMetrics tritt nicht an deren Stelle, bietet aber für einzelne BINT-Einheiten Anschlussmaterial (Abschnitt 7.3).

---

## 7.1 DABA KE09 — Zuordnung der Lerngegenstände

| Lerngegenstand aus KE09 | Anknüpfung im Projekt |
|---|---|
| **OLTP und OLAP: ein Datenbestand, zwei Zwecke** | Das operative ERP-Modell (26 Tabellen) und das analytische Modell (12 Tabellen) liegen beide vor — [Kapitel 2.1 und 2.3](02-datenmodell.md) |
| **Normalisierung und Denormalisierung im DWH** | Die Zusammenführung von `artikel` + `artikelkategorie` + `artikelunterkategorie` zu `dim_product` ist in [Kapitel 2.2](02-datenmodell.md#22-der-übergang-denormalisierung-mit-absicht) mit Vorher/Nachher-SQL belegt |
| **Stern-Schema: eine Faktentabelle, viele Dimensionen** | Ausgangspunkt; das Projekt zeigt zusätzlich, was bei **zwei** Faktentabellen passiert (Abschnitt 7.2) |
| **Faktentabelle vs. Dimensionstabelle** | Kennzahlen/Attribute-Gegenüberstellung in [Kapitel 2.3](02-datenmodell.md#kennzahlen-und-attribute) |
| **Granularität** | [Kapitel 2.4](02-datenmodell.md#24-granularität-die-wichtigste-entscheidung) mit dem Fan-Trap-Beispiel: 70.809.660,60 € statt 14.522.378,70 € |
| **Von Northwind zum Stern-Schema** | Dieselbe Übung mit BurgerMetrics: die Umbautabelle in [Kapitel 2.2](02-datenmodell.md#22-der-übergang-denormalisierung-mit-absicht) |
| **Surrogatschlüssel** | Alle Dimensionen tragen einen eigenen Schlüssel; `dim_date.date_id` im Format `JJJJMMTT` ist ein sprechender Surrogatschlüssel |
| **Der OLAP-Würfel und seine Operationen** | Abschnitt 7.4 — alle sechs Operationen als SQL auf BurgerMetrics |
| **Analytische Funktionen (Window Functions)** | Abschnitt 7.5 |
| **DB-Views als Abstraktionsschicht** | Erweiterungsaufgabe, siehe Abschnitt 7.6 |

---

## 7.2 Wo das Projekt über KE09 hinausgeht

Drei Punkte, die im Kurs nicht vorkommen und sich als Vertiefung anbieten:

**Galaxy-Schema statt Stern-Schema.** KE09 führt das Stern-Schema mit genau einer Faktentabelle ein. BurgerMetrics hat zwei, die sich Dimensionen teilen. Die Bezeichnung dafür ist Galaxy-Schema oder Fact Constellation. Der Übergang lässt sich gut als Frage stellen: *Was ändert sich, wenn ein zweiter Sachverhalt auf einer feineren Ebene gemessen wird — und warum darf man die beiden nicht einfach verbinden?*

**Orphan Dimension.** `dim_supplier` hängt an nichts. Im operativen Modell existiert die Beziehung über den Einkaufspfad; sie ging beim Übergang verloren. Solche Reste finden sich in gewachsenen Auswertungssystemen regelmäßig, sind aber kein Lehrbuchthema.

**Grenzen der Beantwortbarkeit.** Die Frage „Welcher Mitarbeiter hat welchen Umsatz erwirtschaftet?" scheitert nicht am SQL, sondern daran, dass `fact_orders` keine `employee_id` führt. Diese Unterscheidung — Frage nicht beantwortbar wegen Modell, nicht wegen Können — ist erfahrungsgemäß schwer zu vermitteln und hier konkret vorführbar.

---

## 7.3 Anschlussstellen in BINT

| Einheit | Anknüpfung |
|---|---|
| **E04** Analytische Datenmodellierung | Die DABA-Brücke „dasselbe Szenario in 3NF und als Stern-Schema" ist hier vollständig ausgeführt: `erp_datenmodell.excalidraw` gegen das Galaxy-Schema |
| **E05** Validierung und Abweichungsanalyse | [Kapitel 4](04-validierung.md): 185 geprüfte Berichtswerte, 79 automatisiert geprüfte Dokumentationsangaben, drei unabhängige Rechenwege für den Gesamtumsatz |
| **E06** Architekturen und Pipelines | `generate_obt.py` als Miniatur-Ladestrecke mit Schlüssel- und Zeilenzahlprüfung; der byte-identische Nachweis in [Kapitel 3.4](03-etl.md#34-der-nachweis-byte-identische-reproduktion) |
| **E07** Datenbanken und SQL | Der Datenbestand lässt sich in PostgreSQL/Supabase laden; DDL-Beispiel in [`dataset/README.md`](../dataset/README.md) |
| **E08** Python und Warenkorbanalyse | Support, Konfidenz und Lift sind für vier Regeln berechnet — inklusive einer Regel mit Lift 1,03, an der sich „schwache Signale ehrlich interpretieren" konkret zeigen lässt |

---

## 7.4 Die sechs Würfeloperationen auf BurgerMetrics

KE09 führt die Operationen am Würfelbild und in Power BI ein. Hier dieselben Operationen als SQL — geeignet, um den Zusammenhang zwischen Bild, Werkzeug und Abfrage herzustellen.

Ausgangspunkt ist der Würfel *Umsatz nach Zeit × Filiale × Produktkategorie*.

**Roll-up** — eine Ebene höher, von Monat auf Jahr:

```sql
SELECT d.year, SUM(f.net_total) AS umsatz
FROM fact_orders f JOIN dim_date d ON f.date = d.date
GROUP BY d.year ORDER BY d.year;
```

**Drill-Down** — eine Ebene tiefer, vom Jahr auf das Quartal:

```sql
SELECT d.year, d.quarter, SUM(f.net_total) AS umsatz
FROM fact_orders f JOIN dim_date d ON f.date = d.date
GROUP BY d.year, d.quarter ORDER BY d.year, d.quarter;
```

**Slice** — eine Dimension auf einen Wert festlegen, es bleibt eine Scheibe:

```sql
SELECT b.branch_name, SUM(f.net_total) AS umsatz
FROM fact_orders f
JOIN dim_branch b ON f.branch_id = b.branch_id
JOIN dim_date   d ON f.date      = d.date
WHERE d.year = 2025                      -- die Scheibe
GROUP BY b.branch_name;
```

**Dice** — mehrere Dimensionen gleichzeitig einschränken, es bleibt ein Teilwürfel:

```sql
SELECT b.branch_name, p.category, SUM(fi.line_total) AS umsatz
FROM fact_order_items fi
JOIN fact_orders f ON fi.order_id   = f.order_id
JOIN dim_branch  b ON f.branch_id   = b.branch_id
JOIN dim_product p ON fi.product_id = p.product_id
JOIN dim_date    d ON f.date        = d.date
WHERE d.year IN (2024, 2025)             -- Einschränkung 1
  AND b.branch_type = 'Highway'          -- Einschränkung 2
  AND p.category IN ('Burger', 'Drink')  -- Einschränkung 3
GROUP BY b.branch_name, p.category;
```

**Pivot** — dieselben Daten, vertauschte Achsen:

```sql
SELECT p.category,
       SUM(CASE WHEN d.year = 2024 THEN fi.line_total ELSE 0 END) AS "2024",
       SUM(CASE WHEN d.year = 2025 THEN fi.line_total ELSE 0 END) AS "2025"
FROM fact_order_items fi
JOIN fact_orders f ON fi.order_id   = f.order_id
JOIN dim_product p ON fi.product_id = p.product_id
JOIN dim_date    d ON f.date        = d.date
GROUP BY p.category;
```

**Drill-Through** — die Aggregationsebene verlassen und zu den Einzelsätzen gehen:

```sql
SELECT f.order_id, f.date, f.time, p.product_name, fi.quantity, fi.line_total
FROM fact_order_items fi
JOIN fact_orders f ON fi.order_id   = f.order_id
JOIN dim_product p ON fi.product_id = p.product_id
WHERE f.branch_id = 1 AND f.date = '2025-07-04'
ORDER BY f.time;
```

---

## 7.5 Analytische Funktionen auf BurgerMetrics

KE09 behandelt Window Functions vor den OLAP-Modellen. Beide Teile lassen sich hier verbinden — Rangfolgen und Vorperiodenvergleich auf dem Stern-Schema:

```sql
-- Umsatzanteil je Filiale am Gesamtumsatz (OVER ohne PARTITION)
SELECT b.branch_name,
       SUM(f.net_total) AS umsatz,
       ROUND(100.0 * SUM(f.net_total) / SUM(SUM(f.net_total)) OVER (), 1) AS anteil_pct
FROM fact_orders f JOIN dim_branch b ON f.branch_id = b.branch_id
GROUP BY b.branch_name
ORDER BY umsatz DESC;
```

```sql
-- Vorjahresvergleich je Filiale (LAG)
SELECT b.branch_name, d.year,
       SUM(f.net_total) AS umsatz,
       LAG(SUM(f.net_total)) OVER (PARTITION BY b.branch_name ORDER BY d.year) AS vorjahr
FROM fact_orders f
JOIN dim_branch b ON f.branch_id = b.branch_id
JOIN dim_date   d ON f.date      = d.date
GROUP BY b.branch_name, d.year;
```

Der Vorjahresvergleich hat hier eine fachliche Besonderheit: Wegen der gestaffelten Eröffnung ist `vorjahr` für jede Filiale im Eröffnungsjahr leer, und das erste volle Jahr wird mit einem Rumpfjahr verglichen. Der scheinbar dramatische Zuwachs ist ein **Basiseffekt**. Das eignet sich als Anschlussfrage: *Wie erkennt man den Unterschied zwischen echtem Wachstum und einem Basiseffekt — und wie stellt man es richtig dar?*

---

## 7.6 Vorschläge für Aufgabenstellungen

Das vorhandene [Übungsblatt](../dataset/uebungsblatt.md) deckt die Blöcke A bis F ab (Erkundung, Aggregation, Joins, Stern-Schema, OBT-Vergleich, Schema-Auffälligkeiten) und läuft auf MotherDuck.

Ergänzende Aufgaben mit Bezug zu diesem Dokument:

1. **Fan Trap nachvollziehen.** Die falsche Abfrage aus [Kapitel 2.4](02-datenmodell.md#24-granularität-die-wichtigste-entscheidung) ausführen, den Faktor 4,88 erklären — und begründen, warum er nicht 3,91 beträgt.
2. **Orphan Dimension anbinden.** Aus dem operativen Modell einen Weg entwerfen, `dim_supplier` an die Fakten anzubinden. Welche Tabelle fehlt im analytischen Modell, und auf welcher Granularität läge sie?
3. **Views als semantische Schicht.** Eine View `v_umsatz_filiale_jahr` anlegen, die den Join kapselt. Danach: Welche Kennzahldefinition gehört in die View, welche ins Werkzeug?
4. **Basiseffekt behandeln.** Den Vorjahresvergleich aus Abschnitt 7.5 so umbauen, dass Rumpfjahre nicht zu irreführenden Wachstumsraten führen.
5. **Historisierung entwerfen.** Welche Dimension bräuchte eine Historisierung, welcher SCD-Typ wäre angemessen, und was änderte sich an der Faktentabelle?
6. **Gegenprobe rechnen.** Drei Kennzahlen des Berichts auf einem zweiten Weg nachrechnen (SQL gegen pandas gegen OBT) und Abweichungen dokumentieren.

---

## 7.7 Anmerkung zur Terminologie

Dieses Dokument verwendet die DABA-Terminologie: **Stern-Schema**, Faktentabelle, Dimensionstabelle, Kennzahlen, Attribute, Surrogatschlüssel, Granularität.

Der Bericht und die Weboberfläche verwenden an einigen Stellen die englischen Entsprechungen (Star Schema, Measures, Grain). Für BINT ist das stimmig, weil dort die Werkzeugoberflächen englisch sind; wer beide Kurse zusammen betrachtet, sollte den Unterschied einmal explizit machen. Die Begriffe bezeichnen dasselbe.

---

**Weiter:** [Entscheidungsjournal](08-entscheidungen.md)
