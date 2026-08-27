-- 0013_operative_sichten.sql
--
-- Speisekarte und Filialliste fuer Online-Shop und Kasse.
--
-- Anlass: Beide Oberflaechen trugen ihren Artikelstamm als Liste im Quelltext
-- — 33 Artikel je Seite, mit Preisen. Der Abgleich gegen dim_product ergab:
-- KEIN einziger Preis stimmte, weder mit dem Preis von 2017 noch mit dem
-- aktuellen. 13 Artikel der Kasse und 3 des Shops gibt es im Datenmodell gar
-- nicht.
--
-- Das ist nicht nur unsauber. Die Fallstudie behauptet, Shop und Kasse
-- teilten sich denselben Artikelstamm — das ist der Kern der Folie
-- "Beide Anwendungen schreiben in denselben Kern". Solange die Kataloge
-- auseinanderlaufen, ist die Behauptung falsch.
--
-- Was hier NICHT steht und bewusst in den Seiten bleibt: Produktbilder,
-- Beschreibungstexte und Oeffnungszeiten. Sie sind nicht Teil des
-- Datenmodells, und sie hineinzuschreiben, nur damit alles aus einer Quelle
-- kommt, waere der umgekehrte Fehler. Wo eine Seite etwas zeigt, das die
-- Datenbank nicht kennt, gehoert das dorthin, wo es gebraucht wird — und
-- sichtbar getrennt von dem, was gemessen ist.

SET search_path = burgermetrics, public;

-- ---------------------------------------------------------------------------
-- Speisekarte: der Artikelstamm, wie ihn eine Verkaufsoberflaeche braucht.
-- unit_price ist der heutige Preis; base_price_2017 steht daneben, damit die
-- Preisentwicklung im Unterricht sichtbar gemacht werden kann, ohne eine
-- zweite Abfrage.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS v_speisekarte CASCADE;
CREATE VIEW v_speisekarte AS
SELECT p.product_id                       AS artikel_id,
       p.product_name                     AS name,
       p.category                         AS kategorie,
       p.subcategory                      AS unterkategorie,
       p.unit_price                       AS preis,
       p.base_price_2017                  AS preis_2017,
       p.calories                         AS kalorien,
       p.is_vegetarian                    AS vegetarisch,
       p.is_vegan                         AS vegan,
       p.allergens                        AS allergene,
       p.introduced                       AS gelistet_seit
FROM   dim_product p
ORDER  BY p.category, p.product_name;

COMMENT ON VIEW v_speisekarte IS
  'Artikelstamm fuer Shop und Kasse. Bilder und Beschreibungen sind nicht '
  'Teil des Datenmodells und stehen in den Seiten.';

-- ---------------------------------------------------------------------------
-- Filialliste: die Standorte, wie sie eine Kundenoberflaeche zeigt.
-- Oeffnungszeiten fehlen im Datenmodell — sie stehen deshalb in der Seite.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS v_filialliste CASCADE;
CREATE VIEW v_filialliste AS
SELECT b.branch_id                        AS filiale_id,
       b.branch_name                      AS name,
       b.address                          AS adresse,
       b.district                         AS bezirk,
       b.postal_code                      AS plz,
       b.city                             AS ort,
       b.latitude                         AS breite,
       b.longitude                        AS laenge,
       b.branch_type                      AS art,
       b.has_drive_through                AS drive_through,
       b.has_playground                   AS spielplatz,
       b.parking_spots                    AS parkplaetze,
       b.seats_indoor + b.seats_outdoor   AS sitzplaetze,
       b.opening_date                     AS eroeffnet
FROM   dim_branch b
ORDER  BY b.branch_id;

COMMENT ON VIEW v_filialliste IS
  'Standortliste fuer den Online-Shop. Oeffnungszeiten sind nicht Teil des '
  'Datenmodells und stehen in der Seite.';

GRANT SELECT ON v_speisekarte, v_filialliste TO anon, authenticated;
