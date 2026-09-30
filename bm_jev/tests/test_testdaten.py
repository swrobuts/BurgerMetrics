import csv
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bm_jev import muster, testdaten  # noqa: E402

GRUPPEN = {
    "testfaelle": {"lob": 12, "kritik": 14, "beleidigung": 6, "personenbezug": 6, "werbung": 5,
                   "kontakt": 6, "themenfremd": 6, "anweisung": 5, "gesundheit": 10, "grenzfall": 6,
                   "kombination": 4},
    "holdout": {"lob": 3, "kritik": 4, "beleidigung": 2, "personenbezug": 2, "werbung": 2, "kontakt": 2,
                "themenfremd": 2, "anweisung": 2, "gesundheit": 3, "grenzfall": 2},
    "stichprobe": {f"simulation_{n}": 100 for n in range(1, 6)},
}
PRAEFIX = {"testfaelle": "T", "holdout": "H", "stichprobe": "S"}


def produkte():
    """Die Artikelnamen aus dim_product.csv."""
    with (testdaten.WURZEL / "dataset" / "dim_product.csv").open(encoding="utf-8-sig", newline="") as f:
        return {z["product_name"] for z in csv.DictReader(f)}


@pytest.fixture(scope="module", params=list(testdaten.DATEIEN))
def datei(request):
    """Name und Zeilen einer der drei Testdateien."""
    return request.param, testdaten.lesen(testdaten.DATEIEN[request.param])


def test_spalten_und_kennungen(datei):
    name, zeilen = datei
    with testdaten.DATEIEN[name].open(encoding="utf-8", newline="") as f:
        assert next(csv.reader(f)) == testdaten.SPALTEN
    kennungen = [z["fall_id"] for z in zeilen]
    assert len(set(kennungen)) == len(kennungen)
    assert all(k.startswith(PRAEFIX[name]) for k in kennungen)


def test_gruppen_wie_vorgesehen(datei):
    name, zeilen = datei
    assert Counter(z["gruppe"] for z in zeilen) == GRUPPEN[name]


def test_texte_und_produkte(datei):
    _, zeilen = datei
    namen = produkte()
    for z in zeilen:
        text = " ".join(z["text"].split())
        assert 5 <= len(text) <= 500, z["fall_id"]
        assert "\n" not in z["text"], z["fall_id"]
        assert z["produkt"] in namen, z["fall_id"]


def test_soll_werte_sind_null_oder_eins(datei):
    _, zeilen = datei
    for z in zeilen:
        for frage in testdaten.FRAGEN:
            assert z[f"soll_{frage}"] in (0, 1), z["fall_id"]
        assert z["soll_qs_fall"] == z["soll_gesundheitsrisiko"], z["fall_id"]


def test_soll_muster_wie_die_regulaeren_ausdruecke(datei):
    _, zeilen = datei
    for z in zeilen:
        assert muster.treffer(z["text"]) == z["soll_muster"], z["fall_id"]


def test_soll_entscheidung_folgt_aus_den_soll_werten(datei):
    _, zeilen = datei
    for z in zeilen:
        assert testdaten.entscheidung_aus_soll(z).ergebnis == z["soll_entscheidung"], z["fall_id"]


def test_holdout_teilt_keinen_text_mit_den_testfaellen():
    testfaelle = {z["text"] for z in testdaten.lesen(testdaten.DATEIEN["testfaelle"])}
    assert not testfaelle & {z["text"] for z in testdaten.lesen(testdaten.DATEIEN["holdout"])}


def test_stichprobe_ist_harmlos_markiert():
    for z in testdaten.lesen(testdaten.DATEIEN["stichprobe"]):
        assert (z["soll_entscheidung"], z["soll_qs_fall"], z["soll_muster"]) == ("freigegeben", 0, [])
