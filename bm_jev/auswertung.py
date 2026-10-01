"""Kennzahlen für Notebook 09: Fehlerarten, Kosten, Confusion Matrix, Schwellen.

Arbeitet auf Zeilen aus testdaten.lesen(), ergänzt um „muster“ (Liste) und „p“
(Wahrscheinlichkeiten je Frage). Braucht weder pandas noch eine Datenbank.
"""
from collections import Counter
from itertools import product

from . import regeln

# Annahmen aus der Spezifikation (Abschnitt 4.5), in Euro je Fehler.
KOSTEN = {"gesundheitsrisiko_verpasst": 500, "problem_veroeffentlicht": 200,
          "unnoetig_zurueckgehalten": 1, "unnoetiger_qs_fall": 1}


def fehlerart(zeile, entscheidung):
    """Der teuerste Fehler einer Entscheidung gegen das Soll, oder None."""
    if zeile["soll_qs_fall"] and not entscheidung.qs_fall:
        return "gesundheitsrisiko_verpasst"
    if zeile["soll_entscheidung"] == "zurueckgehalten" and entscheidung.ergebnis == "freigegeben":
        return "problem_veroeffentlicht"
    if zeile["soll_entscheidung"] == "freigegeben" and entscheidung.ergebnis == "zurueckgehalten":
        return "unnoetig_zurueckgehalten"
    if entscheidung.qs_fall and not zeile["soll_qs_fall"]:
        return "unnoetiger_qs_fall"
    return None


def bewerten(zeilen, schwellen=None):
    """Wendet die Regeln auf jede Zeile an und ergänzt Ergebnis, QS-Fall, Gründe und Fehlerart."""
    bewertet = []
    for z in zeilen:
        e = regeln.entscheiden(z["p"], z["muster"], schwellen)
        bewertet.append({**z, "ist_entscheidung": e.ergebnis, "ist_qs_fall": e.qs_fall,
                         "ist_gruende": e.gruende, "fehler": fehlerart(z, e)})
    return bewertet


def kosten(bewertet):
    """Summe der Fehlerkosten in Euro."""
    return sum(KOSTEN[z["fehler"]] for z in bewertet if z["fehler"])


def zaehlen(paare):
    """Zählt Paare aus Soll und Ist: tp (beide ja), fp (nur Ist ja), fn (nur Soll ja), tn (beide nein)."""
    k = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for soll, ist in paare:
        if soll and ist:
            k["tp"] += 1
        elif ist:
            k["fp"] += 1
        elif soll:
            k["fn"] += 1
        else:
            k["tn"] += 1
    return k


def schwelle_fuer(frage, schwellen=None):
    """Die Schwelle, ab der eine Frage in den Regeln als „ja“ zählt."""
    s = schwellen or regeln.SCHWELLEN
    if frage in ("gesundheitsrisiko", "themenbezug"):
        return s[frage]
    return s["verstoss"]


def konfusion(bewertet, frage, schwelle):
    """Confusion Matrix einer Frage: Soll-Wert gegen Wahrscheinlichkeit ab der Schwelle."""
    return zaehlen((z[f"soll_{frage}"] == 1, z["p"][frage] >= schwelle) for z in bewertet)


def konfusion_entscheidung(bewertet):
    """Confusion Matrix der Entscheidung; positiv heißt zurückhalten."""
    return zaehlen((z["soll_entscheidung"] == "zurueckgehalten", z["ist_entscheidung"] == "zurueckgehalten")
                   for z in bewertet)


def konfusion_qs(bewertet):
    """Confusion Matrix der QS-Fälle."""
    return zaehlen((z["soll_qs_fall"] == 1, z["ist_qs_fall"]) for z in bewertet)


def recall(k):
    """Anteil der Soll-ja-Fälle, die erkannt wurden; None ohne Soll-ja-Fall."""
    return k["tp"] / (k["tp"] + k["fn"]) if k["tp"] + k["fn"] else None


def praezision(k):
    """Anteil der Ist-ja-Fälle, die stimmen; None ohne Ist-ja-Fall."""
    return k["tp"] / (k["tp"] + k["fp"]) if k["tp"] + k["fp"] else None


def gitter(gesundheitsrisiko=(0.2, 0.3, 0.4, 0.5), verstoss=(0.4, 0.5, 0.6),
           unsicher=(0.1, 0.2, 0.3), themenbezug=(0.6, 0.7, 0.8, 0.9)):
    """Alle Kombinationen der Schwellen; die Unsicherheitsgrenze liegt unter der Verstoß-Schwelle."""
    return [{"gesundheitsrisiko": g, "verstoss": v, "unsicher": u, "themenbezug": t}
            for g, v, u, t in product(gesundheitsrisiko, verstoss, unsicher, themenbezug) if u < v]


def schwellen_durchspielen(zeilen, kombinationen):
    """Fehlerkosten und Fehlerzahlen je Kombination, günstigste zuerst."""
    ergebnisse = []
    for schwellen in kombinationen:
        bewertet = bewerten(zeilen, schwellen)
        zaehler = Counter(z["fehler"] for z in bewertet if z["fehler"])
        ergebnisse.append({**schwellen, "kosten": kosten(bewertet),
                           **{art: zaehler.get(art, 0) for art in KOSTEN}})
    return sorted(ergebnisse, key=lambda e: e["kosten"])
