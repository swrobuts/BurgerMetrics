-- wawi_zu_analytisch.sql
-- Die Zusammenfuehrung: aus dem operativen 3NF-Modell (wawi_mini.sql) werden
-- per JOIN und Umbenennung die Tabellen des analytischen Galaxy-Schemas.
--
-- Das ist die stg-Schicht der Kette raw -> stg -> mart, auf das Wesentliche
-- verdichtet: typisieren entfaellt (schon typisiert), also bleiben zwei
-- Handgriffe je Zieltabelle sichtbar:
--   1. ZUSAMMENFUEHREN  - Verknuepfungen aufloesen, die die Auswertung
--                         nicht jedes Mal neu bezahlen soll
--   2. BENENNEN         - deutsche Betriebsbegriffe -> englisches
--                         Auswertungsvokabular der CSV-Dateien
--
-- Vorher wawi_mini.sql ausfuehren. Der Gleichheitsbeweis steht am Ende.

-- ── dim_product: drei Tabellen werden eine ─────────────────────────────────
-- Kategorie und Unterkategorie stehen danach redundant in jeder Produktzeile.
-- Genau das ist die Denormalisierung der Folie "Fuer die Auswertung wird die
-- Normalisierung zurueckgenommen".
CREATE OR REPLACE VIEW dim_product_neu AS
SELECT a.artikel_id        AS product_id,
       a.name              AS product_name,
       k.name              AS category,
       u.name              AS subcategory,
       a.vegetarisch       AS is_vegetarian,
       a.listenpreis       AS unit_price
FROM artikel a
JOIN artikelunterkategorie u USING (unterkategorie_id)
JOIN artikelkategorie      k USING (kategorie_id);

-- ── dim_branch: der Filialtyp wandert als Attribut in die Filialzeile ──────
CREATE OR REPLACE VIEW dim_branch_neu AS
SELECT f.filiale_id        AS branch_id,
       f.name              AS branch_name,
       f.stadtteil         AS district,
       t.name              AS branch_type,
       f.hat_drive_through AS has_drive_through,
       f.eroeffnet_am      AS opening_date,
       f.monatsmiete       AS monthly_rent_eur,
       f.sitzplaetze_innen AS seats_indoor
FROM filiale f
JOIN filialtyp t USING (filialtyp_id);

-- ── dim_customer: die Loyalty-Stufe wird zum Textattribut ──────────────────
CREATE OR REPLACE VIEW dim_customer_neu AS
SELECT k.kunde_id          AS customer_id,
       k.altersgruppe      AS age_group,
       k.geschlecht        AS gender,
       k.heimat_stadtteil  AS home_district,
       k.hat_app           AS has_app,
       l.name              AS loyalty_tier
FROM kunde k
JOIN loyalty_stufe l ON l.stufe_id = k.loyalty_stufe_id;

-- ── dim_payment_method: nur Umbenennung ────────────────────────────────────
CREATE OR REPLACE VIEW dim_payment_method_neu AS
SELECT zahlungsart_id      AS payment_id,
       bezeichnung         AS payment_type,
       anbieter            AS payment_provider
FROM zahlungsart;

-- ── dim_promotion: aus operativem NULL wird eine echte Dimensionszeile ─────
-- Operativ heisst "keine Aktion" schlicht NULL am Beleg. Ein Stern-Schema
-- will aber verknuepfen koennen, ohne Zeilen zu verlieren - deshalb bekommt
-- "No Promotion" eine eigene Zeile mit der Kennung 0.
CREATE OR REPLACE VIEW dim_promotion_neu AS
SELECT 0 AS promo_id, 'No Promotion' AS promo_name, 'None' AS promo_type, 0 AS discount_pct
UNION ALL
SELECT p.promotion_id, p.name, t.name, p.rabatt_pct
FROM promotion p
JOIN promotionstyp t USING (promotionstyp_id);

-- ── dim_date: die Zeitdimension wird GENERIERT, nicht uebernommen ──────────
-- Es gibt keine operative Kalendertabelle; sie entsteht aus den Bestelldaten.
CREATE OR REPLACE VIEW dim_date_neu AS
SELECT DISTINCT
       bestelldatum                            AS date,
       EXTRACT(year FROM bestelldatum)::INT    AS year,
       'Q' || EXTRACT(quarter FROM bestelldatum)::INT AS quarter,
       EXTRACT(month FROM bestelldatum)::INT   AS month,
       monthname(bestelldatum)                 AS month_name,
       dayname(bestelldatum)                   AS day_name,
       EXTRACT(isodow FROM bestelldatum) >= 6  AS is_weekend,
       CASE WHEN EXTRACT(month FROM bestelldatum) IN (3,4,5)   THEN 'Spring'
            WHEN EXTRACT(month FROM bestelldatum) IN (6,7,8)   THEN 'Summer'
            WHEN EXTRACT(month FROM bestelldatum) IN (9,10,11) THEN 'Autumn'
            ELSE 'Winter' END                  AS season
FROM kundenbestellung;

-- ── fact_orders: Bestellkopf + Rechnungsnachweis, Stunde wird abgeleitet ───
CREATE OR REPLACE VIEW fact_orders_neu AS
SELECT b.bestellung_id                        AS order_id,
       b.bestelldatum                         AS date,
       EXTRACT(hour FROM b.bestellzeit)::INT  AS hour,
       b.filiale_id                           AS branch_id,
       b.kunde_id                             AS customer_id,
       b.zahlungsart_id                       AS payment_id,
       COALESCE(b.promotion_id, 0)            AS promo_id,
       b.bestellkanal                         AS order_channel,
       b.artikel_anzahl                       AS item_count,
       b.brutto_gesamt                        AS gross_total,
       b.rabatt_betrag                        AS discount_amount,
       b.netto_gesamt                         AS net_total,
       b.bestelldauer_min                     AS order_duration_min,
       b.zufriedenheit                        AS satisfaction_score
FROM kundenbestellung b
JOIN rechnung r USING (bestellung_id);     -- 1:1; sichert: nur fakturierte Belege

-- ── fact_order_items: nur Umbenennung — der Grain bleibt die Position ──────
CREATE OR REPLACE VIEW fact_order_items_neu AS
SELECT position_id         AS order_item_id,
       bestellung_id       AS order_id,
       artikel_id          AS product_id,
       menge               AS quantity,
       einzelpreis         AS unit_price,
       positionsbetrag     AS line_total
FROM bestellposition;

-- ── Gleichheitsbeweis ──────────────────────────────────────────────────────
-- Nach zusaetzlichem Laden von burgermetrics_mini.sql muss jede der acht
-- Pruefungen 0 liefern (symmetrische Differenz der Zeilenmengen):
--
--   SELECT count(*) FROM ((SELECT * FROM dim_product_neu EXCEPT SELECT * FROM dim_product)
--                  UNION ALL (SELECT * FROM dim_product EXCEPT SELECT * FROM dim_product_neu)) t;
--
-- ... und analog fuer dim_branch, dim_customer, dim_payment_method,
-- dim_promotion, dim_date, fact_orders, fact_order_items.
