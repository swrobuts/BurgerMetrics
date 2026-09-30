"""Der Prüfdienst gegen die echte Migration 0023 auf dem lokalen Wegwerf-Cluster.

Meldet sich als bm_pruefdienst an, wie im Container; Jev wird nachgebildet.
Braucht BM_SECURITY_TEST_DSN und BM_SECURITY_TEST_CA (db/tests/security_local.sh).
"""
import os
import sys
import uuid
from pathlib import Path

import psycopg2
import pytest

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "pruefdienst"))
sys.path.insert(0, str(WURZEL / "db" / "tests"))
import dienst  # noqa: E402
from bm_jev import datenbank, jev  # noqa: E402
from freigabe_cluster import datenbank_aufbauen  # noqa: E402

# Nur für die Wegwerf-Instanz; sie verschwindet mit dem Container.
TESTPASSWORT = "lokal-pruefdienst-test"
HARMLOS = {"beleidigung": 0.01, "personenbezug": 0.01, "werbung": 0.01,
           "themenbezug": 0.95, "anweisung": 0.01, "gesundheitsrisiko": 0.01}


@pytest.fixture(scope="module")
def betreiber():
    """Superuser-Verbindung auf eine frisch aufgebaute Datenbank mit 0023."""
    dsn = os.environ.get("BM_SECURITY_TEST_DSN")
    if not dsn or not os.environ.get("BM_SECURITY_TEST_CA"):
        pytest.skip("lokale Wegwerf-Instanz nötig: bash db/tests/security_local.sh")
    con = datenbank_aufbauen(dsn, "bm_pruefdienst_test")
    with con.cursor() as cur:
        cur.execute(f"ALTER ROLE bm_pruefdienst PASSWORD '{TESTPASSWORT}'")
    con.commit()
    yield con
    con.close()


@pytest.fixture
def dienst_verbindung(betreiber):
    """Verbindung als bm_pruefdienst, wie der Container sie aufbaut."""
    p = betreiber.get_dsn_parameters()
    dsn = (f"host={p['host']} port={p['port']} dbname={p['dbname']} user=bm_pruefdienst "
           f"password={TESTPASSWORT} sslmode=verify-full sslrootcert={os.environ['BM_SECURITY_TEST_CA']}")
    con = datenbank.verbinden(dsn)
    yield con
    con.close()
    with betreiber.cursor() as cur:
        cur.execute("SELECT * FROM wawi.uebungsrezensionen_loeschen()")
    betreiber.commit()


def anlegen(betreiber, text):
    """Legt eine Shop-Rezension über rezension_anlegen() an und bestätigt sie."""
    with betreiber.cursor() as cur:
        cur.execute("SET ROLE anon")
        cur.execute("SELECT wawi.rezension_anlegen(1, 4, %s, NULL, %s)", (text, "d-" + uuid.uuid4().hex[:8]))
        rid = cur.fetchone()[0]["rezension_id"]
        cur.execute("RESET ROLE")
    betreiber.commit()
    return rid


def status(betreiber, rid):
    """Status einer Rezension, als postgres gelesen."""
    with betreiber.cursor() as cur:
        cur.execute("SELECT status FROM wawi.rezension WHERE rezension_id = %s", (rid,))
        wert = cur.fetchone()[0]
    betreiber.commit()
    return wert


def anfrage_mit(p=None, fehler=None):
    """Nachbau der Anfrage an Jev."""
    def anfrage(text, produkt):
        if fehler:
            raise fehler
        return jev.Antwort({**HARMLOS, **(p or {})}, 900, "jev-1.13.0")
    return anfrage


EINSTELLUNGEN = dienst.Einstellungen(stapel=20, intervall=0, tageslimit=300)


def test_eine_runde_gegen_die_datenbank(betreiber, dienst_verbindung):
    harmlos = anlegen(betreiber, "Der Burger war heiß und frisch.")
    kontakt = anlegen(betreiber, "Ruft mich an: 0931 4567890")
    assert dienst.eine_runde(dienst_verbindung, anfrage_mit(), EINSTELLUNGEN) == 2
    assert status(betreiber, harmlos) == "freigegeben"
    assert status(betreiber, kontakt) == "zurueckgehalten"
    assert datenbank.heute_angefragt(dienst_verbindung) == 2
    assert dienst.eine_runde(dienst_verbindung, anfrage_mit(), EINSTELLUNGEN) == 0


def test_gesundheitsrisiko_legt_qs_fall_an(betreiber, dienst_verbindung):
    rid = anlegen(betreiber, "Im Salat war ein Stück Plastik.")
    dienst.eine_runde(dienst_verbindung, anfrage_mit({"gesundheitsrisiko": 0.9}), EINSTELLUNGEN)
    with betreiber.cursor() as cur:
        cur.execute("SELECT count(*) FROM wawi_intern.qs_fall WHERE rezension_id = %s", (rid,))
        assert cur.fetchone()[0] == 1
    betreiber.commit()


def test_drei_fehlversuche_halten_zurueck(betreiber, dienst_verbindung):
    rid = anlegen(betreiber, "Der Kaffee war gut.")
    ausfall = anfrage_mit(fehler=jev.JevFehler("HTTP 529"))
    for runde in range(3):
        dienst.eine_runde(dienst_verbindung, ausfall, EINSTELLUNGEN)
        # Die Pause von fünf Minuten nach einem Fehler vorspulen
        with betreiber.cursor() as cur:
            cur.execute("""UPDATE wawi_intern.rezension_pruefung SET geprueft_am = geprueft_am - interval '6 minutes'
                           WHERE rezension_id = %s""", (rid,))
        betreiber.commit()
    assert status(betreiber, rid) == "zurueckgehalten"


def test_pruefdienst_sieht_keine_tabellen(dienst_verbindung):
    with dienst_verbindung.cursor() as cur:
        with pytest.raises(psycopg2.errors.InsufficientPrivilege):
            cur.execute("SELECT inhalt FROM wawi.rezension LIMIT 1")
    dienst_verbindung.rollback()
