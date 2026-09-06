-- 0018_wawi_sichten_und_schreiben.sql
-- Zweck: Was Kasse und Shop vom operativen Schema brauchen — lesen und
--        schreiben — und die Rechte dafuer.
--
--        Lesen:     v_speisekarte, v_filialliste (bisher in burgermetrics auf
--                   dim_product und dim_branch; jetzt hier auf artikel und
--                   filiale, mit denselben Spaltennamen — die Seiten merken
--                   den Umzug nur an der Schemaangabe), v_bestellung_letzte.
--        Schreiben: bestellung_anlegen(). Die Rolle anon darf keine Tabelle
--                   beschreiben; sie darf genau diese eine Funktion aufrufen.
--                   Die Funktion prueft die Eingaben, holt die Preise aus dem
--                   Stamm (nie vom Browser) und schreibt Bestellung, Positionen
--                   und Rechnung in einer Transaktion.
--
-- Betrieb: Das Schema muss PostgREST bekannt sein — in
--          /root/supabase/docker/.env die Liste PGRST_DB_SCHEMAS um ,wawi
--          ERGAENZEN (nicht ersetzen: dort stehen auch andere Projekte),
--          dann `docker compose up -d rest`. Ein `restart` genuegt nicht,
--          er liest die .env nicht neu. Details in 0004 und db/README.md.
--
-- Objekte: wawi.v_speisekarte, wawi.v_filialliste, wawi.v_bestellung_letzte,
--          wawi.bestellung_anlegen(); Grants und RLS auf wawi.
-- Ruecknahme: DROP FUNCTION wawi.bestellung_anlegen; DROP VIEW wawi.v_*;
-- Idempotent: ja.

SET search_path TO wawi, burgermetrics;

-- Alle Objekte sind mit Schema qualifiziert. Ohne Qualifikation traefe ein
-- DROP VIEW IF EXISTS ueber den Suchpfad die gleichnamige Sicht in
-- burgermetrics — und die ist nach materialisieren.py eine materialisierte
-- Sicht, an der DROP VIEW scheitert.

-- ---------------------------------------------------------------------------
-- Speisekarte: der Artikelstamm, wie ihn eine Verkaufsoberflaeche braucht.
-- preis ist der heutige Listenpreis, preis_2017 der aelteste Stand aus der
-- Preishistorie — damit die Preisentwicklung im Unterricht sichtbar bleibt.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS wawi.v_speisekarte CASCADE;
CREATE VIEW wawi.v_speisekarte AS
SELECT a.artikel_id,
       a.name,
       k.name                             AS kategorie,
       u.name                             AS unterkategorie,
       a.listenpreis                      AS preis,
       (SELECT h.verkaufspreis FROM preishistorie h
         WHERE h.artikel_id = a.artikel_id
         ORDER BY h.gueltig_ab LIMIT 1)   AS preis_2017,
       a.kalorien,
       a.vegetarisch,
       a.vegan,
       a.allergene,
       a.gelistet_seit
FROM   artikel a
JOIN   artikelunterkategorie u USING (unterkategorie_id)
JOIN   artikelkategorie      k USING (kategorie_id)
ORDER  BY k.name, a.name;

COMMENT ON VIEW wawi.v_speisekarte IS
  'Artikelstamm fuer Shop und Kasse, aus dem operativen Modell. Bilder und '
  'Beschreibungen sind nicht Teil des Datenmodells und stehen in den Seiten.';

-- ---------------------------------------------------------------------------
-- Filialliste: die Standorte, wie sie eine Kundenoberflaeche zeigt.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS wawi.v_filialliste CASCADE;
CREATE VIEW wawi.v_filialliste AS
SELECT f.filiale_id,
       f.name,
       f.adresse,
       f.stadtteil                        AS bezirk,
       f.plz,
       f.ort,
       f.breite,
       f.laenge,
       t.name                             AS art,
       f.hat_drive_through                AS drive_through,
       f.hat_spielplatz                   AS spielplatz,
       f.parkplaetze,
       COALESCE(f.sitzplaetze_innen, 0) + COALESCE(f.sitzplaetze_aussen, 0) AS sitzplaetze,
       f.eroeffnet_am                     AS eroeffnet
FROM   filiale f
LEFT JOIN filialtyp t USING (filialtyp_id)
ORDER  BY f.filiale_id;

COMMENT ON VIEW wawi.v_filialliste IS
  'Standortliste fuer den Online-Shop, aus dem operativen Modell. '
  'Oeffnungszeiten stehen in der Seite.';

-- ---------------------------------------------------------------------------
-- Die letzten Uebungsbestellungen: damit Kasse und Shop im Datenmodus zeigen
-- koennen, wo der Beleg gelandet ist — und Studierende ihn wiederfinden.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS wawi.v_bestellung_letzte CASCADE;
CREATE VIEW wawi.v_bestellung_letzte AS
SELECT b.bestellung_id,
       b.quelle,
       b.sitzung,
       b.bestelldatum,
       b.bestellzeit,
       f.name                             AS filiale,
       b.bestellkanal                     AS kanal,
       z.bezeichnung                      AS zahlungsart,
       b.artikel_anzahl,
       (SELECT count(*) FROM bestellposition p
         WHERE p.bestellung_id = b.bestellung_id)::int AS positionen,
       b.brutto_gesamt,
       b.rabatt_betrag,
       b.netto_gesamt,
       b.erfasst_am,
       EXISTS (SELECT 1 FROM burgermetrics.fact_orders o
               WHERE o.order_id = b.bestellung_id) AS im_warehouse
FROM   kundenbestellung b
JOIN   filiale     f USING (filiale_id)
JOIN   zahlungsart z USING (zahlungsart_id)
WHERE  b.quelle <> 'bestand'
ORDER  BY b.erfasst_am DESC
LIMIT  50;

COMMENT ON VIEW wawi.v_bestellung_letzte IS
  'Die 50 juengsten Uebungsbestellungen aus Kasse und Shop. im_warehouse sagt, '
  'ob der ETL-Schritt (0019) sie schon nach burgermetrics uebernommen hat.';

-- ---------------------------------------------------------------------------
-- Schreiben: eine Bestellung anlegen.
--
-- Parameter heissen wie die Spalten, damit der Aufruf aus PostgREST lesbar
-- bleibt ({"filiale_id": 2, "positionen": [{"artikel_id": 4, "menge": 2}]}).
-- Deshalb #variable_conflict use_variable: unqualifizierte Namen sind die
-- Parameter, Spalten sind im Rumpf IMMER mit Alias qualifiziert.
--
-- SECURITY DEFINER: laeuft mit den Rechten des Eigentuemers (postgres), die
-- aufrufende Rolle braucht auf den Tabellen kein INSERT. search_path ist
-- festgenagelt, damit niemand ueber ein eigenes Schema Tabellen unterschiebt.
-- ---------------------------------------------------------------------------
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
  v_jetzt      timestamptz := now();
  v_lokal      timestamp   := now() AT TIME ZONE 'Europe/Berlin';
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

  -- Bremse: Der Bestand ist oeffentlich beschreibbar, und ein Skript kann
  -- schneller klicken als ein Mensch. 60 Belege je Sitzung und zehn Minuten
  -- reichen fuer jede Uebung.
  IF sitzung IS NOT NULL THEN
    SELECT count(*) INTO v_kuerzlich
    FROM   kundenbestellung b
    WHERE  b.sitzung = sitzung AND b.erfasst_am > v_jetzt - interval '10 minutes';
    IF v_kuerzlich >= 60 THEN
      RAISE EXCEPTION 'zu viele Bestellungen in kurzer Zeit — bitte kurz warten'
        USING ERRCODE = '53400';
    END IF;
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

COMMENT ON FUNCTION wawi.bestellung_anlegen IS
  'Legt Bestellung, Positionen und Rechnung in einer Transaktion an. Preise '
  'kommen aus wawi.artikel, nie vom Aufrufer. Einziger Schreibweg fuer anon.';

-- ---------------------------------------------------------------------------
-- Rechte. Lesen wie in burgermetrics (0004): oeffentlich, RLS mit reiner
-- SELECT-Policy. Schreiben nur ueber die Funktion.
-- ---------------------------------------------------------------------------
GRANT USAGE ON SCHEMA wawi TO anon, authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA wawi TO anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA wawi GRANT SELECT ON TABLES TO anon, authenticated;

DO $$
DECLARE t record;
BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'wawi' LOOP
    EXECUTE format('ALTER TABLE wawi.%I ENABLE ROW LEVEL SECURITY', t.tablename);
    EXECUTE format('DROP POLICY IF EXISTS lesen_alle ON wawi.%I', t.tablename);
    EXECUTE format('CREATE POLICY lesen_alle ON wawi.%I FOR SELECT USING (true)', t.tablename);
  END LOOP;
END $$;

REVOKE ALL ON FUNCTION wawi.bestellung_anlegen(bigint, bigint, text, jsonb, text, text, bigint, bigint, numeric, numeric) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION wawi.bestellung_anlegen(bigint, bigint, text, jsonb, text, text, bigint, bigint, numeric, numeric) TO anon, authenticated;

-- ---------------------------------------------------------------------------
-- Die alten Sichten in burgermetrics (0013) weichen: Es gibt nur noch eine
-- Speisekarte, und die liegt im operativen Schema. Wer 0013 erneut ausfuehrt,
-- bekommt sie zurueck — sie schaden nicht, aber die Seiten lesen sie nicht
-- mehr. materialisieren.py kann sie zwischenzeitlich in Tabellen verwandelt
-- haben, daher die Abfrage der Relationsart.
-- ---------------------------------------------------------------------------
DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT c.relname, c.relkind
           FROM   pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE  n.nspname = 'burgermetrics'
             AND  c.relname IN ('v_speisekarte', 'v_filialliste')
             AND  c.relkind IN ('v', 'm') LOOP
    EXECUTE format('DROP %s IF EXISTS burgermetrics.%I CASCADE',
                   CASE WHEN r.relkind = 'm' THEN 'MATERIALIZED VIEW' ELSE 'VIEW' END,
                   r.relname);
  END LOOP;
END $$;
