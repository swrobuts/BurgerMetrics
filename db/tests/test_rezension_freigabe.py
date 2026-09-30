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


def fehler(cur, sql, argumente=None):
    """Führt sql aus und liefert die Fehlerklasse oder None; die Transaktion bleibt benutzbar.

    Ohne Argumente None statt (): sonst ersetzt psycopg2 %-Platzhalter im SQL-Text.
    """
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


NEUE_TABELLEN = ["wawi_intern.rezension_pruefung", "wawi_intern.rezension_entscheidung",
                 "wawi_intern.qs_fall", "wawi_intern.mitarbeiter_rolle"]


def konto(cur, *rollen):
    """Legt als postgres ein Supabase-Konto mit Rollen an; es lebt nur bis zum Ende des Tests."""
    zurueck(cur)  # wird oft als Argument von als() ausgewertet, während noch eine andere Rolle gilt
    kennung = str(uuid.uuid4())
    cur.execute("INSERT INTO auth.users (id) VALUES (%s)", (kennung,))
    for rolle in rollen:
        cur.execute("INSERT INTO wawi_intern.mitarbeiter_rolle (konto, rolle) VALUES (%s, %s)", (kennung, rolle))
    return kennung


@pytest.mark.parametrize("rolle", ["anon", "authenticated", "studi_daba", "bm_pruefdienst"])
@pytest.mark.parametrize("tabelle", NEUE_TABELLEN)
def test_neue_tabellen_sind_verschlossen(db, rolle, tabelle):
    als(db, rolle)
    assert fehler(db, f"SELECT 1 FROM {tabelle} LIMIT 1") is psycopg2.errors.InsufficientPrivilege


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
    assert fehler(db, "INSERT INTO wawi_intern.mitarbeiter_rolle (konto, rolle) VALUES (%s, 'admin')", (kennung,)) \
        is psycopg2.errors.CheckViolation


def test_rollen_verschwinden_mit_dem_konto(db):
    kennung = konto(db, "moderation", "qualitaet")
    db.execute("DELETE FROM auth.users WHERE id = %s", (kennung,))
    db.execute("SELECT count(*) FROM wawi_intern.mitarbeiter_rolle WHERE konto = %s", (kennung,))
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
                  FROM wawi_intern.rezension_pruefung WHERE rezension_id = %s""", (rid,))
    assert db.fetchone() == (0.97, True, 1000, "jev-1.13.0")


def test_gesundheitsrisiko_legt_qs_fall_an(db):
    rid = shop_rezension(db, "Mir war nach dem Essen übel.")
    assert eintragen(db, rid, "zurueckgehalten", ["Gesundheitsrisiko"], qs=True)["status"] == "zurueckgehalten"
    db.execute("SELECT count(*) FROM wawi_intern.qs_fall WHERE rezension_id = %s AND erledigt_am IS NULL", (rid,))
    assert db.fetchone()[0] == 1
    db.execute("SELECT gruende, qs_fall FROM wawi_intern.rezension_pruefung WHERE rezension_id = %s", (rid,))
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
    db.execute("""SELECT ergebnis, gruende FROM wawi_intern.rezension_pruefung
                  WHERE rezension_id = %s ORDER BY pruefung_id DESC LIMIT 1""", (rid,))
    assert db.fetchone() == ("zurueckgehalten", ["Prüfung nicht möglich"])


def test_nach_einem_fehler_fuenf_minuten_pause(db):
    rid = shop_rezension(db)
    eintragen(db, rid, fehlertext="Zeitüberschreitung")
    als(db, "bm_pruefdienst")
    db.execute("SELECT count(*) FROM wawi.pruefung_offene_holen(10)")
    assert db.fetchone()[0] == 0
    zurueck(db)
    db.execute("""UPDATE wawi_intern.rezension_pruefung SET geprueft_am = geprueft_am - interval '6 minutes'
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
    db.execute("SELECT entscheidung, konto, bemerkung FROM wawi_intern.rezension_entscheidung WHERE rezension_id = %s", (rid,))
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
    db.execute("SELECT qs_fall_id FROM wawi_intern.qs_fall WHERE rezension_id = %s", (rid,))
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
    db.execute("SELECT count(*) FROM wawi_intern.rezension_entscheidung WHERE konto = %s", (kennung,))
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
    for tabelle in ("wawi_intern.rezension_pruefung", "wawi_intern.rezension_entscheidung", "wawi_intern.qs_fall"):
        db.execute(f"SELECT count(*) FROM {tabelle}")
        assert db.fetchone()[0] == 0, tabelle


INTERNE_TABELLEN = ["wawi_intern.rezension_pruefung", "wawi_intern.rezension_entscheidung",
                    "wawi_intern.qs_fall", "wawi_intern.mitarbeiter_rolle"]

EINTRAGEN = ("wawi.pruefung_eintragen(bigint, text, text[], boolean, jsonb, text[], boolean, "
             "text, text, text, text, integer, text)")

# Rechtefehler, die die Probe erkennen und freigabe_rechte() reparieren muss.
REGRESSIONEN = [
    f"GRANT EXECUTE ON FUNCTION {EINTRAGEN} TO anon",
    "GRANT EXECUTE ON FUNCTION wawi.api_rezension_ablehnen(bigint, text) TO anon",
    "GRANT EXECUTE ON FUNCTION wawi.api_qs_fall_erledigen(bigint, text) TO bm_pruefdienst",
    "GRANT EXECUTE ON FUNCTION wawi.hat_rolle(text) TO anon",
    "CREATE POLICY offen ON wawi_intern.qs_fall FOR SELECT USING (true)",
    "CREATE POLICY zweite ON wawi.rezension FOR SELECT USING (true)",
    "ALTER TABLE wawi_intern.mitarbeiter_rolle DISABLE ROW LEVEL SECURITY",
    "GRANT SELECT ON wawi.v_freigabe_statistik TO authenticated",
    "GRANT SELECT ON wawi.v_moderation TO anon",
    "GRANT UPDATE ON wawi.rezension TO anon",
    "GRANT TRUNCATE ON wawi_intern.qs_fall TO anon",
    "GRANT USAGE ON SCHEMA wawi_intern TO studi_daba",
    "GRANT SELECT ON wawi_intern.rezension_pruefung TO authenticated",
    "GRANT INSERT ON wawi.v_rezensionen_lesen TO anon",
    "REVOKE SELECT ON wawi.v_rezensionen_lesen FROM anon",
    "GRANT SELECT ON wawi.rezension TO bm_pruefdienst",
]


def test_erneuter_lauf_von_0018_und_0020_oeffnet_nichts(db):
    shop_rezension(db, "GEHEIM noch offen")
    zurueckgehalten(db, "GEHEIM zurückgehalten")
    for skript in ("0018_wawi_sichten_und_schreiben.sql", "0020_demo_rolle.sql"):
        db.execute((AUFBAU / skript).read_text())
    for rolle in ("anon", "authenticated", "studi_daba"):
        als(db, rolle)
        db.execute("SELECT count(*) FROM wawi.rezension WHERE inhalt LIKE 'GEHEIM%'")
        assert db.fetchone()[0] == 0, rolle
        for tabelle in INTERNE_TABELLEN:
            assert fehler(db, f"SELECT 1 FROM {tabelle} LIMIT 1") is psycopg2.errors.InsufficientPrivilege, \
                (rolle, tabelle)
    zurueck(db)
    assert fehler(db, "SELECT wawi.freigabe_pruefen()") is None


def test_studi_daba_liest_alle_lehrobjekte(db):
    # Dieselbe Bedingung wie am Ende von 0020 und von db/betrieb/studi_daba_lesend.sql.
    db.execute("""SELECT count(*), count(*) FILTER (WHERE has_table_privilege('studi_daba', c.oid, 'SELECT'))
                  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                  WHERE n.nspname IN ('burgermetrics', 'wawi') AND c.relkind IN ('r', 'p', 'v', 'm', 'f')""")
    alle, lesbar = db.fetchone()
    assert alle == lesbar


def test_moderationssichten_bleiben_fuer_studi_daba_zu(db):
    zurueckgehalten(db)
    als(db, "studi_daba")
    for sicht in ("wawi.v_moderation", "wawi.v_qs_faelle", "wawi.v_entscheidungen_letzte"):
        assert fehler(db, f"SELECT 1 FROM {sicht}") is psycopg2.errors.InsufficientPrivilege, sicht


def test_0021_bricht_nach_0023_ab(db):
    assert fehler(db, (AUFBAU / "0021_rezensionen.sql").read_text()) is psycopg2.errors.RaiseException


def test_bestandskopie_gibt_den_bestand_frei(db):
    db.execute("INSERT INTO burgermetrics.dim_date (date_id, date) VALUES (20260101, DATE '2026-01-01')")
    db.execute("INSERT INTO burgermetrics.dim_product (product_id, product_name, category) VALUES (1, 'Test', 'Burger')")
    db.execute("""INSERT INTO burgermetrics.fact_reviews (review_id, date, time, product_id, stars, review_text, source)
                  VALUES (900001, DATE '2026-01-01', TIME '12:00', 1, 5, 'Simuliert und kuratiert', 'simulation')""")
    db.execute((AUFBAU.parent / "betrieb" / "rezensionen_bestand_kopieren.sql").read_text())
    db.execute("SELECT status, quelle, inhalt FROM wawi.rezension WHERE rezension_id = 900001")
    assert db.fetchone() == ("freigegeben", "simulation", "Simuliert und kuratiert")


def test_probe_im_sauberen_stand(db):
    assert fehler(db, "SELECT wawi.freigabe_pruefen()") is None


@pytest.mark.parametrize("regression", REGRESSIONEN)
def test_probe_erkennt_jede_regression(db, regression):
    db.execute(regression)
    assert fehler(db, "SELECT wawi.freigabe_pruefen()") is psycopg2.errors.RaiseException


@pytest.mark.parametrize("regression", REGRESSIONEN)
def test_freigabe_rechte_repariert_jede_regression(db, regression):
    db.execute(regression)
    db.execute("SELECT wawi.freigabe_rechte()")
    assert fehler(db, "SELECT wawi.freigabe_pruefen()") is None


@pytest.mark.parametrize("rolle", ["anon", "authenticated", "studi_daba", "bm_pruefdienst"])
def test_freigabe_funktionen_nur_fuer_postgres(db, rolle):
    als(db, rolle)
    assert fehler(db, "SELECT wawi.freigabe_rechte()") is psycopg2.errors.InsufficientPrivilege
    assert fehler(db, "SELECT wawi.freigabe_pruefen()") is psycopg2.errors.InsufficientPrivilege


def test_migration_wartet_hoechstens_fuenf_sekunden_auf_sperren(db):
    db.execute((AUFBAU / "0023_rezension_freigabe.sql").read_text())
    db.execute("SHOW lock_timeout")
    assert db.fetchone()[0] == "5s"


def test_betriebsskript_studi_daba_lesend_laeuft_nach_0023(db):
    # Das Skript läuft sonst nur in der Datenbank postgres; hier dieselben Schritte in bm_freigabe.
    skript = (AUFBAU.parent / "betrieb" / "studi_daba_lesend.sql").read_text()
    schutz = "IF current_database() <> 'postgres'"
    assert skript.count(schutz) == 1
    db.execute(skript.replace(schutz, "IF current_database() <> current_database()"))
    assert fehler(db, "SELECT wawi.freigabe_pruefen()") is None
