-- 0010_filiale_tabellenspalten.sql
--
-- Die beiden Filialtabellen des Dashboards (Scorecard und Standortvergleich)
-- zeigen Drive-Through, Sitzplaetze und die Mietquote. Die ersten beiden
-- standen bisher nur im HTML, weil v_filiale sie nicht fuehrte; die Mietquote
-- wurde gar nicht gerechnet. Damit die Tabellen aus der Datenbank kommen
-- koennen, muessen die Spalten hier stehen.
--
-- mietquote = Jahresmiete / Jahresumsatz. Bezugsjahr ist das letzte
-- vollstaendige Jahr (2025); die Miete ist ein Monatswert im Stammsatz, der
-- Umsatz in v_filiale dagegen kumuliert ueber die ganze Historie — die beiden
-- direkt ins Verhaeltnis zu setzen waere falsch.

SET search_path = burgermetrics, public;

DROP VIEW IF EXISTS v_filiale CASCADE;
CREATE VIEW v_filiale AS
WITH jahr AS (
  SELECT branch_id, sum(net_total) AS umsatz_2025
  FROM   fact_orders
  WHERE  extract(year FROM date) = 2025
  GROUP  BY branch_id)
SELECT b.branch_id, b.branch_name, b.district, b.branch_type, b.size_sqm,
       b.opening_date, b.monthly_rent_eur,
       b.has_drive_through,
       b.seats_indoor, b.seats_outdoor,
       b.seats_indoor + b.seats_outdoor                AS sitzplaetze,
       count(*)                                        AS bestellungen,
       sum(o.net_total)                                AS umsatz,
       avg(o.net_total)                                AS aov,
       avg(o.satisfaction_score)                       AS zufriedenheit,
       2026 - extract(year FROM b.opening_date)::int   AS betriebsjahre,
       sum(o.net_total) / nullif(b.size_sqm, 0)        AS umsatz_je_qm,
       j.umsatz_2025,
       100.0 * (b.monthly_rent_eur * 12)
             / nullif(j.umsatz_2025, 0)                AS mietquote_pct
FROM   fact_orders o
JOIN   dim_branch  b USING (branch_id)
LEFT   JOIN jahr   j USING (branch_id)
GROUP  BY b.branch_id, b.branch_name, b.district, b.branch_type, b.size_sqm,
         b.opening_date, b.monthly_rent_eur, b.has_drive_through,
         b.seats_indoor, b.seats_outdoor, j.umsatz_2025
ORDER  BY umsatz DESC;

COMMENT ON VIEW v_filiale IS
  'Filialen mit Leistungs- und Stammdaten. mietquote_pct bezieht die Jahresmiete '
  'auf den Umsatz 2025, dem letzten vollstaendigen Jahr.';

GRANT SELECT ON v_filiale TO anon, authenticated;
