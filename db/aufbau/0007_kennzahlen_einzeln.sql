-- 0007_kennzahlen_einzeln.sql
-- Zweck: Sichten fuer die Kacheln, die keine Reihe sind, sondern ein
--        einzelner Wert — und Produktkennzahlen je Jahr.
-- Ruecknahme: DROP VIEW burgermetrics.v_produkt_jahr, v_kennzahl_einzeln;
-- Idempotent: ja.

SET search_path TO burgermetrics;

-- Produkte je Jahr: die Uebersichtskachel "Top-Burger 2025" braucht die
-- Jahreszahl, nicht die kumulierte.
CREATE OR REPLACE VIEW v_produkt_jahr AS
WITH je AS (
  SELECT extract(year FROM o.date)::int AS jahr,
         p.product_id, p.product_name, p.category, p.subcategory,
         sum(i.quantity)   AS menge,
         sum(i.line_total) AS positionsumsatz
  FROM fact_order_items i
  JOIN fact_orders o USING (order_id)
  JOIN dim_product  p USING (product_id)
  GROUP BY 1,2,3,4,5)
SELECT jahr, product_id, product_name, category, subcategory, menge, positionsumsatz,
       100.0 * positionsumsatz / sum(positionsumsatz) OVER (PARTITION BY jahr) AS anteil_pct
FROM je;

-- Einzelwerte. Jede Zeile ist eine Kachel; kennung ist der Schluessel, den
-- das Frontend anspricht. So bleibt auch hier die Definition in der Datenbank.
--
-- MATERIALISIERT: als Sicht mit UNION ALL wertet PostgreSQL die
-- gemeinsamen Ausdruecke je Zweig neu aus — sieben Mal ueber 754.513
-- Bestellungen. Vorberechnet sind es Millisekunden. Auffrischen mit
--   REFRESH MATERIALIZED VIEW burgermetrics.v_kennzahl_einzeln;
DO $$
DECLARE art char;
BEGIN
  SELECT c.relkind INTO art FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='burgermetrics' AND c.relname='v_kennzahl_einzeln';
  IF art = 'v' THEN DROP VIEW burgermetrics.v_kennzahl_einzeln CASCADE;
  ELSIF art = 'm' THEN DROP MATERIALIZED VIEW burgermetrics.v_kennzahl_einzeln CASCADE;
  END IF;
END $$;

CREATE MATERIALIZED VIEW v_kennzahl_einzeln AS
WITH erstjahr AS (
  SELECT customer_id, min(extract(year FROM date))::int AS ej FROM fact_orders GROUP BY 1),
aktivjahr AS (
  SELECT DISTINCT extract(year FROM date)::int AS jahr, customer_id FROM fact_orders),
wieder AS (
  SELECT a.jahr,
         round(100.0 * count(*) FILTER (WHERE e.ej < a.jahr) / count(*), 1) AS pct,
         count(*) FILTER (WHERE e.ej < a.jahr)                              AS stammkunden
  FROM aktivjahr a JOIN erstjahr e USING (customer_id) GROUP BY 1),
zufrieden AS (
  SELECT extract(year FROM date)::int AS jahr, round(avg(satisfaction_score),2) AS wert,
         count(satisfaction_score) AS n
  FROM fact_orders WHERE satisfaction_score IS NOT NULL GROUP BY 1),
tage AS (SELECT date, max(temperature_celsius) t, sum(net_total) u FROM obt_orders GROUP BY 1),
filiale AS (SELECT branch_id, avg(order_duration_min) d, avg(satisfaction_score) s
            FROM fact_orders GROUP BY 1),
kohorte AS (
  SELECT round(avg(100.0 * f.aktive / k.kohortengroesse), 1) AS pct
  FROM (SELECT DISTINCT kohorte, kohortengroesse FROM v_kohorte) k
  JOIN LATERAL (SELECT aktive FROM v_kohorte v
                WHERE v.kohorte = k.kohorte AND v.jahr = k.kohorte + 1) f ON true),
aktiv26 AS (
  SELECT round(100.0 * count(DISTINCT customer_id)
             / (SELECT count(DISTINCT customer_id) FROM fact_orders), 0) AS pct
  FROM fact_orders WHERE extract(year FROM date) = 2026)
SELECT * FROM (VALUES
  ('wiederkehrend_2025',
     (SELECT pct FROM wieder WHERE jahr=2025),
     (SELECT pct FROM wieder WHERE jahr=2024),
     (SELECT stammkunden FROM wieder WHERE jahr=2025)::numeric),
  ('zufriedenheit_2025',
     (SELECT wert FROM zufrieden WHERE jahr=2025),
     (SELECT wert FROM zufrieden WHERE jahr=2024),
     (SELECT n FROM zufrieden WHERE jahr=2025)::numeric),
  ('korr_temperatur_umsatz',       (SELECT round(corr(t,u)::numeric,3) FROM tage), NULL, NULL),
  ('korr_wartezeit_zufriedenheit', (SELECT round(corr(d,s)::numeric,2) FROM filiale), NULL, NULL),
  ('korr_dauer_zufriedenheit',
     (SELECT round(corr(order_duration_min, satisfaction_score)::numeric,3) FROM fact_orders), NULL, NULL),
  ('retention_mittel',             (SELECT pct FROM kohorte), NULL, NULL),
  ('aktiv_2026',                   (SELECT pct FROM aktiv26), NULL, NULL)
) AS w(kennung, wert, vergleich, anzahl);

GRANT SELECT ON ALL TABLES IN SCHEMA burgermetrics TO anon, authenticated;

-- v_zufriedenheit_kanal um die Zahl der BEWERTUNGEN ergaenzen. Ohne sie laesst
-- sich der Gesamtdurchschnitt nicht richtig gewichten: Nur 142.317 der
-- 754.513 Bestellungen tragen eine Bewertung.
DROP VIEW IF EXISTS v_zufriedenheit_kanal CASCADE;
CREATE VIEW v_zufriedenheit_kanal AS
SELECT order_channel AS kanal,
       count(*)                        AS bestellungen,
       count(satisfaction_score)       AS bewertungen,
       avg(satisfaction_score)         AS zufriedenheit
FROM fact_orders GROUP BY 1 ORDER BY 4 DESC;

-- Rollenbezeichnungen auf Deutsch, wie im Dashboard gewohnt.
DROP VIEW IF EXISTS v_personal_rolle CASCADE;
CREATE VIEW v_personal_rolle AS
SELECT role AS rolle,
       CASE role WHEN 'Branch Manager' THEN 'Manager' WHEN 'Cashier' THEN 'Kassierer'
                 WHEN 'Cook' THEN 'Köche' WHEN 'Shift Manager' THEN 'Schichtleiter'
                 WHEN 'Trainee' THEN 'Auszubildende' ELSE role END AS bezeichnung,
       CASE role WHEN 'Branch Manager' THEN 1 WHEN 'Cashier' THEN 2 WHEN 'Cook' THEN 3
                 WHEN 'Shift Manager' THEN 4 ELSE 5 END AS nr,
       count(*) AS anzahl, avg(hourly_wage) AS stundenlohn
FROM dim_employee GROUP BY 1,2,3 ORDER BY nr;

GRANT SELECT ON ALL TABLES IN SCHEMA burgermetrics TO anon, authenticated;

-- Drei weitere Einzelwerte fuer die Management Summary.
REFRESH MATERIALIZED VIEW v_kennzahl_einzeln;
CREATE OR REPLACE VIEW v_kennzahl_zusatz AS
WITH quartal AS (
  SELECT year AS jahr, quarter, sum(net_total) u FROM obt_orders
  WHERE year BETWEEN 2018 AND 2025 GROUP BY 1,2),
best AS (SELECT jahr, quarter, row_number() OVER (PARTITION BY jahr ORDER BY u DESC) rn FROM quartal),
spitze AS (SELECT quarter, count(*) n FROM best WHERE rn=1 GROUP BY 1 ORDER BY 2 DESC LIMIT 1)
SELECT 'artikel_je_bestellung' AS kennung, round(avg(distinct_items),2) AS wert,
       NULL::numeric AS vergleich, NULL::numeric AS anzahl, NULL::text AS text FROM fact_orders
UNION ALL SELECT 'stueck_je_bestellung', round(avg(item_count),2), NULL, NULL, NULL FROM fact_orders
UNION ALL SELECT 'spitzenquartal', NULL, 8, (SELECT n FROM spitze),
       (SELECT quarter || ' Peak' FROM spitze);
GRANT SELECT ON ALL TABLES IN SCHEMA burgermetrics TO anon, authenticated;
