-- PostgreSQL 17, Datenbank postgres, als supabase_admin ausfuehren.
-- Eine Transaktion verwenden (psql -1 -v ON_ERROR_STOP=1 -f ...).
-- Repariert die effektiven Rechte, auch wenn sie ueber PUBLIC kommen.
-- Bestehende andere Rollen behalten ihre bisherigen Rechte. Neue Rollen
-- brauchen fuer die betroffenen Objekte danach ausdrueckliche Grants.
-- Nach neuen Datenbanken, Erweiterungsupdates und Rechteaenderungen erneut
-- ausfuehren/pruefen: ein spaeteres GRANT ... TO PUBLIC kann Rechte oeffnen.
-- Keine Nutzdaten werden veraendert. Laufende studi_daba-Sitzungen nach
-- erfolgreichem COMMIT neu verbinden, insbesondere in anderen Datenbanken.

SET LOCAL search_path = pg_catalog;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '2min';

DO $$
BEGIN
  IF current_database() <> 'postgres'
     OR NOT (SELECT rolsuper FROM pg_roles WHERE rolname = current_user) THEN
    RAISE EXCEPTION 'In postgres als Superuser ausfuehren; Teilkorrekturen sind nicht ausreichend';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'studi_daba') THEN
    RAISE EXCEPTION 'Zuerst aufbau/0020_demo_rolle.sql ausfuehren';
  END IF;
  IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'studi_daba'
             AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls))
     OR EXISTS (SELECT FROM pg_auth_members WHERE member = 'studi_daba'::regrole)
     OR EXISTS (SELECT FROM pg_shdepend WHERE refclassid = 'pg_authid'::regclass
                 AND refobjid = 'studi_daba'::regrole AND deptype = 'o') THEN
    RAISE EXCEPTION 'Unerwartete Sonderrechte, Mitgliedschaften oder Eigentum: zuerst separat klaeren';
  END IF;
  IF EXISTS (SELECT FROM pg_foreign_server WHERE has_server_privilege('studi_daba', oid, 'USAGE')) THEN
    RAISE EXCEPTION 'Unerwarteter Fremdserverzugriff: zuerst separat klaeren';
  END IF;
END $$;

-- Hilfsobjekte existieren nur in dieser Sitzung/Transaktion.
CREATE TEMP TABLE bm_readonly_deny (
  kind text, obj oid, subid integer DEFAULT 0, privilege text, object_sql text,
  PRIMARY KEY (kind, obj, subid, privilege)
) ON COMMIT DROP;

CREATE FUNCTION pg_temp.bm_has_priv(kind text, obj oid, subid integer, privilege text, who oid)
RETURNS boolean LANGUAGE sql AS $$
  SELECT CASE kind
    WHEN 'DATABASE' THEN has_database_privilege(who, obj, privilege)
    WHEN 'SCHEMA' THEN has_schema_privilege(who, obj, privilege)
    WHEN 'TABLE' THEN has_table_privilege(who, obj, privilege)
    WHEN 'COLUMN' THEN has_column_privilege(who, obj, subid::smallint, privilege)
    WHEN 'SEQUENCE' THEN has_sequence_privilege(who, obj, privilege)
    WHEN 'FUNCTION' THEN has_function_privilege(who, obj, privilege)
  END
$$;

-- Andere Datenbanken waeren ein Umweg zu dortigen PUBLIC-Schreibrechten.
INSERT INTO bm_readonly_deny(kind,obj,privilege,object_sql)
SELECT 'DATABASE', d.oid, p, format('DATABASE %I', datname)
FROM pg_database d CROSS JOIN unnest(ARRAY['CONNECT','CREATE','TEMPORARY']) p
WHERE (p <> 'CONNECT' OR datname <> current_database())
  AND has_database_privilege('studi_daba', d.oid, p);

INSERT INTO bm_readonly_deny(kind,obj,privilege,object_sql)
SELECT 'SCHEMA', n.oid, p, format('SCHEMA %I', nspname)
FROM pg_namespace n CROSS JOIN unnest(ARRAY['USAGE','CREATE']) p
WHERE nspname NOT LIKE 'pg_temp_%' AND nspname NOT LIKE 'pg_toast_temp_%'
  AND (p = 'CREATE' OR nspname NOT IN ('pg_catalog','information_schema','burgermetrics','wawi'))
  AND has_schema_privilege('studi_daba', n.oid, p);

INSERT INTO bm_readonly_deny(kind,obj,privilege,object_sql)
SELECT 'TABLE', c.oid, p, format('TABLE %I.%I', n.nspname, c.relname)
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
CROSS JOIN unnest(ARRAY['INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER','MAINTAIN']) p
WHERE c.relkind IN ('r','p','v','m','f') AND n.nspname NOT LIKE 'pg_temp_%'
  AND has_table_privilege('studi_daba', c.oid, p);

-- Spaltengrants gelten unabhaengig von einem REVOKE auf der ganzen Tabelle.
INSERT INTO bm_readonly_deny(kind,obj,subid,privilege,object_sql)
SELECT 'COLUMN', c.oid, a.attnum, p,
       format('(%I) ON TABLE %I.%I', a.attname, n.nspname, c.relname)
FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
CROSS JOIN unnest(ARRAY['INSERT','UPDATE','REFERENCES']) p
WHERE c.relkind IN ('r','p','v','m','f') AND a.attnum > 0 AND NOT a.attisdropped
  AND a.attacl IS NOT NULL AND n.nspname NOT LIKE 'pg_temp_%'
  AND has_column_privilege('studi_daba', c.oid, a.attnum, p);

INSERT INTO bm_readonly_deny(kind,obj,privilege,object_sql)
SELECT 'SEQUENCE', c.oid, p, format('SEQUENCE %I.%I', n.nspname, c.relname)
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
CROSS JOIN unnest(ARRAY['USAGE','UPDATE']) p
WHERE CASE WHEN c.relkind = 'S' THEN has_sequence_privilege('studi_daba', c.oid, p) ELSE false END;

-- SECURITY DEFINER umgeht Tabellenrechte. net hat zusaetzlich native
-- Funktionen mit Nebenwirkungen. LO/WAL-Funktionen schreiben ohne Schema-CREATE.
INSERT INTO bm_readonly_deny(kind,obj,privilege,object_sql)
SELECT 'FUNCTION', p.oid, 'EXECUTE', format('ROUTINE %I.%I(%s)',
       n.nspname, p.proname, pg_get_function_identity_arguments(p.oid))
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE (p.prosecdef OR n.nspname = 'net'
       OR (n.nspname = 'pg_catalog' AND p.proname IN (
         'lo_creat','lo_create','lo_from_bytea','lo_put','lo_unlink',
         'lo_truncate','lo_truncate64','lowrite','lo_import','lo_export',
         'pg_logical_emit_message')))
  AND p.oid <> 'burgermetrics.kurzname(text)'::regprocedure
  AND has_function_privilege('studi_daba', p.oid, 'EXECUTE');

-- Vorherige effektive Rechte aller anderen Rollen sichern. Die expliziten
-- Ersatzgrants geben niemandem mehr als zuvor durch PUBLIC/Mitgliedschaften.
CREATE TEMP TABLE bm_readonly_before ON COMMIT DROP AS
SELECT d.*, r.oid AS role_oid, r.rolname
FROM bm_readonly_deny d CROSS JOIN pg_roles r
WHERE r.rolname <> 'studi_daba'
  AND pg_temp.bm_has_priv(d.kind,d.obj,d.subid,d.privilege,r.oid);

DO $$
DECLARE d record; recipients text; clause text;
BEGIN
  FOR d IN SELECT * FROM bm_readonly_deny ORDER BY kind,obj,subid,privilege LOOP
    SELECT string_agg(format('%I',b.rolname), ', ' ORDER BY b.rolname)
      INTO recipients FROM bm_readonly_before b
      WHERE (b.kind,b.obj,b.subid,b.privilege) = (d.kind,d.obj,d.subid,d.privilege);
    clause := CASE WHEN d.kind = 'COLUMN' THEN d.privilege || ' ' || d.object_sql
                   ELSE d.privilege || ' ON ' || d.object_sql END;
    IF recipients IS NOT NULL THEN
      EXECUTE 'GRANT ' || clause || ' TO ' || recipients;
    END IF;
    EXECUTE 'REVOKE ' || clause || ' FROM PUBLIC, studi_daba';
  END LOOP;
  IF EXISTS (SELECT FROM bm_readonly_deny pending
             WHERE pg_temp.bm_has_priv(pending.kind,pending.obj,pending.subid,pending.privilege,'studi_daba'::regrole)) THEN
    RAISE EXCEPTION 'Mindestens ein effektives Recht blieb bestehen; gesamte Korrektur zurueckrollen';
  END IF;
  IF EXISTS (SELECT FROM bm_readonly_before b
             WHERE NOT pg_temp.bm_has_priv(b.kind,b.obj,b.subid,b.privilege,b.role_oid)) THEN
    RAISE EXCEPTION 'Eine andere Rolle verlor Rechte; gesamte Korrektur zurueckrollen';
  END IF;
  RAISE NOTICE '% effektive Rechte entfernt; % bestehende Rechte anderer Rollen erhalten',
    (SELECT count(*) FROM bm_readonly_deny), (SELECT count(*) FROM bm_readonly_before);
END $$;

-- Neue Routinen sind standardmaessig PUBLIC ausfuehrbar, auch DEFINER.
-- Nur globale Default-Privileges koennen diesen Standard entfernen.
-- Bestehende explizite Defaults bleiben bestehen. Neue Routinen brauchen
-- passende Grants: Ersatz-Defaults an alle Rollen wuerden Betreiberfunktionen
-- nach DROP/CREATE und REVOKE FROM PUBLIC wieder fuer diese Rollen oeffnen.
DO $$
DECLARE owner_row record; d record; schema_clause text; object_kind text;
BEGIN
  FOR owner_row IN
    SELECT r.oid,r.rolname FROM pg_roles r
    LEFT JOIN pg_default_acl a ON a.defaclrole=r.oid AND a.defaclnamespace=0 AND a.defaclobjtype='f'
    WHERE r.rolname <> 'studi_daba' AND r.rolname NOT LIKE 'pg_%'
      AND EXISTS (SELECT FROM aclexplode(COALESCE(a.defaclacl,acldefault('f',r.oid))) x
                   WHERE x.grantee=0 AND x.privilege_type='EXECUTE')
  LOOP
    EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE %I REVOKE EXECUTE ON ROUTINES FROM PUBLIC', owner_row.rolname);
  END LOOP;
  -- Explizite schemaweite PUBLIC-Defaults koennen globale Revokes ergaenzen.
  FOR d IN
    SELECT a.defaclrole::regrole::text AS owner_name,n.nspname,a.defaclobjtype,x.privilege_type
    FROM pg_default_acl a LEFT JOIN pg_namespace n ON n.oid=a.defaclnamespace,
         LATERAL aclexplode(a.defaclacl) x
    WHERE x.grantee=0 AND
      ((a.defaclobjtype='f' AND x.privilege_type='EXECUTE')
       OR (a.defaclobjtype='r' AND x.privilege_type <> 'SELECT')
       OR (a.defaclobjtype='S' AND x.privilege_type IN ('USAGE','UPDATE'))
       OR (a.defaclobjtype='n' AND x.privilege_type='CREATE'))
  LOOP
    schema_clause := CASE WHEN d.nspname IS NULL THEN '' ELSE format(' IN SCHEMA %I',d.nspname) END;
    object_kind := CASE d.defaclobjtype WHEN 'f' THEN 'ROUTINES' WHEN 'r' THEN 'TABLES'
                                         WHEN 'S' THEN 'SEQUENCES' WHEN 'n' THEN 'SCHEMAS' END;
    EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE %s%s REVOKE %s ON %s FROM PUBLIC',
                   d.owner_name,schema_clause,d.privilege_type,object_kind);
  END LOOP;
END $$;

-- Lesefunktion und der komplette Lehrbestand bleiben nutzbar.
DO $$
DECLARE total integer; readable integer;
BEGIN
  SELECT count(*), count(*) FILTER (WHERE has_table_privilege('studi_daba',c.oid,'SELECT'))
  INTO total,readable FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname IN ('burgermetrics','wawi') AND c.relkind IN ('r','p','v','m','f');
  IF total=0 OR total<>readable
     OR NOT has_function_privilege('studi_daba','burgermetrics.kurzname(text)','EXECUTE')
     OR NOT has_database_privilege('studi_daba',current_database(),'CONNECT')
     OR NOT has_schema_privilege('studi_daba','burgermetrics','USAGE')
     OR NOT has_schema_privilege('studi_daba','wawi','USAGE') THEN
    RAISE EXCEPTION 'Legitimer Lesezugriff fehlt; gesamte Korrektur zurueckrollen';
  END IF;
  RAISE NOTICE 'studi_daba: % Lehrdatenobjekte weiterhin lesbar',readable;
END $$;

DROP FUNCTION pg_temp.bm_has_priv(text,oid,integer,text,oid);
DROP TABLE bm_readonly_before, bm_readonly_deny;
