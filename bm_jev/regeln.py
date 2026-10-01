"""Aus Jevs Wahrscheinlichkeiten und den Mustertreffern wird eine Entscheidung.

Die Regeln stehen im Code, nicht im Modell: Jev liefert Wahrscheinlichkeiten,
der Code entscheidet mit Schwellen, die Notebook 09 an Testfällen prüft.
Ablehnen kann nur ein Mensch; der Code gibt frei oder hält zurück.
"""
from dataclasses import dataclass

# Datum und laufende Nummer; steigt mit jeder Änderung an Schwellen oder Regeln.
REGEL_VERSION = "2026-10-01.1"

SCHWELLEN = {
    "gesundheitsrisiko": 0.4,   # ab hier QS-Fall und zurückhalten
    "verstoss": 0.5,            # Beleidigung, Personenbezug, Werbung, Anweisung: sicher
    "unsicher": 0.2,            # ab hier bis zur Verstoß-Schwelle: unsicher
    "themenbezug": 0.8,         # darunter: unsicher
}

VERSTOESSE = {
    "beleidigung": "Beleidigung",
    "personenbezug": "Personenbezug",
    "werbung": "Werbung",
    "anweisung": "Anweisung",
}


@dataclass
class Entscheidung:
    """Ergebnis der Regeln für eine Rezension."""
    ergebnis: str    # 'freigegeben' oder 'zurueckgehalten'
    gruende: list    # Gründe im Klartext, leer bei Freigabe
    qs_fall: bool    # Hinweis auf ein Gesundheitsrisiko


def entscheiden(wahrscheinlichkeiten, muster_treffer, schwellen=None):
    """Wendet die fünf Regeln in ihrer Reihenfolge an und sammelt alle zutreffenden Gründe."""
    s = schwellen or SCHWELLEN
    p = wahrscheinlichkeiten
    gruende = []
    if muster_treffer:
        gruende.append("Kontaktdaten oder Link")
    qs_fall = p["gesundheitsrisiko"] >= s["gesundheitsrisiko"]
    if qs_fall:
        gruende.append("Gesundheitsrisiko")
    for frage, grund in VERSTOESSE.items():
        if p[frage] >= s["verstoss"]:
            gruende.append(grund)
    unsicher = any(s["unsicher"] <= p[frage] < s["verstoss"] for frage in VERSTOESSE)
    if unsicher or p["themenbezug"] < s["themenbezug"]:
        gruende.append("unsicher")
    ergebnis = "zurueckgehalten" if gruende else "freigegeben"
    return Entscheidung(ergebnis, gruende, qs_fall)
