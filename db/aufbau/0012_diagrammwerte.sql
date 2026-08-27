-- 0012_diagrammwerte.sql
--
-- Vier Werte standen noch als Zahl im Skript des Dashboards, weil sie nicht
-- Teil einer Datenreihe sind, sondern einzelne Markierungen in Diagrammen:
-- die Vergleichslinie beim Bestellwert je Filiale, die Basislinie bei der
-- Zufriedenheit je Aktion und die beiden hervorgehobenen Punkte in der
-- Monatskurve.
--
-- Drei davon lassen sich aus vorhandenen Reihen rechnen und wandern deshalb
-- nach reihen.js. Einer nicht: Die Basislinie der Zufriedenheit ist der
-- mittlere Zufriedenheitswert der Bestellungen OHNE Aktion. Diese Groesse
-- steht in keiner Sicht, weil bisher niemand danach gefragt hat. Sie kommt
-- hier dazu.
--
-- Warum das wichtig ist: Der Wert im Skript lautete 3.785 und war korrekt.
-- Der Wert daneben — die Beschriftung des COVID-Punktes — lautete "−62 %"
-- und war falsch; der tatsaechliche Rueckgang zum Vormonat betraegt 54,8
-- Prozent. Genau so altern eingetragene Zahlen: unbemerkt und einzeln.

SET search_path = burgermetrics, public;

-- v_kennzahl_zusatz kann zu diesem Zeitpunkt bereits materialisiert sein.
-- Deshalb erst die Art pruefen und passend abraeumen.
DO $$
DECLARE art char;
BEGIN
  SELECT c.relkind INTO art FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname = 'burgermetrics' AND c.relname = 'v_kennzahl_zusatz';
  IF art = 'v' THEN DROP VIEW burgermetrics.v_kennzahl_zusatz CASCADE;
  ELSIF art = 'm' THEN DROP MATERIALIZED VIEW burgermetrics.v_kennzahl_zusatz CASCADE;
  END IF;
END $$;

CREATE VIEW v_kennzahl_zusatz AS
WITH quartal AS (
  SELECT year AS jahr, quarter, sum(net_total) u FROM obt_orders
  WHERE year BETWEEN 2018 AND 2025 GROUP BY 1,2),
best AS (SELECT jahr, quarter, row_number() OVER (PARTITION BY jahr ORDER BY u DESC) rn FROM quartal),
spitze AS (SELECT quarter, count(*) n FROM best WHERE rn=1 GROUP BY 1 ORDER BY 2 DESC LIMIT 1)
SELECT 'artikel_je_bestellung' AS kennung, round(avg(distinct_items),2) AS wert,
       NULL::numeric AS vergleich, NULL::numeric AS anzahl, NULL::text AS text FROM fact_orders
UNION ALL SELECT 'stueck_je_bestellung', round(avg(item_count),2), NULL, NULL, NULL FROM fact_orders
UNION ALL SELECT 'spitzenquartal', NULL, 8, (SELECT n FROM spitze),
       (SELECT quarter || ' Peak' FROM spitze)
-- Die Basislinie: mittlere Zufriedenheit ohne Aktion, dazu die Zahl der
-- Bewertungen, auf denen sie beruht. Bestellungen ohne Bewertung bleiben
-- aussen vor — sonst waere es kein Mittelwert der Zufriedenheit, sondern
-- einer der Antwortbereitschaft.
UNION ALL SELECT 'zufriedenheit_ohne_aktion',
       round(avg(satisfaction_score)::numeric, 3),
       NULL,
       count(*),
       NULL
FROM   fact_orders
WHERE  promo_id = 0 AND satisfaction_score IS NOT NULL;

COMMENT ON VIEW v_kennzahl_zusatz IS
  'Einzelwerte, die zu keiner Reihe gehoeren. zufriedenheit_ohne_aktion ist '
  'die Vergleichsgroesse fuer das Zufriedenheitsdiagramm der Aktionen.';

GRANT SELECT ON v_kennzahl_zusatz TO anon, authenticated;
