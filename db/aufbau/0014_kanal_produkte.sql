-- 0014_kanal_produkte.sql
--
-- Die meistbestellten Artikel je Bestellkanal.
--
-- Anlass: Im Dashboard stand unter der Ueberschrift "Top-5 Produkte je Kanal —
-- Bestellpraeferenzen unterscheiden sich deutlich" eine Liste aus zwanzig fest
-- eingetragenen Produktnamen. Die Unterzeile nannte sie selbst "Musterdaten".
-- Drei der vier Spalten waren zeichengleich; die Ueberschrift behauptete also
-- einen Unterschied, den ihre eigene Tabelle widerlegte.
--
-- Diese Sicht ersetzt die Liste. Sie beantwortet dieselbe Frage aus dem
-- Bestand — und das Ergebnis ist ein anderes als die Behauptung: Die Kanaele
-- aehneln sich in ihren Spitzenartikeln stark. Genau das ist der Befund, und
-- er gehoert in die Ueberschrift, nicht sein Gegenteil.
--
-- Rang nach Stueckzahl, weil die Ueberschrift von Bestellhaeufigkeit spricht.
-- product_id bricht Gleichstaende, damit die Reihenfolge zwischen zwei
-- Abfragen dieselbe bleibt — dieselbe Vorsichtsmassnahme wie bei den
-- RFM-Quintilen in 0009.

SET search_path = burgermetrics, public;

DROP VIEW IF EXISTS v_kanal_produkt CASCADE;
CREATE VIEW v_kanal_produkt AS
WITH je_kanal AS (
  SELECT o.order_channel        AS kanal,
         p.product_name         AS produkt,
         p.product_id,
         sum(i.quantity)        AS menge,
         count(*)               AS positionen
  FROM   fact_orders      o
  JOIN   fact_order_items i ON i.order_id   = o.order_id
  JOIN   dim_product      p ON p.product_id = i.product_id
  GROUP  BY 1, 2, 3
),
rang AS (
  SELECT kanal, produkt, menge, positionen,
         row_number() OVER (PARTITION BY kanal
                            ORDER BY menge DESC, product_id) AS rang,
         -- Anteil an allen Stueck des Kanals: erst er macht die Zahl
         -- zwischen unterschiedlich grossen Kanaelen vergleichbar.
         100.0 * menge / sum(menge) OVER (PARTITION BY kanal) AS anteil_pct
  FROM   je_kanal
)
SELECT kanal, rang, produkt, menge, positionen, round(anteil_pct, 2) AS anteil_pct
FROM   rang
WHERE  rang <= 5
ORDER  BY kanal, rang;

COMMENT ON VIEW v_kanal_produkt IS
  'Die fuenf meistbestellten Artikel je Bestellkanal, nach Stueckzahl. '
  'Ersetzt die fruehere Musterdatenliste im Dashboard.';

GRANT SELECT ON v_kanal_produkt TO anon, authenticated;
