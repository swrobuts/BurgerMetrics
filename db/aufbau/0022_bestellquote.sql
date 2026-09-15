-- 0022_bestellquote.sql
-- Atomare Quote fuer die oeffentliche Bestell-RPC: 60/10min je Sitzung
-- (einschliesslich NULL), 600/Stunde insgesamt fuer shop und kasse.
-- Voraussetzung: 0018. Als bisheriger Funktionseigentuemer in einer
-- Transaktion ausfuehren. Keine Tabellen-/Rollenrechte werden erweitert.
-- CREATE OR REPLACE erhaelt Signatur, Eigentuemer und bestehende Grants.
-- Idempotent: ja. Die gleiche Definition steht fuer Neuaufbauten in 0018.
-- Ruecknahme wuerde die Umgehung wieder oeffnen; keinen alten Rumpf einspielen.

CREATE OR REPLACE FUNCTION wawi.bestellung_anlegen(
  filiale_id     bigint,
  zahlungsart_id bigint,
  bestellkanal   text,
  positionen     jsonb,            -- [{"artikel_id": 4, "menge": 2}, ...]
  quelle         text,             -- 'kasse' | 'shop'
  sitzung        text    DEFAULT NULL,
  kunde_id       bigint  DEFAULT NULL,
  promotion_id   bigint  DEFAULT NULL,
  rabatt_betrag  numeric DEFAULT 0,
  mwst_satz      numeric DEFAULT 0.07)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = wawi, pg_temp
AS $$
#variable_conflict use_variable
DECLARE
  v_jetzt      timestamptz;
  v_lokal      timestamp;
  v_id         bigint;
  v_rechnung   bigint;
  v_fehlend    text;
  v_positionen integer;
  v_anzahl     integer;
  v_brutto     numeric(10,2);
  v_rabatt     numeric(10,2);
  v_netto      numeric(10,2);
  v_mwst       numeric(10,2);
  v_kuerzlich  integer;
BEGIN
  -- Ein Snapshot von vor dem Warten auf die Quotensperre waere veraltet.
  -- PostgREST verwendet standardmaessig READ COMMITTED.
  IF current_setting('transaction_isolation') <> 'read committed' THEN
    RAISE EXCEPTION 'Bestellungen brauchen READ COMMITTED'
      USING ERRCODE = '25000';
  END IF;
  IF length(sitzung) > 100 THEN
    RAISE EXCEPTION 'sitzung darf hoechstens 100 Zeichen enthalten'
      USING ERRCODE = '22023';
  END IF;
  -- Eingaben pruefen. Jede Meldung nennt, was fehlt — das ist die Antwort,
  -- die der Browser anzeigt.
  IF quelle IS NULL OR quelle NOT IN ('kasse', 'shop') THEN
    RAISE EXCEPTION 'quelle muss kasse oder shop sein, nicht %', quelle
      USING ERRCODE = '22023';
  END IF;
  IF bestellkanal IS NULL OR bestellkanal NOT IN ('Counter', 'Drive-Through', 'Kiosk', 'App Order') THEN
    RAISE EXCEPTION 'unbekannter Bestellkanal: %', bestellkanal USING ERRCODE = '22023';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM filiale f WHERE f.filiale_id = filiale_id) THEN
    RAISE EXCEPTION 'unbekannte Filiale: %', filiale_id USING ERRCODE = '23503';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM zahlungsart z WHERE z.zahlungsart_id = zahlungsart_id) THEN
    RAISE EXCEPTION 'unbekannte Zahlungsart: %', zahlungsart_id USING ERRCODE = '23503';
  END IF;
  IF kunde_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM kunde k WHERE k.kunde_id = kunde_id) THEN
    RAISE EXCEPTION 'unbekannter Kunde: %', kunde_id USING ERRCODE = '23503';
  END IF;
  IF promotion_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM promotion p WHERE p.promotion_id = promotion_id) THEN
    RAISE EXCEPTION 'unbekannte Aktion: %', promotion_id USING ERRCODE = '23503';
  END IF;
  IF mwst_satz IS NULL OR mwst_satz < 0 OR mwst_satz > 0.5 THEN
    RAISE EXCEPTION 'mwst_satz ausserhalb des Sinnvollen: %', mwst_satz USING ERRCODE = '22023';
  END IF;
  IF positionen IS NULL OR jsonb_typeof(positionen) <> 'array' OR jsonb_array_length(positionen) = 0 THEN
    RAISE EXCEPTION 'positionen muss eine nicht leere Liste sein' USING ERRCODE = '22023';
  END IF;
  IF jsonb_array_length(positionen) > 50 THEN
    RAISE EXCEPTION 'hoechstens 50 Positionen je Bestellung' USING ERRCODE = '22023';
  END IF;
  IF EXISTS (SELECT 1 FROM jsonb_to_recordset(positionen) AS p(artikel_id bigint, menge integer)
             WHERE p.artikel_id IS NULL OR p.menge IS NULL OR p.menge < 1 OR p.menge > 50) THEN
    RAISE EXCEPTION 'jede Position braucht artikel_id und eine menge zwischen 1 und 50'
      USING ERRCODE = '22023';
  END IF;
  SELECT string_agg(p.artikel_id::text, ', ') INTO v_fehlend
  FROM   jsonb_to_recordset(positionen) AS p(artikel_id bigint, menge integer)
  WHERE  NOT EXISTS (SELECT 1 FROM artikel a WHERE a.artikel_id = p.artikel_id);
  IF v_fehlend IS NOT NULL THEN
    RAISE EXCEPTION 'unbekannte Artikel: %', v_fehlend USING ERRCODE = '23503';
  END IF;

  -- Eine gemeinsame Transaktionssperre serialisiert Zaehlen UND Schreiben.
  -- Fester Namensraum/Schluessel fuer die Bestellquote, nie vom Client bestimmt.
  PERFORM pg_advisory_xact_lock(1112362324, 1);
  v_jetzt := clock_timestamp();
  v_lokal := v_jetzt AT TIME ZONE 'Europe/Berlin';
  -- NULL ist eine gemeinsame Sitzung; wechselnde Kennungen unterliegen
  -- zusaetzlich der Gesamtquote. Historische Importdaten zaehlen nicht mit.
  SELECT count(*) INTO v_kuerzlich
  FROM kundenbestellung b
  WHERE b.quelle IN ('kasse', 'shop')
    AND b.sitzung IS NOT DISTINCT FROM sitzung
    AND b.erfasst_am > v_jetzt - interval '10 minutes';
  IF v_kuerzlich >= 60 THEN
    RAISE EXCEPTION 'zu viele Bestellungen in kurzer Zeit — bitte kurz warten'
      USING ERRCODE = '53400';
  END IF;
  SELECT count(*) INTO v_kuerzlich
  FROM kundenbestellung b
  WHERE b.quelle IN ('kasse', 'shop')
    AND b.erfasst_am > v_jetzt - interval '1 hour';
  IF v_kuerzlich >= 600 THEN
    RAISE EXCEPTION 'Gesamtquote erreicht — bitte spaeter erneut bestellen'
      USING ERRCODE = '53400';
  END IF;

  -- Betraege aus dem Stamm. Gleiche Artikel werden zu einer Position
  -- zusammengefasst; der Preis ist der Listenpreis von jetzt.
  SELECT count(*), sum(g.menge), sum(g.menge * g.listenpreis)
  INTO   v_positionen, v_anzahl, v_brutto
  FROM  (SELECT a.artikel_id, sum(p.menge)::int AS menge, a.listenpreis
         FROM   jsonb_to_recordset(positionen) AS p(artikel_id bigint, menge integer)
         JOIN   artikel a ON a.artikel_id = p.artikel_id
         GROUP  BY a.artikel_id, a.listenpreis) g;

  v_rabatt := round(LEAST(GREATEST(COALESCE(rabatt_betrag, 0), 0), v_brutto), 2);
  v_netto  := v_brutto - v_rabatt;
  v_mwst   := round(v_netto - v_netto / (1 + mwst_satz), 2);

  INSERT INTO kundenbestellung
        (bestelldatum, bestellzeit, filiale_id, kunde_id, zahlungsart_id, promotion_id,
         bestellkanal, artikel_anzahl, brutto_gesamt, rabatt_betrag, netto_gesamt,
         quelle, sitzung, erfasst_am)
  VALUES (v_lokal::date, v_lokal::time(0), filiale_id, kunde_id, zahlungsart_id, promotion_id,
          bestellkanal, v_anzahl, v_brutto, v_rabatt, v_netto,
          quelle, sitzung, v_jetzt)
  RETURNING kundenbestellung.bestellung_id INTO v_id;

  INSERT INTO bestellposition (bestellung_id, artikel_id, menge, einzelpreis, positionsbetrag)
  SELECT v_id, g.artikel_id, g.menge, g.listenpreis, round(g.menge * g.listenpreis, 2)
  FROM  (SELECT a.artikel_id, sum(p.menge)::int AS menge, a.listenpreis
         FROM   jsonb_to_recordset(positionen) AS p(artikel_id bigint, menge integer)
         JOIN   artikel a ON a.artikel_id = p.artikel_id
         GROUP  BY a.artikel_id, a.listenpreis) g
  ORDER  BY g.artikel_id;

  INSERT INTO rechnung (bestellung_id, rechnungsdatum, zahlbetrag, mwst_satz, mwst_betrag, zahlungsart_id)
  VALUES (v_id, v_lokal::date, v_netto, mwst_satz, v_mwst, zahlungsart_id)
  RETURNING rechnung.rechnung_id INTO v_rechnung;

  RETURN jsonb_build_object(
    'bestellung_id',  v_id,
    'rechnung_id',    v_rechnung,
    'bestelldatum',   v_lokal::date,
    'bestellzeit',    v_lokal::time(0),
    'positionen',     v_positionen,
    'artikel_anzahl', v_anzahl,
    'brutto_gesamt',  v_brutto,
    'rabatt_betrag',  v_rabatt,
    'netto_gesamt',   v_netto,
    'mwst_satz',      mwst_satz,
    'mwst_betrag',    v_mwst,
    'quelle',         quelle);
END $$;

NOTIFY pgrst, 'reload schema';
