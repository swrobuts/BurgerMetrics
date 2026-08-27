-- 0011_promotion_uplift.sql
--
-- Der "ROI" der Aktionen ist keine Messung, sondern eine Umformung des
-- Rabattsatzes. Nachgerechnet ueber alle neun Aktionen:
--
--     roi = umsatz / rabattsumme
--         = brutto * (1 - r) / (brutto * r)
--         = (1 - r) / r
--
-- Die brutto kuerzt sich weg. Uebrig bleibt eine Funktion allein des
-- Rabattsatzes — auf sechs Nachkommastellen exakt. Drei Aktionen mit
-- 10 Prozent Rabatt haben deshalb denselben "ROI" von 9,00, obwohl ihr
-- Bestellwert vor Rabatt zwischen 16,36 und 21,00 EUR liegt. Wer Aktionen
-- danach sortiert, sortiert sie nach dem Rabattsatz und nennt es Wirtschaft-
-- lichkeit.
--
-- Die Spalte bleibt, weil das Dashboard sie zeigt und der Fall lehrreich ist.
-- Daneben tritt die Groesse, die tatsaechlich etwas aussagt: der Bestellwert
-- VOR Abzug des Rabatts, gegen den Bestellwert ohne Aktion. Er beantwortet die
-- eigentliche Frage — kaufen Gaeste mit Aktion mehr ein als ohne?

SET search_path = burgermetrics, public;

DROP VIEW IF EXISTS v_promotion_roi CASCADE;
CREATE VIEW v_promotion_roi AS
WITH basis AS (
  SELECT avg(net_total) AS baseline_aov FROM fact_orders WHERE promo_id = 0)
SELECT p.aktion, p.art, p.rabatt_pct, p.bestellungen, p.umsatz, p.aov,
       p.zufriedenheit, p.rabattsumme,
       b.baseline_aov,
       -- Umformung des Rabattsatzes; siehe Kopf der Datei.
       p.umsatz / nullif(p.rabattsumme, 0)                       AS roi,
       -- Der Warenkorb, bevor der Rabatt greift.
       (p.umsatz + p.rabattsumme) / nullif(p.bestellungen, 0)    AS aov_vor_rabatt,
       -- Was die Aktion am Einkauf aendert: Warenkorb vor Rabatt gegen den
       -- Bestellwert ohne Aktion. Positiv heisst groesserer Einkauf.
       100.0 * (((p.umsatz + p.rabattsumme) / nullif(p.bestellungen, 0))
                - b.baseline_aov) / nullif(b.baseline_aov, 0)    AS uplift_pct,
       -- Und was davon nach dem Rabatt uebrig bleibt.
       100.0 * (p.aov - b.baseline_aov) / nullif(b.baseline_aov, 0)
                                                                 AS netto_pct
FROM   v_promotion p CROSS JOIN basis b
ORDER  BY uplift_pct DESC;

COMMENT ON VIEW v_promotion_roi IS
  'Aktionen mit Wirtschaftlichkeit. roi ist eine Umformung des Rabattsatzes '
  '((100-r)/r) und taugt nicht zum Vergleich; uplift_pct misst, ob der '
  'Warenkorb vor Rabatt groesser ausfaellt als ohne Aktion.';

GRANT SELECT ON v_promotion_roi TO anon, authenticated;
