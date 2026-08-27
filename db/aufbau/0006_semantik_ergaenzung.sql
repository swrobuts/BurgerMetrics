-- 0006_semantik_ergaenzung.sql
-- Zweck: vier Sichten, die das Dashboard braucht und die in 0005 fehlten.
-- Ruecknahme: DROP VIEW burgermetrics.v_rfm_segment, v_kanal_stunde,
--             v_wetter_regen, v_promotion_roi;
-- Idempotent: ja.

SET search_path TO burgermetrics;

-- ── RFM-Segmentierung ──────────────────────────────────────────────────────
-- Die Segmentgroessen des alten Dashboards liessen sich mit keiner Regel
-- nachrechnen (es behauptete 4.396 "Verlorene" mit im Mittel 249 Tagen
-- Inaktivitaet; im Bestand gibt es nur 2.042 Kunden mit mehr als 180 Tagen).
-- Diese Sicht rechnet deshalb neu, nach offengelegten Schwellen:
--
--   Stichtag       = 31.03.2026, der letzte Tag des Bestands
--   R (Recency)    = Tage seit dem letzten Kauf, Quintil 5 = juengster Kauf
--   F (Frequency)  = Zahl der Bestellungen, Quintil 5 = haeufigster Kaeufer
--   M (Monetary)   = Summe net_total, Quintil 5 = hoechster Umsatz
--
-- Segmentregeln (in dieser Reihenfolge geprueft, erste Zuordnung gewinnt):
--   Champions           R >= 4 und F >= 4   zuletzt aktiv, kauft oft
--   Loyal               R >= 3 und F >= 3   regelmaessig, etwas laenger her
--   Potenzial           R >= 4 und F >= 2   zuletzt aktiv, noch ausbaufaehig
--   Neukunden           R >= 4 und F  = 1   zuletzt aktiv, kauft erst selten
--   Schlaefer           R  = 3              laesst nach
--   Abwanderungsgefahr  R  = 2              deutlich nachgelassen
--   Verloren            R  = 1              seit langem nicht mehr da
CREATE OR REPLACE VIEW v_rfm_kunde AS
WITH basis AS (
  SELECT customer_id,
         (DATE '2026-03-31' - max(date))::int AS recency_tage,
         count(*)::int                        AS frequenz,
         sum(net_total)                       AS monetaer,
         min(date)                            AS erste_bestellung
  FROM fact_orders GROUP BY 1),
bewertet AS (
  SELECT *,
         6 - ntile(5) OVER (ORDER BY recency_tage) AS r_wert,
         ntile(5) OVER (ORDER BY frequenz)         AS f_wert,
         ntile(5) OVER (ORDER BY monetaer)         AS m_wert
  FROM basis)
SELECT customer_id, recency_tage, frequenz, monetaer, erste_bestellung,
       r_wert, f_wert, m_wert,
       CASE
         WHEN r_wert >= 4 AND f_wert >= 4 THEN 'Champions'
         WHEN r_wert >= 3 AND f_wert >= 3 THEN 'Loyal'
         WHEN r_wert >= 4 AND f_wert >= 2 THEN 'Potenzial'
         WHEN r_wert >= 4                 THEN 'Neukunden'
         WHEN r_wert  = 3                 THEN 'Schläfer'
         WHEN r_wert  = 2                 THEN 'Abwanderungsgefahr'
         ELSE                                  'Verloren'
       END AS segment
FROM bewertet;

CREATE OR REPLACE VIEW v_rfm_segment AS
SELECT segment,
       count(*)                                   AS kunden,
       100.0 * count(*) / sum(count(*)) OVER ()    AS anteil_pct,
       round(avg(recency_tage))                    AS recency_tage,
       round(avg(frequenz), 1)                     AS frequenz,
       round(avg(monetaer))                        AS lebenswert,
       sum(monetaer)                               AS umsatz_gesamt
FROM v_rfm_kunde GROUP BY 1 ORDER BY umsatz_gesamt DESC;

-- ── Kanalanteile im Tagesverlauf ───────────────────────────────────────────
CREATE OR REPLACE VIEW v_kanal_stunde AS
WITH je AS (SELECT hour AS stunde, order_channel AS kanal, count(*) AS bestellungen
            FROM fact_orders GROUP BY 1,2)
SELECT stunde, kanal, bestellungen,
       100.0 * bestellungen / sum(bestellungen) OVER (PARTITION BY stunde) AS anteil_pct
FROM je ORDER BY stunde, kanal;

-- ── Niederschlagsklassen ───────────────────────────────────────────────────
CREATE OR REPLACE VIEW v_wetter_regen AS
WITH tage AS (
  SELECT o.date, max(w.precipitation_mm) AS regen,
         sum(o.net_total) AS umsatz, count(*) AS bestellungen
  FROM fact_orders o JOIN dim_weather w USING (date) GROUP BY 1)
SELECT CASE WHEN regen = 0 THEN '0mm' WHEN regen < 2 THEN '0-2mm'
            WHEN regen < 5 THEN '2-5mm' WHEN regen < 10 THEN '5-10mm'
            ELSE '>10mm' END AS klasse,
       CASE WHEN regen = 0 THEN 1 WHEN regen < 2 THEN 2
            WHEN regen < 5 THEN 3 WHEN regen < 10 THEN 4 ELSE 5 END AS nr,
       count(*) AS tage, avg(umsatz) AS umsatz_je_tag, avg(bestellungen) AS bestellungen_je_tag
FROM tage GROUP BY 1,2 ORDER BY nr;

-- ── Aktionen mit Wirtschaftlichkeit ────────────────────────────────────────
-- ROI = Umsatz je eingesetztem Rabatt-Euro. Die Formel ist aus den Werten des
--       alten Dashboards zurueckgerechnet und trifft alle neun Aktionen exakt
--       (Student 11,5x, Birthday 3,0x). Sie misst die Hebelwirkung, nicht den
--       Zusatzumsatz: Ein niedriger Rabattsatz erzeugt zwangslaeufig einen
--       hohen Wert. baseline_aov (19,45 EUR) steht daneben, damit sichtbar
--       bleibt, dass Aktionsbestellungen im Mittel KLEINER sind als andere.
CREATE OR REPLACE VIEW v_promotion_roi AS
WITH basis AS (SELECT avg(net_total) AS baseline_aov FROM fact_orders WHERE promo_id = 0)
SELECT p.aktion, p.art, p.rabatt_pct, p.bestellungen, p.umsatz, p.aov,
       p.zufriedenheit, p.rabattsumme, b.baseline_aov,
       p.umsatz / nullif(p.rabattsumme, 0) AS roi
FROM v_promotion p CROSS JOIN basis b ORDER BY p.bestellungen DESC;

GRANT SELECT ON ALL TABLES IN SCHEMA burgermetrics TO anon, authenticated;

-- v_filiale um die Betriebsjahre ergaenzen: volle Jahre seit Eroeffnung,
-- bezogen auf das Ende des Bestands. Traegt die Normierung, ohne die
-- absolute Filialumsaetze in die Irre fuehren (Basiseffekt).
DROP VIEW IF EXISTS v_filiale CASCADE;
CREATE VIEW v_filiale AS
SELECT b.branch_id, b.branch_name, b.district, b.branch_type, b.size_sqm,
       b.opening_date, b.monthly_rent_eur,
       count(*)         AS bestellungen,
       sum(o.net_total) AS umsatz,
       avg(o.net_total) AS aov,
       avg(o.satisfaction_score) AS zufriedenheit,
       2026 - extract(year FROM b.opening_date)::int AS betriebsjahre,
       sum(o.net_total) / nullif(b.size_sqm, 0)      AS umsatz_je_qm
FROM fact_orders o JOIN dim_branch b USING (branch_id)
GROUP BY b.branch_id, b.branch_name, b.district, b.branch_type, b.size_sqm,
         b.opening_date, b.monthly_rent_eur
ORDER BY umsatz DESC;
GRANT SELECT ON ALL TABLES IN SCHEMA burgermetrics TO anon, authenticated;
