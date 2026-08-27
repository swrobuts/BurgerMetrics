-- 0004_sicherheit.sql
-- Zweck: Lesezugriff fuer die Web-Rollen und Aufnahme des Schemas in die
--        PostgREST-Konfiguration. Der Lehrbestand ist bewusst oeffentlich
--        lesbar; geschrieben wird ausschliesslich als postgres.
-- Objekte: Grants, RLS-Policies (nur SELECT), pgrst.db_schemas.
-- Ruecknahme: REVOKE ... ; ALTER ROLE authenticator RESET pgrst.db_schemas;
-- Idempotent: ja.

GRANT USAGE ON SCHEMA burgermetrics TO anon, authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA burgermetrics TO anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA burgermetrics
  GRANT SELECT ON TABLES TO anon, authenticated;

-- RLS: eingeschaltet, eine reine Lese-Policy je Tabelle.
DO $$
DECLARE t record;
BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='burgermetrics' LOOP
    EXECUTE format('ALTER TABLE burgermetrics.%I ENABLE ROW LEVEL SECURITY', t.tablename);
    EXECUTE format('DROP POLICY IF EXISTS lesen_alle ON burgermetrics.%I', t.tablename);
    EXECUTE format('CREATE POLICY lesen_alle ON burgermetrics.%I FOR SELECT USING (true)', t.tablename);
  END LOOP;
END $$;

-- PostgREST: Das Schema muss in der exponierten Liste stehen. Hier stand
-- frueher ein ALTER ROLE authenticator SET pgrst.db_schemas — das ist aus
-- zwei Gruenden falsch und deshalb entfernt:
--
--   1. Es wirkt nicht. PostgREST liest die Schemaliste aus der Umgebung des
--      Containers (PGRST_DB_SCHEMAS); die Einstellung an der Rolle wird davon
--      ueberstimmt. Auch NOTIFY pgrst, 'reload config' bleibt folgenlos,
--      solange PGRST_DB_CHANNEL_ENABLED=false gesetzt ist.
--   2. Es scheitert ohnehin, wenn man die Kette nicht als Superuser faehrt —
--      ALTER ROLE verlangt CREATEROLE und ADMIN OPTION auf authenticator.
--
-- Der Schritt gehoert damit nicht in die Datenbank, sondern in den Betrieb.
-- Bei einem selbst gehosteten Supabase:
--
--   1. In /root/supabase/docker/.env die Zeile PGRST_DB_SCHEMAS um den
--      Schemanamen ergaenzen (vorher sichern).
--   2. docker compose restart rest
--
-- Ohne Docker startet man PostgREST mit db-schemas in seiner Konfiguration.
-- Wer nur mit psql oder einem BI-Werkzeug direkt auf die Datenbank geht,
-- braucht diesen Schritt gar nicht — die Grants oben genuegen.
