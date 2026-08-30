-- 0005_semantik.sql
-- Zweck: die Semantikschicht des Projekts. Jede Kennzahl des Dashboards ist
--        hier EINMAL definiert; das Frontend kennt nur diese Sichten, nie
--        eine Spalte oder einen Join. Genau die Schicht, die das BI-Deck
--        auf der Folie "Die Kennzahl einmal definieren" beschreibt.
--
-- Vertrag: Jede Sicht heisst v_<thema> und liefert stabile Spaltennamen.
--          Wer spaeter MySQL, Snowflake oder ein Lakehouse anschliesst,
--          muss genau diese Sichten nachbauen — sonst nichts.
--
-- Kennzahlendefinition, verbindlich:
--   umsatz      = SUM(net_total)  (Nettobetrag NACH Rabatt)
--   bestellungen= COUNT(*)
--   aov         = AVG(net_total)
--   positionsumsatz = SUM(line_total) (Bruttobetrag, Positionsebene)
--
-- Ruecknahme: DROP VIEW burgermetrics.v_* ;
-- Idempotent: ja (CREATE OR REPLACE).

SET search_path TO burgermetrics;

-- Kennzahlen je Jahr — traegt Umsatzkacheln, Jahresverlauf, AOV-Entwicklung
CREATE OR REPLACE VIEW v_kennzahlen_jahr AS
SELECT extract(year FROM date)::int AS jahr,
       count(*)                     AS bestellungen,
       sum(net_total)               AS umsatz,
       avg(net_total)               AS aov,
       sum(gross_total)             AS bruttoumsatz,
       sum(discount_amount)         AS rabatt
FROM fact_orders GROUP BY 1 ORDER BY 1;

-- Monatsverlauf
CREATE OR REPLACE VIEW v_umsatz_monat AS
SELECT to_char(date, 'YYYY-MM') AS monat,
       count(*) AS bestellungen, sum(net_total) AS umsatz
FROM fact_orders GROUP BY 1 ORDER BY 1;

-- Filialen, kumuliert und je Jahr
CREATE OR REPLACE VIEW v_filiale AS
SELECT b.branch_id, b.branch_name, b.district, b.branch_type, b.size_sqm,
       b.opening_date, b.monthly_rent_eur,
       count(*)         AS bestellungen,
       sum(o.net_total) AS umsatz,
       avg(o.net_total) AS aov,
       avg(o.satisfaction_score) AS zufriedenheit,
       extract(year FROM max(o.date)) - extract(year FROM min(o.date)) + 1 AS jahre
FROM fact_orders o JOIN dim_branch b USING (branch_id)
GROUP BY 1,2,3,4,5,6,7 ORDER BY umsatz DESC;

-- Produkte und Kategorien (Positionsebene!)
CREATE OR REPLACE VIEW v_produkt AS
SELECT p.product_id, p.product_name, p.category, p.subcategory,
       p.is_vegetarian, p.is_vegan,
       sum(i.quantity)   AS menge,
       sum(i.line_total) AS positionsumsatz
FROM fact_order_items i JOIN dim_product p USING (product_id)
GROUP BY 1,2,3,4,5,6 ORDER BY positionsumsatz DESC;

CREATE OR REPLACE VIEW v_kategorie AS
SELECT p.category, sum(i.quantity) AS menge, sum(i.line_total) AS positionsumsatz
FROM fact_order_items i JOIN dim_product p USING (product_id)
GROUP BY 1 ORDER BY positionsumsatz DESC;

-- Vegetarier-Anteil je Jahr, innerhalb der Kategorie Burger (Mengenanteil)
CREATE OR REPLACE VIEW v_veggie_anteil AS
SELECT extract(year FROM o.date)::int AS jahr,
       100.0 * sum(CASE WHEN p.is_vegetarian OR p.is_vegan THEN i.quantity ELSE 0 END)
             / nullif(sum(i.quantity),0) AS anteil_pct
FROM fact_order_items i JOIN fact_orders o USING (order_id)
JOIN dim_product p USING (product_id)
WHERE p.category = 'Burger' GROUP BY 1 ORDER BY 1;

-- Kanaele je Jahr
CREATE OR REPLACE VIEW v_kanal_jahr AS
WITH je AS (
  SELECT extract(year FROM date)::int AS jahr, order_channel AS kanal,
         count(*) AS bestellungen, sum(net_total) AS umsatz, avg(net_total) AS aov
  FROM fact_orders GROUP BY 1,2)
SELECT jahr, kanal, bestellungen, umsatz, aov,
       100.0*bestellungen / sum(bestellungen) OVER (PARTITION BY jahr) AS anteil_pct
FROM je ORDER BY jahr, bestellungen DESC;

-- Zahlarten je Jahr
CREATE OR REPLACE VIEW v_zahlart_jahr AS
WITH je AS (SELECT year AS jahr, payment_type AS zahlart, count(*) AS bestellungen
            FROM obt_orders GROUP BY 1,2)
SELECT jahr, zahlart, bestellungen,
       100.0*bestellungen / sum(bestellungen) OVER (PARTITION BY jahr) AS anteil_pct
FROM je ORDER BY jahr, bestellungen DESC;

-- Zeitachsen
CREATE OR REPLACE VIEW v_wochentag AS
SELECT day_name AS wochentag,
       CASE day_name WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3
            WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 ELSE 7 END AS nr,
       count(*) AS bestellungen, sum(net_total) AS umsatz
FROM obt_orders GROUP BY 1,2 ORDER BY nr;

CREATE OR REPLACE VIEW v_stunde AS
SELECT hour AS stunde, count(*) AS bestellungen, sum(net_total) AS umsatz,
       avg(satisfaction_score) AS zufriedenheit
FROM fact_orders GROUP BY 1 ORDER BY 1;

CREATE OR REPLACE VIEW v_heatmap AS
SELECT day_name AS wochentag, hour AS stunde, count(*) AS bestellungen
FROM obt_orders GROUP BY 1,2;

-- Kundenstruktur
CREATE OR REPLACE VIEW v_kunde_alter AS
SELECT age_group AS altersgruppe, count(*) AS kunden FROM dim_customer GROUP BY 1 ORDER BY 1;

CREATE OR REPLACE VIEW v_kunde_loyalty AS
SELECT loyalty_tier AS stufe, count(*) AS kunden FROM dim_customer GROUP BY 1;

CREATE OR REPLACE VIEW v_kunde_bezirk AS
SELECT home_district AS bezirk, count(*) AS kunden FROM dim_customer GROUP BY 1 ORDER BY 2 DESC;

-- Personal
CREATE OR REPLACE VIEW v_personal_filiale AS
SELECT b.branch_name, b.branch_type,
       count(DISTINCT e.employee_id) AS mitarbeiter,
       (SELECT sum(o.net_total) FROM fact_orders o WHERE o.branch_id=b.branch_id)
         / count(DISTINCT e.employee_id) AS umsatz_je_ma,
       (SELECT count(*) FROM fact_orders o WHERE o.branch_id=b.branch_id)
         / count(DISTINCT e.employee_id) AS bestellungen_je_ma,
       (SELECT avg(o.satisfaction_score) FROM fact_orders o WHERE o.branch_id=b.branch_id) AS zufriedenheit,
       (SELECT avg(o.order_duration_min) FROM fact_orders o WHERE o.branch_id=b.branch_id) AS dauer
FROM dim_branch b JOIN dim_employee e USING (branch_id)
GROUP BY b.branch_id, b.branch_name, b.branch_type ORDER BY umsatz_je_ma;

CREATE OR REPLACE VIEW v_personal_rolle AS
SELECT role AS rolle, count(*) AS anzahl, avg(hourly_wage) AS stundenlohn
FROM dim_employee GROUP BY 1 ORDER BY 2 DESC;

CREATE OR REPLACE VIEW v_zufriedenheit_kanal AS
SELECT order_channel AS kanal, count(*) AS bestellungen,
       avg(satisfaction_score) AS zufriedenheit
FROM fact_orders GROUP BY 1 ORDER BY 3 DESC;

CREATE OR REPLACE VIEW v_zufriedenheit_dauer AS
SELECT CASE WHEN order_duration_min <= 3 THEN '1-3' WHEN order_duration_min <= 5 THEN '3-5'
            WHEN order_duration_min <= 7 THEN '5-7' WHEN order_duration_min <= 10 THEN '7-10'
            WHEN order_duration_min <= 15 THEN '10-15' ELSE '15+' END AS dauer_klasse,
       min(order_duration_min) AS nr,
       avg(satisfaction_score) AS zufriedenheit, count(*) AS bestellungen
FROM fact_orders GROUP BY 1 ORDER BY nr;

-- Aktionen
CREATE OR REPLACE VIEW v_promotion AS
SELECT pr.promo_name AS aktion, pr.promo_type AS art, pr.discount_pct AS rabatt_pct,
       count(*) AS bestellungen, sum(o.net_total) AS umsatz, avg(o.net_total) AS aov,
       avg(o.satisfaction_score) AS zufriedenheit, sum(o.discount_amount) AS rabattsumme
FROM fact_orders o JOIN dim_promotion pr USING (promo_id)
WHERE pr.promo_id <> 0 GROUP BY 1,2,3 ORDER BY bestellungen DESC;

-- Wetter
CREATE OR REPLACE VIEW v_wetter_tag AS
SELECT o.date AS tag, w.condition AS wetterlage, w.temperature_celsius AS temperatur,
       w.precipitation_mm AS niederschlag,
       count(*) AS bestellungen, sum(o.net_total) AS umsatz
FROM fact_orders o JOIN dim_weather w USING (date)
GROUP BY 1,2,3,4 ORDER BY 1;

CREATE OR REPLACE VIEW v_wetter_lage AS
WITH tage AS (SELECT date, condition, sum(net_total) u, count(*) n
              FROM obt_orders GROUP BY 1,2)
SELECT condition AS wetterlage, count(*) AS tage,
       avg(u) AS umsatz_je_tag, avg(n) AS bestellungen_je_tag
FROM tage GROUP BY 1 ORDER BY 3 DESC;

CREATE OR REPLACE VIEW v_wetter_temperatur AS
WITH tage AS (SELECT date, max(temperature_celsius) t, sum(net_total) u, count(*) n
              FROM obt_orders GROUP BY 1)
SELECT width_bucket(t, -15, 35, 10) AS klasse,
       min(t) AS von, max(t) AS bis, count(*) AS tage,
       avg(u) AS umsatz_je_tag, avg(n) AS bestellungen_je_tag
FROM tage GROUP BY 1 ORDER BY 1;

-- Kohorten. Die Zugehoerigkeit kommt aus dim_customer.first_visit_year, NICHT
-- aus der ersten Bestellung in fact_orders. Beides ist begruendbar, aber nur
-- das erste passt zum uebrigen Dashboard — und die Zahlen gehen weit
-- auseinander (Kohorte 2017: 1.502 gegen 9.575), weil der Erstbesuch dem
-- ersten erfassten Kauf vorausgehen kann.
CREATE OR REPLACE VIEW v_kohorte AS
WITH erst AS (SELECT customer_id, first_visit_year AS kohorte FROM dim_customer
              WHERE first_visit_year IS NOT NULL),
     aktiv AS (SELECT DISTINCT customer_id, extract(year FROM date)::int AS jahr FROM fact_orders)
SELECT e.kohorte, a.jahr, count(DISTINCT a.customer_id) AS aktive,
       (SELECT count(*) FROM erst e2 WHERE e2.kohorte = e.kohorte) AS kohortengroesse
FROM erst e JOIN aktiv a USING (customer_id)
GROUP BY 1,2 ORDER BY 1,2;

-- Warenkorbanalyse: alle Produktpaare mit Support, Konfidenz, Lift.
-- MATERIALISIERT: die Selbstverknuepfung ueber 2,95 Mio. Positionen braucht
-- 4,4 s und reisst damit das statement_timeout der Rolle anon. Der Bestand
-- ist ein Abzug und aendert sich nur beim Neuladen — genau der Fall, fuer den
-- eine materialisierte Sicht gedacht ist. Auffrischen: REFRESH MATERIALIZED
-- VIEW burgermetrics.v_warenkorb_regeln;
-- Typsichere Ruecknahme: DROP VIEW auf eine materialisierte Sicht (und
-- umgekehrt) ist ein Fehler, kein stiller Treffer. Deshalb ueber relkind.
DO $$
DECLARE art char;
BEGIN
  SELECT c.relkind INTO art FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='burgermetrics' AND c.relname='v_warenkorb_regeln';
  IF art = 'v' THEN
    DROP VIEW burgermetrics.v_warenkorb_regeln CASCADE;
  ELSIF art = 'm' THEN
    DROP MATERIALIZED VIEW burgermetrics.v_warenkorb_regeln CASCADE;
  END IF;
END $$;
CREATE MATERIALIZED VIEW v_warenkorb_regeln AS
WITH korb AS (SELECT DISTINCT order_id, product_id FROM fact_order_items),
     gesamt AS (SELECT count(DISTINCT order_id)::numeric n FROM korb),
     einzeln AS (SELECT product_id, count(*)::numeric n FROM korb GROUP BY 1),
     paare AS (SELECT a.product_id pa, b.product_id pb, count(*)::numeric n
               FROM korb a JOIN korb b ON a.order_id=b.order_id AND a.product_id < b.product_id
               GROUP BY 1,2 HAVING count(*) > 5000)
SELECT pa.product_name AS produkt_a, pb.product_name AS produkt_b,
       p.n AS gemeinsam,
       100.0 * p.n / g.n            AS support_pct,
       100.0 * p.n / ea.n           AS konfidenz_pct,
       (p.n / g.n) / ((ea.n / g.n) * (eb.n / g.n)) AS lift
FROM paare p CROSS JOIN gesamt g
JOIN einzeln ea ON ea.product_id = p.pa
JOIN einzeln eb ON eb.product_id = p.pb
JOIN dim_product pa ON pa.product_id = p.pa
JOIN dim_product pb ON pb.product_id = p.pb
ORDER BY lift DESC;
CREATE INDEX ix_regeln_lift ON v_warenkorb_regeln(lift DESC);

-- Simulationsbasis: Burger mit Preis, Kosten, Menge
CREATE OR REPLACE VIEW v_simulation_basis AS
SELECT p.product_name AS produkt, p.unit_price AS preis, p.cost_price AS kosten,
       sum(i.quantity) AS menge, sum(i.line_total) AS umsatz
FROM fact_order_items i JOIN dim_product p USING (product_id)
WHERE p.category = 'Burger'
GROUP BY 1,2,3 ORDER BY umsatz DESC;

GRANT SELECT ON ALL TABLES IN SCHEMA burgermetrics TO anon, authenticated;
NOTIFY pgrst, 'reload config';

-- Kurznamen fuer die Achsenbeschriftung. Frueher standen sie als vierte
-- Spalte in der Handliste und mussten zur dort gewaehlten Reihenfolge passen.
-- Als Funktion koennen Etikett und Richtung nicht mehr auseinanderlaufen.
CREATE OR REPLACE FUNCTION kurzname(name text) RETURNS text AS $$
  SELECT CASE name
    WHEN 'Medium Fries'       THEN 'M.Fries'
    WHEN 'Small Fries'        THEN 'S.Fries'
    WHEN 'Large Fries'        THEN 'L.Fries'
    WHEN 'Cola 0.5l'          THEN 'Cola 0.5'
    WHEN 'Cola 0.3l'          THEN 'Cola 0.3'
    WHEN 'Beyond Burger'      THEN 'Beyond'
    WHEN 'Green Goddess Bowl' THEN 'G.Goddess'
    WHEN 'Side Salad'         THEN 'Salad'
    WHEN 'Chicken Nuggets 6pc' THEN 'Nuggets 6'
    WHEN 'Chicken Nuggets 9pc' THEN 'Nuggets 9'
    WHEN 'BBQ Sauce'          THEN 'BBQ'
    ELSE name
  END;
$$ LANGUAGE sql IMMUTABLE;

GRANT EXECUTE ON FUNCTION kurzname(text) TO anon, authenticated;

-- Die 15 Paare, die das Dashboard zeigt — eine kuratierte Auswahl aus
-- v_warenkorb_regeln. Die Auswahl ist eine fachliche Entscheidung (Burger,
-- Beilagen, Getraenke, dazu die staerkste Regel des Bestands) und gehoert
-- deshalb in die Semantikschicht, nicht ins
-- Frontend. Die Reihenfolge der Liste folgt dem Support; sie wurde von Hand
-- gesetzt und ist deshalb gegen Datenaenderungen nicht abgesichert.
CREATE OR REPLACE VIEW v_warenkorb_auswahl AS
WITH paare(nr, a, b) AS (VALUES
  ( 1,'Medium Fries','Cola 0.5l'),
  ( 2,'Small Fries','Cola 0.3l'),
  ( 3,'Cola 0.3l','Cola 0.5l'),
  ( 4,'Cola 0.3l','Medium Fries'),
  ( 5,'Beyond Burger','Cola 0.5l'),
  ( 6,'Small Fries','Cola 0.5l'),
  ( 7,'Beyond Burger','Medium Fries'),
  ( 8,'Small Fries','Medium Fries'),
  ( 9,'Beyond Burger','Side Salad'),
  (10,'Large Fries','Cola 0.5l'),
  (11,'Side Salad','Cola 0.5l'),
  (12,'Green Goddess Bowl','Cola 0.5l'),
  (13,'Large Fries','Medium Fries'),
  (14,'Beyond Burger','Cola 0.3l'),
  (15,'Side Salad','Medium Fries'),
  -- Die staerksten Regeln des Bestands: Lift 8,97 und 8,90, also rund
  -- neunmal haeufiger als bei Unabhaengigkeit. Sie stehen am Ende, weil
  -- die Reihenfolge dem Support folgt und der hier bei 1,4 % liegt.
  -- Beide Groessen sind aufgenommen: Ihre Werte liegen so dicht
  -- beieinander, dass eine Auswahl willkuerlich waere.
  (16,'Chicken Nuggets 6pc','BBQ Sauce'),
  (17,'Chicken Nuggets 9pc','BBQ Sauce'))
-- Die Auswahl nennt ein Paar, nicht eine Richtung: Der JOIN trifft die Regel
-- in beiden Reihenfolgen. Angezeigt werden muss aber die Richtung, zu der die
-- Konfidenz gehoert — sie ist nicht symmetrisch. Vorher standen hier p.a und
-- p.b, also die Reihenfolge der Handliste. Bei drei der fuenfzehn Paare war
-- die Regel andersherum gespeichert, und die Tabelle zeigte die Konfidenz der
-- Gegenrichtung: "Large Fries -> Medium Fries 15,6 %" war in Wahrheit
-- P(Large Fries | Medium Fries); richtig sind 30,6 %. Ebenso bei
-- "Side Salad -> Medium Fries" (15,4 statt 30,9 %) und
-- "Cola 0.3l -> Medium Fries" (24,5 statt 32,4 %).
-- Support, Lift und die gemeinsame Zahl sind symmetrisch und waren richtig.
--
-- Die Kurzbezeichnung wird aus derselben Richtung gebaut, damit Etikett und
-- Zahl nicht auseinanderlaufen koennen.
SELECT p.nr,
       kurzname(r.produkt_a) || '→' || kurzname(r.produkt_b) AS regel,
       r.produkt_a, r.produkt_b,
       r.gemeinsam, r.support_pct, r.konfidenz_pct, r.lift
FROM paare p
JOIN v_warenkorb_regeln r
  ON (r.produkt_a = p.a AND r.produkt_b = p.b)
  OR (r.produkt_a = p.b AND r.produkt_b = p.a)
ORDER BY p.nr;

GRANT SELECT ON ALL TABLES IN SCHEMA burgermetrics TO anon, authenticated;
NOTIFY pgrst, 'reload schema';
