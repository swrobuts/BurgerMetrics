"""Der Aktualisierungsschalter darf kuratierte Quellen weiterhin lesen."""
import ast
import json
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def umgebung(tmp_path):
    notebook = Path(__file__).resolve().parents[1] / "05_wetter_und_ereignisse.ipynb"
    zellen = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    quelle = next("".join(z["source"]) for z in zellen
                  if z["cell_type"] == "code" and "def hole_oder_lies" in "".join(z["source"]))
    funktion = next(n for n in ast.parse(quelle).body
                    if isinstance(n, ast.FunctionDef) and n.name == "hole_oder_lies")
    namespace = {"pd": pd, "DATEN": tmp_path, "AKTUALISIEREN": True,
                 "GITHUB": "https://example.invalid/daten", "zahl": str}
    exec(compile(ast.Module(body=[funktion], type_ignores=[]), str(notebook), "exec"), namespace)
    return namespace


def test_kuratierte_datei_bleibt_bei_aktualisierung_lesbar(umgebung):
    pfad = umgebung["DATEN"] / "vpi_jahr.csv"
    pfad.write_text("jahr,vpi_2020_100\n2020,100\n", encoding="utf-8")
    vorher = pfad.read_bytes()
    daten = umgebung["hole_oder_lies"]("vpi_jahr")
    assert daten.to_dict("records") == [{"jahr": 2020, "vpi_2020_100": 100}]
    assert pfad.read_bytes() == vorher


def test_kuratierte_datei_ohne_lokale_kopie_wird_aus_github_gelesen(umgebung, monkeypatch):
    aufrufe = []
    def github_lesen(url):
        aufrufe.append(url)
        return pd.DataFrame({"jahr": [2020], "vpi_2020_100": [100]})
    monkeypatch.setattr(pd, "read_csv", github_lesen)
    assert len(umgebung["hole_oder_lies"]("vpi_jahr")) == 1
    assert aufrufe == ["https://example.invalid/daten/vpi_jahr.csv"]


@pytest.mark.parametrize("aktualisieren, erwartet", [(False, 10), (True, 20)])
def test_api_quelle_wird_nur_auf_wunsch_aktualisiert(umgebung, aktualisieren, erwartet):
    pfad = umgebung["DATEN"] / "wetter.csv"
    pd.DataFrame({"temperatur": [10]}).to_csv(pfad, index=False)
    umgebung["AKTUALISIEREN"] = aktualisieren
    aufrufe = []
    def holen():
        aufrufe.append(True)
        return pd.DataFrame({"temperatur": [20]})
    daten = umgebung["hole_oder_lies"]("wetter", holen)
    assert daten["temperatur"].tolist() == [erwartet]
    assert pd.read_csv(pfad)["temperatur"].tolist() == [erwartet]
    assert len(aufrufe) == int(aktualisieren)
