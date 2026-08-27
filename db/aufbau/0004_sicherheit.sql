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

-- PostgREST: Schema in die exponierte Liste aufnehmen (in-database config)
-- und die Konfiguration neu laden. Der bestehende Wert bleibt erhalten.
DO $$
DECLARE aktuelle text;
BEGIN
  SELECT split_part(unnest, '=', 2) INTO aktuelle
  FROM unnest((SELECT setconfig FROM pg_db_role_setting s
               JOIN pg_roles r ON r.oid = s.setrole
               WHERE r.rolname = 'authenticator' AND s.setdatabase = 0))
  WHERE unnest LIKE 'pgrst.db_schemas=%';
  IF aktuelle IS NULL THEN
    RAISE EXCEPTION 'pgrst.db_schemas nicht gefunden — Konfiguration pruefen';
  END IF;
  IF position('burgermetrics' IN aktuelle) = 0 THEN
    EXECUTE format('ALTER ROLE authenticator SET pgrst.db_schemas = %L',
                   aktuelle || ', burgermetrics');
  END IF;
END $$;
NOTIFY pgrst, 'reload config';
