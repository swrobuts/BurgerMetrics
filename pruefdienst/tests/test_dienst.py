import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import psycopg2
import pytest

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "pruefdienst"))
import dienst  # noqa: E402
from bm_jev import jev  # noqa: E402

HARMLOS = {"beleidigung": 0.01, "personenbezug": 0.01, "werbung": 0.01,
           "themenbezug": 0.95, "anweisung": 0.01, "gesundheitsrisiko": 0.01}


@dataclass
class Rezension:
    """Wie bm_jev.datenbank.OffeneRezension."""
    rezension_id: int
    artikel: str
    inhalt: str


class Datenbank:
    """Nachbau von bm_jev.datenbank im Speicher."""
    def __init__(self, offene, angefragt=0, fehler=None):
        self.offene, self.angefragt, self.fehler = list(offene), angefragt, fehler
        self.eintraege = []

    def heute_angefragt(self, verbindung):
        if self.fehler:
            raise self.fehler
        return self.angefragt

    def offene_holen(self, verbindung, anzahl):
        return self.offene[:anzahl]

    def eintragen(self, verbindung, rezension_id, **felder):
        self.eintraege.append((rezension_id, felder))
        return {"rezension_id": rezension_id, "status": felder.get("ergebnis") or "offen",
                "uebersprungen": False}


def anfrage_mit(p=None, fehler=None):
    """Nachbau der Anfrage an Jev; zählt die Aufrufe."""
    def anfrage(text, produkt):
        anfrage.aufrufe.append((text, produkt))
        if fehler:
            raise fehler
        return jev.Antwort({**HARMLOS, **(p or {})}, 950, "jev-1.13.0")
    anfrage.aufrufe = []
    return anfrage


EINSTELLUNGEN = dienst.Einstellungen(stapel=20, intervall=30, tageslimit=300)


def test_harmlose_rezension_wird_freigegeben():
    db = Datenbank([Rezension(1, "Classic Burger", "Lecker und heiß.")])
    assert dienst.eine_runde(None, anfrage_mit(), EINSTELLUNGEN, db) == 1
    rezension_id, felder = db.eintraege[0]
    assert rezension_id == 1
    assert (felder["ergebnis"], felder["gruende"], felder["qs_fall"]) == ("freigegeben", [], False)
    assert felder["jev_angefragt"] is True and felder["input_tokens"] == 950
    assert felder["modell"] == "jev-1.13.0" and felder["regel_version"] and felder["fragen_fingerabdruck"]


def test_muster_haelt_zurueck_und_jev_wird_trotzdem_gefragt():
    anfrage = anfrage_mit()
    db = Datenbank([Rezension(2, "Cola 0.3l", "Ruft mich an: 0931 4567890")])
    dienst.eine_runde(None, anfrage, EINSTELLUNGEN, db)
    felder = db.eintraege[0][1]
    assert felder["gruende"] == ["Kontaktdaten oder Link"]
    assert felder["muster_treffer"] == ["Telefonnummer"]
    assert len(anfrage.aufrufe) == 1


def test_gesundheitsrisiko_legt_qs_fall_an():
    db = Datenbank([Rezension(3, "Chicken Burger", "Innen roh, mir war übel.")])
    dienst.eine_runde(None, anfrage_mit({"gesundheitsrisiko": 0.9}), EINSTELLUNGEN, db)
    felder = db.eintraege[0][1]
    assert (felder["ergebnis"], felder["qs_fall"]) == ("zurueckgehalten", True)


def test_fehler_von_jev_wird_eingetragen():
    db = Datenbank([Rezension(4, "Donut", "GEHEIM Donut war gut.")])
    dienst.eine_runde(None, anfrage_mit(fehler=jev.JevFehler("HTTP 529")), EINSTELLUNGEN, db)
    felder = db.eintraege[0][1]
    assert felder["fehler"] == "HTTP 529"
    assert "ergebnis" not in felder and felder["jev_angefragt"] is True


def test_tageslimit_mitten_im_stapel():
    anfrage = anfrage_mit()
    offene = [Rezension(i, "Coffee", f"Kaffee Nummer {i} war gut.") for i in (5, 6, 7)]
    db = Datenbank(offene, angefragt=299)
    dienst.eine_runde(None, anfrage, EINSTELLUNGEN, db)
    assert len(anfrage.aufrufe) == 1
    assert [f["gruende"] for _, f in db.eintraege[1:]] == [["Tageslimit erreicht"]] * 2
    assert [f["jev_angefragt"] for _, f in db.eintraege] == [True, False, False]


def test_stapel_begrenzt_die_runde():
    db = Datenbank([Rezension(i, "Coffee", "Guter Kaffee.") for i in range(25)])
    assert dienst.eine_runde(None, anfrage_mit(), EINSTELLUNGEN, db) == 20


def test_runde_nach_datenbankfehler():
    db = Datenbank([], fehler=psycopg2.OperationalError("weg"))
    with pytest.raises(psycopg2.OperationalError):
        dienst.eine_runde(None, anfrage_mit(), EINSTELLUNGEN, db)


def test_protokoll_ohne_text(caplog):
    caplog.set_level(logging.INFO, logger="bm-pruefdienst")
    db = Datenbank([Rezension(8, "Donut", "GEHEIM erster Text"), Rezension(9, "Donut", "GEHEIM zweiter Text")])
    dienst.eine_runde(None, anfrage_mit(), EINSTELLUNGEN, db)
    dienst.eine_runde(None, anfrage_mit(fehler=jev.JevFehler("HTTP 529")), EINSTELLUNGEN, db)
    assert "rezension=8 status=freigegeben" in caplog.text
    assert "fehler=HTTP 529" in caplog.text
    assert "GEHEIM" not in caplog.text


def test_einstellungen_lesen():
    assert dienst.einstellungen_lesen({}) == dienst.Einstellungen(20, 30, 300)
    eigene = {"BM_PRUEF_STAPEL": "5", "BM_PRUEF_INTERVALL": "10", "BM_JEV_TAGESLIMIT": "1"}
    assert dienst.einstellungen_lesen(eigene) == dienst.Einstellungen(5, 10, 1)


def test_warten_endet_bei_anhalten(monkeypatch):
    schlaefe = []
    monkeypatch.setattr(dienst.time, "sleep", lambda s: schlaefe.append(s))
    zustand = {"laufen": True}

    def weiter():
        if len(schlaefe) == 3:
            zustand["laufen"] = False
        return zustand["laufen"]
    dienst.warten(30, weiter)
    assert len(schlaefe) == 3


def test_ohne_schluessel_startet_der_dienst_nicht(monkeypatch, caplog):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://x@localhost/y")
    assert dienst.main() == 1
    assert "startet nicht" in caplog.text
