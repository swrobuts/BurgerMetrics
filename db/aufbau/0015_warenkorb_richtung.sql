-- 0015_warenkorb_richtung.sql
--
-- Die Konfidenz einer Assoziationsregel ist gerichtet. P(B | A) ist nicht
-- P(A | B) — das steht so auch im Begleittext des Dashboards: "Die Richtung
-- ist dabei nicht umkehrbar."
--
-- v_warenkorb_auswahl hielt sich nicht daran. Die Sicht waehlt fuenfzehn Paare
-- aus v_warenkorb_regeln aus und trifft sie im JOIN in beiden Reihenfolgen:
--
--     ON (r.produkt_a = p.a AND r.produkt_b = p.b)
--     OR (r.produkt_a = p.b AND r.produkt_b = p.a)
--
-- Angezeigt wurden danach aber p.a und p.b, also die Reihenfolge der von Hand
-- geschriebenen Auswahlliste, waehrend die Konfidenz aus r stammte. Bei drei
-- der fuenfzehn Paare ist die Regel andersherum gespeichert. Dort stand die
-- Konfidenz der Gegenrichtung:
--
--     angezeigt                      gezeigt   richtig
--     Cola 0.3l    → Medium Fries     24,5 %    32,4 %
--     Large Fries  → Medium Fries     15,6 %    30,6 %
--     Side Salad   → Medium Fries     15,4 %    30,9 %
--
-- Zweimal um den Faktor zwei daneben. Support, Lift und die gemeinsame Zahl
-- sind symmetrisch und waren richtig; nur die Konfidenz war betroffen.
--
-- Behoben, indem die Sicht die Richtung aus der Regel nimmt statt aus der
-- Auswahlliste. Die Auswahl nennt damit nur noch das Paar — was sie immer
-- schon meinte.
--
-- Diese Datei existiert getrennt von 0005, weil die Sichten auf dem Server
-- materialisiert sind: Ein CREATE OR REPLACE VIEW scheitert an einer
-- materialisierten Sicht. 0005 enthaelt dieselbe Korrektur, damit ein Neuaufbau
-- von vorn richtig ist.
--
-- Nach dieser Datei muss materialisieren.py laufen, sonst liest das Dashboard
-- weiter die alte materialisierte Fassung.

SET search_path = burgermetrics, public;

-- Kurznamen fuer die Achsenbeschriftung. Sie standen als vierte Spalte in der
-- Auswahlliste und mussten zur dort gewaehlten Reihenfolge passen. Als Funktion
-- koennen Etikett und Richtung nicht mehr auseinanderlaufen.
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
    ELSE name
  END;
$$ LANGUAGE sql IMMUTABLE;

GRANT EXECUTE ON FUNCTION kurzname(text) TO anon, authenticated;

-- Beide Formen abraeumen: Auf dem Server liegt eine materialisierte Sicht,
-- lokal nach einem frischen 0005 eine gewoehnliche.
DROP MATERIALIZED VIEW IF EXISTS v_warenkorb_auswahl;
DROP VIEW IF EXISTS v_warenkorb_auswahl;

CREATE VIEW v_warenkorb_auswahl AS
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
  (15,'Side Salad','Medium Fries'))
SELECT p.nr,
       kurzname(r.produkt_a) || '→' || kurzname(r.produkt_b) AS regel,
       r.produkt_a, r.produkt_b,
       r.gemeinsam, r.support_pct, r.konfidenz_pct, r.lift
FROM paare p
JOIN v_warenkorb_regeln r
  ON (r.produkt_a = p.a AND r.produkt_b = p.b)
  OR (r.produkt_a = p.b AND r.produkt_b = p.a)
ORDER BY p.nr;

COMMENT ON VIEW v_warenkorb_auswahl IS
  'Fuenfzehn kuratierte Produktpaare aus v_warenkorb_regeln. Die Richtung '
  'stammt aus der Regel, nicht aus der Auswahlliste — sonst gehoerte die '
  'Konfidenz zur Gegenrichtung.';

GRANT SELECT ON v_warenkorb_auswahl TO anon, authenticated;
