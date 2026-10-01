#!/usr/bin/env python3
"""moderation_stichprobe.py — zieht 500 simulierte Rezensionen für Notebook 09.

100 je Sternzahl aus fact_reviews.csv, Startwert 2026. Soll ist für alle
„freigegeben ohne QS-Fall“: Der Simulationsbestand ist kuratiert. Die
Stichprobe misst, wie oft die Regeln harmlose Texte unnötig zurückhalten.

    python3 dataset/moderation_stichprobe.py
"""
import csv
import random
import sys
from pathlib import Path

ORDNER = Path(__file__).resolve().parent
sys.path.insert(0, str(ORDNER.parent))
from bm_jev import testdaten  # noqa: E402


def produktnamen():
    """product_id → product_name aus dim_product.csv."""
    with (ORDNER / "dim_product.csv").open(encoding="utf-8-sig", newline="") as f:
        return {int(z["product_id"]): z["product_name"] for z in csv.DictReader(f)}


def ziehen(je_stern=100, startwert=2026):
    """Zieht je Sternzahl dieselbe Zahl simulierter Rezensionen, immer dieselben."""
    namen = produktnamen()
    with (ORDNER / "fact_reviews.csv").open(encoding="utf-8-sig", newline="") as f:
        bestand = [z for z in csv.DictReader(f) if z["source"] == "simulation"]
    zufall = random.Random(startwert)
    auswahl = []
    for sterne in "12345":
        kandidaten = [z for z in bestand if z["stars"] == sterne]
        auswahl += zufall.sample(kandidaten, je_stern)
    return [zeile(z, namen) for z in auswahl]


def zeile(rezension, namen):
    """Eine Zeile im Format der Testdateien, Soll: harmlos."""
    soll = {f"soll_{frage}": 0 for frage in testdaten.FRAGEN}
    soll["soll_themenbezug"] = 1
    return {"fall_id": f"S{int(rezension['review_id']):05d}", "gruppe": f"simulation_{rezension['stars']}",
            "produkt": namen[int(rezension["product_id"])], "text": rezension["review_text"], **soll,
            "soll_muster": [], "soll_entscheidung": "freigegeben", "soll_qs_fall": 0}


if __name__ == "__main__":
    zeilen = ziehen()
    testdaten.schreiben(testdaten.DATEIEN["stichprobe"], zeilen)
    print(f"{len(zeilen)} Rezensionen nach {testdaten.DATEIEN['stichprobe'].name} geschrieben.")
