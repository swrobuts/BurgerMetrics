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
