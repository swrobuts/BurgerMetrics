#!/usr/bin/env python3
"""zusammenfuehren.py — baut aus Rohstand und geglätteten Losen den Bestand fact_reviews.csv.

    python3 dataset/glaettung/zusammenfuehren.py

Regeln je Text: 5 bis 500 Zeichen, kein Zeilenumbruch, Länge höchstens
30 Prozent vom Rohtext entfernt. Rezensionen ohne geglätteten Text behalten
den Rohtext — das wird gemeldet, ist aber kein Fehler (Abbruchkriterium der
Spec). Unbekannte Kennungen und Regelverstöße sind Fehler: Exit-Code 1, und
die Ausgabedatei wird nicht geschrieben.
"""
import sys
from pathlib import Path

import pandas as pd

HIER = Path(__file__).resolve().parent
ROH = HIER.parent / "fact_reviews_roh.csv"
ZIEL = HIER.parent / "fact_reviews.csv"
LOSE = HIER / "lose"


def pruefe_text(alt, neu):
    """Prüft einen geglätteten Text gegen die Regeln; leere Liste heißt in Ordnung."""
    befunde = []
    if not isinstance(neu, str) or not neu.strip():
        return ["Text ist leer"]
    if "\n" in neu or "\r" in neu:
        befunde.append("Text enthält einen Zeilenumbruch")
    if len(neu) < 5:
        befunde.append("Text ist zu kurz (unter 5 Zeichen)")
    if len(neu) > 500:
        befunde.append("Text ist zu lang (über 500 Zeichen)")
    if len(neu) > 1.3 * len(alt) + 10:
        befunde.append(f"Text ist zu lang gegenüber dem Rohtext ({len(neu)} statt {len(alt)} Zeichen)")
    if len(neu) < 0.7 * len(alt) - 10:
        befunde.append(f"Text ist zu kurz gegenüber dem Rohtext ({len(neu)} statt {len(alt)} Zeichen)")
    return befunde


def lade_lose(ordner):
    """Liest alle geglätteten Lose zu einer Tabelle review_id, review_text zusammen."""
    dateien = sorted(Path(ordner).glob("geglaettet_*.csv"))
    if not dateien:
        return pd.DataFrame({"review_id": pd.Series(dtype=int), "review_text": pd.Series(dtype=str)})
    return pd.concat([pd.read_csv(d, encoding="utf-8") for d in dateien], ignore_index=True)


def zusammenfuehren(roh, geglaettet):
    """Ersetzt die Texte per review_id; gibt den Bestand und die Befunde zurück."""
    befunde = []
    bekannt = set(roh.review_id)
    for kennung in geglaettet.review_id:
        if kennung not in bekannt:
            befunde.append(f"FEHLER: unbekannte review_id {kennung}")
    if geglaettet.review_id.duplicated().any():
        befunde.append("FEHLER: review_id kommt in den Losen mehrfach vor")
    neu = dict(zip(geglaettet.review_id, geglaettet.review_text))
    ergebnis = roh.copy()
    fehlend = []
    for i, zeile in ergebnis.iterrows():
        if zeile.review_id not in neu:
            fehlend.append(int(zeile.review_id))
            continue
        for befund in pruefe_text(zeile.review_text, neu[zeile.review_id]):
            befunde.append(f"FEHLER: review_id {zeile.review_id}: {befund}")
        ergebnis.at[i, "review_text"] = neu[zeile.review_id].strip()
    if fehlend:
        befunde.append(f"{len(fehlend)} Rezensionen ohne geglätteten Text, roh belassen (z. B. {fehlend[:5]})")
    return ergebnis, befunde


def main():
    """Rohstand und Lose lesen, zusammenführen, Befunde ausgeben, Bestand schreiben."""
    roh = pd.read_csv(ROH, encoding="utf-8-sig")
    geglaettet = lade_lose(LOSE)
    ergebnis, befunde = zusammenfuehren(roh, geglaettet)
    for befund in befunde:
        print("  " + befund)
    if any(b.startswith("FEHLER") for b in befunde):
        sys.exit("Abbruch: Fehler in den Losen, fact_reviews.csv nicht geschrieben.")
    ergebnis.to_csv(ZIEL, index=False, encoding="utf-8-sig", lineterminator="\n")
    print(f"{len(geglaettet)} von {len(roh)} Texten geglättet, geschrieben: {ZIEL}")


if __name__ == "__main__":
    main()
