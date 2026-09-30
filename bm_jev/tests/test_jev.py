import json
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bm_jev import fragen, jev, testdaten, umgebung  # noqa: E402

TEXT = "GEHEIMER TEXT: Der Burger war heiß."


class Antwort:
    """Nachbau einer requests-Antwort."""
    def __init__(self, status_code, daten=None):
        self.status_code = status_code
        self._daten = daten

    def json(self):
        return self._daten


def gute_antwort(wert=0.1):
    """Eine vollständige Antwort der API mit derselben Wahrscheinlichkeit je Frage."""
    return {"model": "jev-1.13.0",
            "answers": {name: {"type": "noul", "noul": wert} for name in fragen.FRAGEN},
            "usage": {"input_tokens": 980, "output_tokens": 12}}


class Sender:
    """Zeichnet Aufrufe auf und liefert eine feste Antwort oder wirft einen Fehler."""
    def __init__(self, antwort=None, fehler=None):
        self.antwort, self.fehler, self.aufrufe = antwort, fehler, []

    def __call__(self, url, **kwargs):
        self.aufrufe.append((url, kwargs))
        if self.fehler:
            raise self.fehler
        return self.antwort


def test_anfrage_enthaelt_state_modell_und_fragen():
    koerper = jev.anfrage("Text", "Classic Burger")
    assert koerper["state"] == {"rezension": {"text": "Text", "produkt": "Classic Burger"}}
    assert koerper["model"] == "jev-1.13.0"
    assert list(koerper["questions"]) == list(fragen.FRAGEN)


def test_schluessel_folgt_text_modell_und_wortlaut(monkeypatch):
    basis = jev.schluessel(jev.anfrage("Text", "Cola 0.3l"))
    assert jev.schluessel(jev.anfrage("Text", "Cola 0.3l")) == basis
    assert jev.schluessel(jev.anfrage("Anderer Text", "Cola 0.3l")) != basis
    assert jev.schluessel(jev.anfrage("Text", "Cola 0.3l", "jev-1.14.0")) != basis
    monkeypatch.setitem(fragen.FRAGEN["werbung"], "instructions", "Anders: `rezension.text`?")
    assert jev.schluessel(jev.anfrage("Text", "Cola 0.3l")) != basis


def test_fragen_stellen_liest_wahrscheinlichkeiten_und_tokens():
    sender = Sender(Antwort(200, gute_antwort(0.25)))
    antwort = jev.fragen_stellen(TEXT, "Classic Burger", api_key="testschluessel", senden=sender)
    assert antwort.wahrscheinlichkeiten == {name: 0.25 for name in fragen.FRAGEN}
    assert (antwort.input_tokens, antwort.modell, antwort.aus_cache) == (980, "jev-1.13.0", False)
    url, kwargs = sender.aufrufe[0]
    assert url == "https://api.typesafe.ai/v1/systemone"
    assert kwargs["headers"]["Authorization"] == "Bearer testschluessel"
    assert kwargs["timeout"] == 20
    assert kwargs["json"]["state"]["rezension"]["text"] == TEXT


@pytest.mark.parametrize("sender, meldung", [
    (Sender(Antwort(529)), "HTTP 529"),
    (Sender(Antwort(401)), "HTTP 401"),
    (Sender(fehler=requests.ConnectionError("weg")), "keine Verbindung: ConnectionError"),
    (Sender(fehler=requests.Timeout("zu langsam")), "keine Verbindung: Timeout"),
])
def test_fehlermeldung_ohne_rezensionstext(sender, meldung):
    with pytest.raises(jev.JevFehler) as fehler:
        jev.fragen_stellen(TEXT, "Classic Burger", api_key="testschluessel", senden=sender)
    assert str(fehler.value) == meldung
    assert "GEHEIM" not in str(fehler.value)


def test_unvollstaendige_antwort_wird_jevfehler():
    daten = gute_antwort()
    del daten["answers"]["gesundheitsrisiko"]
    with pytest.raises(jev.JevFehler, match="Antwort unvollständig"):
        jev.fragen_stellen(TEXT, "Classic Burger", api_key="k", senden=Sender(Antwort(200, daten)))


class KeinJson(Antwort):
    """HTTP 200, aber der Körper ist kein JSON, etwa eine HTML-Fehlerseite."""
    def json(self):
        raise requests.exceptions.JSONDecodeError("Expecting value", "<html>", 0)


def test_antwort_ohne_json_wird_jevfehler():
    with pytest.raises(jev.JevFehler, match="Antwort kein JSON"):
        jev.fragen_stellen(TEXT, "Classic Burger", api_key="k", senden=Sender(KeinJson(200)))


@pytest.mark.parametrize("wert", [float("nan"), float("inf"), -0.1, 1.2, True, "0.5", None])
def test_keine_wahrscheinlichkeit_wird_jevfehler(wert):
    with pytest.raises(jev.JevFehler, match="Antwort unvollständig"):
        jev.fragen_stellen(TEXT, "Classic Burger", api_key="k", senden=Sender(Antwort(200, gute_antwort(wert))))


@pytest.mark.parametrize("usage, tokens", [
    (None, None), ({}, None), ({"input_tokens": 980.0}, 980), ({"input_tokens": "viele"}, None),
    (["980"], None),
])
def test_tokens_als_ganze_zahl_oder_none(usage, tokens):
    daten = gute_antwort()
    daten["usage"] = usage
    antwort = jev.fragen_stellen(TEXT, "Classic Burger", api_key="k", senden=Sender(Antwort(200, daten)))
    assert (antwort.input_tokens, type(antwort.input_tokens)) == (tokens, type(tokens))


def test_anfrage_nimmt_den_gewaehlten_stand():
    assert jev.anfrage("Text", "Cola 0.3l")["questions"] is fragen.FRAGEN
    assert jev.anfrage("Text", "Cola 0.3l", fragen=fragen.FRAGEN_STAND_1)["questions"] is fragen.FRAGEN_STAND_1


def test_fragen_stellen_schickt_den_gewaehlten_stand():
    sender = Sender(Antwort(200, gute_antwort()))
    jev.fragen_stellen(TEXT, "Donut", api_key="k", senden=sender, fragen=fragen.FRAGEN_STAND_1)
    assert sender.aufrufe[0][1]["json"]["questions"] is fragen.FRAGEN_STAND_1


def test_frueherer_stand_bleibt_im_cache_erreichbar():
    zeile = testdaten.lesen(testdaten.DATEIEN["testfaelle"])[0]
    cache = jev.Cache(testdaten.WURZEL / "dataset" / "cache" / "moderation_jev.jsonl")
    antwort = jev.beurteilen(zeile["text"], zeile["produkt"], cache=cache, fragen=fragen.FRAGEN_STAND_1)
    assert antwort.aus_cache and set(antwort.wahrscheinlichkeiten) == set(fragen.FRAGEN)


def test_beurteilen_fragt_einmal_und_liest_danach_den_cache(tmp_path):
    datei = tmp_path / "cache.jsonl"
    sender = Sender(Antwort(200, gute_antwort(0.3)))
    erste = jev.beurteilen(TEXT, "Cola 0.3l", cache=jev.Cache(datei), api_key="k", senden=sender)
    zweite = jev.beurteilen(TEXT, "Cola 0.3l", cache=jev.Cache(datei), api_key=None, senden=sender)
    assert len(sender.aufrufe) == 1
    assert zweite.aus_cache and zweite.wahrscheinlichkeiten == erste.wahrscheinlichkeiten
    zeilen = datei.read_text(encoding="utf-8").splitlines()
    assert len(zeilen) == 1 and "GEHEIM" not in zeilen[0]
    assert set(json.loads(zeilen[0])) == {"schluessel", "antwort"}


def test_ohne_schluessel_und_ohne_cache_keine_anfrage(tmp_path):
    sender = Sender(Antwort(200, gute_antwort()))
    with pytest.raises(jev.KeinCacheTreffer):
        jev.beurteilen(TEXT, "Cola 0.3l", cache=jev.Cache(tmp_path / "leer.jsonl"), senden=sender)
    assert sender.aufrufe == []


def test_api_schluessel_aus_der_umgebung(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "  abc  ")
    assert jev.api_schluessel() == "abc"
    monkeypatch.setenv("TYPESAFE_API_KEY", "")
    assert jev.api_schluessel() is None


def test_env_laden_ueberschreibt_nichts(tmp_path, monkeypatch):
    datei = tmp_path / ".env"
    datei.write_text("# Kommentar\nBM_TEST_A=eins\nBM_TEST_B = zwei\n", encoding="utf-8")
    monkeypatch.setenv("BM_TEST_A", "vorher")
    monkeypatch.delenv("BM_TEST_B", raising=False)
    umgebung.env_laden(datei)
    assert (umgebung.os.environ["BM_TEST_A"], umgebung.os.environ["BM_TEST_B"]) == ("vorher", "zwei")
