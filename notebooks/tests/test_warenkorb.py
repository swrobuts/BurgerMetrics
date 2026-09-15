"""Regression: distinct product pairs must survive equal support values."""
import json
from pathlib import Path

import pandas as pd


def test_equal_support_keeps_distinct_pairs_and_both_directions():
    path = Path(__file__).resolve().parents[1] / "03_warenkorbanalyse.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    cell = next("".join(c["source"]) for c in notebook["cells"]
                if c["cell_type"] == "code" and "def beide_richtungen" in "".join(c["source"]))
    pairs = pd.DataFrame([
        {"A": "Burger", "B": "Pommes", "support": 0.1, "lift": 3.0, "confidence": 0.5},
        {"A": "Pommes", "B": "Burger", "support": 0.1, "lift": 3.0, "confidence": 0.4},
        {"A": "Nuggets", "B": "Sauce", "support": 0.1, "lift": 2.0, "confidence": 0.6},
        {"A": "Sauce", "B": "Nuggets", "support": 0.1, "lift": 2.0, "confidence": 0.3},
    ])
    namespace = {"paare": pairs, "pd": pd}
    exec(compile(cell, str(path), "exec"), namespace)
    selected = namespace["beste"]
    assert len(selected) == 2
    assert {frozenset((row.A, row.B)) for row in selected.itertuples()} == {
        frozenset(("Burger", "Pommes")), frozenset(("Nuggets", "Sauce"))}
    directions = namespace["beide_richtungen"]("Burger", "Pommes")
    assert directions["konfidenz_A_B"] == 0.5
    assert directions["konfidenz_B_A"] == 0.4
