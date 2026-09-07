-- 0020_demo_rolle.sql
-- Zweck: eine Anmeldung fuer Studierende, die mit psql, DBeaver oder einem
--        BI-Werkzeug direkt auf die Datenbank gehen: Rolle studi, Kennwort
--        thws, Lesezugriff auf beide Schemata des Projekts.
--
--        Das Kennwort steht absichtlich im Quelltext. Die Rolle darf nur
--        lesen, der Bestand ist synthetisch und ohnehin ueber den anon-
--        Schluessel oeffentlich. Wer die Rolle fuer etwas anderes benutzen
--        will, vergibt ein eigenes Kennwort — nicht hier, sondern im Betrieb.
--
--        Was studi NICHT darf: schreiben (kein INSERT, UPDATE, DELETE),
--        Bestellungen anlegen (kein EXECUTE auf wawi.bestellung_anlegen),
--        andere Schemata der Instanz lesen, Rollen anlegen, eine Abfrage
--        laenger als eine Minute laufen lassen, mehr als zwanzig Sitzungen
--        gleichzeitig halten.
--
-- Voraussetzung: als Superuser ausfuehren (supabase_admin). Die Rolle
--          postgres des Supabase-Images darf keine Rollen anlegen.
-- Objekte: Rolle studi; Grants auf burgermetrics und wawi.
-- Ruecknahme: siehe Ende der Datei.
-- Idempotent: ja.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'studi') THEN
    CREATE ROLE studi LOGIN PASSWORD 'thws'
      NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS
      CONNECTION LIMIT 20;
  ELSE
    ALTER ROLE studi WITH LOGIN PASSWORD 'thws'
      NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS
      CONNECTION LIMIT 20;
  END IF;
END $$;

-- Eine Uebungsabfrage darf nicht die Instanz belegen. Eine Minute reicht
-- fuer jede Aufgabe des Uebungsblatts; die Selbstverknuepfung ueber 2,95
-- Millionen Positionen braucht 4,4 Sekunden.
ALTER ROLE studi SET statement_timeout = '60s';
ALTER ROLE studi SET idle_in_transaction_session_timeout = '5min';
-- Beide Schemata im Suchpfad, das operative zuerst — so trifft
-- SELECT * FROM artikel und SELECT * FROM fact_orders ohne Praefix.
ALTER ROLE studi SET search_path = wawi, burgermetrics, public;

GRANT CONNECT ON DATABASE postgres TO studi;
GRANT USAGE ON SCHEMA burgermetrics, wawi TO studi;
GRANT SELECT ON ALL TABLES IN SCHEMA burgermetrics, wawi TO studi;   -- Tabellen, Sichten, materialisierte Sichten
GRANT SELECT ON ALL SEQUENCES IN SCHEMA burgermetrics, wawi TO studi;
GRANT EXECUTE ON FUNCTION burgermetrics.kurzname(text) TO studi;

-- Auch kuenftige Tabellen und Sichten, die postgres in den beiden Schemata
-- anlegt (materialisieren.py, weitere Aufbauskripte).
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA burgermetrics GRANT SELECT ON TABLES TO studi;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA wawi          GRANT SELECT ON TABLES TO studi;

-- Row Level Security ist auf allen Tabellen eingeschaltet (0004, 0018); die
-- Policy lesen_alle gilt fuer jede Rolle, studi braucht also keine eigene.
-- Ausdruecklich KEIN Schreibweg:
REVOKE EXECUTE ON FUNCTION wawi.bestellung_anlegen(bigint, bigint, text, jsonb, text, text, bigint, bigint, numeric, numeric) FROM studi;

COMMENT ON ROLE studi IS
  'Demo-Anmeldung fuer Studierende: nur lesen, Schemata burgermetrics und wawi.';

-- Ruecknahme:
--   REVOKE ALL ON ALL TABLES IN SCHEMA burgermetrics, wawi FROM studi;
--   REVOKE ALL ON ALL SEQUENCES IN SCHEMA burgermetrics, wawi FROM studi;
--   REVOKE USAGE ON SCHEMA burgermetrics, wawi FROM studi;
--   REVOKE CONNECT ON DATABASE postgres FROM studi;
--   ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA burgermetrics REVOKE SELECT ON TABLES FROM studi;
--   ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA wawi          REVOKE SELECT ON TABLES FROM studi;
--   DROP ROLE studi;
