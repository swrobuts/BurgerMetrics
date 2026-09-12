import difflib
import json
import re
from pathlib import Path

import pytest

BASIS = Path(__file__).resolve().parent.parent
EMOJI = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")


@pytest.fixture(scope="module")
def bausteine():
    return json.loads((BASIS / "rezension_bausteine.json").read_text(encoding="utf-8"))


def alle_saetze(knoten):
    """Sammelt jede Zeichenkette aus dem verschachtelten JSON ein."""
    if isinstance(knoten, str):
        return [knoten]
    if isinstance(knoten, list):
        return [s for k in knoten for s in alle_saetze(k)]
    return [s for k in knoten.values() for s in alle_saetze(k)]


def test_mindestzahlen(bausteine):
    for stufe in "12345":
        assert len(bausteine["einstieg"][stufe]) >= 25
        assert len(bausteine["schluss"][stufe]) >= 15
    for kategorie in ["Burger", "Side", "Drink", "Dessert", "Breakfast"]:
        for polaritaet in ["negativ", "neutral", "positiv"]:
            assert len(bausteine["produkt"][kategorie][polaritaet]) >= 20, (kategorie, polaritaet)
    w = bausteine["kontext"]["wartezeit"]
    assert len(w["kurz"]) >= 12 and len(w["mittel"]) >= 12
    assert len(w["lang"]["negativ"]) >= 12 and len(w["lang"]["positiv"]) >= 12
    for kanal in ["Counter", "Drive-Through", "Kiosk", "App Order"]:
        assert len(bausteine["kontext"]["kanal"][kanal]) >= 8
    assert len(bausteine["kontext"]["filiale"]) >= 10
    for schluessel in ["mit_aktion", "negativ", "neutral", "positiv"]:
        assert len(bausteine["kontext"]["preis"][schluessel]) >= 8


def test_platzhalter(bausteine):
    for kategorie, polaritaeten in bausteine["produkt"].items():
        for saetze in polaritaeten.values():
            assert all("{produkt}" in s for s in saetze), kategorie
    assert all("{filiale}" in s for s in bausteine["kontext"]["filiale"])


def test_form(bausteine):
    for satz in alle_saetze(bausteine):
        assert "\n" not in satz
        assert not EMOJI.search(satz), satz
        assert satz.strip() == satz
        assert satz[-1] in ".!?", satz
        assert 8 <= len(satz) <= 160, satz


def test_keine_doppelten(bausteine):
    saetze = alle_saetze(bausteine)
    assert len(saetze) == len(set(saetze))


def normalisiert(satz):
    """Platzhalter, Satzzeichen und Großschreibung ausblenden, damit nur der Wortlaut zählt."""
    satz = satz.replace("{produkt}", "").replace("{filiale}", "").lower()
    return re.sub(r"[^a-zäöüß ]+", " ", satz).strip()


def test_keine_beinahe_doppelten(bausteine):
    saetze = [normalisiert(s) for s in alle_saetze(bausteine)]
    for i, a in enumerate(saetze):
        for b in saetze[i + 1:]:
            assert difflib.SequenceMatcher(None, a, b).ratio() < 0.85, (a, b)
