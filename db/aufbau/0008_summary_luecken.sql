-- 0008_summary_luecken.sql
--
-- Zwei Sichten fuer die sechs breiten Karten der Management Summary.
-- Vier der sechs liessen sich aus vorhandenen Sichten rechnen; diese beiden
-- nicht, weil bisher keine Sicht Umsatz nach Altersgruppe und keine den
-- Wohnort des Kunden gegen den Bezirk der Filiale stellt.

SET search_path = burgermetrics, public;

-- ---------------------------------------------------------------------------
-- Umsatz je Altersgruppe
--
-- v_kunde_alter zaehlt nur Koepfe. Fuer die Aussage "umsatzstaerkste
-- Altersgruppe" braucht es den Umsatz. Beide Groessen stehen hier
-- nebeneinander, damit man den Unterschied sieht: die groesste Gruppe muss
-- nicht die umsatzstaerkste sein.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS v_alter_umsatz CASCADE;
CREATE VIEW v_alter_umsatz AS
SELECT c.age_group                                   AS altersgruppe,
       count(DISTINCT c.customer_id)                 AS kunden,
       count(o.order_id)                             AS bestellungen,
       sum(o.net_total)                              AS umsatz,
       round(100.0 * sum(o.net_total)
             / sum(sum(o.net_total)) OVER (), 2)     AS umsatzanteil_pct
FROM   dim_customer c
JOIN   fact_orders  o ON o.customer_id = c.customer_id
GROUP  BY c.age_group
ORDER  BY sum(o.net_total) DESC;

COMMENT ON VIEW v_alter_umsatz IS
  'Umsatz und Kundenzahl je Altersgruppe. Anteil bezogen auf den Gesamtumsatz.';

-- ---------------------------------------------------------------------------
-- Bestellungen aus dem Heimat-Stadtteil
--
-- Deckt sich der Wohnbezirk des Kunden mit dem Bezirk der Filiale, in der er
-- bestellt? Der Anteil beantwortet, ob die Standorte aus der Nachbarschaft
-- leben oder ueberregional ziehen. Gaeste ohne Kundenkonto bleiben aussen vor,
-- deshalb der INNER JOIN auf dim_customer.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS v_heimatbezirk CASCADE;
CREATE VIEW v_heimatbezirk AS
SELECT count(*)                                                   AS bestellungen,
       count(*) FILTER (WHERE c.home_district = b.district)        AS aus_heimatbezirk,
       round(100.0 * count(*) FILTER (WHERE c.home_district = b.district)
             / nullif(count(*), 0), 2)                             AS anteil_pct,
       count(DISTINCT b.district)                                  AS filialbezirke,
       count(DISTINCT c.home_district)                             AS wohnbezirke
FROM   fact_orders  o
JOIN   dim_customer c ON c.customer_id = o.customer_id
JOIN   dim_branch   b ON b.branch_id   = o.branch_id;

COMMENT ON VIEW v_heimatbezirk IS
  'Anteil der Bestellungen, bei denen Wohnbezirk des Kunden und Bezirk der '
  'Filiale uebereinstimmen. Nur Bestellungen mit Kundenbezug.';

GRANT SELECT ON v_alter_umsatz, v_heimatbezirk TO anon, authenticated;
