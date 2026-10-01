# Freigabe A: Datenbank — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `wawi.rezension` bekommt einen Status. Öffentlich lesbar sind nur freigegebene Rezensionen, auch bei direktem Zugriff auf die Tabelle. Dazu kommen Tabellen, Funktionen und Sichten für den Prüfdienst (Phase D), die Leseansicht im Shop (Phase B) und die Moderation im POS (Phase E).

**Architecture:** Eine neue Migration `db/aufbau/0023_rezension_freigabe.sql`, wiederholbar, in sechs Abschnitten: Status, Tabellen und Rollen, Dienstfunktionen, menschliche Entscheidungen, Sichten, Probe. Geschrieben wird nur über `SECURITY DEFINER`-Funktionen mit Rollenprüfung. Gelesen wird über Sichten, die `postgres` gehören. Getestet wird auf einem lokalen Wegwerf-Cluster in Docker nach dem Muster von `db/tests/test_security_boundaries.py`, nie gegen die Produktion. Dort wird die Migration erst am Ende eingespielt und über die API geprüft.

**Tech Stack:** PostgreSQL 17 (Supabase selbstgehostet, lokal `postgres:17-alpine` in Docker), PL/pgSQL, Python 3.12 mit `pytest` und `psycopg2`, Node 24 (`node --test`) für die Integrationstests gegen PostgREST.

**Spec:** `docs/superpowers/specs/2026-09-30-rezensionen-jev-freigabe-design.md`, Abschnitte 3 (Aufbau), 5 (Datenbank und Rechte), 10 (Abnahme) und 11 (Reihenfolge, Phase A).

## Global Constraints

- Deutsch mit echten Umlauten in neuen Kommentaren, Meldungen, Dokumentation und Commit-Nachrichten. Bezeichner (Tabellen, Spalten, Funktionen, Variablen) bleiben ASCII. Bestehende ASCII-Kommentare in älteren Skripten bleiben unangetastet.
- Lehrcode für Anfänger: kurze Funktionen, deutsche Namen, ein Kommentar je Funktion (das Warum), keine Tricks.
- Statuswerte wörtlich: `offen`, `freigegeben`, `zurueckgehalten`, `abgelehnt`. Rollen: `moderation`, `qualitaet`. Datenbankrolle des Dienstes: `bm_pruefdienst`.
- Gründe, die die Datenbank selbst schreibt, wörtlich: `Prüfung nicht möglich`. Weitere Gründe setzt der Prüfdienst (Phase C/D): `Kontaktdaten oder Link`, `Gesundheitsrisiko`, `Beleidigung`, `Personenbezug`, `Werbung`, `Anweisung`, `unsicher`, `Tageslimit erreicht`.
- PL/pgSQL-Funktionen: Parameter heißen wie die Spalten, mit `#variable_conflict use_variable` (Muster `0021`). SQL-Funktionen (`LANGUAGE sql`): Parameter mit Präfix `p_`, weil dort die Spalte gewinnt, wenn ein Parameter wie eine Spalte heißt.
- Alle Funktionen `SECURITY DEFINER` mit `SET search_path = wawi, pg_temp`; Objekte immer mit Schema nennen.
- Jede neue Tabelle und Sicht: erst `REVOKE ALL … FROM PUBLIC, anon, authenticated, studi_daba`, dann nur die Rechte aus Spec 5.3. `0018` und `0020` vergeben sonst automatisch `SELECT`.
- Die Migration ist wiederholbar, läuft in einer Transaktion (`db/skript_ausfuehren.py`), endet mit einer Probe (`RAISE EXCEPTION` bei Abweichung) und `NOTIFY pgrst, 'reload schema';`.
- Keine Konto-ID, keine E-Mail-Adresse, kein Passwort im Repo.
- Tests nur gegen den lokalen Wegwerf-Cluster (`db/tests/security_local.sh`). In der Produktion wird nur gelesen; die Node-Integrationstests schreiben nie erfolgreich.
- Commits: `git -c core.fileMode=false add <Dateien>` (nie `tableau/BurgerMetrics.twb`), Nachricht deutsch, zweiter Absatz `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Branch `bm-analyse`; am Ende ein PR auf `main`, Merge nur nach Roberts Zusage.
- Arbeitsverzeichnis für alle Befehle: `/Users/robert/Library/CloudStorage/OneDrive-Persönlich/Vorlesungen/Datenbasierte Fallstudien/BurgerMetrics/BurgerMetrics_Website` (im Folgenden Repo). Dateien außerhalb des Claude-Worktrees schreibt der Executor per Bash (Heredoc oder Python), weil der Write-Hook sie sperrt.

## Review Focus

Fünf Fälle, die die Spec nicht ausdrücklich nennt, die aber Menschen treffen würden. Jeder bekommt einen Test in der zuständigen Aufgabe.

1. **Direkter Zugriff auf die Tabelle.** Wer `GET /rest/v1/rezension` mit dem öffentlichen Schlüssel aufruft, darf keine ungeprüften Texte sehen. Test: `test_tabelle_zeigt_nur_freigegebene` (Aufgabe 1) und der Node-Test „wawi.rezension zeigt ohne Anmeldung nur freigegebene Zeilen“ (Aufgabe 7).
2. **Erneuter Lauf von `0018`.** `0018` vergibt `SELECT` auf alle Tabellen in `wawi`, auch auf die neuen. Der Zeilenschutz muss dann trotzdem halten. Test: `test_zeilenschutz_haelt_auch_nach_erneutem_lauf_von_0018` (Aufgabe 2).
3. **Neuladen der CSV über `0021`.** `0021` kopiert Simulationszeilen ohne Status; sie müssen trotzdem freigegeben sein. Test: `test_simulation_ist_immer_freigegeben` (Aufgabe 1).
4. **Kurzer Ausfall von Jev.** Drei Fehlversuche innerhalb von 90 Sekunden dürfen nicht jede neue Rezension zurückhalten. Nach einem Fehler wartet eine Rezension deshalb fünf Minuten. Test: `test_nach_einem_fehler_fuenf_minuten_pause` (Aufgabe 3).
5. **Mensch und Dienst gleichzeitig.** Entscheidet eine Moderatorin, während der Dienst noch prüft, darf der Dienst ihre Entscheidung nicht überschreiben. Test: `test_menschliche_entscheidung_bleibt` (Aufgabe 4).

---

## Dateistruktur

| Datei | Verantwortung |
|---|---|
| `db/aufbau/0023_rezension_freigabe.sql` (neu) | die Migration in sechs Abschnitten |
| `db/tests/freigabe_cluster.py` (neu) | baut auf der lokalen Wegwerf-Instanz eine Datenbank mit `wawi` bis `0023` auf; wird in Phase D wiederverwendet |
| `db/tests/test_rezension_freigabe.py` (neu) | Rechte, Status, Dienstfunktionen, Entscheidungen, Sichten |
| `db/tests/security_local.sh` (ändern) | nimmt die neue Testdatei in den Lauf auf |
| `db/tests/README.md` (ändern) | ein Absatz zur neuen Testdatei |
| `db/aufbau/0021_rezensionen.sql` (ändern, nur Kommentar) | Hinweis: nach erneutem Lauf `0023` wiederholen |
| `web/tests/datenquelle_rezensionen.test.mjs` (ändern) | Status in `v_rezension_letzte`, verschlossene Endpunkte, Tabelle nur freigegeben |
| `db/README.md` (ändern) | Tabelle der Aufbauskripte, Abschnitt Rezensionen, Rechte von `anon` |
| `docs/02-datenmodell.md` (ändern) | ein Halbsatz: Shop-Rezensionen erreichen `fact_reviews` erst nach der Freigabe |

Die Doku zum ETL-Schritt `wawi` → `burgermetrics` steht in `db/README.md`, nicht in `docs/03-etl.md`. Deshalb ändert diese Phase `db/README.md` statt `docs/03-etl.md` (Abweichung von Spec 11, Absatz Dokumentation).

---

### Task 1: Testgerüst und Status je Rezension

**Files:**
- Create: `db/tests/freigabe_cluster.py`
- Create: `db/tests/test_rezension_freigabe.py`
- Create: `db/aufbau/0023_rezension_freigabe.sql` (Kopf und Abschnitt 1)
- Modify: `db/tests/security_local.sh` (letzte Zeile)

**Interfaces:**
- Consumes: `db/aufbau/0016_wawi_schema.sql`, `0018`, `0020`, `0021`; `wawi.rezension_anlegen(artikel_id bigint, sterne integer, inhalt text, filiale_id bigint, sitzung text) → jsonb` aus `0021`.
- Produces: `freigabe_cluster.datenbank_aufbauen(dsn: str, name: str) -> psycopg2.connection`, `freigabe_cluster.AUFBAU: Path`; Spalte `wawi.rezension.status text NOT NULL DEFAULT 'offen'`; Richtlinie `lesen_freigegeben`; `wawi.rezension_anlegen()` liefert zusätzlich `"status": "offen"`. Test-Helfer `als(cur, rolle, konto=None)`, `zurueck(cur)`, `fehler(cur, sql, argumente=()) -> type | None`, `shop_rezension(cur, text=…, sterne=4) -> int`.

- [ ] **Step 1: Docker Desktop starten**

Run: `open -a Docker`, dann warten, bis `docker info --format '{{.ServerVersion}}'` eine Versionsnummer liefert (Monitor mit Schleife, höchstens zwei Minuten).
Expected: eine Versionsnummer, kein „failed to connect“.

- [ ] **Step 2: Aufbau des Testclusters schreiben**

`db/tests/freigabe_cluster.py`:

```python
"""Baut auf einer lokalen Wegwerf-Instanz eine Datenbank mit wawi bis 0023 auf.

Gebraucht von db/tests/test_rezension_freigabe.py und vom Integrationstest
des Prüfdienstes (Phase D). Nur Schemata, Rollen und wenige Stammdaten;
kein Supabase, keine Anwendungsdaten.
"""
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[2]
AUFBAU = ROOT / "db" / "aufbau"

# Nachbau dessen, was 0023 von Supabase braucht. auth.uid() entspricht der
# Definition auf supabase.butscher.cloud (Stand 30.09.2026).
AUTH = """
CREATE SCHEMA auth;
CREATE TABLE auth.users (id uuid PRIMARY KEY);
CREATE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE AS $$
  SELECT coalesce(
    nullif(current_setting('request.jwt.claim.sub', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
  )::uuid
$$;
"""

# Nur die Spalten, auf die 0018 und 0021 mit Fremdschlüsseln und Sichten zeigen.
BURGERMETRICS = """
CREATE SCHEMA burgermetrics;
CREATE TABLE burgermetrics.dim_date (date_id bigint, date date PRIMARY KEY);
CREATE TABLE burgermetrics.dim_customer (customer_id bigint PRIMARY KEY);
CREATE TABLE burgermetrics.dim_product (product_id bigint PRIMARY KEY, product_name text, category text);
CREATE TABLE burgermetrics.dim_branch (branch_id bigint PRIMARY KEY);
CREATE TABLE burgermetrics.fact_orders (order_id bigint PRIMARY KEY);
CREATE FUNCTION burgermetrics.kurzname(text) RETURNS text LANGUAGE sql AS 'SELECT $1';
CREATE SCHEMA net;
CREATE TABLE net.http_request_queue (url text);
CREATE TABLE net._http_response (content text);
"""

STAMMDATEN = """
INSERT INTO wawi.filiale (filiale_id, name) VALUES (1, 'Test');
INSERT INTO wawi.zahlungsart (zahlungsart_id, bezeichnung) VALUES (1, 'Test');
INSERT INTO wawi.artikelkategorie (kategorie_id, name) VALUES (1, 'Test');
INSERT INTO wawi.artikelunterkategorie (unterkategorie_id, name, kategorie_id) VALUES (1, 'Test', 1);
INSERT INTO wawi.artikel (artikel_id, name, unterkategorie_id, listenpreis) VALUES (1, 'Test', 1, 5);
"""

# Rollen gelten für den ganzen Cluster; die Sicherheitstests legen sie
# vielleicht schon an.
ROLLEN = """
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN CREATE ROLE anon; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN CREATE ROLE authenticated; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'studi') THEN CREATE ROLE studi; END IF;
END $$;
"""


def datenbank_aufbauen(dsn, name):
    """Legt die Datenbank name neu an, spielt 0016 bis 0023 ein und gibt eine offene Verbindung zurück."""
    params = psycopg2.extensions.parse_dsn(dsn)
    assert params["host"] == "localhost", "nur eine lokale Wegwerf-Instanz verwenden"
    verwaltung = psycopg2.connect(dsn)
    verwaltung.autocommit = True
    with verwaltung.cursor() as cur:
        cur.execute(f'DROP DATABASE IF EXISTS "{name}"')
        cur.execute(f'CREATE DATABASE "{name}"')
        cur.execute(ROLLEN)
    verwaltung.close()
    con = psycopg2.connect(**dict(params, dbname=name))
    with con.cursor() as cur:
        cur.execute(AUTH)
        cur.execute(BURGERMETRICS)
        ddl = (AUFBAU / "0016_wawi_schema.sql").read_text().split("INSERT INTO filialtyp", 1)[0]
        cur.execute(ddl)
        cur.execute(STAMMDATEN)
        cur.execute((AUFBAU / "0018_wawi_sichten_und_schreiben.sql").read_text())
        cur.execute((AUFBAU / "0020_demo_rolle.sql").read_text())
        # db/betrieb/studi_daba_lesend.sql läuft nur in der Datenbank postgres
        # (Schutz im Skript) und gehört nicht hierher; 0023 setzt die Rechte
        # seiner Objekte selbst.
        # 0021 legt Funktionen an, deren Tabellen hier fehlen (0019). Ihr Rumpf
        # wird sonst beim Anlegen geprüft; aufgerufen werden sie hier nicht.
        cur.execute("SET check_function_bodies = off")
        cur.execute((AUFBAU / "0021_rezensionen.sql").read_text())
        cur.execute("RESET check_function_bodies")
        migration = (AUFBAU / "0023_rezension_freigabe.sql").read_text()
        cur.execute(migration)
        cur.execute(migration)  # wiederholbar
    con.commit()
    return con
```

- [ ] **Step 3: Testdatei mit Fixture, Helfern und den ersten Tests schreiben**

`db/tests/test_rezension_freigabe.py`:

```python
"""Freigabe von Rezensionen (db/aufbau/0023) auf einem lokalen Wegwerf-Cluster.

Wie test_security_boundaries.py: BM_SECURITY_TEST_DSN zeigt auf eine leere,
wegwerfbare PostgreSQL-Instanz, BM_SECURITY_TEST_CA ist ihr Zertifikat;
security_local.sh startet beides in Docker. Die Tests legen eine eigene
Datenbank an, kontaktieren keinen Supabase-Endpunkt und rollen jeden Test
am Ende zurück.
"""
import json
import os
import sys
import uuid
from decimal import Decimal
from pathlib import Path

import psycopg2
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from freigabe_cluster import AUFBAU, datenbank_aufbauen  # noqa: E402


@pytest.fixture(scope="module")
def verbindung():
    """Baut die Testdatenbank einmal je Modul auf."""
    dsn = os.environ.get("BM_SECURITY_TEST_DSN")
    if not dsn or not os.environ.get("BM_SECURITY_TEST_CA"):
        pytest.skip("lokale Wegwerf-Instanz nötig: bash db/tests/security_local.sh")
    con = datenbank_aufbauen(dsn, "bm_freigabe")
    yield con
    con.close()


@pytest.fixture
def db(verbindung):
    """Ein Cursor je Test; am Ende wird alles zurückgerollt."""
    cur = verbindung.cursor()
    yield cur
    verbindung.rollback()
    cur.close()


def als(cur, rolle, konto=None):
    """Wechselt in eine Datenbankrolle, mit Konto wie nach einer Anmeldung über Supabase."""
    cur.execute("RESET ROLE")
    anspruch = json.dumps({"sub": str(konto), "role": rolle}) if konto else ""
    cur.execute("SELECT set_config('request.jwt.claims', %s, true)", (anspruch,))
    cur.execute(f"SET LOCAL ROLE {rolle}")


def zurueck(cur):
    """Zurück zu postgres, ohne Anmeldung."""
    cur.execute("RESET ROLE")
    cur.execute("SELECT set_config('request.jwt.claims', '', true)")


def fehler(cur, sql, argumente=()):
    """Führt sql aus und liefert die Fehlerklasse oder None; die Transaktion bleibt benutzbar."""
    cur.execute("SAVEPOINT probe")
    try:
        cur.execute(sql, argumente)
    except psycopg2.Error as e:
        cur.execute("ROLLBACK TO SAVEPOINT probe")
        return type(e)
    cur.execute("RELEASE SAVEPOINT probe")
    return None


def shop_rezension(cur, text="Der Burger war heiß und frisch.", sterne=4):
    """Legt eine Rezension über den öffentlichen Weg an (Rolle anon) und liefert ihre ID."""
    als(cur, "anon")
    cur.execute("SELECT wawi.rezension_anlegen(1, %s, %s, NULL, %s)",
                (sterne, text, "test-" + uuid.uuid4().hex[:8]))
    antwort = cur.fetchone()[0]
    zurueck(cur)
    return antwort["rezension_id"]


def test_shop_rezension_startet_offen(db):
    als(db, "anon")
    db.execute("SELECT wawi.rezension_anlegen(1, 4, 'Guter Burger, schnell serviert.', NULL, 'test-a')")
    antwort = db.fetchone()[0]
    assert antwort["status"] == "offen"
    zurueck(db)
    db.execute("SELECT status FROM wawi.rezension WHERE rezension_id = %s", (antwort["rezension_id"],))
    assert db.fetchone()[0] == "offen"


def test_simulation_ist_immer_freigegeben(db):
    # 0021 kopiert Simulationszeilen ohne Status, etwa nach einem Neuladen der CSV.
    db.execute("""INSERT INTO wawi.rezension (artikel_id, sterne, inhalt, quelle)
                  VALUES (1, 5, 'Simulierter Text', 'simulation') RETURNING status""")
    assert db.fetchone()[0] == "freigegeben"
    assert fehler(db, "UPDATE wawi.rezension SET status = 'offen' WHERE quelle = 'simulation'") \
        is psycopg2.errors.CheckViolation


def test_unbekannter_status_wird_abgewiesen(db):
    rid = shop_rezension(db)
    assert fehler(db, "UPDATE wawi.rezension SET status = 'geloescht' WHERE rezension_id = %s", (rid,)) \
        is psycopg2.errors.CheckViolation


@pytest.mark.parametrize("rolle", ["anon", "authenticated", "studi_daba"])
def test_tabelle_zeigt_nur_freigegebene(db, rolle):
    rid = shop_rezension(db, "GEHEIM, noch nicht geprüft")
    als(db, rolle)
    db.execute("SELECT count(*) FROM wawi.rezension WHERE rezension_id = %s", (rid,))
    assert db.fetchone()[0] == 0
    zurueck(db)
    db.execute("UPDATE wawi.rezension SET status = 'freigegeben' WHERE rezension_id = %s", (rid,))
    als(db, rolle)
    db.execute("SELECT count(*) FROM wawi.rezension WHERE rezension_id = %s", (rid,))
    assert db.fetchone()[0] == 1
```

- [ ] **Step 4: Die neue Testdatei in den lokalen Lauf aufnehmen**

In `db/tests/security_local.sh` die letzte Zeile

```bash
"$test_python" -m pytest db/tests/test_security_boundaries.py db/tests/test_materialisieren.py "$@"
```

ersetzen durch

```bash
"$test_python" -m pytest db/tests/test_security_boundaries.py db/tests/test_materialisieren.py \
  db/tests/test_rezension_freigabe.py "$@"
```

- [ ] **Step 5: Test laufen lassen, er muss scheitern**

Run: `bash db/tests/security_local.sh -q -k rezension_freigabe`
Expected: FEHLER beim Aufbau der Fixture, `FileNotFoundError: … 0023_rezension_freigabe.sql`.

- [ ] **Step 6: Migration mit Kopf und Abschnitt 1 anlegen**

`db/aufbau/0023_rezension_freigabe.sql`:

```sql
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
```

- [ ] **Step 7: Tests laufen lassen**

Run: `bash db/tests/security_local.sh -q -k rezension_freigabe`
Expected: `6 passed` (4 Testfunktionen, eine davon dreifach parametrisiert).

- [ ] **Step 8: Commit**

```bash
git -c core.fileMode=false add db/tests/freigabe_cluster.py db/tests/test_rezension_freigabe.py db/tests/security_local.sh db/aufbau/0023_rezension_freigabe.sql
git commit -m "Freigabe A: Status je Rezension und Leserichtlinie" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Prüftabellen, Rollen und `hat_rolle()`

**Files:**
- Modify: `db/aufbau/0023_rezension_freigabe.sql` (Abschnitt 2 ans Ende anhängen)
- Test: `db/tests/test_rezension_freigabe.py` (ans Ende anhängen)

**Interfaces:**
- Consumes: Helfer aus Task 1.
- Produces: Tabellen `wawi.rezension_pruefung`, `wawi.rezension_entscheidung`, `wawi.qs_fall` (Constraint `qs_fall_je_rezension`), `wawi.mitarbeiter_rolle (konto uuid, rolle text)`; Rolle `bm_pruefdienst` (LOGIN, NOINHERIT, CONNECTION LIMIT 3, ohne Passwort); `wawi.hat_rolle(p_rolle text) → boolean` (nur `authenticated`). Test-Helfer `konto(cur, *rollen) -> str`, Konstante `NEUE_TABELLEN`.

- [ ] **Step 1: Tests anhängen**

```python
NEUE_TABELLEN = ["wawi.rezension_pruefung", "wawi.rezension_entscheidung",
                 "wawi.qs_fall", "wawi.mitarbeiter_rolle"]


def konto(cur, *rollen):
    """Legt als postgres ein Supabase-Konto mit Rollen an; es lebt nur bis zum Ende des Tests."""
    zurueck(cur)  # wird oft als Argument von als() ausgewertet, während noch eine andere Rolle gilt
    kennung = str(uuid.uuid4())
    cur.execute("INSERT INTO auth.users (id) VALUES (%s)", (kennung,))
    for rolle in rollen:
        cur.execute("INSERT INTO wawi.mitarbeiter_rolle (konto, rolle) VALUES (%s, %s)", (kennung, rolle))
    return kennung


@pytest.mark.parametrize("rolle", ["anon", "authenticated", "studi_daba", "bm_pruefdienst"])
@pytest.mark.parametrize("tabelle", NEUE_TABELLEN)
def test_neue_tabellen_sind_verschlossen(db, rolle, tabelle):
    als(db, rolle)
    assert fehler(db, f"SELECT 1 FROM {tabelle} LIMIT 1") is psycopg2.errors.InsufficientPrivilege


def test_zeilenschutz_haelt_auch_nach_erneutem_lauf_von_0018(db):
    # 0018 vergibt SELECT auf alle Tabellen in wawi. Ohne Richtlinie bleiben die Zeilen trotzdem unsichtbar.
    rid = shop_rezension(db)
    db.execute("INSERT INTO wawi.rezension_pruefung (rezension_id, fehler) VALUES (%s, 'Test')", (rid,))
    db.execute("GRANT SELECT ON wawi.rezension_pruefung TO anon")
    als(db, "anon")
    db.execute("SELECT count(*) FROM wawi.rezension_pruefung")
    assert db.fetchone()[0] == 0


def test_hat_rolle_liest_das_angemeldete_konto(db):
    moderation = konto(db, "moderation")
    ohne = konto(db)
    als(db, "authenticated", moderation)
    db.execute("SELECT wawi.hat_rolle('moderation'), wawi.hat_rolle('qualitaet')")
    assert db.fetchone() == (True, False)
    als(db, "authenticated", ohne)
    db.execute("SELECT wawi.hat_rolle('moderation')")
    assert db.fetchone()[0] is False
    als(db, "authenticated")
    db.execute("SELECT wawi.hat_rolle('moderation')")
    assert db.fetchone()[0] is False


@pytest.mark.parametrize("rolle", ["anon", "studi_daba", "bm_pruefdienst"])
def test_hat_rolle_nur_fuer_angemeldete(db, rolle):
    als(db, rolle)
    assert fehler(db, "SELECT wawi.hat_rolle('moderation')") is psycopg2.errors.InsufficientPrivilege


def test_unbekannte_rolle_wird_abgewiesen(db):
    kennung = str(uuid.uuid4())
    db.execute("INSERT INTO auth.users (id) VALUES (%s)", (kennung,))
    assert fehler(db, "INSERT INTO wawi.mitarbeiter_rolle (konto, rolle) VALUES (%s, 'admin')", (kennung,)) \
        is psycopg2.errors.CheckViolation


def test_rollen_verschwinden_mit_dem_konto(db):
    kennung = konto(db, "moderation", "qualitaet")
    db.execute("DELETE FROM auth.users WHERE id = %s", (kennung,))
    db.execute("SELECT count(*) FROM wawi.mitarbeiter_rolle WHERE konto = %s", (kennung,))
    assert db.fetchone()[0] == 0


def test_pruefdienst_rolle_ohne_tabellenrechte(db):
    db.execute("SELECT rolcanlogin, rolinherit, rolconnlimit FROM pg_roles WHERE rolname = 'bm_pruefdienst'")
    assert db.fetchone() == (True, False, 3)
    db.execute("SELECT count(*) FROM information_schema.role_table_grants WHERE grantee = 'bm_pruefdienst'")
    assert db.fetchone()[0] == 0
```

- [ ] **Step 2: Tests laufen lassen, sie müssen scheitern**

Run: `bash db/tests/security_local.sh -q -k rezension_freigabe`
Expected: FAIL, unter anderem `UndefinedTable: relation "wawi.rezension_pruefung" does not exist` und `UndefinedFunction … wawi.hat_rolle`.

- [ ] **Step 3: Abschnitt 2 an die Migration anhängen**

```sql
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
```

- [ ] **Step 4: Tests laufen lassen**

Run: `bash db/tests/security_local.sh -q -k rezension_freigabe`
Expected: alle bestanden (`6` aus Task 1 und `24` aus Task 2, also `30 passed`).

- [ ] **Step 5: Commit**

```bash
git -c core.fileMode=false add db/aufbau/0023_rezension_freigabe.sql db/tests/test_rezension_freigabe.py
git commit -m "Freigabe A: Prüftabellen, Rollen und hat_rolle()" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Dienstfunktionen für den Prüfdienst

**Files:**
- Modify: `db/aufbau/0023_rezension_freigabe.sql` (Abschnitt 3 anhängen)
- Test: `db/tests/test_rezension_freigabe.py` (anhängen)

**Interfaces:**
- Consumes: Tabellen und Rolle aus Task 2.
- Produces (Phase D ruft genau diese Signaturen):
  - `wawi.pruefung_offene_holen(p_anzahl integer) → TABLE (rezension_id bigint, artikel text, inhalt text, erstellt_am timestamptz)`. Nur `quelle = 'shop'` und `status = 'offen'`, älteste zuerst, höchstens 100, ohne Rezensionen mit Fehlversuch in den letzten fünf Minuten.
  - `wawi.pruefung_eintragen(rezension_id bigint, ergebnis text DEFAULT NULL, gruende text[] DEFAULT '{}', qs_fall_anlegen boolean DEFAULT false, wahrscheinlichkeiten jsonb DEFAULT NULL, muster_treffer text[] DEFAULT '{}', jev_angefragt boolean DEFAULT false, modell text DEFAULT NULL, fragen_stand text DEFAULT NULL, fragen_fingerabdruck text DEFAULT NULL, regel_version text DEFAULT NULL, input_tokens integer DEFAULT NULL, fehler text DEFAULT NULL) → jsonb {rezension_id, status, uebersprungen}`. `wahrscheinlichkeiten` hat die Schlüssel `beleidigung`, `personenbezug`, `werbung`, `themenbezug`, `anweisung`, `gesundheitsrisiko`.
  - `wawi.pruefung_heute() → integer`.
  - Test-Helfer `P_HARMLOS`, `eintragen(cur, rezension_id, ergebnis=None, gruende=(), qs=False, fehlertext=None, jev=True) -> dict`, `zurueckgehalten(cur, text=…, gruende=("unsicher",)) -> int`.

- [ ] **Step 1: Tests anhängen**

```python
P_HARMLOS = {"beleidigung": 0.01, "personenbezug": 0.02, "werbung": 0.01,
             "themenbezug": 0.97, "anweisung": 0.01, "gesundheitsrisiko": 0.02}


def eintragen(cur, rezension_id, ergebnis=None, gruende=(), qs=False, fehlertext=None, jev=True):
    """Trägt ein Prüfergebnis ein wie der Prüfdienst (Rolle bm_pruefdienst)."""
    als(cur, "bm_pruefdienst")
    cur.execute(
        """SELECT wawi.pruefung_eintragen(
             rezension_id => %s, ergebnis => %s, gruende => %s::text[], qs_fall_anlegen => %s,
             wahrscheinlichkeiten => %s::jsonb, muster_treffer => '{}'::text[], jev_angefragt => %s,
             modell => 'jev-1.13.0', fragen_stand => 'test', fragen_fingerabdruck => 'test',
             regel_version => 'test', input_tokens => 1000, fehler => %s)""",
        (rezension_id, ergebnis, list(gruende), qs, json.dumps(P_HARMLOS), jev, fehlertext))
    antwort = cur.fetchone()[0]
    zurueck(cur)
    return antwort


def zurueckgehalten(cur, text="Die Bedienung war unmöglich.", gruende=("unsicher",)):
    """Eine Shop-Rezension, die der Prüfdienst zurückgehalten hat."""
    rid = shop_rezension(cur, text)
    eintragen(cur, rid, "zurueckgehalten", gruende)
    return rid


def test_holen_liefert_offene_shop_rezensionen_aelteste_zuerst(db):
    db.execute("""INSERT INTO wawi.rezension (artikel_id, sterne, inhalt, quelle)
                  VALUES (1, 5, 'Simulierter Text', 'simulation')""")
    erste = shop_rezension(db, "Erste Rezension")
    zweite = shop_rezension(db, "Zweite Rezension")
    geprueft = shop_rezension(db, "Schon geprüft")
    eintragen(db, geprueft, "freigegeben")
    als(db, "bm_pruefdienst")
    db.execute("SELECT rezension_id, artikel, inhalt FROM wawi.pruefung_offene_holen(10)")
    assert db.fetchall() == [(erste, "Test", "Erste Rezension"), (zweite, "Test", "Zweite Rezension")]
    db.execute("SELECT count(*) FROM wawi.pruefung_offene_holen(1)")
    assert db.fetchone()[0] == 1


def test_freigeben_setzt_den_status(db):
    rid = shop_rezension(db)
    assert eintragen(db, rid, "freigegeben") == {"rezension_id": rid, "status": "freigegeben",
                                                 "uebersprungen": False}
    db.execute("SELECT status FROM wawi.rezension WHERE rezension_id = %s", (rid,))
    assert db.fetchone()[0] == "freigegeben"
    db.execute("""SELECT p_themenbezug, jev_angefragt, input_tokens, modell
                  FROM wawi.rezension_pruefung WHERE rezension_id = %s""", (rid,))
    assert db.fetchone() == (0.97, True, 1000, "jev-1.13.0")


def test_gesundheitsrisiko_legt_qs_fall_an(db):
    rid = shop_rezension(db, "Mir war nach dem Essen übel.")
    assert eintragen(db, rid, "zurueckgehalten", ["Gesundheitsrisiko"], qs=True)["status"] == "zurueckgehalten"
    db.execute("SELECT count(*) FROM wawi.qs_fall WHERE rezension_id = %s AND erledigt_am IS NULL", (rid,))
    assert db.fetchone()[0] == 1
    db.execute("SELECT gruende, qs_fall FROM wawi.rezension_pruefung WHERE rezension_id = %s", (rid,))
    assert db.fetchone() == (["Gesundheitsrisiko"], True)


@pytest.mark.parametrize("ergebnis, gruende, qs", [
    ("freigegeben", [], True),          # QS-Fall ohne Zurückhalten
    ("zurueckgehalten", [], False),     # Zurückhalten ohne Grund
    ("abgelehnt", ["Werbung"], False),  # ablehnen darf nur ein Mensch
    (None, [], False),                  # weder Ergebnis noch Fehler
])
def test_ungueltige_eintraege_werden_abgewiesen(db, ergebnis, gruende, qs):
    rid = shop_rezension(db)
    als(db, "bm_pruefdienst")
    sql = ("SELECT wawi.pruefung_eintragen(rezension_id => %s, ergebnis => %s, "
           "gruende => %s::text[], qs_fall_anlegen => %s)")
    assert fehler(db, sql, (rid, ergebnis, gruende, qs)) is psycopg2.errors.InvalidParameterValue


def test_zweiter_eintrag_wird_uebersprungen(db):
    rid = zurueckgehalten(db)
    assert eintragen(db, rid, "freigegeben") == {"rezension_id": rid, "status": "zurueckgehalten",
                                                 "uebersprungen": True}


def test_dritter_fehler_haelt_zurueck(db):
    rid = shop_rezension(db)
    assert eintragen(db, rid, fehlertext="Zeitüberschreitung")["status"] == "offen"
    assert eintragen(db, rid, fehlertext="HTTP 529")["status"] == "offen"
    assert eintragen(db, rid, fehlertext="HTTP 529")["status"] == "zurueckgehalten"
    db.execute("""SELECT ergebnis, gruende FROM wawi.rezension_pruefung
                  WHERE rezension_id = %s ORDER BY pruefung_id DESC LIMIT 1""", (rid,))
    assert db.fetchone() == ("zurueckgehalten", ["Prüfung nicht möglich"])


def test_nach_einem_fehler_fuenf_minuten_pause(db):
    rid = shop_rezension(db)
    eintragen(db, rid, fehlertext="Zeitüberschreitung")
    als(db, "bm_pruefdienst")
    db.execute("SELECT count(*) FROM wawi.pruefung_offene_holen(10)")
    assert db.fetchone()[0] == 0
    zurueck(db)
    db.execute("""UPDATE wawi.rezension_pruefung SET geprueft_am = geprueft_am - interval '6 minutes'
                  WHERE rezension_id = %s""", (rid,))
    als(db, "bm_pruefdienst")
    db.execute("SELECT count(*) FROM wawi.pruefung_offene_holen(10)")
    assert db.fetchone()[0] == 1


def test_heute_zaehlt_nur_anfragen_an_jev(db):
    a, b, c = shop_rezension(db), shop_rezension(db), shop_rezension(db)
    eintragen(db, a, "freigegeben")
    eintragen(db, b, fehlertext="Zeitüberschreitung")
    eintragen(db, c, "zurueckgehalten", ["Tageslimit erreicht"], jev=False)
    als(db, "bm_pruefdienst")
    db.execute("SELECT wawi.pruefung_heute()")
    assert db.fetchone()[0] == 2


def test_simulation_wird_nie_geprueft(db):
    db.execute("""INSERT INTO wawi.rezension (artikel_id, sterne, inhalt, quelle)
                  VALUES (1, 5, 'Simulation', 'simulation') RETURNING rezension_id""")
    rid = db.fetchone()[0]
    als(db, "bm_pruefdienst")
    assert fehler(db, "SELECT wawi.pruefung_eintragen(rezension_id => %s, ergebnis => 'freigegeben')",
                  (rid,)) is psycopg2.errors.ForeignKeyViolation


@pytest.mark.parametrize("rolle", ["anon", "authenticated", "studi_daba"])
@pytest.mark.parametrize("aufruf", [
    "SELECT * FROM wawi.pruefung_offene_holen(1)",
    "SELECT wawi.pruefung_heute()",
    "SELECT wawi.pruefung_eintragen(rezension_id => 1, ergebnis => 'freigegeben')",
])
def test_dienstfunktionen_nur_fuer_den_pruefdienst(db, rolle, aufruf):
    als(db, rolle)
    assert fehler(db, aufruf) is psycopg2.errors.InsufficientPrivilege


def test_pruefdienst_liest_keine_tabellen(db):
    als(db, "bm_pruefdienst")
    assert fehler(db, "SELECT 1 FROM wawi.rezension LIMIT 1") is psycopg2.errors.InsufficientPrivilege
```

- [ ] **Step 2: Tests laufen lassen, sie müssen scheitern**

Run: `bash db/tests/security_local.sh -q -k rezension_freigabe`
Expected: FAIL mit `UndefinedFunction: function wawi.pruefung_eintragen(…) does not exist`.

- [ ] **Step 3: Abschnitt 3 an die Migration anhängen**

```sql
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
```

- [ ] **Step 4: Tests laufen lassen**

Run: `bash db/tests/security_local.sh -q -k rezension_freigabe`
Expected: alle bestanden (`30` bisher und `22` neu, also `52 passed`).

- [ ] **Step 5: Commit**

```bash
git -c core.fileMode=false add db/aufbau/0023_rezension_freigabe.sql db/tests/test_rezension_freigabe.py
git commit -m "Freigabe A: Dienstfunktionen für den Prüfdienst" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Entscheidungen von Menschen

**Files:**
- Modify: `db/aufbau/0023_rezension_freigabe.sql` (Abschnitt 4 anhängen)
- Test: `db/tests/test_rezension_freigabe.py` (anhängen)

**Interfaces:**
- Consumes: `hat_rolle()`, Tabellen, Helfer `konto`, `eintragen`, `zurueckgehalten`.
- Produces (Phase E ruft diese über PostgREST mit genau diesen JSON-Schlüsseln):
  - `wawi.api_rezension_freigeben(rezension_id bigint, bemerkung text DEFAULT NULL) → jsonb {rezension_id, status}`
  - `wawi.api_rezension_ablehnen(rezension_id bigint, bemerkung text DEFAULT NULL) → jsonb {rezension_id, status}`
  - `wawi.api_qs_fall_erledigen(qs_fall_id bigint, bemerkung text DEFAULT NULL) → jsonb {qs_fall_id, erledigt_am}`
  - Fehlercodes: `42501` ohne Rolle (PostgREST: HTTP 401/403), `23503` unbekannte Rezension oder unbekannter Fall, `55000` schon entschieden oder erledigt, `22023` Bemerkung über 500 Zeichen.
  - interne Hilfe `wawi.rezension_entscheiden(rezension_id bigint, entscheidung text, bemerkung text)`, für niemanden ausführbar außer `postgres`.

- [ ] **Step 1: Tests anhängen**

```python
def test_freigeben_braucht_die_rolle_moderation(db):
    rid = zurueckgehalten(db)
    als(db, "authenticated", konto(db))
    assert fehler(db, "SELECT wawi.api_rezension_freigeben(%s)", (rid,)) is psycopg2.errors.InsufficientPrivilege
    als(db, "authenticated", konto(db, "qualitaet"))
    assert fehler(db, "SELECT wawi.api_rezension_freigeben(%s)", (rid,)) is psycopg2.errors.InsufficientPrivilege
    als(db, "anon")
    assert fehler(db, "SELECT wawi.api_rezension_freigeben(%s)", (rid,)) is psycopg2.errors.InsufficientPrivilege


def test_freigeben_macht_die_rezension_oeffentlich(db):
    rid = zurueckgehalten(db, "Der Service war super, danke!")
    kennung = konto(db, "moderation")
    als(db, "authenticated", kennung)
    db.execute("SELECT wawi.api_rezension_freigeben(%s, '  geprüft  ')", (rid,))
    assert db.fetchone()[0] == {"rezension_id": rid, "status": "freigegeben"}
    zurueck(db)
    db.execute("SELECT entscheidung, konto, bemerkung FROM wawi.rezension_entscheidung WHERE rezension_id = %s", (rid,))
    assert db.fetchone() == ("freigegeben", kennung, "geprüft")
    als(db, "anon")
    db.execute("SELECT inhalt FROM wawi.rezension WHERE rezension_id = %s", (rid,))
    assert db.fetchone()[0] == "Der Service war super, danke!"


def test_ablehnen_und_keine_zweite_entscheidung(db):
    rid = zurueckgehalten(db)
    als(db, "authenticated", konto(db, "moderation"))
    db.execute("SELECT wawi.api_rezension_ablehnen(%s)", (rid,))
    assert db.fetchone()[0] == {"rezension_id": rid, "status": "abgelehnt"}
    assert fehler(db, "SELECT wawi.api_rezension_freigeben(%s)", (rid,)) \
        is psycopg2.errors.ObjectNotInPrerequisiteState


def test_offene_rezension_laesst_sich_direkt_entscheiden(db):
    # Fällt der Prüfdienst aus, entscheidet ein Mensch auch über offene Rezensionen.
    rid = shop_rezension(db)
    als(db, "authenticated", konto(db, "moderation"))
    db.execute("SELECT wawi.api_rezension_freigeben(%s)", (rid,))
    assert db.fetchone()[0]["status"] == "freigegeben"


def test_simulation_laesst_sich_nicht_entscheiden(db):
    db.execute("""INSERT INTO wawi.rezension (artikel_id, sterne, inhalt, quelle)
                  VALUES (1, 5, 'Simulation', 'simulation') RETURNING rezension_id""")
    rid = db.fetchone()[0]
    als(db, "authenticated", konto(db, "moderation"))
    assert fehler(db, "SELECT wawi.api_rezension_ablehnen(%s)", (rid,)) is psycopg2.errors.ForeignKeyViolation


def test_bemerkung_hoechstens_500_zeichen(db):
    rid = zurueckgehalten(db)
    als(db, "authenticated", konto(db, "moderation"))
    assert fehler(db, "SELECT wawi.api_rezension_freigeben(%s, %s)", (rid, "x" * 501)) \
        is psycopg2.errors.InvalidParameterValue


def test_menschliche_entscheidung_bleibt(db):
    rid = shop_rezension(db)
    als(db, "authenticated", konto(db, "moderation"))
    db.execute("SELECT wawi.api_rezension_ablehnen(%s, 'Werbung')", (rid,))
    zurueck(db)
    assert eintragen(db, rid, "freigegeben") == {"rezension_id": rid, "status": "abgelehnt",
                                                 "uebersprungen": True}


def test_qs_fall_erledigen_braucht_die_rolle_qualitaet(db):
    rid = shop_rezension(db, "Im Salat war ein Stück Plastik.")
    eintragen(db, rid, "zurueckgehalten", ["Gesundheitsrisiko"], qs=True)
    db.execute("SELECT qs_fall_id FROM wawi.qs_fall WHERE rezension_id = %s", (rid,))
    fall = db.fetchone()[0]
    als(db, "authenticated", konto(db, "moderation"))
    assert fehler(db, "SELECT wawi.api_qs_fall_erledigen(%s)", (fall,)) is psycopg2.errors.InsufficientPrivilege
    als(db, "authenticated", konto(db, "qualitaet"))
    db.execute("SELECT wawi.api_qs_fall_erledigen(%s, 'Filiale informiert')", (fall,))
    assert db.fetchone()[0]["qs_fall_id"] == fall
    assert fehler(db, "SELECT wawi.api_qs_fall_erledigen(%s)", (fall,)) \
        is psycopg2.errors.ObjectNotInPrerequisiteState
    zurueck(db)
    # Den QS-Fall zu erledigen gibt die Rezension nicht frei.
    db.execute("SELECT status FROM wawi.rezension WHERE rezension_id = %s", (rid,))
    assert db.fetchone()[0] == "zurueckgehalten"


def test_rollen_gehen_mit_dem_konto_entscheidungen_bleiben(db):
    rid = shop_rezension(db)
    kennung = konto(db, "moderation")
    als(db, "authenticated", kennung)
    db.execute("SELECT wawi.api_rezension_ablehnen(%s)", (rid,))
    zurueck(db)
    db.execute("DELETE FROM auth.users WHERE id = %s", (kennung,))
    db.execute("SELECT count(*) FROM wawi.rezension_entscheidung WHERE konto = %s", (kennung,))
    assert db.fetchone()[0] == 1


@pytest.mark.parametrize("rolle", ["authenticated", "bm_pruefdienst", "anon"])
def test_hilfsfunktion_ist_nicht_aufrufbar(db, rolle):
    als(db, rolle, konto(db, "moderation") if rolle == "authenticated" else None)
    assert fehler(db, "SELECT wawi.rezension_entscheiden(1, 'freigegeben', NULL)") \
        is psycopg2.errors.InsufficientPrivilege


def test_pruefdienst_darf_nicht_entscheiden(db):
    als(db, "bm_pruefdienst")
    assert fehler(db, "SELECT wawi.api_rezension_freigeben(1)") is psycopg2.errors.InsufficientPrivilege
    assert fehler(db, "SELECT wawi.api_qs_fall_erledigen(1)") is psycopg2.errors.InsufficientPrivilege
```

- [ ] **Step 2: Tests laufen lassen, sie müssen scheitern**

Run: `bash db/tests/security_local.sh -q -k rezension_freigabe`
Expected: FAIL mit `UndefinedFunction: function wawi.api_rezension_freigeben(…) does not exist`.

- [ ] **Step 3: Abschnitt 4 an die Migration anhängen**

```sql
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
```

- [ ] **Step 4: Tests laufen lassen**

Run: `bash db/tests/security_local.sh -q -k rezension_freigabe`
Expected: alle bestanden (`52` bisher und `13` neu, also `65 passed`).

- [ ] **Step 5: Commit**

```bash
git -c core.fileMode=false add db/aufbau/0023_rezension_freigabe.sql db/tests/test_rezension_freigabe.py
git commit -m "Freigabe A: Freigeben, Ablehnen und QS-Fälle für Menschen" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Sichten für Shop, POS und Notebook

**Files:**
- Modify: `db/aufbau/0023_rezension_freigabe.sql` (Abschnitt 5 anhängen)
- Test: `db/tests/test_rezension_freigabe.py` (anhängen)

**Interfaces:**
- Consumes: alles aus Task 1 bis 4.
- Produces (Spaltennamen sind Schnittstelle für Phase B, D, E und das Notebook):
  - `wawi.stg_fact_reviews` wie bisher, nur freigegebene Zeilen.
  - `wawi.v_rezension_produkt`: `artikel_id, name, anzahl, sterne_mittel, letzte, anzahl_1, anzahl_2, anzahl_3, anzahl_4, anzahl_5` (nur freigegebene).
  - `wawi.v_kundenstimmen`: wie bisher, drei jüngste freigegebene je Artikel aus beiden Quellen.
  - `wawi.v_rezension_letzte`: wie bisher plus `status`; `inhalt` ist `NULL`, solange nicht freigegeben.
  - `wawi.v_rezensionen_lesen`: `artikel_id, rezension_id, sterne, inhalt, datum, erstellt_am, quelle, status` (nur freigegebene).
  - `wawi.v_rezension_status`: `rezension_id, status` (alle Shop-Rezensionen, ohne Text).
  - `wawi.v_moderation`: `rezension_id, status, artikel, filiale, sterne, inhalt, erstellt_am, geprueft_am, gruende, qs_fall, muster_treffer, fehler, p_beleidigung, p_personenbezug, p_werbung, p_themenbezug, p_anweisung, p_gesundheitsrisiko`. Nur mit Rolle `moderation`; zurückgehaltene und offene älter als fünf Minuten.
  - `wawi.v_qs_faelle`: `qs_fall_id, rezension_id, angelegt_am, artikel, filiale, sterne, inhalt, erstellt_am, status, p_gesundheitsrisiko`. Nur mit Rolle `qualitaet`, nur unerledigte.
  - `wawi.v_entscheidungen_letzte`: `entscheidung_id, rezension_id, entscheidung, entschieden_am, bemerkung, artikel, sterne, inhalt` (höchstens 20, nur mit Rolle `moderation`).
  - `wawi.v_pruefdienst_stand`: eine Zeile `letzte_pruefung, offen, aelteste_offene_min, zurueckgehalten, qs_offen` (ohne Texte, auch für `anon`).
  - `wawi.v_freigabe_statistik`: `tag, status, anzahl` (Shop-Rezensionen, nur `studi_daba`).

- [ ] **Step 1: Tests anhängen**

```python
@pytest.mark.parametrize("rolle", ["anon", "studi_daba"])
def test_oeffentliche_sichten_zeigen_nur_freigegebene_texte(db, rolle):
    offen = shop_rezension(db, "GEHEIM offen")
    halten = zurueckgehalten(db, "GEHEIM zurückgehalten")
    frei = shop_rezension(db, "Sichtbar und lecker")
    eintragen(db, frei, "freigegeben")
    als(db, rolle)
    for sicht, spalte in [("wawi.v_rezensionen_lesen", "inhalt"), ("wawi.v_kundenstimmen", "inhalt"),
                          ("wawi.v_rezension_letzte", "inhalt"), ("wawi.stg_fact_reviews", "review_text")]:
        db.execute(f"SELECT count(*) FROM {sicht} WHERE {spalte} LIKE 'GEHEIM%'")
        assert db.fetchone()[0] == 0, sicht
    db.execute("SELECT inhalt, status FROM wawi.v_rezensionen_lesen WHERE rezension_id = %s", (frei,))
    assert db.fetchone() == ("Sichtbar und lecker", "freigegeben")
    db.execute("SELECT status, inhalt FROM wawi.v_rezension_letzte WHERE rezension_id = %s", (offen,))
    assert db.fetchone() == ("offen", None)
    db.execute("SELECT status FROM wawi.v_rezension_status WHERE rezension_id = %s", (halten,))
    assert db.fetchone()[0] == "zurueckgehalten"


def test_kundenstimmen_zeigen_auch_freigegebene_besuchertexte(db):
    rid = shop_rezension(db, "Schneller Service, gerne wieder.")
    eintragen(db, rid, "freigegeben")
    als(db, "anon")
    db.execute("SELECT inhalt FROM wawi.v_kundenstimmen WHERE rezension_id = %s", (rid,))
    assert db.fetchone()[0] == "Schneller Service, gerne wieder."


def test_verteilung_summiert_sich_zur_anzahl(db):
    for sterne in (5, 5, 4, 1):
        rid = shop_rezension(db, sterne=sterne)
        eintragen(db, rid, "freigegeben")
    shop_rezension(db, sterne=3)  # offen, zählt nicht
    als(db, "anon")
    db.execute("""SELECT anzahl, anzahl_1, anzahl_2, anzahl_3, anzahl_4, anzahl_5, sterne_mittel
                  FROM wawi.v_rezension_produkt WHERE artikel_id = 1""")
    assert db.fetchone() == (4, 1, 0, 0, 1, 2, Decimal("3.8"))


def test_moderationssicht_nur_mit_rolle(db):
    halten = zurueckgehalten(db)
    alt = shop_rezension(db, "wartet schon lange")
    db.execute("UPDATE wawi.rezension SET erstellt_am = erstellt_am - interval '6 minutes' WHERE rezension_id = %s", (alt,))
    shop_rezension(db, "gerade geschrieben")
    als(db, "authenticated", konto(db))
    db.execute("SELECT count(*) FROM wawi.v_moderation")
    assert db.fetchone()[0] == 0
    als(db, "authenticated", konto(db, "moderation"))
    db.execute("SELECT rezension_id, gruende FROM wawi.v_moderation ORDER BY rezension_id")
    assert db.fetchall() == [(halten, ["unsicher"]), (alt, None)]
    als(db, "anon")
    assert fehler(db, "SELECT 1 FROM wawi.v_moderation") is psycopg2.errors.InsufficientPrivilege


def test_qs_sicht_nur_mit_rolle_qualitaet(db):
    rid = shop_rezension(db, "Ich habe eine Nussallergie und bekam Ausschlag.")
    eintragen(db, rid, "zurueckgehalten", ["Gesundheitsrisiko"], qs=True)
    als(db, "authenticated", konto(db, "moderation"))
    db.execute("SELECT count(*) FROM wawi.v_qs_faelle")
    assert db.fetchone()[0] == 0
    als(db, "authenticated", konto(db, "qualitaet"))
    db.execute("SELECT rezension_id, inhalt, status FROM wawi.v_qs_faelle")
    assert db.fetchall() == [(rid, "Ich habe eine Nussallergie und bekam Ausschlag.", "zurueckgehalten")]


def test_entscheidungen_letzte_hoechstens_zwanzig(db):
    kennung = konto(db, "moderation")
    for _ in range(21):
        rid = shop_rezension(db)
        als(db, "authenticated", kennung)
        db.execute("SELECT wawi.api_rezension_freigeben(%s)", (rid,))
        zurueck(db)
    als(db, "authenticated", kennung)
    db.execute("SELECT count(*) FROM wawi.v_entscheidungen_letzte")
    assert db.fetchone()[0] == 20


def test_pruefdienst_stand_ohne_anmeldung(db):
    rid = shop_rezension(db)
    db.execute("UPDATE wawi.rezension SET erstellt_am = now() - interval '7 minutes' WHERE rezension_id = %s", (rid,))
    zurueckgehalten(db)
    qs = shop_rezension(db, "Das Fleisch war innen roh.")
    eintragen(db, qs, "zurueckgehalten", ["Gesundheitsrisiko"], qs=True)
    als(db, "anon")
    db.execute("SELECT offen, aelteste_offene_min, zurueckgehalten, qs_offen FROM wawi.v_pruefdienst_stand")
    assert db.fetchone() == (1, 7, 2, 1)


def test_freigabe_statistik_nur_fuer_studi_daba(db):
    shop_rezension(db)
    frei = shop_rezension(db)
    eintragen(db, frei, "freigegeben")
    als(db, "studi_daba")
    db.execute("SELECT status, anzahl FROM wawi.v_freigabe_statistik ORDER BY status")
    assert db.fetchall() == [("freigegeben", 1), ("offen", 1)]
    for rolle in ("anon", "authenticated"):
        als(db, rolle)
        assert fehler(db, "SELECT 1 FROM wawi.v_freigabe_statistik") is psycopg2.errors.InsufficientPrivilege


def test_uebungsrezensionen_loeschen_raeumt_alles_ab(db):
    rid = shop_rezension(db, "Im Burger war ein Haar.")
    eintragen(db, rid, "zurueckgehalten", ["Gesundheitsrisiko"], qs=True)
    als(db, "authenticated", konto(db, "moderation"))
    db.execute("SELECT wawi.api_rezension_ablehnen(%s)", (rid,))
    zurueck(db)
    db.execute("SELECT * FROM wawi.uebungsrezensionen_loeschen()")
    for tabelle in ("wawi.rezension_pruefung", "wawi.rezension_entscheidung", "wawi.qs_fall"):
        db.execute(f"SELECT count(*) FROM {tabelle}")
        assert db.fetchone()[0] == 0, tabelle
```

- [ ] **Step 2: Tests laufen lassen, sie müssen scheitern**

Run: `bash db/tests/security_local.sh -q -k rezension_freigabe`
Expected: FAIL mit `UndefinedTable: relation "wawi.v_rezensionen_lesen" does not exist` und falschen Zählungen in `v_rezension_produkt`.

- [ ] **Step 3: Abschnitt 5 an die Migration anhängen**

```sql
-- ---------------------------------------------------------------------------
-- 5 Sichten. Bestehende Sichten werden mit CREATE OR REPLACE geändert; neue
--   Spalten stehen hinten, Rechte bleiben erhalten. Neue Sichten bekommen
--   ausdrücklich nur die Rechte aus der Spezifikation (Abschnitt 5.3).
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
LEFT JOIN LATERAL (SELECT x.* FROM wawi.rezension_pruefung x
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
FROM   wawi.qs_fall q
JOIN   wawi.rezension r ON r.rezension_id = q.rezension_id
JOIN   wawi.artikel a ON a.artikel_id = r.artikel_id
LEFT JOIN wawi.filiale f ON f.filiale_id = r.filiale_id
LEFT JOIN LATERAL (SELECT x.p_gesundheitsrisiko FROM wawi.rezension_pruefung x
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
FROM   wawi.rezension_entscheidung e
JOIN   wawi.rezension r ON r.rezension_id = e.rezension_id
JOIN   wawi.artikel a ON a.artikel_id = r.artikel_id
WHERE  wawi.hat_rolle('moderation')
ORDER  BY e.entschieden_am DESC, e.entscheidung_id DESC
LIMIT  20;

-- Zustand des Prüfdienstes ohne Texte, auch ohne Anmeldung lesbar.
CREATE OR REPLACE VIEW wawi.v_pruefdienst_stand AS
SELECT (SELECT max(p.geprueft_am) FROM wawi.rezension_pruefung p)                  AS letzte_pruefung,
       (SELECT count(*)::int FROM wawi.rezension r
        WHERE r.status = 'offen' AND r.quelle = 'shop')                            AS offen,
       (SELECT floor(extract(epoch FROM now() - min(r.erstellt_am)) / 60)::int
        FROM wawi.rezension r WHERE r.status = 'offen' AND r.quelle = 'shop')       AS aelteste_offene_min,
       (SELECT count(*)::int FROM wawi.rezension r WHERE r.status = 'zurueckgehalten') AS zurueckgehalten,
       (SELECT count(*)::int FROM wawi.qs_fall q WHERE q.erledigt_am IS NULL)      AS qs_offen;

-- Shop-Rezensionen je Tag und Status, ohne Texte; für Notebook 09.
CREATE OR REPLACE VIEW wawi.v_freigabe_statistik AS
SELECT (r.erstellt_am AT TIME ZONE 'Europe/Berlin')::date AS tag, r.status, count(*)::int AS anzahl
FROM   wawi.rezension r
WHERE  r.quelle = 'shop'
GROUP  BY 1, 2
ORDER  BY 1, 2;

REVOKE ALL ON wawi.v_rezensionen_lesen, wawi.v_rezension_status, wawi.v_moderation,
              wawi.v_qs_faelle, wawi.v_entscheidungen_letzte, wawi.v_pruefdienst_stand,
              wawi.v_freigabe_statistik
  FROM PUBLIC, anon, authenticated, studi_daba;
GRANT SELECT ON wawi.v_rezensionen_lesen, wawi.v_rezension_status, wawi.v_pruefdienst_stand
  TO anon, authenticated, studi_daba;
GRANT SELECT ON wawi.v_moderation, wawi.v_qs_faelle, wawi.v_entscheidungen_letzte TO authenticated;
GRANT SELECT ON wawi.v_freigabe_statistik TO studi_daba;
```

- [ ] **Step 4: Tests laufen lassen**

Run: `bash db/tests/security_local.sh -q -k rezension_freigabe`
Expected: alle bestanden (`65` bisher und `10` neu, also `75 passed`).

- [ ] **Step 5: Commit**

```bash
git -c core.fileMode=false add db/aufbau/0023_rezension_freigabe.sql db/tests/test_rezension_freigabe.py
git commit -m "Freigabe A: Sichten für Shop, POS und Notebook" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Probe, Rücknahme und Hinweis in `0021`

**Files:**
- Modify: `db/aufbau/0023_rezension_freigabe.sql` (Abschnitt 6 anhängen)
- Modify: `db/aufbau/0021_rezensionen.sql` (nur der Kopfkommentar)
- Modify: `db/tests/README.md`
- Test: `db/tests/test_rezension_freigabe.py` (anhängen)

**Interfaces:**
- Consumes: alle Objekte aus Task 1 bis 5.
- Produces: `NOTICE 'Freigabe: Status, Prüftabellen, Rollen und Sichten wie vorgesehen.'` bei Erfolg; `RAISE EXCEPTION` bei Abweichung. Abschnittsmarke `-- 6 Probe` (der Test schneidet daran).

- [ ] **Step 1: Test anhängen**

```python
def probe_text():
    """Abschnitt 6 der Migration ohne den Rest der Markenzeile."""
    text = (AUFBAU / "0023_rezension_freigabe.sql").read_text()
    return text.split("-- 6 Probe", 1)[1].split("\n", 1)[1]


def test_probe_meldet_ein_offenes_recht(db):
    probe = probe_text()
    db.execute("GRANT SELECT ON wawi.qs_fall TO anon")
    assert fehler(db, probe) is psycopg2.errors.RaiseException


def test_probe_laeuft_im_sauberen_stand(db):
    probe = probe_text()
    assert fehler(db, probe) is None
```

- [ ] **Step 2: Tests laufen lassen, sie müssen scheitern**

Run: `bash db/tests/security_local.sh -q -k probe`
Expected: FAIL mit `IndexError: list index out of range` (die Marke `-- 6 Probe` fehlt noch).

- [ ] **Step 3: Abschnitt 6 an die Migration anhängen**

```sql
-- ---------------------------------------------------------------------------
-- 6 Probe: Status, Richtlinie und Rechte wie vorgesehen. Bricht mit
--   EXCEPTION ab, wenn nicht.
-- ---------------------------------------------------------------------------
DO $$
DECLARE
  v_anzahl bigint;
  v_objekt text;
BEGIN
  SELECT count(*) INTO v_anzahl FROM wawi.rezension
  WHERE  quelle = 'simulation' AND status <> 'freigegeben';
  IF v_anzahl > 0 THEN
    RAISE EXCEPTION '% Simulationszeilen sind nicht freigegeben', v_anzahl;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policy
                 WHERE polrelid = 'wawi.rezension'::regclass AND polname = 'lesen_freigegeben')
     OR EXISTS (SELECT 1 FROM pg_policy
                WHERE polrelid = 'wawi.rezension'::regclass AND polname = 'lesen_alle') THEN
    RAISE EXCEPTION 'Richtlinie auf wawi.rezension nicht wie vorgesehen';
  END IF;
  FOREACH v_objekt IN ARRAY ARRAY['wawi.rezension_pruefung', 'wawi.rezension_entscheidung',
                                  'wawi.qs_fall', 'wawi.mitarbeiter_rolle'] LOOP
    IF has_table_privilege('anon', v_objekt, 'SELECT')
       OR has_table_privilege('authenticated', v_objekt, 'SELECT')
       OR has_table_privilege('studi_daba', v_objekt, 'SELECT')
       OR has_table_privilege('bm_pruefdienst', v_objekt, 'SELECT') THEN
      RAISE EXCEPTION '% ist nicht verschlossen', v_objekt;
    END IF;
  END LOOP;
  FOREACH v_objekt IN ARRAY ARRAY['wawi.v_moderation', 'wawi.v_qs_faelle',
                                  'wawi.v_entscheidungen_letzte', 'wawi.v_freigabe_statistik'] LOOP
    IF has_table_privilege('anon', v_objekt, 'SELECT') THEN
      RAISE EXCEPTION 'anon liest %', v_objekt;
    END IF;
  END LOOP;
  IF NOT has_table_privilege('anon', 'wawi.v_rezensionen_lesen', 'SELECT')
     OR NOT has_table_privilege('anon', 'wawi.v_pruefdienst_stand', 'SELECT')
     OR NOT has_table_privilege('studi_daba', 'wawi.v_freigabe_statistik', 'SELECT') THEN
    RAISE EXCEPTION 'Leserechte der neuen Sichten fehlen';
  END IF;
  IF has_function_privilege('anon', 'wawi.api_rezension_freigeben(bigint, text)', 'EXECUTE')
     OR has_function_privilege('authenticated', 'wawi.pruefung_offene_holen(integer)', 'EXECUTE')
     OR has_function_privilege('authenticated', 'wawi.rezension_entscheiden(bigint, text, text)', 'EXECUTE')
     OR NOT has_function_privilege('bm_pruefdienst', 'wawi.pruefung_offene_holen(integer)', 'EXECUTE')
     OR NOT has_function_privilege('authenticated', 'wawi.api_rezension_freigeben(bigint, text)', 'EXECUTE') THEN
    RAISE EXCEPTION 'Funktionsrechte nicht wie vorgesehen';
  END IF;
  RAISE NOTICE 'Freigabe: Status, Prüftabellen, Rollen und Sichten wie vorgesehen.';
END $$;

NOTIFY pgrst, 'reload schema';

-- Rücknahme (als postgres, in dieser Reihenfolge):
--   DROP VIEW wawi.v_freigabe_statistik, wawi.v_pruefdienst_stand, wawi.v_entscheidungen_letzte,
--             wawi.v_qs_faelle, wawi.v_moderation, wawi.v_rezension_status, wawi.v_rezensionen_lesen;
--   DROP FUNCTION wawi.api_qs_fall_erledigen(bigint, text), wawi.api_rezension_ablehnen(bigint, text),
--                 wawi.api_rezension_freigeben(bigint, text), wawi.rezension_entscheiden(bigint, text, text),
--                 wawi.pruefung_heute(), wawi.pruefung_offene_holen(integer),
--                 wawi.pruefung_eintragen(bigint, text, text[], boolean, jsonb, text[], boolean,
--                                         text, text, text, text, integer, text),
--                 wawi.hat_rolle(text);
--   DROP TABLE wawi.qs_fall, wawi.rezension_entscheidung, wawi.rezension_pruefung, wawi.mitarbeiter_rolle;
--   REVOKE USAGE ON SCHEMA wawi FROM bm_pruefdienst;
--   DROP ROLE bm_pruefdienst;   -- vorher den Prüfdienst auf dem VPS anhalten
--   DROP POLICY lesen_freigegeben ON wawi.rezension;
--   0021 erneut einspielen (Sichten, stg_fact_reviews, rezension_anlegen, Richtlinie lesen_alle);
--   DROP TRIGGER rezension_status_vorgabe ON wawi.rezension;
--   DROP FUNCTION wawi.rezension_status_vorgabe();
--   ALTER TABLE wawi.rezension DROP CONSTRAINT rezension_simulation_freigegeben,
--                              DROP CONSTRAINT rezension_status_gueltig, DROP COLUMN status;
```

- [ ] **Step 4: Hinweis in den Kopf von `0021` setzen**

In `db/aufbau/0021_rezensionen.sql` nach der Zeile

```sql
-- und faehrt dieses Skript danach erneut. etl_probe() zeigt jede Abweichung.
```

einfügen:

```sql
-- Seit 0023 danach auch 0023_rezension_freigabe.sql erneut ausführen: dieses
-- Skript setzt Sichten und Richtlinie auf den Stand ohne Freigabe zurück.
```

- [ ] **Step 5: `db/tests/README.md` ergänzen**

Am Ende anfügen:

```markdown
`test_rezension_freigabe.py` prüft die Freigabe der Rezensionen aus `0023` auf
derselben Wegwerf-Instanz, in einer eigenen Datenbank `bm_freigabe`
(`freigabe_cluster.py` baut sie auf): Status und Leserichtlinie, verschlossene
Prüftabellen, die Dienstfunktionen der Rolle `bm_pruefdienst`, Freigeben,
Ablehnen und QS-Fälle mit nachgestellter Supabase-Anmeldung, die Sichten und
die Probe. Nur diese Tests: `bash db/tests/security_local.sh -q -k rezension_freigabe`.
```

- [ ] **Step 6: Alle Freigabetests laufen lassen**

Run: `bash db/tests/security_local.sh -q -k rezension_freigabe`
Expected: `77 passed`.

- [ ] **Step 7: Commit**

```bash
git -c core.fileMode=false add db/aufbau/0023_rezension_freigabe.sql db/aufbau/0021_rezensionen.sql db/tests/README.md db/tests/test_rezension_freigabe.py
git commit -m "Freigabe A: Probe, Rücknahme und Hinweis in 0021" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Produktion, Integrationstests, Dokumentation, PR

**Files:**
- Modify: `web/tests/datenquelle_rezensionen.test.mjs`
- Modify: `db/README.md`
- Modify: `docs/02-datenmodell.md`

**Interfaces:**
- Consumes: die fertige Migration; `QUELLE` aus `web/js/konfiguration.js`; `.env` im Repo (Betreiberkonto `postgres`, nie ausgeben).
- Produces: `0023` live auf `supabase.butscher.cloud`; PR „Freigabe A“ auf `main`.

- [ ] **Step 1: Integrationstests gegen PostgREST anpassen und ergänzen**

In `web/tests/datenquelle_rezensionen.test.mjs` den Test `letzteRezensionen: Liste mit den Feldern der Sicht` ersetzen durch:

```js
test('letzteRezensionen: Status je Zeile, Text nur bei freigegebenen', async () => {
  const zeilen = await quelle.letzteRezensionen();
  assert.ok(Array.isArray(zeilen));
  for (const z of zeilen) {
    for (const feld of ['rezension_id', 'artikel', 'sterne', 'erstellt_am', 'im_warehouse', 'status']) {
      assert.ok(feld in z, `Feld ${feld} fehlt`);
    }
    assert.ok(['offen', 'freigegeben', 'zurueckgehalten', 'abgelehnt'].includes(z.status), `Status ${z.status}`);
    if (z.status !== 'freigegeben') assert.equal(z.inhalt, null);
  }
});
```

und am Ende der Datei anfügen:

```js
// Ohne Anmeldung: dieselben Kopfzeilen wie der Shop, nur der öffentliche Schlüssel.
function kopf(art) {
  return {
    apikey: QUELLE.schluessel,
    Authorization: `Bearer ${QUELLE.schluessel}`,
    [art === 'GET' ? 'Accept-Profile' : 'Content-Profile']: 'wawi',
    'Content-Type': 'application/json',
  };
}

test('wawi.rezension zeigt ohne Anmeldung nur freigegebene Zeilen', async () => {
  const antwort = await fetch(`${QUELLE.url}/rest/v1/rezension?status=neq.freigegeben&select=rezension_id&limit=1`,
    { headers: kopf('GET') });
  assert.equal(antwort.status, 200);
  assert.deepEqual(await antwort.json(), []);
});

for (const [pfad, art, koerper] of [
  ['v_moderation?limit=1', 'GET', null],
  ['v_qs_faelle?limit=1', 'GET', null],
  ['v_freigabe_statistik?limit=1', 'GET', null],
  ['rpc/api_rezension_freigeben', 'POST', { rezension_id: 1 }],
  ['rpc/pruefung_offene_holen', 'POST', { p_anzahl: 1 }],
  ['rpc/pruefung_eintragen', 'POST', { rezension_id: 1, ergebnis: 'freigegeben' }],
]) {
  test(`ohne Anmeldung verschlossen: ${pfad}`, async () => {
    const antwort = await fetch(`${QUELLE.url}/rest/v1/${pfad}`, {
      method: art, headers: kopf(art), body: koerper ? JSON.stringify(koerper) : undefined });
    assert.ok([401, 403].includes(antwort.status), `HTTP ${antwort.status}`);
  });
}

test('pruefdienstStand ist ohne Anmeldung lesbar und ohne Text', async () => {
  const antwort = await fetch(`${QUELLE.url}/rest/v1/v_pruefdienst_stand`, { headers: kopf('GET') });
  assert.equal(antwort.status, 200);
  const [zeile] = await antwort.json();
  assert.deepEqual(Object.keys(zeile).sort(),
    ['aelteste_offene_min', 'letzte_pruefung', 'offen', 'qs_offen', 'zurueckgehalten']);
});
```

- [ ] **Step 2: Integrationstests laufen lassen, sie müssen scheitern**

Run: `node --test "web/tests/*.test.mjs"`
Expected: FAIL. Die neuen Tests scheitern, weil `0023` in der Produktion noch fehlt (`Feld status fehlt`, `HTTP 404` bei `v_pruefdienst_stand`).

- [ ] **Step 3: Migration in der Produktion einspielen, zweimal**

Run: `python3 db/skript_ausfuehren.py db/aufbau/0023_rezension_freigabe.sql`
Expected: NOTICE `Freigabe: Status, Prüftabellen, Rollen und Sichten wie vorgesehen.`, Rückgabecode 0.

Run (Wiederholbarkeit): `python3 db/skript_ausfuehren.py db/aufbau/0023_rezension_freigabe.sql`
Expected: dieselbe NOTICE, Rückgabecode 0.

- [ ] **Step 4: Stand in der Produktion lesend prüfen**

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, "db")
from skript_ausfuehren import verbinde
con = verbinde(); cur = con.cursor()
cur.execute("SELECT quelle, status, count(*) FROM wawi.rezension GROUP BY 1, 2 ORDER BY 1, 2")
print(cur.fetchall())
cur.execute("SELECT count(*) FROM pg_roles WHERE rolname = 'bm_pruefdienst'")
print("bm_pruefdienst:", cur.fetchone()[0])
cur.execute("SELECT * FROM wawi.etl_probe()")
print(cur.fetchall())
con.close()
PY
```

Expected: `[('simulation', 'freigegeben', 10000)]` plus gegebenenfalls Zeilen `('shop', 'offen', n)`; `bm_pruefdienst: 1`; `etl_probe()` liefert je Tabelle `0` und `0`.

- [ ] **Step 5: Integrationstests erneut laufen lassen**

Run: `node --test "web/tests/*.test.mjs"`
Expected: alle bestanden. Antwortet PostgREST bei `v_pruefdienst_stand` weiter mit `404`, hat es das Schema nicht neu geladen: `ssh vps 'docker restart supabase-rest'`, 20 Sekunden warten, erneut laufen lassen.

- [ ] **Step 6: Shop im Browser kurz prüfen**

`https://swrobuts.github.io/BurgerMetrics/shop.html` im eingebauten Browser öffnen (Pages liefert noch den alten Stand von `main`): Die Karten zeigen Bewertungen wie vorher (Simulation, 10.000 freigegeben), die Kundenstimmen erscheinen, die Konsole zeigt keinen Fehler. Keine Rezension absenden.

- [ ] **Step 7: `db/README.md` nachziehen**

1. In der Tabelle der Aufbauskripte nach der Zeile für `aufbau/0022_bestellquote.sql` einfügen:

```markdown
| `aufbau/0023_rezension_freigabe.sql` | Freigabe der Shop-Rezensionen: Status in `wawi.rezension`, Prüftabellen, Rolle `bm_pruefdienst`, Rollen `moderation` und `qualitaet`, Sichten für Shop und POS — nach jedem erneuten Lauf von `0021` wiederholen |
```

2. Im Abschnitt „Rezensionen: vom Shop ins Warehouse“ den Absatz, der mit „Öffentlich sichtbar sind nur Aggregate“ beginnt und mit „das prüft die Probe am Ende von `0021`.“ endet, ersetzen durch:

```markdown
Seit `0023` hat jede Rezension einen Status: `offen`, `freigegeben`,
`zurueckgehalten` oder `abgelehnt`. Der Simulationsbestand ist freigegeben,
Shop-Rezensionen beginnen offen. Öffentlich lesbar sind nur freigegebene, in
den Sichten und über die Richtlinie `lesen_freigegeben` auch in der Tabelle
selbst; `v_rezension_letzte` zeigt Status und Datensatz, den Text aber erst
nach der Freigabe. Den Status setzen der Prüfdienst (Rolle `bm_pruefdienst`,
nur `pruefung_offene_holen()`, `pruefung_eintragen()` und `pruefung_heute()`)
und Menschen mit den Rollen `moderation` und `qualitaet` im POS
(`api_rezension_freigeben()`, `api_rezension_ablehnen()`,
`api_qs_fall_erledigen()`); ablehnen kann nur ein Mensch. Die Rollen stehen in
`wawi.mitarbeiter_rolle` und hängen am Supabase-Konto. `stg_fact_reviews` und
damit `fact_reviews` nehmen nur freigegebene Rezensionen auf. `studi_daba`
liest wie `anon` nur freigegebene Texte und zusätzlich die Zählung
`v_freigabe_statistik`; die Prüf- und Entscheidungstabellen bleiben allen
außer `postgres` verschlossen. Das prüft die Probe am Ende von `0023`.
```

3. Im Absatz „**Was `anon` darf:**“ den Satzanfang „beide Schemata lesen und die beiden Schreibfunktionen“ ersetzen durch „beide Schemata lesen (in `wawi.rezension` nur freigegebene Zeilen, die Prüf- und Entscheidungstabellen aus `0023` gar nicht) und die beiden Schreibfunktionen“.

- [ ] **Step 8: `docs/02-datenmodell.md` nachziehen**

Den Satzteil „seit September 2026 auch `fact_reviews` (Kapitel 5.5).“ ersetzen durch „seit September 2026 auch `fact_reviews` (Kapitel 5.5); Shop-Rezensionen kommen dort erst nach ihrer Freigabe an (`db/README.md`, Abschnitt Rezensionen).“

- [ ] **Step 9: Suchlauf nach Geheimnissen, dann Commit**

Run: `git grep -n -I -E "(eyJ[A-Za-z0-9_-]{20,}\.|sk-[A-Za-z0-9]{20,}|PGPASSWORD=.|password=[^ '\"]{6,})" -- db web/tests docs | head`
Expected: keine Treffer. (Der öffentliche anon-Schlüssel steht nur in `web/js/konfiguration.js`, außerhalb der durchsuchten Pfade.)

```bash
git -c core.fileMode=false add web/tests/datenquelle_rezensionen.test.mjs db/README.md docs/02-datenmodell.md
git commit -m "Freigabe A: live eingespielt, Integrationstests und Doku" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 10: Push und PR**

```bash
git push origin bm-analyse
gh pr create --repo swrobuts/BurgerMetrics --base main --head bm-analyse \
  --title "Freigabe A: Status, Prüftabellen, Rollen und Sichten für Rezensionen" \
  --body "$(cat <<'EOF'
Phase A der Spezifikation docs/superpowers/specs/2026-09-30-rezensionen-jev-freigabe-design.md.

- Migration db/aufbau/0023_rezension_freigabe.sql, in der Produktion eingespielt (zweimal, wiederholbar)
- Öffentlich lesbar sind nur freigegebene Rezensionen, auch bei direktem Zugriff auf wawi.rezension
- Prüftabellen, Rolle bm_pruefdienst, Rollen moderation und qualitaet, Sichten für Shop, POS und Notebook
- 77 Tests auf einem lokalen Wegwerf-Cluster (db/tests/test_rezension_freigabe.py), Integrationstests gegen PostgREST grün

Neue Besuchertexte bleiben bis Phase D offen und unsichtbar, wie bisher.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Danach den PR mit `get_status` des Desktop-PR-Werkzeugs prüfen und, falls nicht gebunden, mit `bind_pr` binden. Robert um die Zusage zum Merge bitten; nicht selbst mergen.
