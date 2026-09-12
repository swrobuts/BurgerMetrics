import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

BASIS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASIS))
import generate_reviews as g  # noqa: E402


@pytest.fixture(scope="module")
def kandidaten():
    return g.lade_kandidaten(BASIS)


@pytest.fixture(scope="module")
def bausteine():
    return json.loads((BASIS / "rezension_bausteine.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def probe(kandidaten, bausteine):
    return g.erzeuge_rezensionen(kandidaten, bausteine, anzahl=3000, seed=2026)


def test_kandidaten_sind_bewertete_bestellungen_ohne_extras(kandidaten):
    assert kandidaten.satisfaction_score.notna().all()
    assert (kandidaten.category != "Extra").all()
    assert len(kandidaten) > 500_000
    ohne_app_am_schalter = kandidaten[(kandidaten.order_channel == "Counter") & (kandidaten.has_app == False)]
    jahr = pd.to_datetime(ohne_app_am_schalter.date).dt.year
    erwartetes_gewicht = 1 + (jahr - 2017) / 3
    assert np.isclose(ohne_app_am_schalter.gewicht, erwartetes_gewicht).all()
    assert np.isclose(kandidaten.gewicht.min(), 1.0)
    assert np.isclose(kandidaten.gewicht.max(), 4 * 3 * 2)


def test_spalten_und_umfang(probe):
    assert list(probe.columns) == ["review_id", "date", "time", "customer_id", "product_id",
                                   "branch_id", "order_id", "stars", "review_text", "source"]
    assert len(probe) == 3000
    assert list(probe.review_id) == list(range(1, 3001))
    assert probe.order_id.is_unique
    assert (probe.source == "simulation").all()


def test_regeln_je_zeile(probe, kandidaten):
    assert probe.stars.between(1, 5).all()
    laengen = probe.review_text.str.len()
    assert laengen.between(5, 500).all()
    assert not probe.review_text.str.contains("\n").any()
    assert (probe.date <= "2026-03-31").all()
    bestelldatum = probe.merge(kandidaten[["order_id", "date"]].drop_duplicates("order_id"),
                               on="order_id", suffixes=("", "_bestellung"))
    assert (pd.to_datetime(bestelldatum.date) >= pd.to_datetime(bestelldatum.date_bestellung)).all()
    stunden = probe.time.str[:2].astype(int)
    assert stunden.between(7, 23).all()
    assert probe.time.str.match(r"^\d{2}:\d{2}:\d{2}$").all()


def test_sterneverteilung(probe):
    anteile = probe.stars.value_counts(normalize=True) * 100
    for sterne, soll in [(5, 38), (4, 27), (3, 13), (2, 9), (1, 13)]:
        assert abs(anteile[sterne] - soll) <= 3, (sterne, anteile[sterne])


def test_sterne_haengen_an_zufriedenheit(probe, kandidaten):
    zusammen = probe.merge(kandidaten[["order_id", "satisfaction_score", "order_duration_min"]]
                           .drop_duplicates("order_id"), on="order_id")
    assert zusammen.stars.corr(zusammen.satisfaction_score) > 0.3
    assert zusammen.stars.corr(zusammen.order_duration_min) < -0.05


def test_deterministisch(kandidaten, bausteine):
    a = g.erzeuge_rezensionen(kandidaten, bausteine, anzahl=300, seed=7)
    b = g.erzeuge_rezensionen(kandidaten, bausteine, anzahl=300, seed=7)
    assert a.equals(b)


def test_umgangssprache_anteil(probe):
    klein = probe.review_text.str.match(r"^[a-z]").mean()
    assert 0.10 <= klein <= 0.20
