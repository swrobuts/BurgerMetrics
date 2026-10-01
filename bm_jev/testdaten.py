"""Die Testfälle der Moderation lesen und schreiben (dataset/moderation_*.csv)."""
import csv
from pathlib import Path

from . import regeln

WURZEL = Path(__file__).resolve().parent.parent
DATEIEN = {
    "testfaelle": WURZEL / "dataset" / "moderation_testfaelle.csv",
    "holdout": WURZEL / "dataset" / "moderation_holdout.csv",
    "stichprobe": WURZEL / "dataset" / "moderation_stichprobe.csv",
    "holdout_2": WURZEL / "dataset" / "moderation_holdout_2.csv",
}
FRAGEN = ["beleidigung", "personenbezug", "werbung", "themenbezug", "anweisung", "gesundheitsrisiko"]
SPALTEN = ["fall_id", "gruppe", "produkt", "text", *[f"soll_{frage}" for frage in FRAGEN],
           "soll_muster", "soll_entscheidung", "soll_qs_fall"]


def lesen(pfad):
    """Liest eine Testdatei; Soll-Werte als Zahlen, die Muster als Liste."""
    with Path(pfad).open(encoding="utf-8", newline="") as f:
        zeilen = list(csv.DictReader(f))
    for z in zeilen:
        for spalte in [f"soll_{frage}" for frage in FRAGEN] + ["soll_qs_fall"]:
            z[spalte] = int(z[spalte])
        z["soll_muster"] = [m for m in z["soll_muster"].split("|") if m]
    return zeilen


def schreiben(pfad, zeilen):
    """Schreibt Zeilen im Format von SPALTEN; die Muster wieder mit | verbunden."""
    with Path(pfad).open("w", encoding="utf-8", newline="") as f:
        schreiber = csv.DictWriter(f, fieldnames=SPALTEN)
        schreiber.writeheader()
        for z in zeilen:
            schreiber.writerow({**z, "soll_muster": "|".join(z["soll_muster"])})


def entscheidung_aus_soll(zeile):
    """Die Soll-Entscheidung folgt aus den Soll-Werten nach denselben Regeln wie im Dienst."""
    p = {frage: float(zeile[f"soll_{frage}"]) for frage in FRAGEN}
    return regeln.entscheiden(p, zeile["soll_muster"])
