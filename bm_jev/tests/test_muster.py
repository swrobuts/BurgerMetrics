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
    "",
])
def test_keine_falschen_treffer(text):
    assert muster.treffer(text) == []


def test_e_mail_ist_kein_zusaetzlicher_link():
    assert muster.treffer("Kontakt: julia.berger@example.de") == ["E-Mail"]
    assert muster.treffer(None) == []
