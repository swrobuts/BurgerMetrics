-- 0023_rezension_freigabe.sql
-- Zweck: Rezensionen aus dem Shop erscheinen erst nach einer Prüfung.
--        wawi.rezension bekommt einen Status. Der Prüfdienst (Rolle
--        bm_pruefdienst) trägt Jevs Urteil ein; Menschen mit den Rollen
--        moderation und qualitaet entscheiden im POS. Öffentlich lesbar sind
--        nur freigegebene Rezensionen, in den Sichten und über die Richtlinie
--        lesen_freigegeben auch in der Tabelle selbst.
--
--        Die Prüf- und Entscheidungstabellen liegen im Schema wawi_intern, das
--        die API nicht kennt und das keine schemaweiten Rechte aus 0018 und
--        0020 erreichen. Zeilenschutz und alle Rechte stehen an einer Stelle,
--        in wawi.freigabe_rechte() (Abschnitt 6); wawi.freigabe_pruefen()
--        prüft sie und bricht bei jeder Abweichung ab.
--
-- Aufruf (als postgres):
--   python3 db/skript_ausfuehren.py db/aufbau/0023_rezension_freigabe.sql
--
-- Voraussetzung: 0001–0022 sind gelaufen; das Supabase-Schema auth
--   (auth.users, auth.uid()) ist vorhanden.
-- Nach diesem Skript bricht 0021 gleich am Anfang ab; den Simulationsbestand
--   lädt db/betrieb/rezensionen_bestand_kopieren.sql neu. 0018 und 0020 rufen
--   an ihrem Ende wawi.freigabe_rechte() auf und öffnen deshalb nichts.
-- Idempotent: ja.
--
-- Rollen vergeben (einmalig, als postgres; die Konto-ID steht in auth.users,
-- weder ID noch E-Mail-Adresse gehören ins Repo):
--   INSERT INTO wawi_intern.mitarbeiter_rolle (konto, rolle)
--   VALUES ('<konto-id>', 'moderation'), ('<konto-id>', 'qualitaet')
--   ON CONFLICT DO NOTHING;
-- Das Passwort der Rolle bm_pruefdienst setzt pruefdienst/passwort_setzen.py.

-- Wartet höchstens fünf Sekunden auf Sperren, statt Shop und Anmeldung
-- hinter sich warten zu lassen.
SET LOCAL lock_timeout = '5s';

-- ---------------------------------------------------------------------------
-- 1 Status je Rezension. Der Simulationsbestand ist kuratiert und gilt als
--   freigegeben; Shop-Rezensionen beginnen offen.
-- ---------------------------------------------------------------------------
ALTER TABLE wawi.rezension ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'offen';

-- Setzt den Status des Simulationsbestands, auch wenn 0021 ihn nach einem
-- Neuladen der CSV erneut kopiert.
CREATE OR REPLACE FUNCTION wawi.rezension_status_vorgabe()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.quelle = 'simulation' THEN
    NEW.status := 'freigegeben';
  END IF;
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS rezension_status_vorgabe ON wawi.rezension;
CREATE TRIGGER rezension_status_vorgabe
  BEFORE INSERT ON wawi.rezension
  FOR EACH ROW EXECUTE FUNCTION wawi.rezension_status_vorgabe();

UPDATE wawi.rezension SET status = 'freigegeben'
WHERE  quelle = 'simulation' AND status <> 'freigegeben';

ALTER TABLE wawi.rezension DROP CONSTRAINT IF EXISTS rezension_status_gueltig;
ALTER TABLE wawi.rezension ADD CONSTRAINT rezension_status_gueltig
  CHECK (status IN ('offen', 'freigegeben', 'zurueckgehalten', 'abgelehnt'));
ALTER TABLE wawi.rezension DROP CONSTRAINT IF EXISTS rezension_simulation_freigegeben;
ALTER TABLE wawi.rezension ADD CONSTRAINT rezension_simulation_freigegeben
  CHECK (quelle <> 'simulation' OR status = 'freigegeben');

CREATE INDEX IF NOT EXISTS ix_wawi_rezension_artikel_status
  ON wawi.rezension (artikel_id, status, erstellt_am DESC);

COMMENT ON COLUMN wawi.rezension.status IS
  'offen (wartet auf den Prüfdienst), freigegeben (öffentlich lesbar), '
  'zurueckgehalten (wartet auf einen Menschen), abgelehnt (bleibt verborgen).';

-- rezension_anlegen() wie in 0021; die Rückgabe nennt zusätzlich den Status.
-- CREATE OR REPLACE erhält Signatur, Eigentümer und Rechte.
CREATE OR REPLACE FUNCTION wawi.rezension_anlegen(
  artikel_id  bigint,
  sterne      integer,
  inhalt      text,
  filiale_id  bigint DEFAULT NULL,
  sitzung     text   DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = wawi, pg_temp
AS $$
#variable_conflict use_variable
DECLARE
  v_jetzt     timestamptz := now();
  v_text      text        := btrim(regexp_replace(COALESCE(inhalt, ''), '\s+', ' ', 'g'));
  v_id        bigint;
  v_name      text;
  v_kuerzlich integer;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM artikel a WHERE a.artikel_id = artikel_id) THEN
    RAISE EXCEPTION 'unbekannter Artikel: %', artikel_id USING ERRCODE = '23503';
  END IF;
  IF sterne IS NULL OR sterne < 1 OR sterne > 5 THEN
    RAISE EXCEPTION 'sterne muss zwischen 1 und 5 liegen, nicht %', sterne USING ERRCODE = '22023';
  END IF;
  IF char_length(v_text) < 5 OR char_length(v_text) > 500 THEN
    RAISE EXCEPTION 'der Text braucht 5 bis 500 Zeichen, nicht %', char_length(v_text)
      USING ERRCODE = '22023';
  END IF;
  IF filiale_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM filiale f WHERE f.filiale_id = filiale_id) THEN
    RAISE EXCEPTION 'unbekannte Filiale: %', filiale_id USING ERRCODE = '23503';
  END IF;

  IF sitzung IS NOT NULL AND char_length(sitzung) > 100 THEN
    RAISE EXCEPTION 'sitzung darf höchstens 100 Zeichen lang sein' USING ERRCODE = '22023';
  END IF;

  -- Bremse je Sitzung: 20 Rezensionen in zehn Minuten; Aufrufe ohne Sitzung
  -- teilen sich einen gemeinsamen Eimer.
  SELECT count(*) INTO v_kuerzlich
  FROM   rezension r
  WHERE  r.sitzung IS NOT DISTINCT FROM sitzung
  AND    r.erstellt_am > v_jetzt - interval '10 minutes';
  IF v_kuerzlich >= 20 THEN
    RAISE EXCEPTION 'zu viele Rezensionen in kurzer Zeit — bitte kurz warten'
      USING ERRCODE = '53400';
  END IF;
  -- Notbremse insgesamt: 600 Shop-Rezensionen je Stunde.
  SELECT count(*) INTO v_kuerzlich
  FROM   rezension r
  WHERE  r.quelle = 'shop' AND r.erstellt_am > v_jetzt - interval '1 hour';
  IF v_kuerzlich >= 600 THEN
    RAISE EXCEPTION 'zu viele Rezensionen in der letzten Stunde — bitte später erneut'
      USING ERRCODE = '53400';
  END IF;

  INSERT INTO rezension (artikel_id, kunde_id, bestellung_id, filiale_id, sterne, inhalt,
                         erstellt_am, quelle, sitzung)
  VALUES (artikel_id, NULL, NULL, filiale_id, sterne, v_text, v_jetzt, 'shop', sitzung)
  RETURNING rezension.rezension_id INTO v_id;

  SELECT a.name INTO v_name FROM artikel a WHERE a.artikel_id = artikel_id;
  RETURN jsonb_build_object(
    'rezension_id', v_id,
    'artikel',      v_name,
    'sterne',       sterne,
    'erstellt_am',  v_jetzt,
    'quelle',       'shop',
    'status',       'offen');
END $$;

-- ---------------------------------------------------------------------------
-- 2 Prüfungen, Entscheidungen, QS-Fälle und Rollen im Schema wawi_intern.
--   Die API kennt es nicht; gelesen wird über Sichten in wawi, geschrieben
--   über Funktionen.
-- ---------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS wawi_intern;
COMMENT ON SCHEMA wawi_intern IS
  'Prüfungen, Entscheidungen, QS-Fälle und Rollen der Freigabe von Rezensionen. Nicht über '
  'die API erreichbar; gelesen wird über Sichten in wawi, geschrieben über Funktionen.';

CREATE TABLE IF NOT EXISTS wawi_intern.rezension_pruefung (
  pruefung_id          bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  rezension_id         bigint NOT NULL REFERENCES wawi.rezension(rezension_id) ON DELETE CASCADE,
  geprueft_am          timestamptz NOT NULL DEFAULT now(),
  modell               text,
  fragen_stand         text,
  fragen_fingerabdruck text,
  regel_version        text,
  p_beleidigung        double precision CHECK (p_beleidigung BETWEEN 0 AND 1),
  p_personenbezug      double precision CHECK (p_personenbezug BETWEEN 0 AND 1),
  p_werbung            double precision CHECK (p_werbung BETWEEN 0 AND 1),
  p_themenbezug        double precision CHECK (p_themenbezug BETWEEN 0 AND 1),
  p_anweisung          double precision CHECK (p_anweisung BETWEEN 0 AND 1),
  p_gesundheitsrisiko  double precision CHECK (p_gesundheitsrisiko BETWEEN 0 AND 1),
  muster_treffer       text[]  NOT NULL DEFAULT '{}',
  jev_angefragt        boolean NOT NULL DEFAULT false,
  ergebnis             text CHECK (ergebnis IN ('freigegeben', 'zurueckgehalten')),
  gruende              text[]  NOT NULL DEFAULT '{}',
  qs_fall              boolean NOT NULL DEFAULT false,
  input_tokens         integer CHECK (input_tokens >= 0),
  fehler               text
);
CREATE INDEX IF NOT EXISTS ix_wawi_rezension_pruefung_rezension
  ON wawi_intern.rezension_pruefung (rezension_id, geprueft_am DESC);
COMMENT ON TABLE wawi_intern.rezension_pruefung IS
  'Eine Zeile je Prüflauf: Jevs Wahrscheinlichkeiten, Mustertreffer, Ergebnis und Gründe. '
  'ergebnis bleibt leer, wenn der Lauf scheiterte (fehler gesetzt), außer beim dritten Fehlversuch.';

CREATE TABLE IF NOT EXISTS wawi_intern.rezension_entscheidung (
  entscheidung_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  rezension_id    bigint NOT NULL REFERENCES wawi.rezension(rezension_id) ON DELETE CASCADE,
  entscheidung    text NOT NULL CHECK (entscheidung IN ('freigegeben', 'abgelehnt')),
  entschieden_am  timestamptz NOT NULL DEFAULT now(),
  konto           uuid NOT NULL,
  bemerkung       text CHECK (char_length(bemerkung) <= 500)
);
COMMENT ON TABLE wawi_intern.rezension_entscheidung IS
  'Entscheidungen von Menschen im POS. konto ist die Supabase-Kennung; die Zeile bleibt, '
  'auch wenn das Konto später gelöscht wird.';

CREATE TABLE IF NOT EXISTS wawi_intern.qs_fall (
  qs_fall_id   bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  rezension_id bigint NOT NULL REFERENCES wawi.rezension(rezension_id) ON DELETE CASCADE,
  angelegt_am  timestamptz NOT NULL DEFAULT now(),
  erledigt_am  timestamptz,
  konto        uuid,
  bemerkung    text CHECK (char_length(bemerkung) <= 500),
  CONSTRAINT qs_fall_je_rezension UNIQUE (rezension_id)
);
COMMENT ON TABLE wawi_intern.qs_fall IS
  'Hinweis auf ein Gesundheitsrisiko für die Qualitätssicherung; erledigt setzt die Rolle qualitaet.';

CREATE TABLE IF NOT EXISTS wawi_intern.mitarbeiter_rolle (
  konto uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  rolle text NOT NULL CHECK (rolle IN ('moderation', 'qualitaet')),
  PRIMARY KEY (konto, rolle)
);
COMMENT ON TABLE wawi_intern.mitarbeiter_rolle IS
  'Rollen für die Moderation im POS, je Supabase-Konto. Vergeben nur durch postgres.';

-- Anmelderolle des Prüfdienstes: keine Tabellenrechte, nur die drei
-- Dienstfunktionen aus Abschnitt 3. Das Passwort setzt
-- pruefdienst/passwort_setzen.py.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bm_pruefdienst') THEN
    CREATE ROLE bm_pruefdienst LOGIN NOINHERIT CONNECTION LIMIT 3;
  END IF;
END $$;
ALTER ROLE bm_pruefdienst SET statement_timeout = '15s';

-- Hat das angemeldete Konto (auth.uid() aus dem JWT) diese Rolle?
-- Vereinfachtes Muster von velocity.hat_rolle: die Rolle hängt direkt am Konto.
CREATE OR REPLACE FUNCTION wawi.hat_rolle(p_rolle text)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = wawi, pg_temp
AS $$
  SELECT EXISTS (SELECT 1 FROM wawi_intern.mitarbeiter_rolle mr
                 WHERE mr.konto = auth.uid() AND mr.rolle = p_rolle);
$$;

-- ---------------------------------------------------------------------------
-- 3 Der Prüfdienst: drei Funktionen, sonst nichts. Sie laufen als postgres;
--   bm_pruefdienst darf nur sie ausführen.
-- ---------------------------------------------------------------------------

-- Offene Shop-Rezensionen, älteste zuerst. Nach einem gescheiterten Versuch
-- wartet eine Rezension fünf Minuten, damit ein kurzer Ausfall von Jev nicht
-- in drei schnellen Fehlversuchen endet.
CREATE OR REPLACE FUNCTION wawi.pruefung_offene_holen(p_anzahl integer)
RETURNS TABLE (rezension_id bigint, artikel text, inhalt text, erstellt_am timestamptz)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = wawi, pg_temp
AS $$
  SELECT r.rezension_id, a.name, r.inhalt, r.erstellt_am
  FROM   wawi.rezension r
  JOIN   wawi.artikel a ON a.artikel_id = r.artikel_id
  WHERE  r.status = 'offen'
  AND    r.quelle = 'shop'
  AND    NOT EXISTS (SELECT 1 FROM wawi_intern.rezension_pruefung p
                     WHERE p.rezension_id = r.rezension_id
                     AND   p.fehler IS NOT NULL
                     AND   p.geprueft_am > now() - interval '5 minutes')
  ORDER  BY r.erstellt_am, r.rezension_id
  LIMIT  least(greatest(p_anzahl, 1), 100);
$$;

-- Schreibt eine Prüfzeile, setzt den Status und legt bei Bedarf den QS-Fall
-- an, alles in einer Transaktion. Hat inzwischen ein Mensch entschieden,
-- bleibt alles, wie es ist. Beim dritten Fehlversuch hält die Funktion die
-- Rezension selbst zurück.
CREATE OR REPLACE FUNCTION wawi.pruefung_eintragen(
  rezension_id         bigint,
  ergebnis             text    DEFAULT NULL,
  gruende              text[]  DEFAULT '{}',
  qs_fall_anlegen      boolean DEFAULT false,
  wahrscheinlichkeiten jsonb   DEFAULT NULL,
  muster_treffer       text[]  DEFAULT '{}',
  jev_angefragt        boolean DEFAULT false,
  modell               text    DEFAULT NULL,
  fragen_stand         text    DEFAULT NULL,
  fragen_fingerabdruck text    DEFAULT NULL,
  regel_version        text    DEFAULT NULL,
  input_tokens         integer DEFAULT NULL,
  fehler               text    DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = wawi, pg_temp
AS $$
#variable_conflict use_variable
DECLARE
  v_status   text;
  v_fehler   integer;
  v_ergebnis text    := ergebnis;
  v_gruende  text[]  := coalesce(gruende, '{}');
  v_p        jsonb   := coalesce(wahrscheinlichkeiten, '{}'::jsonb);
BEGIN
  SELECT r.status INTO v_status
  FROM   wawi.rezension r
  WHERE  r.rezension_id = rezension_id AND r.quelle = 'shop'
  FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'unbekannte Shop-Rezension: %', rezension_id USING ERRCODE = '23503';
  END IF;
  IF v_status <> 'offen' THEN
    RETURN jsonb_build_object('rezension_id', rezension_id, 'status', v_status, 'uebersprungen', true);
  END IF;

  IF fehler IS NOT NULL THEN
    SELECT count(*) INTO v_fehler
    FROM   wawi_intern.rezension_pruefung p
    WHERE  p.rezension_id = rezension_id AND p.fehler IS NOT NULL;
    IF v_fehler >= 2 THEN
      v_ergebnis := 'zurueckgehalten';
      v_gruende  := ARRAY['Prüfung nicht möglich'];
    ELSE
      v_ergebnis := NULL;
    END IF;
  ELSIF v_ergebnis IS NULL OR v_ergebnis NOT IN ('freigegeben', 'zurueckgehalten') THEN
    RAISE EXCEPTION 'ergebnis muss freigegeben oder zurueckgehalten sein, nicht %', v_ergebnis
      USING ERRCODE = '22023';
  END IF;
  IF v_ergebnis = 'zurueckgehalten' AND cardinality(v_gruende) = 0 THEN
    RAISE EXCEPTION 'eine zurückgehaltene Rezension braucht einen Grund' USING ERRCODE = '22023';
  END IF;
  IF coalesce(qs_fall_anlegen, false) AND v_ergebnis IS DISTINCT FROM 'zurueckgehalten' THEN
    RAISE EXCEPTION 'ein QS-Fall hält die Rezension immer zurück' USING ERRCODE = '22023';
  END IF;

  INSERT INTO wawi_intern.rezension_pruefung
        (rezension_id, modell, fragen_stand, fragen_fingerabdruck, regel_version,
         p_beleidigung, p_personenbezug, p_werbung, p_themenbezug, p_anweisung,
         p_gesundheitsrisiko, muster_treffer, jev_angefragt, ergebnis, gruende, qs_fall,
         input_tokens, fehler)
  VALUES (rezension_id, modell, fragen_stand, fragen_fingerabdruck, regel_version,
          (v_p ->> 'beleidigung')::double precision, (v_p ->> 'personenbezug')::double precision,
          (v_p ->> 'werbung')::double precision, (v_p ->> 'themenbezug')::double precision,
          (v_p ->> 'anweisung')::double precision, (v_p ->> 'gesundheitsrisiko')::double precision,
          coalesce(muster_treffer, '{}'), coalesce(jev_angefragt, false), v_ergebnis, v_gruende,
          coalesce(qs_fall_anlegen, false), input_tokens, left(fehler, 500));

  IF v_ergebnis IS NOT NULL THEN
    UPDATE wawi.rezension r SET status = v_ergebnis WHERE r.rezension_id = rezension_id;
  END IF;
  IF coalesce(qs_fall_anlegen, false) THEN
    INSERT INTO wawi_intern.qs_fall (rezension_id) VALUES (rezension_id)
    ON CONFLICT ON CONSTRAINT qs_fall_je_rezension DO NOTHING;
  END IF;
  RETURN jsonb_build_object('rezension_id', rezension_id,
                            'status', coalesce(v_ergebnis, 'offen'),
                            'uebersprungen', false);
END $$;

-- Wie viele Anfragen an Jev hat der Prüfdienst heute gestellt (Europe/Berlin)?
-- Grundlage des Tageslimits; Zeilen ohne Anfrage (Tageslimit) zählen nicht.
CREATE OR REPLACE FUNCTION wawi.pruefung_heute()
RETURNS integer
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = wawi, pg_temp
AS $$
  SELECT count(*)::int
  FROM   wawi_intern.rezension_pruefung p
  WHERE  p.jev_angefragt
  AND    (p.geprueft_am AT TIME ZONE 'Europe/Berlin')::date
       = (now() AT TIME ZONE 'Europe/Berlin')::date;
$$;

-- ---------------------------------------------------------------------------
-- 4 Entscheidungen von Menschen. Nur angemeldete Konten mit Rolle; ablehnen
--   kann nur ein Mensch.
-- ---------------------------------------------------------------------------

-- Gemeinsamer Weg für Freigeben und Ablehnen: Rolle prüfen, Zustand prüfen,
-- Entscheidung festhalten, Status setzen. Nicht direkt aufrufbar.
CREATE OR REPLACE FUNCTION wawi.rezension_entscheiden(rezension_id bigint, entscheidung text, bemerkung text)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = wawi, pg_temp
AS $$
#variable_conflict use_variable
DECLARE
  v_konto  uuid := auth.uid();
  v_status text;
BEGIN
  IF v_konto IS NULL OR NOT wawi.hat_rolle('moderation') THEN
    RAISE EXCEPTION 'keine Berechtigung: die Rolle moderation fehlt' USING ERRCODE = '42501';
  END IF;
  IF bemerkung IS NOT NULL AND char_length(bemerkung) > 500 THEN
    RAISE EXCEPTION 'die Bemerkung darf höchstens 500 Zeichen lang sein' USING ERRCODE = '22023';
  END IF;
  SELECT r.status INTO v_status
  FROM   wawi.rezension r
  WHERE  r.rezension_id = rezension_id AND r.quelle = 'shop'
  FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'unbekannte Shop-Rezension: %', rezension_id USING ERRCODE = '23503';
  END IF;
  IF v_status NOT IN ('offen', 'zurueckgehalten') THEN
    RAISE EXCEPTION 'über die Rezension % ist schon entschieden (%)', rezension_id, v_status
      USING ERRCODE = '55000';
  END IF;
  INSERT INTO wawi_intern.rezension_entscheidung (rezension_id, entscheidung, konto, bemerkung)
  VALUES (rezension_id, entscheidung, v_konto, nullif(btrim(bemerkung), ''));
  UPDATE wawi.rezension r SET status = entscheidung WHERE r.rezension_id = rezension_id;
  RETURN jsonb_build_object('rezension_id', rezension_id, 'status', entscheidung);
END $$;

-- Gibt eine offene oder zurückgehaltene Shop-Rezension frei (Rolle moderation).
CREATE OR REPLACE FUNCTION wawi.api_rezension_freigeben(rezension_id bigint, bemerkung text DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = wawi, pg_temp
AS $$
#variable_conflict use_variable
BEGIN
  RETURN wawi.rezension_entscheiden(rezension_id, 'freigegeben', bemerkung);
END $$;

-- Lehnt eine offene oder zurückgehaltene Shop-Rezension ab (Rolle moderation).
CREATE OR REPLACE FUNCTION wawi.api_rezension_ablehnen(rezension_id bigint, bemerkung text DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = wawi, pg_temp
AS $$
#variable_conflict use_variable
BEGIN
  RETURN wawi.rezension_entscheiden(rezension_id, 'abgelehnt', bemerkung);
END $$;

-- Schließt einen QS-Fall (Rolle qualitaet). Die Rezension selbst bleibt,
-- wie sie ist; über sie entscheidet die Moderation.
CREATE OR REPLACE FUNCTION wawi.api_qs_fall_erledigen(qs_fall_id bigint, bemerkung text DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = wawi, pg_temp
AS $$
#variable_conflict use_variable
DECLARE
  v_konto    uuid := auth.uid();
  v_erledigt timestamptz;
  v_jetzt    timestamptz := now();
BEGIN
  IF v_konto IS NULL OR NOT wawi.hat_rolle('qualitaet') THEN
    RAISE EXCEPTION 'keine Berechtigung: die Rolle qualitaet fehlt' USING ERRCODE = '42501';
  END IF;
  IF bemerkung IS NOT NULL AND char_length(bemerkung) > 500 THEN
    RAISE EXCEPTION 'die Bemerkung darf höchstens 500 Zeichen lang sein' USING ERRCODE = '22023';
  END IF;
  SELECT q.erledigt_am INTO v_erledigt
  FROM   wawi_intern.qs_fall q
  WHERE  q.qs_fall_id = qs_fall_id
  FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'unbekannter QS-Fall: %', qs_fall_id USING ERRCODE = '23503';
  END IF;
  IF v_erledigt IS NOT NULL THEN
    RAISE EXCEPTION 'der QS-Fall % ist schon erledigt', qs_fall_id USING ERRCODE = '55000';
  END IF;
  UPDATE wawi_intern.qs_fall q
  SET    erledigt_am = v_jetzt, konto = v_konto, bemerkung = nullif(btrim(bemerkung), '')
  WHERE  q.qs_fall_id = qs_fall_id;
  RETURN jsonb_build_object('qs_fall_id', qs_fall_id, 'erledigt_am', v_jetzt);
END $$;

-- ---------------------------------------------------------------------------
-- 5 Sichten. Bestehende Sichten werden mit CREATE OR REPLACE geändert; neue
--   Spalten stehen hinten, Rechte bleiben erhalten. Die Rechte der neuen
--   Sichten setzt Abschnitt 6.
-- ---------------------------------------------------------------------------

-- ETL: nur freigegebene Rezensionen gehen ins Warehouse. etl_probe()
-- vergleicht über dieselbe Sicht.
CREATE OR REPLACE VIEW wawi.stg_fact_reviews AS
SELECT r.rezension_id                                          AS review_id,
       (r.erstellt_am AT TIME ZONE 'Europe/Berlin')::date       AS date,
       date_trunc('second', r.erstellt_am AT TIME ZONE 'Europe/Berlin')::time AS time,
       r.kunde_id                                              AS customer_id,
       r.artikel_id                                            AS product_id,
       r.filiale_id                                            AS branch_id,
       r.bestellung_id                                         AS order_id,
       r.sterne                                                AS stars,
       r.inhalt                                                AS review_text,
       r.quelle                                                AS source
FROM   wawi.rezension r
WHERE  r.status = 'freigegeben';

-- Bewertungsstand je Artikel mit Verteilung der Sterne, nur freigegebene.
CREATE OR REPLACE VIEW wawi.v_rezension_produkt AS
SELECT a.artikel_id,
       a.name,
       count(r.rezension_id)::int                                   AS anzahl,
       round(avg(r.sterne), 1)                                      AS sterne_mittel,
       max((r.erstellt_am AT TIME ZONE 'Europe/Berlin')::date)      AS letzte,
       (count(r.rezension_id) FILTER (WHERE r.sterne = 1))::int      AS anzahl_1,
       (count(r.rezension_id) FILTER (WHERE r.sterne = 2))::int      AS anzahl_2,
       (count(r.rezension_id) FILTER (WHERE r.sterne = 3))::int      AS anzahl_3,
       (count(r.rezension_id) FILTER (WHERE r.sterne = 4))::int      AS anzahl_4,
       (count(r.rezension_id) FILTER (WHERE r.sterne = 5))::int      AS anzahl_5
FROM   wawi.artikel a
LEFT JOIN wawi.rezension r ON r.artikel_id = a.artikel_id AND r.status = 'freigegeben'
GROUP  BY a.artikel_id, a.name
ORDER  BY a.artikel_id;
COMMENT ON VIEW wawi.v_rezension_produkt IS
  'Je Artikel: Anzahl, mittlere Sterne und Verteilung der freigegebenen Rezensionen.';

-- Die drei jüngsten freigegebenen Rezensionen je Artikel, beide Quellen.
CREATE OR REPLACE VIEW wawi.v_kundenstimmen AS
SELECT s.artikel_id, s.rezension_id, s.sterne, s.inhalt,
       (s.erstellt_am AT TIME ZONE 'Europe/Berlin')::date AS datum
FROM  (SELECT r.*,
              row_number() OVER (PARTITION BY r.artikel_id
                                 ORDER BY r.erstellt_am DESC, r.rezension_id DESC) AS rang
       FROM   wawi.rezension r
       WHERE  r.status = 'freigegeben') s
WHERE  s.rang <= 3
ORDER  BY s.artikel_id, s.rang;
COMMENT ON VIEW wawi.v_kundenstimmen IS
  'Die drei jüngsten freigegebenen Rezensionen je Artikel, aus Simulation und Shop.';

-- Die 50 jüngsten Shop-Rezensionen mit Status; den Text erst nach der Freigabe.
CREATE OR REPLACE VIEW wawi.v_rezension_letzte AS
SELECT r.rezension_id,
       r.sitzung,
       a.name                              AS artikel,
       f.name                              AS filiale,
       r.sterne,
       CASE WHEN r.status = 'freigegeben' THEN r.inhalt END AS inhalt,
       r.erstellt_am,
       EXISTS (SELECT 1 FROM burgermetrics.fact_reviews x
               WHERE x.review_id = r.rezension_id) AS im_warehouse,
       r.status
FROM   wawi.rezension r
JOIN   wawi.artikel a ON a.artikel_id = r.artikel_id
LEFT JOIN wawi.filiale f ON f.filiale_id = r.filiale_id
WHERE  r.quelle = 'shop'
ORDER  BY r.erstellt_am DESC
LIMIT  50;
COMMENT ON VIEW wawi.v_rezension_letzte IS
  'Die 50 jüngsten Übungsrezensionen aus dem Shop mit Status; inhalt nur, wenn freigegeben.';

-- Leseansicht im Shop: freigegebene Rezensionen, gefiltert und seitenweise
-- über PostgREST (artikel_id, sterne, order, limit, offset).
CREATE OR REPLACE VIEW wawi.v_rezensionen_lesen AS
SELECT r.artikel_id,
       r.rezension_id,
       r.sterne,
       r.inhalt,
       (r.erstellt_am AT TIME ZONE 'Europe/Berlin')::date AS datum,
       r.erstellt_am,
       r.quelle,
       r.status
FROM   wawi.rezension r
WHERE  r.status = 'freigegeben';
COMMENT ON VIEW wawi.v_rezensionen_lesen IS
  'Freigegebene Rezensionen für die Leseansicht im Shop.';

-- Status jeder Shop-Rezension ohne Text, für den Datenmodus des Shops.
CREATE OR REPLACE VIEW wawi.v_rezension_status AS
SELECT r.rezension_id, r.status
FROM   wawi.rezension r
WHERE  r.quelle = 'shop';

-- Arbeitsliste der Moderation: zurückgehaltene Rezensionen und offene, die
-- länger als fünf Minuten warten, mit der jüngsten Prüfung.
CREATE OR REPLACE VIEW wawi.v_moderation AS
SELECT r.rezension_id, r.status, a.name AS artikel, f.name AS filiale, r.sterne, r.inhalt,
       r.erstellt_am, p.geprueft_am, p.gruende, p.qs_fall, p.muster_treffer, p.fehler,
       p.p_beleidigung, p.p_personenbezug, p.p_werbung, p.p_themenbezug, p.p_anweisung,
       p.p_gesundheitsrisiko
FROM   wawi.rezension r
JOIN   wawi.artikel a ON a.artikel_id = r.artikel_id
LEFT JOIN wawi.filiale f ON f.filiale_id = r.filiale_id
LEFT JOIN LATERAL (SELECT x.* FROM wawi_intern.rezension_pruefung x
                   WHERE x.rezension_id = r.rezension_id
                   ORDER BY x.geprueft_am DESC, x.pruefung_id DESC
                   LIMIT 1) p ON true
WHERE  wawi.hat_rolle('moderation')
AND    r.quelle = 'shop'
AND   (r.status = 'zurueckgehalten'
       OR (r.status = 'offen' AND r.erstellt_am < now() - interval '5 minutes'))
ORDER  BY r.erstellt_am;

-- Offene QS-Fälle mit Text, nur für die Qualitätssicherung.
CREATE OR REPLACE VIEW wawi.v_qs_faelle AS
SELECT q.qs_fall_id, q.rezension_id, q.angelegt_am, a.name AS artikel, f.name AS filiale,
       r.sterne, r.inhalt, r.erstellt_am, r.status, p.p_gesundheitsrisiko
FROM   wawi_intern.qs_fall q
JOIN   wawi.rezension r ON r.rezension_id = q.rezension_id
JOIN   wawi.artikel a ON a.artikel_id = r.artikel_id
LEFT JOIN wawi.filiale f ON f.filiale_id = r.filiale_id
LEFT JOIN LATERAL (SELECT x.p_gesundheitsrisiko FROM wawi_intern.rezension_pruefung x
                   WHERE x.rezension_id = r.rezension_id
                   ORDER BY x.geprueft_am DESC, x.pruefung_id DESC
                   LIMIT 1) p ON true
WHERE  wawi.hat_rolle('qualitaet')
AND    q.erledigt_am IS NULL
ORDER  BY q.angelegt_am;

-- Die letzten 20 Entscheidungen, zum Nachsehen im POS.
CREATE OR REPLACE VIEW wawi.v_entscheidungen_letzte AS
SELECT e.entscheidung_id, e.rezension_id, e.entscheidung, e.entschieden_am, e.bemerkung,
       a.name AS artikel, r.sterne, r.inhalt
FROM   wawi_intern.rezension_entscheidung e
JOIN   wawi.rezension r ON r.rezension_id = e.rezension_id
JOIN   wawi.artikel a ON a.artikel_id = r.artikel_id
WHERE  wawi.hat_rolle('moderation')
ORDER  BY e.entschieden_am DESC, e.entscheidung_id DESC
LIMIT  20;

-- Zustand des Prüfdienstes ohne Texte, auch ohne Anmeldung lesbar.
CREATE OR REPLACE VIEW wawi.v_pruefdienst_stand AS
SELECT (SELECT max(p.geprueft_am) FROM wawi_intern.rezension_pruefung p)                  AS letzte_pruefung,
       (SELECT count(*)::int FROM wawi.rezension r
        WHERE r.status = 'offen' AND r.quelle = 'shop')                            AS offen,
       (SELECT floor(extract(epoch FROM now() - min(r.erstellt_am)) / 60)::int
        FROM wawi.rezension r WHERE r.status = 'offen' AND r.quelle = 'shop')       AS aelteste_offene_min,
       (SELECT count(*)::int FROM wawi.rezension r WHERE r.status = 'zurueckgehalten') AS zurueckgehalten,
       (SELECT count(*)::int FROM wawi_intern.qs_fall q WHERE q.erledigt_am IS NULL)      AS qs_offen;

-- Shop-Rezensionen je Tag und Status, ohne Texte; für Notebook 09.
CREATE OR REPLACE VIEW wawi.v_freigabe_statistik AS
SELECT (r.erstellt_am AT TIME ZONE 'Europe/Berlin')::date AS tag, r.status, count(*)::int AS anzahl
FROM   wawi.rezension r
WHERE  r.quelle = 'shop'
GROUP  BY 1, 2
ORDER  BY 1, 2;

-- ---------------------------------------------------------------------------
-- 6 Zeilenschutz und Rechte an einer Stelle. freigabe_rechte() setzt sie,
--   freigabe_pruefen() prüft sie und bricht bei jeder Abweichung ab; beide
--   darf nur postgres aufrufen. 0018 und 0020 rufen freigabe_rechte() an
--   ihrem Ende auf: Ihre schemaweiten Grants und die Richtlinie lesen_alle
--   öffneten sonst ungeprüfte Rezensionen.
-- ---------------------------------------------------------------------------

-- Prüft Status, Zeilenschutz und Rechte der Freigabe. Sammelt jede
-- Abweichung und bricht mit allen zusammen ab.
CREATE OR REPLACE FUNCTION wawi.freigabe_pruefen()
RETURNS void
LANGUAGE plpgsql
SET search_path = wawi, pg_temp
AS $$
DECLARE
  v_rollen  text[] := ARRAY['public', 'anon', 'authenticated', 'studi_daba', 'bm_pruefdienst'];
  v_befunde text[] := '{}';
  v_rolle   text;
  v_anzahl  bigint;
  v_liste   text;
  r         record;
BEGIN
  SELECT count(*) INTO v_anzahl FROM wawi.rezension
  WHERE  quelle = 'simulation' AND status <> 'freigegeben';
  IF v_anzahl > 0 THEN
    v_befunde := v_befunde || format('%s Simulationszeilen sind nicht freigegeben', v_anzahl);
  END IF;

  -- wawi.rezension: Zeilenschutz an, genau eine Richtlinie für alle Rollen.
  IF NOT (SELECT c.relrowsecurity FROM pg_class c WHERE c.oid = 'wawi.rezension'::regclass) THEN
    v_befunde := v_befunde || 'Zeilenschutz auf wawi.rezension ist aus'::text;
  END IF;
  IF (SELECT count(*) FROM pg_policies p
      WHERE p.schemaname = 'wawi' AND p.tablename = 'rezension') <> 1
     OR NOT EXISTS (SELECT 1 FROM pg_policies p
                    WHERE  p.schemaname = 'wawi' AND p.tablename = 'rezension'
                    AND    p.policyname = 'lesen_freigegeben' AND p.permissive = 'PERMISSIVE'
                    AND    p.roles = '{public}'::name[] AND p.cmd = 'SELECT'
                    AND    p.qual = '(status = ''freigegeben''::text)') THEN
    v_befunde := v_befunde || 'wawi.rezension braucht genau die Richtlinie lesen_freigegeben'::text;
  END IF;

  -- wawi.rezension lesen alle (der Zeilenschutz filtert), ändern keiner.
  FOREACH v_rolle IN ARRAY v_rollen LOOP
    IF has_any_column_privilege(v_rolle, 'wawi.rezension', 'INSERT, UPDATE, REFERENCES')
       OR has_table_privilege(v_rolle, 'wawi.rezension', 'DELETE, TRUNCATE, TRIGGER') THEN
      v_befunde := v_befunde || format('%s darf wawi.rezension ändern', v_rolle);
    END IF;
  END LOOP;

  -- wawi_intern: Zeilenschutz an, keine Richtlinie, für keine Rolle erreichbar.
  FOR r IN SELECT c.oid, c.relname, c.relkind, c.relrowsecurity
           FROM   pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE  n.nspname = 'wawi_intern' AND c.relkind IN ('r', 'p', 'S') LOOP
    IF r.relkind <> 'S' AND NOT r.relrowsecurity THEN
      v_befunde := v_befunde || format('Zeilenschutz auf wawi_intern.%s ist aus', r.relname);
    END IF;
    FOREACH v_rolle IN ARRAY v_rollen LOOP
      IF (CASE WHEN r.relkind = 'S'
               THEN has_sequence_privilege(v_rolle, r.oid, 'USAGE, SELECT, UPDATE')
               ELSE has_any_column_privilege(v_rolle, r.oid, 'SELECT, INSERT, UPDATE, REFERENCES')
                    OR has_table_privilege(v_rolle, r.oid, 'DELETE, TRUNCATE, TRIGGER') END) THEN
        v_befunde := v_befunde || format('%s hat Rechte auf wawi_intern.%s', v_rolle, r.relname);
      END IF;
    END LOOP;
  END LOOP;
  IF EXISTS (SELECT 1 FROM pg_policies p WHERE p.schemaname = 'wawi_intern') THEN
    v_befunde := v_befunde || 'auf wawi_intern gehört keine Richtlinie'::text;
  END IF;
  FOREACH v_rolle IN ARRAY v_rollen LOOP
    IF has_schema_privilege(v_rolle, 'wawi_intern', 'USAGE, CREATE') THEN
      v_befunde := v_befunde || format('%s darf das Schema wawi_intern benutzen', v_rolle);
    END IF;
  END LOOP;

  -- Der Prüfdienst liest in wawi nichts; er ruft nur seine Funktionen auf.
  SELECT string_agg('wawi.' || c.relname, ', ' ORDER BY c.relname) INTO v_liste
  FROM   pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE  n.nspname = 'wawi'
  AND    CASE WHEN c.relkind = 'S'
              THEN has_sequence_privilege('bm_pruefdienst', c.oid, 'USAGE, SELECT, UPDATE')
              WHEN c.relkind IN ('r', 'p', 'v', 'm', 'f')
              THEN has_any_column_privilege('bm_pruefdienst', c.oid, 'SELECT, INSERT, UPDATE, REFERENCES')
                   OR has_table_privilege('bm_pruefdienst', c.oid, 'DELETE, TRUNCATE, TRIGGER')
              ELSE false END;
  IF v_liste IS NOT NULL THEN
    v_befunde := v_befunde || format('bm_pruefdienst hat Rechte auf %s', v_liste);
  END IF;
  IF NOT has_schema_privilege('bm_pruefdienst', 'wawi', 'USAGE') THEN
    v_befunde := v_befunde || 'bm_pruefdienst fehlt USAGE auf wawi'::text;
  END IF;

  -- Sichten: SELECT genau für die vorgesehenen Rollen, ändern für keine.
  FOR r IN SELECT s.sicht, s.leser
           FROM  (VALUES ('wawi.v_rezensionen_lesen',     ARRAY['anon', 'authenticated', 'studi_daba']),
                         ('wawi.v_rezension_status',      ARRAY['anon', 'authenticated', 'studi_daba']),
                         ('wawi.v_pruefdienst_stand',     ARRAY['anon', 'authenticated', 'studi_daba']),
                         ('wawi.v_moderation',            ARRAY['authenticated', 'studi_daba']),
                         ('wawi.v_qs_faelle',             ARRAY['authenticated', 'studi_daba']),
                         ('wawi.v_entscheidungen_letzte', ARRAY['authenticated', 'studi_daba']),
                         ('wawi.v_freigabe_statistik',    ARRAY['studi_daba'])) AS s (sicht, leser) LOOP
    FOREACH v_rolle IN ARRAY v_rollen LOOP
      IF v_rolle = ANY (r.leser) AND NOT has_table_privilege(v_rolle, r.sicht, 'SELECT') THEN
        v_befunde := v_befunde || format('%s fehlt SELECT auf %s', v_rolle, r.sicht);
      ELSIF v_rolle <> ALL (r.leser) AND has_any_column_privilege(v_rolle, r.sicht, 'SELECT') THEN
        v_befunde := v_befunde || format('%s liest %s', v_rolle, r.sicht);
      END IF;
      IF has_any_column_privilege(v_rolle, r.sicht, 'INSERT, UPDATE, REFERENCES')
         OR has_table_privilege(v_rolle, r.sicht, 'DELETE, TRUNCATE, TRIGGER') THEN
        v_befunde := v_befunde || format('%s darf %s ändern', v_rolle, r.sicht);
      END IF;
    END LOOP;
  END LOOP;

  -- Funktionen: EXECUTE genau für die vorgesehenen Rollen.
  FOR r IN SELECT f.funktion, f.aufrufer
           FROM  (VALUES
             ('wawi.rezension_anlegen(bigint, integer, text, bigint, text)', ARRAY['anon', 'authenticated']),
             ('wawi.hat_rolle(text)',                          ARRAY['authenticated']),
             ('wawi.api_rezension_freigeben(bigint, text)',    ARRAY['authenticated']),
             ('wawi.api_rezension_ablehnen(bigint, text)',     ARRAY['authenticated']),
             ('wawi.api_qs_fall_erledigen(bigint, text)',      ARRAY['authenticated']),
             ('wawi.pruefung_offene_holen(integer)',           ARRAY['bm_pruefdienst']),
             ('wawi.pruefung_heute()',                         ARRAY['bm_pruefdienst']),
             ('wawi.pruefung_eintragen(bigint, text, text[], boolean, jsonb, text[], boolean, text, text, text, text, integer, text)',
                                                               ARRAY['bm_pruefdienst']),
             ('wawi.rezension_entscheiden(bigint, text, text)', ARRAY[]::text[]),
             ('wawi.rezension_status_vorgabe()',               ARRAY[]::text[]),
             ('wawi.freigabe_rechte()',                        ARRAY[]::text[]),
             ('wawi.freigabe_pruefen()',                       ARRAY[]::text[])) AS f (funktion, aufrufer) LOOP
    FOREACH v_rolle IN ARRAY v_rollen LOOP
      IF v_rolle = ANY (r.aufrufer) AND NOT has_function_privilege(v_rolle, r.funktion, 'EXECUTE') THEN
        v_befunde := v_befunde || format('%s fehlt EXECUTE auf %s', v_rolle, r.funktion);
      ELSIF v_rolle <> ALL (r.aufrufer) AND has_function_privilege(v_rolle, r.funktion, 'EXECUTE') THEN
        v_befunde := v_befunde || format('%s darf %s ausführen', v_rolle, r.funktion);
      END IF;
    END LOOP;
  END LOOP;

  IF cardinality(v_befunde) > 0 THEN
    RAISE EXCEPTION 'Freigabe nicht wie vorgesehen: %', array_to_string(v_befunde, '; ');
  END IF;
  RAISE NOTICE 'Freigabe: Status, Zeilenschutz und Rechte wie vorgesehen.';
END $$;

-- Setzt Zeilenschutz und Rechte der Freigabe neu und prüft sie danach.
-- Läuft am Ende dieses Skripts und am Ende von 0018 und 0020.
CREATE OR REPLACE FUNCTION wawi.freigabe_rechte()
RETURNS void
LANGUAGE plpgsql
SET search_path = wawi, pg_temp
AS $$
DECLARE
  r record;
BEGIN
  -- Zeilenschutz: wawi.rezension zeigt nur freigegebene Zeilen, die Tabellen
  -- in wawi_intern zeigen keine. Andere Richtlinien (lesen_alle aus 0018 und
  -- 0021) fallen weg.
  FOR r IN SELECT p.schemaname, p.tablename, p.policyname
           FROM   pg_policies p
           WHERE (p.schemaname = 'wawi' AND p.tablename = 'rezension')
           OR     p.schemaname = 'wawi_intern' LOOP
    EXECUTE format('DROP POLICY %I ON %I.%I', r.policyname, r.schemaname, r.tablename);
  END LOOP;
  ALTER TABLE wawi.rezension ENABLE ROW LEVEL SECURITY;
  CREATE POLICY lesen_freigegeben ON wawi.rezension FOR SELECT USING (status = 'freigegeben');
  FOR r IN SELECT c.relname
           FROM   pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE  n.nspname = 'wawi_intern' AND c.relkind IN ('r', 'p') LOOP
    EXECUTE format('ALTER TABLE wawi_intern.%I ENABLE ROW LEVEL SECURITY', r.relname);
  END LOOP;

  -- wawi_intern erreicht nur postgres.
  REVOKE ALL ON SCHEMA wawi_intern FROM PUBLIC, anon, authenticated, studi_daba, bm_pruefdienst;
  REVOKE ALL ON ALL TABLES IN SCHEMA wawi_intern
    FROM PUBLIC, anon, authenticated, studi_daba, bm_pruefdienst;
  REVOKE ALL ON ALL SEQUENCES IN SCHEMA wawi_intern
    FROM PUBLIC, anon, authenticated, studi_daba, bm_pruefdienst;

  -- wawi.rezension ändern nur die Funktionen, die als postgres laufen.
  REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON wawi.rezension
    FROM PUBLIC, anon, authenticated, studi_daba;

  -- Der Prüfdienst liest in wawi nichts; er ruft nur seine drei Funktionen auf.
  REVOKE ALL ON ALL TABLES IN SCHEMA wawi FROM bm_pruefdienst;
  REVOKE ALL ON ALL SEQUENCES IN SCHEMA wawi FROM bm_pruefdienst;
  GRANT USAGE ON SCHEMA wawi TO bm_pruefdienst;

  -- Sichten (Spezifikation, Abschnitt 5.3). studi_daba darf die drei
  -- Moderationssichten lesen, weil 0020 alles in wawi lesbar hält. Abfragen
  -- scheitern trotzdem, weil nur authenticated hat_rolle() ausführen darf:
  -- Ein direkt angemeldetes Konto könnte sich sonst über request.jwt.claims
  -- als Moderator ausgeben.
  REVOKE ALL ON wawi.v_rezensionen_lesen, wawi.v_rezension_status, wawi.v_pruefdienst_stand,
                wawi.v_moderation, wawi.v_qs_faelle, wawi.v_entscheidungen_letzte,
                wawi.v_freigabe_statistik
    FROM PUBLIC, anon, authenticated, studi_daba, bm_pruefdienst;
  GRANT SELECT ON wawi.v_rezensionen_lesen, wawi.v_rezension_status, wawi.v_pruefdienst_stand
    TO anon, authenticated, studi_daba;
  GRANT SELECT ON wawi.v_moderation, wawi.v_qs_faelle, wawi.v_entscheidungen_letzte
    TO authenticated, studi_daba;
  GRANT SELECT ON wawi.v_freigabe_statistik TO studi_daba;

  -- Funktionen: erst allen alles entziehen, dann gezielt erlauben.
  REVOKE ALL ON FUNCTION wawi.rezension_anlegen(bigint, integer, text, bigint, text),
    wawi.hat_rolle(text), wawi.rezension_status_vorgabe(),
    wawi.pruefung_offene_holen(integer), wawi.pruefung_heute(),
    wawi.pruefung_eintragen(bigint, text, text[], boolean, jsonb, text[], boolean, text, text, text,
                            text, integer, text),
    wawi.rezension_entscheiden(bigint, text, text), wawi.api_rezension_freigeben(bigint, text),
    wawi.api_rezension_ablehnen(bigint, text), wawi.api_qs_fall_erledigen(bigint, text),
    wawi.freigabe_rechte(), wawi.freigabe_pruefen()
    FROM PUBLIC, anon, authenticated, studi_daba, bm_pruefdienst;
  GRANT EXECUTE ON FUNCTION wawi.rezension_anlegen(bigint, integer, text, bigint, text)
    TO anon, authenticated;
  GRANT EXECUTE ON FUNCTION wawi.hat_rolle(text), wawi.api_rezension_freigeben(bigint, text),
    wawi.api_rezension_ablehnen(bigint, text), wawi.api_qs_fall_erledigen(bigint, text)
    TO authenticated;
  GRANT EXECUTE ON FUNCTION wawi.pruefung_offene_holen(integer), wawi.pruefung_heute(),
    wawi.pruefung_eintragen(bigint, text, text[], boolean, jsonb, text[], boolean, text, text, text,
                            text, integer, text)
    TO bm_pruefdienst;

  PERFORM wawi.freigabe_pruefen();
END $$;

-- Rechte setzen und prüfen; bricht bei jeder Abweichung ab.
SELECT wawi.freigabe_rechte();

-- Auf dem VPS wirkt NOTIFY nicht (PGRST_DB_CHANNEL_ENABLED=false); dort nach
-- dem Einspielen den Container supabase-rest neu starten.
NOTIFY pgrst, 'reload schema';

-- Rücknahme (als postgres, in dieser Reihenfolge; vorher den Prüfdienst auf
-- dem VPS anhalten):
--   DROP VIEW wawi.v_freigabe_statistik, wawi.v_pruefdienst_stand, wawi.v_entscheidungen_letzte,
--             wawi.v_qs_faelle, wawi.v_moderation, wawi.v_rezension_status, wawi.v_rezensionen_lesen;
--   DROP FUNCTION wawi.freigabe_rechte(), wawi.freigabe_pruefen(),
--                 wawi.api_qs_fall_erledigen(bigint, text), wawi.api_rezension_ablehnen(bigint, text),
--                 wawi.api_rezension_freigeben(bigint, text), wawi.rezension_entscheiden(bigint, text, text),
--                 wawi.pruefung_heute(), wawi.pruefung_offene_holen(integer),
--                 wawi.pruefung_eintragen(bigint, text, text[], boolean, jsonb, text[], boolean,
--                                         text, text, text, text, integer, text),
--                 wawi.hat_rolle(text);
--   DROP SCHEMA wawi_intern CASCADE;   -- Prüfungen, Entscheidungen, QS-Fälle, Rollen
--   REVOKE USAGE ON SCHEMA wawi FROM bm_pruefdienst;
--   DROP ROLE bm_pruefdienst;          -- nennt es noch Rechte: als supabase_admin
--                                      -- DROP OWNED BY bm_pruefdienst, dann erneut
--   DROP TRIGGER rezension_status_vorgabe ON wawi.rezension;
--   DROP FUNCTION wawi.rezension_status_vorgabe();
--   ALTER TABLE wawi.rezension DROP COLUMN status CASCADE;   -- mit Index, Prüfregeln,
--                                      -- Richtlinie lesen_freigegeben und den Sichten aus Abschnitt 5
--   0021 erneut einspielen (Sichten, stg_fact_reviews, rezension_anlegen, Richtlinie lesen_alle);
--   ohne die Spalte status läuft es wieder. Die Aufrufe von freigabe_rechte() am
--   Ende von 0018 und 0020 tun ohne die Funktion nichts.
