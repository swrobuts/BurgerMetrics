import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bm_jev import muster  # noqa: E402


@pytest.mark.parametrize("text, erwartet", [
    ("Schreib mir: max@example.de", ["E-Mail"]),
    ("Ruf an: 0931 123456", ["Telefonnummer"]),
    ("Handy +49 171 2345678, abends", ["Telefonnummer"]),
    ("Nummer 0171-2345678", ["Telefonnummer"]),
    ("Festnetz 0931/123456", ["Telefonnummer"]),
    ("Alles auf www.example.com", ["Link"]),
    ("Siehe https://example.org/essen", ["Link"]),
    ("Mehr auf burgerblog.de", ["Link"]),
    ("Mail an a.b@example.org und Infos auf www.example.com", ["E-Mail", "Link"]),
    ("Ruf an: (0931) 123456", ["Telefonnummer"]),
    ("Handy +49 (0)171 2345678", ["Telefonnummer"]),
    ("Tel. 0931.123456", ["Telefonnummer"]),
    ("Aus Wien: +43 660 1234567", ["Telefonnummer"]),
    ("Bestellt über shop.frittenfritz.de", ["Link"]),
    ("Mehr auf blog.burgerfan.de/beste", ["Link"]),
    ("Folgt uns: m.facebook.com/burgerfan", ["Link"]),
    ("Besser: burgerblog.at", ["Link"]),
    ("Auch auf burgerblog.ch und burgerblog.eu", ["Link"]),
    ("Kurz: bit.ly/3abc", ["Link"]),
    ("Kanal t.me/burgerfan", ["Link"]),
])
def test_treffer(text, erwartet):
    assert muster.treffer(text) == erwartet


@pytest.mark.parametrize("text", [
    "Kostet 3,50 Euro und war kalt.",
    "Wir kamen um 12:30 an und warteten 20 Minuten.",
    "Bestellung 4711 kam vollständig.",
    "Mit Käse, z.B. Cheddar, wäre es besser.",
    "Die Filiale Sanderring. Die Pommes waren gut.",
    "Seit 2026 gibt es 0,5l Cola.",
    "Am 01.10.2026 um 12.30 Uhr bestellt.",
    "Um 09.30 Uhr war es voll, Preis 0.99 und 0.49 Euro.",
    "Filiale in 01067 Dresden.",
    "",
])
def test_keine_falschen_treffer(text):
    assert muster.treffer(text) == []


def test_e_mail_ist_kein_zusaetzlicher_link():
    assert muster.treffer("Kontakt: julia.berger@example.de") == ["E-Mail"]
    assert muster.treffer(None) == []


@pytest.mark.parametrize("text, erwartet", [
    ("Bestellnummer 0815 4711", ["Telefonnummer"]),
    ("Die Pommes waren kalt.Info an die Filiale", ["Link"]),
])
def test_bekannte_fehlalarme(text, erwartet):
    """Bewusst hingenommen: Die Rezension wartet auf einen Menschen, veröffentlicht wird nichts Falsches."""
    assert muster.treffer(text) == erwartet


def test_keine_treffer_in_den_simulierten_rezensionen():
    import csv
    datei = Path(__file__).resolve().parents[2] / "dataset" / "fact_reviews.csv"
    with datei.open(encoding="utf-8-sig", newline="") as f:
        texte = [z["review_text"] for z in csv.DictReader(f)]
    assert len(texte) == 10000
    assert [t for t in texte if muster.treffer(t)] == []
