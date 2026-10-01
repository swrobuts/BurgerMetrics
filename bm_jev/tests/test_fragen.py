import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bm_jev import fragen  # noqa: E402

SCHLUESSEL = ["beleidigung", "personenbezug", "werbung", "themenbezug", "anweisung", "gesundheitsrisiko"]


def test_sechs_noul_fragen_mit_kriterien():
    assert list(fragen.FRAGEN) == SCHLUESSEL
    for frage in fragen.FRAGEN.values():
        assert frage["type"] == "noul"
        assert "`rezension.text`" in frage["instructions"]
        assert frage["criteria"]["true"] and frage["criteria"]["false"]


def test_fingerabdruck_folgt_dem_wortlaut(monkeypatch):
    vorher = fragen.fingerabdruck()
    assert len(vorher) == 10 and int(vorher, 16) >= 0
    assert fragen.fingerabdruck() == vorher
    monkeypatch.setitem(fragen.FRAGEN["werbung"], "instructions", "Anders gefragt: `rezension.text`?")
    assert fragen.fingerabdruck() != vorher


def test_stand_und_fingerabdruck_gehoeren_zusammen():
    """Ändert sich ein Wort, müssen Stand und erwarteter Fingerabdruck bewusst mitgehen."""
    assert (fragen.FRAGEN_STAND, fragen.fingerabdruck()) == ("2", "430ea6f880")
    assert fragen.fingerabdruck(fragen.FRAGEN_STAND_1) == "6a79d0f916"


def test_stand_1_unterscheidet_sich_nur_im_themenbezug():
    assert list(fragen.FRAGEN_STAND_1) == SCHLUESSEL
    anders = [k for k in SCHLUESSEL if fragen.FRAGEN[k] != fragen.FRAGEN_STAND_1[k]]
    assert anders == ["themenbezug"]


def test_themenbezug_nennt_shop_und_produkt():
    anweisung = fragen.FRAGEN["themenbezug"]["instructions"]
    assert "`rezension.produkt`" in anweisung and "Shop von BurgerMetrics" in anweisung

