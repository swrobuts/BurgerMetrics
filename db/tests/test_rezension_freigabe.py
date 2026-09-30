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
