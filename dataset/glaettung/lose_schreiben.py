#!/usr/bin/env python3
"""lose_schreiben.py — teilt den Rohstand in Lose à 100 Rezensionen für die Glättung.

    python3 dataset/glaettung/lose_schreiben.py          # schreibt lose/los_001.csv …

Jedes Los trägt review_id, stars und review_text. Die Lose werden nicht
versioniert (gitignore); der Rohstand bleibt jederzeit aus generate_reviews.py
reproduzierbar.
"""
from pathlib import Path

import pandas as pd

HIER = Path(__file__).resolve().parent
ROH = HIER.parent / "fact_reviews_roh.csv"


def lose_schreiben(roh, ordner, groesse=100):
    """Schreibt die Zeilen in nummerierte Lose und gibt die Dateipfade zurück."""
    ordner = Path(ordner)
    ordner.mkdir(parents=True, exist_ok=True)
    dateien = []
    for nummer, start in enumerate(range(0, len(roh), groesse), start=1):
        los = roh.iloc[start:start + groesse][["review_id", "stars", "review_text"]]
        pfad = ordner / f"los_{nummer:03d}.csv"
        los.to_csv(pfad, index=False, encoding="utf-8", lineterminator="\n")
        dateien.append(pfad)
    return dateien


def main():
    """Rohstand lesen, Lose schreiben, Anzahl nennen."""
    roh = pd.read_csv(ROH, encoding="utf-8-sig")
    dateien = lose_schreiben(roh, HIER / "lose")
    print(f"{len(dateien)} Lose in {HIER / 'lose'} geschrieben")


if __name__ == "__main__":
    main()
