import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bm_jev.regeln import REGEL_VERSION, SCHWELLEN, entscheiden  # noqa: E402

HARMLOS = {"beleidigung": 0.01, "personenbezug": 0.01, "werbung": 0.01,
           "themenbezug": 0.95, "anweisung": 0.01, "gesundheitsrisiko": 0.01}


def p(**aenderung):
    """Harmlose Wahrscheinlichkeiten mit einzelnen Änderungen."""
    return {**HARMLOS, **aenderung}


def test_harmlos_wird_freigegeben():
    e = entscheiden(p(), [])
    assert (e.ergebnis, e.gruende, e.qs_fall) == ("freigegeben", [], False)


def test_muster_haelt_zurueck():
    e = entscheiden(p(), ["Link"])
    assert (e.ergebnis, e.gruende) == ("zurueckgehalten", ["Kontaktdaten oder Link"])


def test_gesundheitsrisiko_ab_der_schwelle():
    s = SCHWELLEN["gesundheitsrisiko"]
    assert entscheiden(p(gesundheitsrisiko=s - 0.01), []).qs_fall is False
    e = entscheiden(p(gesundheitsrisiko=s), [])
    assert (e.ergebnis, e.gruende, e.qs_fall) == ("zurueckgehalten", ["Gesundheitsrisiko"], True)


@pytest.mark.parametrize("frage, grund", [("beleidigung", "Beleidigung"), ("personenbezug", "Personenbezug"),
                                          ("werbung", "Werbung"), ("anweisung", "Anweisung")])
def test_verstoss_ab_der_schwelle(frage, grund):
    assert entscheiden(p(**{frage: SCHWELLEN["verstoss"]}), []).gruende == [grund]


def test_unsicher_zwischen_den_schwellen():
    u, v = SCHWELLEN["unsicher"], SCHWELLEN["verstoss"]
    assert entscheiden(p(werbung=u - 0.01), []).gruende == []
    assert entscheiden(p(werbung=u), []).gruende == ["unsicher"]
    assert entscheiden(p(werbung=v - 0.01), []).gruende == ["unsicher"]


def test_themenbezug_unter_der_schwelle_ist_unsicher():
    t = SCHWELLEN["themenbezug"]
    assert entscheiden(p(themenbezug=t), []).gruende == []
    assert entscheiden(p(themenbezug=t - 0.01), []).gruende == ["unsicher"]


def test_alle_gruende_in_fester_reihenfolge():
    e = entscheiden(p(gesundheitsrisiko=0.9, beleidigung=0.9, werbung=0.3), ["E-Mail"])
    assert e.gruende == ["Kontaktdaten oder Link", "Gesundheitsrisiko", "Beleidigung", "unsicher"]
    assert e.qs_fall is True


def test_eigene_schwellen():
    eigene = {**SCHWELLEN, "gesundheitsrisiko": 0.25}
    assert entscheiden(p(gesundheitsrisiko=0.3), [], eigene).qs_fall is True


def test_regel_version_traegt_ein_datum():
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}\.\d+", REGEL_VERSION)
