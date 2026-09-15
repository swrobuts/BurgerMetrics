-- bm_sichten.sql — Sichten der Semantikschicht auf dem Miniaturbestand des BM-Lab.
-- In der Datenbank der Fallstudie sind sie materialisiert (db/aufbau/0005 ff.);
-- hier reichen einfache Sichten auf 19 Bestellungen. Erwartet die Schemata
-- wawi und burgermetrics (Saatfolge in assets/bm.js und tools/sql.mjs).

CREATE VIEW burgermetrics.v_kennzahlen_jahr AS
SELECT extract(year FROM date)::int AS jahr, count(*) AS bestellungen,
       round(sum(net_total), 2) AS umsatz, round(avg(net_total), 2) AS aov
FROM burgermetrics.fact_orders GROUP BY 1;

CREATE VIEW burgermetrics.v_umsatz_monat AS
SELECT to_char(date, 'YYYY-MM') AS monat, count(*) AS bestellungen, round(sum(net_total), 2) AS umsatz
FROM burgermetrics.fact_orders GROUP BY 1;

CREATE VIEW burgermetrics.v_kanal_jahr AS
WITH je_kanal AS (
  SELECT extract(year FROM date)::int AS jahr, order_channel AS kanal, count(*) AS bestellungen
  FROM burgermetrics.fact_orders GROUP BY 1, 2)
SELECT jahr, kanal, bestellungen,
       round(100.0 * bestellungen / sum(bestellungen) OVER (PARTITION BY jahr), 1) AS anteil_pct
FROM je_kanal;

CREATE VIEW burgermetrics.v_rezension_produkt AS
SELECT p.product_id, p.product_name, p.category, count(r.review_id) AS anzahl,
       round(avg(r.stars), 2) AS sterne_mittel,
       round(100.0 * avg(CASE WHEN r.stars >= 4 THEN 1 ELSE 0 END), 1) AS anteil_positiv_pct
FROM burgermetrics.dim_product p LEFT JOIN burgermetrics.fact_reviews r USING (product_id)
GROUP BY p.product_id, p.product_name, p.category;

CREATE VIEW wawi.v_rezension_produkt AS
SELECT a.artikel_id, a.name, count(r.rezension_id) AS anzahl,
       round(avg(r.sterne), 2) AS sterne_mittel, max(r.erstellt_am) AS letzte
FROM wawi.artikel a LEFT JOIN wawi.rezension r USING (artikel_id)
GROUP BY a.artikel_id, a.name;

CREATE VIEW wawi.v_rezension_letzte AS
SELECT r.rezension_id, a.name AS artikel, r.sterne, r.inhalt, r.erstellt_am, r.quelle
FROM wawi.rezension r JOIN wawi.artikel a USING (artikel_id);
