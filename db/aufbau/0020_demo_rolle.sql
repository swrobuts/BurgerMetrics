-- 0020_demo_rolle.sql
-- Zweck: eine Anmeldung fuer Studierende, die mit psql, DBeaver oder einem
--        BI-Werkzeug direkt auf die Datenbank gehen: Rolle studi_daba,
--        Kennwort thws, Lesezugriff auf beide Schemata des Projekts.
--
--        Das Kennwort steht absichtlich im Quelltext. Die Rolle darf nur
--        lesen, der Bestand ist synthetisch und ohnehin ueber den anon-
--        Schluessel oeffentlich. Wer die Rolle fuer etwas anderes benutzen
--        will, vergibt ein eigenes Kennwort — nicht hier, sondern im Betrieb.
--
--        Warum ein eigener Name: Auf der Instanz gibt es schon die Rolle
--        studi der VeloCity-Fallstudie (Schema velocity, dort
--        db/betrieb/studizugang_lesend.sql) mit Suchpfad velocity. Eine Rolle
--        hat genau einen Suchpfad, und kunde, mitarbeiter, rechnung und
--        zahlungsart gibt es in velocity UND in wawi — ein gemeinsamer
--        Suchpfad waere mehrdeutig. Deshalb je Projekt eine Rolle. Rechte,
--        die studi aus einer frueheren Fassung dieses Skripts auf
--        burgermetrics und wawi bekommen hatte, nimmt der letzte Block
--        zurueck; die Rolle selbst und ihre Einstellungen bleiben unberuehrt.
--
--        Was studi_daba NICHT darf: schreiben (kein INSERT, UPDATE, DELETE),
--        Bestellungen anlegen (kein EXECUTE auf wawi.bestellung_anlegen),
--        andere Schemata der Instanz lesen, Rollen anlegen, eine Abfrage
--        laenger als eine Minute laufen lassen, mehr als zwanzig Sitzungen
--        gleichzeitig halten.
--
-- Voraussetzung: als Superuser ausfuehren (supabase_admin). Die Rolle
--          postgres des Supabase-Images darf keine Rollen anlegen.
-- Objekte: Rolle studi_daba; Grants auf burgermetrics und wawi.
-- Ruecknahme: siehe Ende der Datei.
-- Idempotent: ja.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'studi_daba') THEN
    CREATE ROLE studi_daba LOGIN PASSWORD 'thws'
      NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS
      CONNECTION LIMIT 20;
  ELSE
    ALTER ROLE studi_daba WITH LOGIN PASSWORD 'thws'
      NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS
      CONNECTION LIMIT 20;
  END IF;
END $$;

-- Eine Uebungsabfrage darf nicht die Instanz belegen. Eine Minute reicht
-- fuer jede Aufgabe des Uebungsblatts; die Selbstverknuepfung ueber 2,95
-- Millionen Positionen braucht 4,4 Sekunden.
ALTER ROLE studi_daba SET statement_timeout = '60s';
ALTER ROLE studi_daba SET idle_in_transaction_session_timeout = '5min';
-- Jede Transaktion nur lesend — zweiter Riegel neben den fehlenden Grants.
ALTER ROLE studi_daba SET default_transaction_read_only = on;
-- Beide Schemata im Suchpfad, das operative zuerst — so trifft
-- SELECT * FROM artikel und SELECT * FROM fact_orders ohne Praefix.
ALTER ROLE studi_daba SET search_path = wawi, burgermetrics;

GRANT CONNECT ON DATABASE postgres TO studi_daba;
GRANT USAGE ON SCHEMA burgermetrics, wawi TO studi_daba;
GRANT SELECT ON ALL TABLES IN SCHEMA burgermetrics, wawi TO studi_daba;   -- Tabellen, Sichten, materialisierte Sichten
GRANT SELECT ON ALL SEQUENCES IN SCHEMA burgermetrics, wawi TO studi_daba;
GRANT EXECUTE ON FUNCTION burgermetrics.kurzname(text) TO studi_daba;
-- Das Supabase-Image gibt PUBLIC Rechte auf public; die Rolle braucht sie nicht.
REVOKE ALL ON SCHEMA public FROM studi_daba;

-- Auch kuenftige Tabellen und Sichten, die postgres in den beiden Schemata
-- anlegt (materialisieren.py, weitere Aufbauskripte).
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA burgermetrics GRANT SELECT ON TABLES TO studi_daba;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA wawi          GRANT SELECT ON TABLES TO studi_daba;

-- Row Level Security ist auf allen Tabellen eingeschaltet (0004, 0018); die
-- Policy lesen_alle gilt fuer jede Rolle, studi_daba braucht also keine eigene.
-- Ausdruecklich KEIN Schreibweg:
REVOKE EXECUTE ON FUNCTION wawi.bestellung_anlegen(bigint, bigint, text, jsonb, text, text, bigint, bigint, numeric, numeric) FROM studi_daba;

COMMENT ON ROLE studi_daba IS
  'Demo-Anmeldung fuer Studierende (BurgerMetrics): nur lesen, Schemata burgermetrics und wawi.';

-- Aufraeumen: die geteilte Rolle studi (VeloCity) hatte aus einer frueheren
-- Fassung Rechte auf burgermetrics und wawi. Zurueck auf ihr eigenes Projekt.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'studi') THEN
    REVOKE ALL ON ALL TABLES    IN SCHEMA burgermetrics, wawi FROM studi;
    REVOKE ALL ON ALL SEQUENCES IN SCHEMA burgermetrics, wawi FROM studi;
    REVOKE ALL ON ALL FUNCTIONS IN SCHEMA burgermetrics, wawi FROM studi;
    REVOKE USAGE ON SCHEMA burgermetrics, wawi FROM studi;
    ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA burgermetrics REVOKE SELECT ON TABLES FROM studi;
    ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA wawi          REVOKE SELECT ON TABLES FROM studi;
  END IF;
END $$;

-- Probe: jede Tabelle, Sicht und materialisierte Sicht beider Schemata fuer
-- studi_daba lesbar, keine schreibbar; studi sieht hier nichts mehr.
DO $$
DECLARE
  v_alle    integer;
  v_lesbar  integer;
  v_schreib integer;
  v_fremd   integer;
BEGIN
  SELECT count(*),
         count(*) FILTER (WHERE has_table_privilege('studi_daba', c.oid, 'SELECT')),
         count(*) FILTER (WHERE has_table_privilege('studi_daba', c.oid, 'INSERT')
                             OR has_table_privilege('studi_daba', c.oid, 'UPDATE')
                             OR has_table_privilege('studi_daba', c.oid, 'DELETE')),
         count(*) FILTER (WHERE EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'studi')
                            AND has_table_privilege('studi', c.oid, 'SELECT'))
    INTO v_alle, v_lesbar, v_schreib, v_fremd
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname IN ('burgermetrics', 'wawi') AND c.relkind IN ('r', 'v', 'm', 'p');
  IF v_lesbar <> v_alle OR v_schreib <> 0 THEN
    RAISE EXCEPTION 'studi_daba: % von % Objekten lesbar, % schreibbar', v_lesbar, v_alle, v_schreib;
  END IF;
  IF v_fremd <> 0 THEN
    RAISE EXCEPTION 'studi (VeloCity) liest noch % Objekte in burgermetrics/wawi', v_fremd;
  END IF;
  IF has_function_privilege('studi_daba',
       'wawi.bestellung_anlegen(bigint, bigint, text, jsonb, text, text, bigint, bigint, numeric, numeric)', 'EXECUTE') THEN
    RAISE EXCEPTION 'studi_daba darf bestellung_anlegen() ausfuehren';
  END IF;
  RAISE NOTICE 'studi_daba liest % Objekte in burgermetrics und wawi, schreibt keines', v_lesbar;
END $$;

-- Ruecknahme:
--   REVOKE ALL ON ALL TABLES IN SCHEMA burgermetrics, wawi FROM studi_daba;
--   REVOKE ALL ON ALL SEQUENCES IN SCHEMA burgermetrics, wawi FROM studi_daba;
--   REVOKE EXECUTE ON FUNCTION burgermetrics.kurzname(text) FROM studi_daba;
--   REVOKE USAGE ON SCHEMA burgermetrics, wawi FROM studi_daba;
--   REVOKE CONNECT ON DATABASE postgres FROM studi_daba;
--   ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA burgermetrics REVOKE SELECT ON TABLES FROM studi_daba;
--   ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA wawi          REVOKE SELECT ON TABLES FROM studi_daba;
--   DROP ROLE studi_daba;
