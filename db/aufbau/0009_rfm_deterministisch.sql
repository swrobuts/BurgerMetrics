-- 0009_rfm_deterministisch.sql
--
-- v_rfm_kunde lieferte bei jeder Abfrage leicht andere Segmentgroessen:
-- Champions schwankten zwischen 4.179 und 4.187, Loyal zwischen 5.037 und
-- 5.051. Vier Abfragen hintereinander, vier Ergebnisse.
--
-- Ursache ist ntile(). Die Funktion fuellt fuenf gleich grosse Faecher und
-- muss dafuer auch dort trennen, wo Werte gleich sind: 24.992 Kunden
-- verteilen sich auf gut 100 verschiedene Bestellhaeufigkeiten, an jeder
-- Quintilsgrenze stehen also hunderte Kunden mit identischem Wert. Welche
-- davon ins vierte und welche ins fuenfte Fach fallen, entscheidet die
-- Reihenfolge, in der die Zeilen ankommen — und die haengt bei parallelem
-- Scan vom Zufall ab. Die Segmentgrenzen selbst sind stabil; nur die
-- Zuordnung der Gleichstaende wankt.
--
-- Ein Zweitschluessel in der ORDER BY macht die Reihenfolge eindeutig.
-- customer_id ist dafuer geeignet: eindeutig, unveraenderlich, ohne
-- Zusammenhang mit den drei Kennzahlen. Die Gleichstaende werden damit nicht
-- besser aufgeloest, aber immer gleich — und darauf kommt es an, wenn eine
-- Segmentgroesse in Folien steht und nachpruefbar sein soll.

SET search_path = burgermetrics, public;

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
         -- customer_id bricht Gleichstaende immer gleich auf.
         6 - ntile(5) OVER (ORDER BY recency_tage, customer_id) AS r_wert,
         ntile(5) OVER (ORDER BY frequenz,     customer_id)     AS f_wert,
         ntile(5) OVER (ORDER BY monetaer,     customer_id)     AS m_wert
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

COMMENT ON VIEW v_rfm_kunde IS
  'RFM je Kunde. Quintile ueber ntile(5) mit customer_id als Zweitschluessel, '
  'damit Gleichstaende reproduzierbar zugeordnet werden. Stichtag 2026-03-31.';
