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
