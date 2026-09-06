-- 0017_wawi_bestand.sql
-- Zweck: die historischen Bestellungen in das operative Schema uebernehmen.
--
--        Ein operatives System, das nur die Belege von heute kennt, waere
--        keins: Kasse und Shop sollen ihre Bestellung dort ablegen, wo auch
--        die 754.513 Belege der neun Jahre liegen. Und nur mit dem vollen
--        Bestand laesst sich die Probe aus 0019 ueber den ganzen Bestand
--        fuehren — nicht nur ueber 19 Zeilen wie im Mini.
--
--        Die CSV-Dateien bleiben Quelle der Wahrheit. Dieser Schritt ist der
--        einmalige Weg rueckwaerts (Galaxy-Schema -> 3NF); danach fuehrt der
--        Weg nur noch vorwaerts, von wawi nach burgermetrics.
--
-- Abbildung (Umkehrung von dataset/wawi_zu_analytisch.sql):
--   fact_orders.date, time/hour    -> bestelldatum, bestellzeit
--   fact_orders.promo_id = 0       -> promotion_id NULL (operativ: keine Aktion)
--   fact_orders                    -> rechnung 1:1 (Steuer 19 % vereinfacht,
--                                     wie im Mini; neue Belege tragen den
--                                     tatsaechlichen Satz, siehe 0018)
--   fact_order_items               -> bestellposition
--
-- Laufzeit auf dem VPS: rund zwei Minuten fuer 3,7 Millionen Zeilen.
-- Ruecknahme: DELETE FROM wawi.kundenbestellung WHERE quelle = 'bestand';
-- Idempotent: ja — laeuft nur, wenn noch kein Bestand vorhanden ist.

SET search_path TO wawi, burgermetrics;

DO $$
DECLARE
  n bigint;
BEGIN
  SELECT count(*) INTO n FROM wawi.kundenbestellung WHERE quelle = 'bestand';
  IF n > 0 THEN
    RAISE NOTICE 'wawi: Bestand bereits vorhanden (% Belege), nichts zu tun.', n;
    RETURN;
  END IF;

  INSERT INTO wawi.kundenbestellung
        (bestellung_id, bestelldatum, bestellzeit, filiale_id, kunde_id, mitarbeiter_id,
         zahlungsart_id, promotion_id, bestellkanal, artikel_anzahl, brutto_gesamt,
         rabatt_betrag, netto_gesamt, bestelldauer_min, zufriedenheit, quelle, sitzung,
         erfasst_am)
  SELECT o.order_id, o.date,
         COALESCE(o.time, make_time(COALESCE(o.hour, 0), 0, 0)),
         o.branch_id, o.customer_id, NULL,
         o.payment_id, NULLIF(o.promo_id, 0), o.order_channel, o.item_count,
         o.gross_total, COALESCE(o.discount_amount, 0), o.net_total,
         o.order_duration_min, o.satisfaction_score, 'bestand', NULL,
         (o.date + COALESCE(o.time, make_time(COALESCE(o.hour, 0), 0, 0)))::timestamptz
  FROM   burgermetrics.fact_orders o;
  GET DIAGNOSTICS n = ROW_COUNT;
  RAISE NOTICE 'wawi.kundenbestellung: % Belege uebernommen.', n;

  INSERT INTO wawi.bestellposition (position_id, bestellung_id, artikel_id, menge, einzelpreis, positionsbetrag)
  SELECT i.order_item_id, i.order_id, i.product_id, i.quantity, i.unit_price, i.line_total
  FROM   burgermetrics.fact_order_items i;
  GET DIAGNOSTICS n = ROW_COUNT;
  RAISE NOTICE 'wawi.bestellposition: % Positionen uebernommen.', n;

  -- Rechnung 1:1 je Beleg. Steuer 19 % vereinfacht (wie wawi_mini.sql):
  -- Das Faktenmodell fuehrt kein Steuerfeld, der Satz ist fuer den Bestand
  -- also nicht rekonstruierbar. Er ist ausgewiesen, damit niemand ihn fuer
  -- eine Messung haelt.
  INSERT INTO wawi.rechnung (bestellung_id, rechnungsdatum, zahlbetrag, mwst_satz, mwst_betrag, zahlungsart_id)
  SELECT b.bestellung_id, b.bestelldatum, b.netto_gesamt, 0.19,
         round(b.netto_gesamt - b.netto_gesamt / 1.19, 2), b.zahlungsart_id
  FROM   wawi.kundenbestellung b
  WHERE  b.quelle = 'bestand';
  GET DIAGNOSTICS n = ROW_COUNT;
  RAISE NOTICE 'wawi.rechnung: % Rechnungen erzeugt.', n;

  -- Die Zaehler hinter den Bestand setzen, damit neue Belege der Kasse
  -- keine Kennung des Bestands wiederverwenden.
  PERFORM setval(pg_get_serial_sequence('wawi.kundenbestellung', 'bestellung_id'),
                 GREATEST((SELECT max(bestellung_id) FROM wawi.kundenbestellung), 1));
  PERFORM setval(pg_get_serial_sequence('wawi.bestellposition', 'position_id'),
                 GREATEST((SELECT max(position_id) FROM wawi.bestellposition), 1));
  PERFORM setval(pg_get_serial_sequence('wawi.rechnung', 'rechnung_id'),
                 GREATEST((SELECT max(rechnung_id) FROM wawi.rechnung), 1));
END $$;

ANALYZE wawi.kundenbestellung;
ANALYZE wawi.bestellposition;
ANALYZE wawi.rechnung;
