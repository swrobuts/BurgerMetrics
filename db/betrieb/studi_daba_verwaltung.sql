-- betrieb/studi_daba_verwaltung.sql
-- Zweck: die Rolle postgres darf die Einstellungen der Studierendenrolle
--        studi_daba aendern (statement_timeout, Sitzungslimit, Suchpfad),
--        ohne dass jedes Mal supabase_admin auf dem Server noetig ist.
--
--        Hintergrund: Seit PostgreSQL 16 darf eine Rolle mit CREATEROLE
--        fremde Rollen nur noch aendern, wenn sie auf ihnen ADMIN OPTION
--        hat. studi_daba wurde von supabase_admin angelegt; postgres, die
--        Rolle des MCP-Servers und der Aufbauskripte, bekam dabei nichts.
--        Ein ALTER ROLE studi_daba SET ... als postgres endet deshalb mit
--        "permission denied to alter role".
--
--        Was der Grant gibt: postgres darf ALTER ROLE studi_daba SET/RESET
--        ausfuehren und die Mitgliedschaft in studi_daba weitergeben.
--        Was er bewusst nicht gibt: INHERIT FALSE — postgres erbt keine
--        Rechte von studi_daba; SET FALSE — postgres kann nicht per
--        SET ROLE zu studi_daba werden. Superuser bleibt allein
--        supabase_admin.
--
-- Voraussetzung: einmalig als supabase_admin ausfuehren. Auf dem Server:
--
--   docker exec -i supabase-db psql -U supabase_admin -d postgres \
--     < db/betrieb/studi_daba_verwaltung.sql
--
--   oder den Inhalt in eine psql-Sitzung des Containers einfuegen.
--
-- Danach kann postgres, etwa ueber den MCP-Server mit ausfuehren():
--
--   ALTER ROLE studi_daba SET statement_timeout = '10min';
--   ALTER ROLE studi_daba CONNECTION LIMIT 30;
--
-- Objekte: Mitgliedschaft postgres in studi_daba mit ADMIN OPTION.
-- Ruecknahme: siehe Ende der Datei.
-- Idempotent: ja.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM   pg_auth_members m
    JOIN   pg_roles g ON g.oid = m.roleid
    JOIN   pg_roles r ON r.oid = m.member
    WHERE  g.rolname = 'studi_daba' AND r.rolname = 'postgres' AND m.admin_option
  ) THEN
    GRANT studi_daba TO postgres WITH ADMIN TRUE, INHERIT FALSE, SET FALSE;
  END IF;
END $$;

-- Pruefung: postgres hat ADMIN OPTION, erbt nichts, darf nicht SET ROLE.
DO $$
DECLARE v record;
BEGIN
  SELECT m.admin_option, m.inherit_option, m.set_option INTO v
  FROM   pg_auth_members m
  JOIN   pg_roles g ON g.oid = m.roleid
  JOIN   pg_roles r ON r.oid = m.member
  WHERE  g.rolname = 'studi_daba' AND r.rolname = 'postgres';
  IF v IS NULL OR NOT v.admin_option THEN
    RAISE EXCEPTION 'postgres hat keine ADMIN OPTION auf studi_daba';
  END IF;
  IF v.inherit_option OR v.set_option THEN
    RAISE EXCEPTION 'postgres erbt von studi_daba oder darf SET ROLE - nicht gewollt';
  END IF;
  RAISE NOTICE 'postgres verwaltet studi_daba (ADMIN OPTION), ohne Rechte zu erben';
END $$;

-- Ruecknahme:
--   REVOKE studi_daba FROM postgres;
