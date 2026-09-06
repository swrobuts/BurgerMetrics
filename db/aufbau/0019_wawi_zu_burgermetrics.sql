-- 0019_wawi_zu_burgermetrics.sql
-- Zweck: der ETL-Schritt vom operativen Modell ins Galaxy-Schema — als
--        laufender Weg, nicht als Behauptung.
--
--        dataset/wawi_zu_analytisch.sql zeigt die Abbildung an 19 Belegen.
--        Hier steht dieselbe Abbildung als stg-Sichten ueber dem ganzen
--        Bestand, dazu eine Ladefunktion, die neue Belege nach burgermetrics
--        uebernimmt, eine Probe, die beide Seiten zeilengleich vergleicht,
--        und ein Aufraeumen fuer die Uebungsbestellungen.
--
--        Was der Schritt NICHT tut: Er laeuft nicht von allein. Das Dashboard
--        zeigt den kuratierten Bestand (754.513 Belege), und jede Uebung
--        wuerde seine Zahlen veraendern. Die Uebernahme ist deshalb ein
--        bewusster Aufruf durch postgres — genau wie ein naechtlicher
--        Ladelauf in einem echten Betrieb ein geplanter Schritt ist.
--
-- Aufruf (als postgres):
--   SELECT * FROM burgermetrics.uebernahme_aus_wawi();     -- neue Belege laden
--   SELECT * FROM wawi.etl_probe();                        -- 0 und 0 je Tabelle
--   SELECT * FROM wawi.uebungsbestellungen_loeschen();     -- Uebung zuruecksetzen
--   python3 db/materialisieren.py --neu                    -- Sichten auffrischen
--
-- Objekte: wawi.stg_dim_date, wawi.stg_fact_orders, wawi.stg_fact_order_items,
--          burgermetrics.uebernahme_aus_wawi(), wawi.etl_probe(),
--          wawi.uebungsbestellungen_loeschen().
-- Ruecknahme: DROP FUNCTION ...; DROP VIEW wawi.stg_*;
-- Idempotent: ja.

SET search_path TO wawi, burgermetrics;

-- ---------------------------------------------------------------------------
-- stg: Die Zusammenfuehrung, lesbar. Deutsche Betriebsbegriffe werden zum
-- englischen Auswertungsvokabular, Verknuepfungen werden aufgeloest.
-- ---------------------------------------------------------------------------

-- Bestellkopf + Rechnungsnachweis. Der JOIN auf rechnung sichert: nur
-- fakturierte Belege. Aus operativem NULL (keine Aktion) wird promo_id 0.
CREATE OR REPLACE VIEW wawi.stg_fact_orders AS
SELECT b.bestellung_id                          AS order_id,
       b.bestelldatum                           AS date,
       b.bestellzeit                            AS time,
       extract(hour FROM b.bestellzeit)::int    AS hour,
       b.filiale_id                             AS branch_id,
       b.kunde_id                               AS customer_id,
       b.zahlungsart_id                         AS payment_id,
       COALESCE(b.promotion_id, 0)              AS promo_id,
       b.bestellkanal                           AS order_channel,
       b.artikel_anzahl                         AS item_count,
       (SELECT count(*) FROM wawi.bestellposition p
         WHERE p.bestellung_id = b.bestellung_id)::int AS distinct_items,
       b.brutto_gesamt                          AS gross_total,
       b.rabatt_betrag                          AS discount_amount,
       b.netto_gesamt                           AS net_total,
       b.bestelldauer_min                       AS order_duration_min,
       b.zufriedenheit                          AS satisfaction_score,
       b.quelle
FROM   wawi.kundenbestellung b
JOIN   wawi.rechnung r USING (bestellung_id);

-- Positionen: nur Umbenennung, der Grain bleibt die Position.
CREATE OR REPLACE VIEW wawi.stg_fact_order_items AS
SELECT p.position_id        AS order_item_id,
       p.bestellung_id      AS order_id,
       p.artikel_id         AS product_id,
       p.menge              AS quantity,
       p.einzelpreis        AS unit_price,
       p.positionsbetrag    AS line_total
FROM   wawi.bestellposition p;

-- Zeitdimension: Es gibt keine operative Kalendertabelle; die Zeile fuer
-- einen neuen Tag wird aus dem Bestelldatum erzeugt. Feiertage und
-- Sonderereignisse kann das Datum allein nicht wissen — sie bleiben leer und
-- werden, wie im Bestand, redaktionell gepflegt.
CREATE OR REPLACE VIEW wawi.stg_dim_date AS
SELECT DISTINCT
       to_char(b.bestelldatum, 'YYYYMMDD')::bigint        AS date_id,
       b.bestelldatum                                    AS date,
       extract(year FROM b.bestelldatum)::int            AS year,
       'Q' || extract(quarter FROM b.bestelldatum)::int  AS quarter,
       extract(month FROM b.bestelldatum)::int           AS month,
       to_char(b.bestelldatum, 'FMMonth')                AS month_name,
       extract(week FROM b.bestelldatum)::int            AS calendar_week,
       extract(day FROM b.bestelldatum)::int             AS day_of_month,
       extract(isodow FROM b.bestelldatum)::int          AS day_of_week,
       to_char(b.bestelldatum, 'FMDay')                  AS day_name,
       extract(isodow FROM b.bestelldatum) >= 6          AS is_weekend,
       false                                             AS is_holiday,
       NULL::text                                        AS holiday_name,
       NULL::text                                        AS special_event,
       CASE WHEN extract(month FROM b.bestelldatum) IN (3, 4, 5)   THEN 'Spring'
            WHEN extract(month FROM b.bestelldatum) IN (6, 7, 8)   THEN 'Summer'
            WHEN extract(month FROM b.bestelldatum) IN (9, 10, 11) THEN 'Autumn'
            ELSE 'Winter' END                            AS season
FROM   wawi.kundenbestellung b
WHERE  NOT EXISTS (SELECT 1 FROM burgermetrics.dim_date d WHERE d.date = b.bestelldatum);

-- ---------------------------------------------------------------------------
-- Laden: alles, was in wawi fakturiert ist und in burgermetrics noch fehlt.
-- Nur Einfuegen, nie Aendern — der Bestand ist ein Abzug, kein Strom.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION burgermetrics.uebernahme_aus_wawi()
RETURNS TABLE (neue_tage integer, neue_bestellungen integer, neue_positionen integer)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = burgermetrics, wawi, pg_temp
AS $$
DECLARE
  n_tage integer; n_best integer; n_pos integer;
BEGIN
  INSERT INTO burgermetrics.dim_date
        (date_id, date, year, quarter, month, month_name, calendar_week, day_of_month,
         day_of_week, day_name, is_weekend, is_holiday, holiday_name, special_event, season)
  SELECT s.date_id, s.date, s.year, s.quarter, s.month, s.month_name, s.calendar_week,
         s.day_of_month, s.day_of_week, s.day_name, s.is_weekend, s.is_holiday,
         s.holiday_name, s.special_event, s.season
  FROM   wawi.stg_dim_date s;
  GET DIAGNOSTICS n_tage = ROW_COUNT;

  INSERT INTO burgermetrics.fact_orders
        (order_id, date, time, hour, branch_id, customer_id, payment_id, promo_id,
         order_channel, item_count, distinct_items, gross_total, discount_amount,
         net_total, order_duration_min, satisfaction_score)
  SELECT s.order_id, s.date, s.time, s.hour, s.branch_id, s.customer_id, s.payment_id,
         s.promo_id, s.order_channel, s.item_count, s.distinct_items, s.gross_total,
         s.discount_amount, s.net_total, s.order_duration_min, s.satisfaction_score
  FROM   wawi.stg_fact_orders s
  WHERE  NOT EXISTS (SELECT 1 FROM burgermetrics.fact_orders o WHERE o.order_id = s.order_id)
  ORDER  BY s.order_id;
  GET DIAGNOSTICS n_best = ROW_COUNT;

  INSERT INTO burgermetrics.fact_order_items
        (order_item_id, order_id, product_id, quantity, unit_price, line_total)
  SELECT s.order_item_id, s.order_id, s.product_id, s.quantity, s.unit_price, s.line_total
  FROM   wawi.stg_fact_order_items s
  WHERE  NOT EXISTS (SELECT 1 FROM burgermetrics.fact_order_items i
                     WHERE i.order_item_id = s.order_item_id)
    AND  EXISTS (SELECT 1 FROM burgermetrics.fact_orders o WHERE o.order_id = s.order_id)
  ORDER  BY s.order_item_id;
  GET DIAGNOSTICS n_pos = ROW_COUNT;

  RETURN QUERY SELECT n_tage, n_best, n_pos;
END $$;

COMMENT ON FUNCTION burgermetrics.uebernahme_aus_wawi IS
  'ETL wawi -> burgermetrics: fehlende Kalendertage, Bestellungen und Positionen '
  'einfuegen. Danach materialisieren.py --neu, sonst zeigt das Dashboard den alten Stand.';

-- ---------------------------------------------------------------------------
-- Probe: die symmetrische Differenz der Zeilenmengen, wie im Mini — aber
-- ueber den ganzen Bestand. Beide Zahlen muessen 0 sein. Vor einer
-- Uebernahme zeigt nur_in_wawi, wie viele Belege noch nicht im Warehouse
-- sind; nur_in_burgermetrics muss immer 0 sein.
-- Verglichen werden die Spalten, die den Weg in beide Richtungen ueberleben;
-- distinct_items und time koennen im CSV-Bestand anders belegt sein und
-- stehen deshalb nicht in der Probe.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION wawi.etl_probe()
RETURNS TABLE (tabelle text, nur_in_wawi bigint, nur_in_burgermetrics bigint)
LANGUAGE sql
SECURITY DEFINER
SET search_path = wawi, burgermetrics, pg_temp
AS $$
  WITH w AS (SELECT order_id, date, hour, branch_id, customer_id, payment_id, promo_id,
                    order_channel, item_count, gross_total, discount_amount, net_total,
                    order_duration_min, satisfaction_score
             FROM wawi.stg_fact_orders),
       b AS (SELECT order_id, date, hour, branch_id, customer_id, payment_id, promo_id,
                    order_channel, item_count, gross_total, discount_amount, net_total,
                    order_duration_min, satisfaction_score
             FROM burgermetrics.fact_orders)
  SELECT 'fact_orders'::text,
         (SELECT count(*) FROM (SELECT * FROM w EXCEPT SELECT * FROM b) x),
         (SELECT count(*) FROM (SELECT * FROM b EXCEPT SELECT * FROM w) x)
  UNION ALL
  SELECT 'fact_order_items',
         (SELECT count(*) FROM (SELECT * FROM wawi.stg_fact_order_items
                                EXCEPT SELECT * FROM burgermetrics.fact_order_items) x),
         (SELECT count(*) FROM (SELECT * FROM burgermetrics.fact_order_items
                                EXCEPT SELECT * FROM wawi.stg_fact_order_items) x);
$$;

-- ---------------------------------------------------------------------------
-- Aufraeumen: alle Uebungsbestellungen entfernen — aus dem Warehouse, falls
-- sie uebernommen wurden, und aus dem operativen Schema. Der Bestand
-- (quelle = 'bestand') bleibt unberuehrt.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION wawi.uebungsbestellungen_loeschen()
RETURNS TABLE (aus_burgermetrics integer, aus_wawi integer)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = wawi, burgermetrics, pg_temp
AS $$
DECLARE
  n_bm integer; n_w integer;
BEGIN
  DELETE FROM burgermetrics.fact_order_items i
  WHERE  i.order_id IN (SELECT b.bestellung_id FROM wawi.kundenbestellung b WHERE b.quelle <> 'bestand');
  DELETE FROM burgermetrics.fact_orders o
  WHERE  o.order_id IN (SELECT b.bestellung_id FROM wawi.kundenbestellung b WHERE b.quelle <> 'bestand');
  GET DIAGNOSTICS n_bm = ROW_COUNT;

  -- Positionen und Rechnung folgen per ON DELETE CASCADE.
  DELETE FROM wawi.kundenbestellung b WHERE b.quelle <> 'bestand';
  GET DIAGNOSTICS n_w = ROW_COUNT;

  RETURN QUERY SELECT n_bm, n_w;
END $$;

-- Diese drei Funktionen sind Betriebswerkzeuge fuer postgres — nicht fuer
-- die Web-Rollen. PUBLIC hat auf neue Funktionen standardmaessig EXECUTE,
-- deshalb der ausdrueckliche Entzug.
REVOKE ALL ON FUNCTION burgermetrics.uebernahme_aus_wawi()    FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION wawi.etl_probe()                       FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION wawi.uebungsbestellungen_loeschen()    FROM PUBLIC, anon, authenticated;

-- Die stg-Sichten duerfen gelesen werden: Sie sind Lehrgegenstand.
GRANT SELECT ON wawi.stg_fact_orders, wawi.stg_fact_order_items, wawi.stg_dim_date TO anon, authenticated;
