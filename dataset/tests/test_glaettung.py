# dataset/tests/test_glaettung.py
import sys
from pathlib import Path

import pandas as pd

BASIS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASIS / "glaettung"))
import zusammenfuehren as z  # noqa: E402
import lose_schreiben as l  # noqa: E402


def roh_beispiel():
    return pd.DataFrame({
        "review_id": [1, 2, 3], "date": ["2025-01-01"] * 3, "time": ["12:00:00"] * 3,
        "customer_id": [5, 6, 7], "product_id": [1, 2, 3], "branch_id": [1, 1, 2], "order_id": [10, 11, 12],
        "stars": [5, 1, 3],
        "review_text": ["Rundum zufrieden, das passt. Der Classic Burger war saftig, gut belegt und heiß.",
                        "Das war leider ein Reinfall. Der Cheeseburger war trocken und lauwarm.",
                        "Ganz in Ordnung, mehr aber auch nicht. Die Small Fries waren okay, nicht mehr."],
        "source": ["simulation"] * 3})


def test_pruefe_text_gut():
    assert z.pruefe_text("Der Burger war gut und heiß.", "Der Burger kam heiß und schmeckte gut.") == []


def test_pruefe_text_befunde():
    alt = "Der Burger war gut und heiß."
    assert any("Zeilenumbruch" in b for b in z.pruefe_text(alt, "Der Burger\nwar gut."))
    assert any("zu lang" in b for b in z.pruefe_text(alt, alt + " " + "Und noch ein sehr langer Zusatz. " * 3))
    assert any("zu kurz" in b for b in z.pruefe_text(alt, "Gut."))
    assert any("leer" in b for b in z.pruefe_text(alt, "   "))


def test_zusammenfuehren_ersetzt_und_meldet():
    roh = roh_beispiel()
    geglaettet = pd.DataFrame({"review_id": [1, 2, 99],
                               "review_text": ["Rundum zufrieden. Der Classic Burger kam saftig, gut belegt und heiß an den Tisch.",
                                               "Ein Reinfall: Der Cheeseburger war trocken und nur lauwarm.",
                                               "Unbekannte Kennung."]})
    ergebnis, befunde = z.zusammenfuehren(roh, geglaettet)
    assert ergebnis.loc[ergebnis.review_id == 1, "review_text"].item().startswith("Rundum zufrieden. Der Classic")
    assert ergebnis.loc[ergebnis.review_id == 3, "review_text"].item() == roh.loc[2, "review_text"]
    assert list(ergebnis.columns) == list(roh.columns)
    assert any("99" in b for b in befunde)
    assert any("3" in b and "roh" in b for b in befunde)


def test_zusammenfuehren_behaelt_sterne_und_reihenfolge():
    roh = roh_beispiel()
    geglaettet = pd.DataFrame({"review_id": [2], "review_text": ["Leider ein Reinfall, der Cheeseburger war trocken und lauwarm."]})
    ergebnis, _ = z.zusammenfuehren(roh, geglaettet)
    assert list(ergebnis.stars) == [5, 1, 3]
    assert list(ergebnis.review_id) == [1, 2, 3]


def test_lose_schreiben(tmp_path):
    roh = pd.concat([roh_beispiel()] * 70, ignore_index=True)
    roh["review_id"] = range(1, len(roh) + 1)
    dateien = l.lose_schreiben(roh, tmp_path, groesse=100)
    assert len(dateien) == 3
    erstes = pd.read_csv(dateien[0], encoding="utf-8")
    assert list(erstes.columns) == ["review_id", "stars", "review_text"]
    assert len(erstes) == 100 and len(pd.read_csv(dateien[-1], encoding="utf-8")) == 10
