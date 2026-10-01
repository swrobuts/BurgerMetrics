import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bm_jev import auswertung  # noqa: E402
from bm_jev.regeln import SCHWELLEN, Entscheidung  # noqa: E402

HARMLOS = {"beleidigung": 0.01, "personenbezug": 0.01, "werbung": 0.01,
           "themenbezug": 0.95, "anweisung": 0.01, "gesundheitsrisiko": 0.01}


def fall(soll_entscheidung="freigegeben", soll_qs=0, muster=(), **p):
    """Eine Testzeile mit Soll-Werten und Wahrscheinlichkeiten."""
    zeile = {"fall_id": "T", "soll_entscheidung": soll_entscheidung, "soll_qs_fall": soll_qs,
             "muster": list(muster), "p": {**HARMLOS, **p}}
    for frage in HARMLOS:
        zeile[f"soll_{frage}"] = 1 if frage == "themenbezug" else 0
    zeile["soll_gesundheitsrisiko"] = soll_qs
    return zeile


@pytest.mark.parametrize("zeile, entscheidung, art", [
    (fall("zurueckgehalten", 1), Entscheidung("zurueckgehalten", ["unsicher"], False), "gesundheitsrisiko_verpasst"),
    (fall("zurueckgehalten"), Entscheidung("freigegeben", [], False), "problem_veroeffentlicht"),
    (fall("freigegeben"), Entscheidung("zurueckgehalten", ["unsicher"], False), "unnoetig_zurueckgehalten"),
    (fall("zurueckgehalten"), Entscheidung("zurueckgehalten", ["Gesundheitsrisiko"], True), "unnoetiger_qs_fall"),
    (fall("freigegeben"), Entscheidung("freigegeben", [], False), None),
])
def test_fehlerart(zeile, entscheidung, art):
    assert auswertung.fehlerart(zeile, entscheidung) == art


def test_bewerten_und_kosten():
    zeilen = [fall(), fall("zurueckgehalten", 1, gesundheitsrisiko=0.1), fall("freigegeben", werbung=0.3)]
    bewertet = auswertung.bewerten(zeilen)
    assert [z["fehler"] for z in bewertet] == [None, "gesundheitsrisiko_verpasst", "unnoetig_zurueckgehalten"]
    assert bewertet[2]["ist_gruende"] == ["unsicher"]
    assert auswertung.kosten(bewertet) == 501


def test_zaehlen_recall_und_praezision():
    k = auswertung.zaehlen([(True, True), (True, False), (False, True), (False, False), (False, False)])
    assert k == {"tp": 1, "fp": 1, "fn": 1, "tn": 2}
    assert auswertung.recall(k) == 0.5 and auswertung.praezision(k) == 0.5
    assert auswertung.recall({"tp": 0, "fp": 0, "fn": 0, "tn": 3}) is None


def test_konfusion_einer_frage_und_der_entscheidung():
    bewertet = auswertung.bewerten([fall("zurueckgehalten", 1, gesundheitsrisiko=0.9), fall()])
    assert auswertung.konfusion(bewertet, "gesundheitsrisiko", 0.4) == {"tp": 1, "fp": 0, "fn": 0, "tn": 1}
    assert auswertung.konfusion_entscheidung(bewertet) == {"tp": 1, "fp": 0, "fn": 0, "tn": 1}
    assert auswertung.konfusion_qs(bewertet) == {"tp": 1, "fp": 0, "fn": 0, "tn": 1}


def test_schwelle_fuer():
    assert auswertung.schwelle_fuer("gesundheitsrisiko") == SCHWELLEN["gesundheitsrisiko"]
    assert auswertung.schwelle_fuer("themenbezug") == SCHWELLEN["themenbezug"]
    assert auswertung.schwelle_fuer("werbung") == SCHWELLEN["verstoss"]


def test_gitter():
    kombinationen = auswertung.gitter()
    assert len(kombinationen) == 144
    assert all(k["unsicher"] < k["verstoss"] for k in kombinationen)
    assert auswertung.gitter((0.4,), (0.4,), (0.3, 0.5), (0.8,)) == [
        {"gesundheitsrisiko": 0.4, "verstoss": 0.4, "unsicher": 0.3, "themenbezug": 0.8}]


def test_schwellen_durchspielen_guenstigste_zuerst():
    zeilen = [fall("zurueckgehalten", 1, gesundheitsrisiko=0.35), fall()]
    ergebnisse = auswertung.schwellen_durchspielen(zeilen, auswertung.gitter())
    assert ergebnisse[0]["kosten"] == 0 and ergebnisse[0]["gesundheitsrisiko"] <= 0.3
    assert ergebnisse[-1]["kosten"] >= 500
    assert set(auswertung.KOSTEN) <= set(ergebnisse[0])
