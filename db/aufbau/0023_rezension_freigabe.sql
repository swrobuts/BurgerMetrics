-- 0023_rezension_freigabe.sql
-- Zweck: Rezensionen aus dem Shop erscheinen erst nach einer Prüfung.
--        wawi.rezension bekommt einen Status. Der Prüfdienst (Rolle
--        bm_pruefdienst) trägt Jevs Urteil ein; Menschen mit den Rollen
--        moderation und qualitaet entscheiden im POS. Öffentlich lesbar sind
--        nur freigegebene Rezensionen, in den Sichten und über die Richtlinie
--        lesen_freigegeben auch in der Tabelle selbst.
--
--        Rechte werden ausdrücklich gesetzt. 0018 und 0020 geben neuen
--        Tabellen und Sichten in wawi automatisch SELECT für anon,
--        authenticated und studi_daba. Dieses Skript entzieht das bei jedem
--        neuen Objekt und vergibt danach nur, was gebraucht wird.
--
-- Aufruf (als postgres):
--   python3 db/skript_ausfuehren.py db/aufbau/0023_rezension_freigabe.sql
--
-- Voraussetzung: 0001–0022 sind gelaufen; das Supabase-Schema auth
--   (auth.users, auth.uid()) ist vorhanden.
-- Wer 0021 erneut ausführt (etwa nach einem Neuladen von fact_reviews.csv),
--   führt danach auch dieses Skript erneut aus: 0021 setzt die Sichten und
--   die Richtlinie lesen_alle auf den Stand ohne Freigabe zurück.
-- Idempotent: ja.
--
-- Rollen vergeben (einmalig, als postgres; die Konto-ID steht in auth.users,
-- weder ID noch E-Mail-Adresse gehören ins Repo):
--   INSERT INTO wawi.mitarbeiter_rolle (konto, rolle)
--   VALUES ('<konto-id>', 'moderation'), ('<konto-id>', 'qualitaet')
--   ON CONFLICT DO NOTHING;
-- Das Passwort der Rolle bm_pruefdienst setzt pruefdienst/passwort_setzen.py.

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
REVOKE ALL ON FUNCTION wawi.rezension_status_vorgabe() FROM PUBLIC;
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

-- Die Tabelle zeigt anon, authenticated und studi_daba nur freigegebene
-- Zeilen. Sichten und Funktionen gehören postgres, dem Eigentümer der
-- Tabelle, und lesen weiter alles.
DROP POLICY IF EXISTS lesen_alle ON wawi.rezension;
DROP POLICY IF EXISTS lesen_freigegeben ON wawi.rezension;
CREATE POLICY lesen_freigegeben ON wawi.rezension
  FOR SELECT USING (status = 'freigegeben');

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
-- 2 Prüfungen, Entscheidungen, QS-Fälle und Rollen. Keine dieser Tabellen ist
--   direkt lesbar; gelesen wird über Sichten, geschrieben über Funktionen.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS wawi.rezension_pruefung (
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
  ON wawi.rezension_pruefung (rezension_id, geprueft_am DESC);
COMMENT ON TABLE wawi.rezension_pruefung IS
  'Eine Zeile je Prüflauf: Jevs Wahrscheinlichkeiten, Mustertreffer, Ergebnis und Gründe. '
  'ergebnis bleibt leer, wenn der Lauf scheiterte (fehler gesetzt), außer beim dritten Fehlversuch.';

CREATE TABLE IF NOT EXISTS wawi.rezension_entscheidung (
  entscheidung_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  rezension_id    bigint NOT NULL REFERENCES wawi.rezension(rezension_id) ON DELETE CASCADE,
  entscheidung    text NOT NULL CHECK (entscheidung IN ('freigegeben', 'abgelehnt')),
  entschieden_am  timestamptz NOT NULL DEFAULT now(),
  konto           uuid NOT NULL,
  bemerkung       text CHECK (char_length(bemerkung) <= 500)
);
COMMENT ON TABLE wawi.rezension_entscheidung IS
  'Entscheidungen von Menschen im POS. konto ist die Supabase-Kennung; die Zeile bleibt, '
  'auch wenn das Konto später gelöscht wird.';

CREATE TABLE IF NOT EXISTS wawi.qs_fall (
  qs_fall_id   bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  rezension_id bigint NOT NULL REFERENCES wawi.rezension(rezension_id) ON DELETE CASCADE,
  angelegt_am  timestamptz NOT NULL DEFAULT now(),
  erledigt_am  timestamptz,
  konto        uuid,
  bemerkung    text CHECK (char_length(bemerkung) <= 500),
  CONSTRAINT qs_fall_je_rezension UNIQUE (rezension_id)
);
COMMENT ON TABLE wawi.qs_fall IS
  'Hinweis auf ein Gesundheitsrisiko für die Qualitätssicherung; erledigt setzt die Rolle qualitaet.';

CREATE TABLE IF NOT EXISTS wawi.mitarbeiter_rolle (
  konto uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  rolle text NOT NULL CHECK (rolle IN ('moderation', 'qualitaet')),
  PRIMARY KEY (konto, rolle)
);
COMMENT ON TABLE wawi.mitarbeiter_rolle IS
  'Rollen für die Moderation im POS, je Supabase-Konto. Vergeben nur durch postgres.';

ALTER TABLE wawi.rezension_pruefung     ENABLE ROW LEVEL SECURITY;
ALTER TABLE wawi.rezension_entscheidung ENABLE ROW LEVEL SECURITY;
ALTER TABLE wawi.qs_fall                ENABLE ROW LEVEL SECURITY;
ALTER TABLE wawi.mitarbeiter_rolle      ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON wawi.rezension_pruefung, wawi.rezension_entscheidung, wawi.qs_fall,
              wawi.mitarbeiter_rolle
  FROM PUBLIC, anon, authenticated, studi_daba;

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
GRANT USAGE ON SCHEMA wawi TO bm_pruefdienst;

-- Hat das angemeldete Konto (auth.uid() aus dem JWT) diese Rolle?
-- Vereinfachtes Muster von velocity.hat_rolle: die Rolle hängt direkt am Konto.
CREATE OR REPLACE FUNCTION wawi.hat_rolle(p_rolle text)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = wawi, pg_temp
AS $$
  SELECT EXISTS (SELECT 1 FROM wawi.mitarbeiter_rolle mr
                 WHERE mr.konto = auth.uid() AND mr.rolle = p_rolle);
$$;
REVOKE ALL ON FUNCTION wawi.hat_rolle(text) FROM PUBLIC, anon, studi_daba;
GRANT EXECUTE ON FUNCTION wawi.hat_rolle(text) TO authenticated;

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
  AND    NOT EXISTS (SELECT 1 FROM wawi.rezension_pruefung p
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
    FROM   wawi.rezension_pruefung p
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

  INSERT INTO wawi.rezension_pruefung
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
    INSERT INTO wawi.qs_fall (rezension_id) VALUES (rezension_id)
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
  FROM   wawi.rezension_pruefung p
  WHERE  p.jev_angefragt
  AND    (p.geprueft_am AT TIME ZONE 'Europe/Berlin')::date
       = (now() AT TIME ZONE 'Europe/Berlin')::date;
$$;

REVOKE ALL ON FUNCTION wawi.pruefung_offene_holen(integer), wawi.pruefung_heute(),
  wawi.pruefung_eintragen(bigint, text, text[], boolean, jsonb, text[], boolean, text, text, text,
                          text, integer, text)
  FROM PUBLIC, anon, authenticated, studi_daba;
GRANT EXECUTE ON FUNCTION wawi.pruefung_offene_holen(integer), wawi.pruefung_heute(),
  wawi.pruefung_eintragen(bigint, text, text[], boolean, jsonb, text[], boolean, text, text, text,
                          text, integer, text)
  TO bm_pruefdienst;

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
  INSERT INTO wawi.rezension_entscheidung (rezension_id, entscheidung, konto, bemerkung)
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
  FROM   wawi.qs_fall q
  WHERE  q.qs_fall_id = qs_fall_id
  FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'unbekannter QS-Fall: %', qs_fall_id USING ERRCODE = '23503';
  END IF;
  IF v_erledigt IS NOT NULL THEN
    RAISE EXCEPTION 'der QS-Fall % ist schon erledigt', qs_fall_id USING ERRCODE = '55000';
  END IF;
  UPDATE wawi.qs_fall q
  SET    erledigt_am = v_jetzt, konto = v_konto, bemerkung = nullif(btrim(bemerkung), '')
  WHERE  q.qs_fall_id = qs_fall_id;
  RETURN jsonb_build_object('qs_fall_id', qs_fall_id, 'erledigt_am', v_jetzt);
END $$;

REVOKE ALL ON FUNCTION wawi.rezension_entscheiden(bigint, text, text),
  wawi.api_rezension_freigeben(bigint, text), wawi.api_rezension_ablehnen(bigint, text),
  wawi.api_qs_fall_erledigen(bigint, text)
  FROM PUBLIC, anon, authenticated, studi_daba, bm_pruefdienst;
GRANT EXECUTE ON FUNCTION wawi.api_rezension_freigeben(bigint, text),
  wawi.api_rezension_ablehnen(bigint, text), wawi.api_qs_fall_erledigen(bigint, text)
  TO authenticated;
