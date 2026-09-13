"""Prüft die Datenfunktionen der Dash-App gegen die Datenbank und den Aufbau der App."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import app  # noqa: E402


def test_kennzahlen_vier_kacheln():
    kacheln = app.lade_kennzahlen()
    assert list(kacheln) == ["Umsatz 2025", "Bestellungen 2025", "Ø Bestellwert 2025", "Zufriedenheit 2025"]
    assert kacheln["Bestellungen 2025"] == "136.557"
    assert kacheln["Zufriedenheit 2025"].startswith("3,8")


def test_umsatz_monat_ohne_und_mit_filiale():
    alle = app.lade_umsatz_monat(None)
    eine = app.lade_umsatz_monat(1)
    assert list(alle.columns) == ["monat", "umsatz"] and list(eine.columns) == ["monat", "umsatz"]
    assert alle["monat"].iloc[0] == "2017-03" and alle["monat"].iloc[-1] == "2026-03"
    assert len(alle) == 109 and len(eine) == 109
    assert eine["umsatz"].sum() < alle["umsatz"].sum()


def test_filialen_und_kanaele():
    filialen = app.lade_filialen()
    assert len(filialen) == 8 and filialen["branch_id"].iloc[0] == 1
    kanaele = app.lade_kanaele()
    assert set(kanaele["kanal"]) == {"App Order", "Counter", "Drive-Through", "Kiosk"}
    assert abs(kanaele[kanaele["jahr"] == 2025]["anteil_pct"].sum() - 100) < 0.5


def test_rezensionen_je_produkt():
    daten = app.lade_rezensionen()
    assert len(daten) >= 50 and daten["anzahl"].sum() == 10000
    assert daten["sterne_mittel"].between(1, 5).all()


def test_app_hat_vier_karten():
    dash_app = app.baue_app()
    ids = [k.id for k in dash_app.layout.children if getattr(k, "id", None)]
    assert ids == ["kacheln", "karte-umsatz", "karte-kanaele", "karte-rezensionen"]
    assert "linie-umsatz.figure" in dash_app.callback_map
