#!/usr/bin/env python3
"""moderation_jev_lauf.py — schickt Testfälle, beide Holdouts und Stichprobe einmal an Jev.

Gefragt wird mit dem aktuellen Fragen-Stand und mit Stand 1, damit Notebook 09
beide vergleichen kann. Die Antworten landen im Cache dataset/cache/moderation_jev.jsonl;
jeder weitere Lauf liest nur noch dort und kostet nichts. Ohne TYPESAFE_API_KEY in der .env
bricht das Skript ab, sobald eine Antwort fehlt. Es gibt nur Zählungen aus,
keine Ergebnisse je Fall (der Holdout bleibt bis zum Notebook ungesehen) und
nie den Schlüssel.

    python3 dataset/moderation_jev_lauf.py
"""
import sys
import time
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
from bm_jev import fragen, jev, testdaten, umgebung  # noqa: E402

CACHE = WURZEL / "dataset" / "cache" / "moderation_jev.jsonl"
STAENDE = {fragen.FRAGEN_STAND: fragen.FRAGEN, "1": fragen.FRAGEN_STAND_1}


def mit_wiederholung(frage, versuche=3):
    """Wiederholt eine Anfrage bei Überlastung oder Netzfehler mit wachsender Pause."""
    for versuch in range(versuche):
        try:
            return frage()
        except jev.JevFehler:
            if versuch == versuche - 1:
                raise
            time.sleep(5 * 2 ** versuch)


def main():
    """Beurteilt alle Zeilen der vier Dateien je Fragen-Stand und meldet neue Anfragen, Tokens und Kosten."""
    umgebung.env_laden()
    schluessel = jev.api_schluessel()
    cache = jev.Cache(CACHE)
    neu = aus_cache = tokens = 0
    for stand, wortlaut in STAENDE.items():
        for name, pfad in testdaten.DATEIEN.items():
            for z in testdaten.lesen(pfad):
                antwort = mit_wiederholung(lambda: jev.beurteilen(z["text"], z["produkt"], cache=cache,
                                                                  api_key=schluessel, fragen=wortlaut))
                if antwort.aus_cache:
                    aus_cache += 1
                else:
                    neu += 1
                    tokens += antwort.input_tokens or 0
            print(f"Stand {stand}, {name}: fertig")
    kosten = tokens / 1_000_000 * jev.PREIS_INPUT
    tausender = f"{tokens:,}".replace(",", ".")
    print(f"neu gefragt: {neu}, aus dem Cache: {aus_cache}, Input-Tokens: {tausender}, "
          f"Kosten: {kosten:.3f} US-Dollar")


if __name__ == "__main__":
    main()
