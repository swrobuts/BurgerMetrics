-- betrieb/rezensionen_bestand_kopieren.sql
-- Zweck: den Simulationsbestand der Rezensionen nach einem Neuladen von
--        dataset/fact_reviews.csv erneut nach wawi.rezension kopieren. Seit
--        0023 ersetzt dieses Skript den erneuten Lauf von 0021, der die
--        Freigabe überschreiben würde; 0021 bricht deshalb ab.
--
-- Ablauf (als postgres):
--   DELETE FROM wawi.rezension WHERE quelle = 'simulation';
--   python3 db/lade_csv.py --nur fact_reviews
--   python3 db/skript_ausfuehren.py db/betrieb/rezensionen_bestand_kopieren.sql
--   SELECT * FROM wawi.etl_probe();   -- 0 und 0 je Tabelle
--
-- Die Kopie läuft nur, solange wawi.rezension keine Simulationszeilen hat.
-- Den Status setzt der Trigger rezension_status_vorgabe aus 0023: freigegeben.

DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM wawi.rezension WHERE quelle = 'simulation';
  IF n > 0 THEN
    RAISE NOTICE 'wawi.rezension: Simulationsbestand vorhanden (% Zeilen), nichts zu tun.', n;
    RETURN;
  END IF;
  SELECT count(*) INTO n FROM burgermetrics.fact_reviews WHERE source = 'simulation';
  IF n = 0 THEN
    RAISE NOTICE 'burgermetrics.fact_reviews ist leer — erst lade_csv.py --nur fact_reviews, dann dieses Skript erneut.';
    RETURN;
  END IF;
  INSERT INTO wawi.rezension
        (rezension_id, artikel_id, kunde_id, bestellung_id, filiale_id, sterne, inhalt,
         erstellt_am, quelle, sitzung)
  SELECT r.review_id, r.product_id, r.customer_id, r.order_id, r.branch_id, r.stars, r.review_text,
         (r.date + COALESCE(r.time, TIME '12:00')) AT TIME ZONE 'Europe/Berlin', 'simulation', NULL
  FROM   burgermetrics.fact_reviews r
  WHERE  r.source = 'simulation'
  ORDER  BY r.review_id;
  GET DIAGNOSTICS n = ROW_COUNT;
  RAISE NOTICE 'wawi.rezension: % Rezensionen übernommen.', n;
  PERFORM setval(pg_get_serial_sequence('wawi.rezension', 'rezension_id'),
                 GREATEST((SELECT max(rezension_id) FROM wawi.rezension), 1));
END $$;

ANALYZE wawi.rezension;
