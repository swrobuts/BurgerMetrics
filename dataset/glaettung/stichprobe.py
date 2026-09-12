#!/usr/bin/env python3
"""stichprobe.py — zeigt 50 zufällige Rezensionen mit Sternen zum Gegenlesen.

    python3 dataset/glaettung/stichprobe.py [--seed 1]
"""
import argparse
from pathlib import Path

import pandas as pd

ZIEL = Path(__file__).resolve().parent.parent / "fact_reviews.csv"


def main():
    """50 Zeilen ziehen und Sterne neben Text ausgeben."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    r = pd.read_csv(ZIEL, encoding="utf-8-sig")
    for _, zeile in r.sample(50, random_state=args.seed).sort_values("stars").iterrows():
        print(f"{zeile.review_id:>5}  {zeile.stars}★  {zeile.review_text}")


if __name__ == "__main__":
    main()
