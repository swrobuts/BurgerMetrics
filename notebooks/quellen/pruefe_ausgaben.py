#!/usr/bin/env python3
"""pruefe_ausgaben.py — prüft ein ausgeführtes Notebook.

    python3 notebooks/quellen/pruefe_ausgaben.py notebooks/00_zugang_und_daten.ipynb

Befunde: eine Codezelle ohne Ausführungsnummer (nie gelaufen), eine Ausgabe vom Typ
error, ein fehlender Pflichtabschnitt. Exit 1 bei mindestens einem Befund.
"""
import sys

import nbformat

PFLICHT = ["## Fragestellung", "## Daten", "## Vorgehen", "## Ergebnis", "## Was offen bleibt"]


def befunde(pfad):
    """Sammelt alle Befunde eines Notebooks als Liste von Sätzen."""
    nb = nbformat.read(pfad, as_version=4)
    liste = []
    markdown = "\n".join(z.source for z in nb.cells if z.cell_type == "markdown")
    for abschnitt in PFLICHT:
        if abschnitt not in markdown:
            liste.append(f"Abschnitt fehlt: {abschnitt}")
    for nummer, zelle in enumerate(nb.cells, 1):
        if zelle.cell_type != "code":
            continue
        if zelle.execution_count is None:
            liste.append(f"Zelle {nummer} wurde nicht ausgeführt")
        for ausgabe in zelle.outputs:
            if ausgabe.output_type == "error":
                liste.append(f"Zelle {nummer} endet mit {ausgabe.ename}: {ausgabe.evalue[:120]}")
    return liste


if __name__ == "__main__":
    fehler = 0
    for pfad in sys.argv[1:]:
        liste = befunde(pfad)
        print(f"{pfad}: {len(liste)} Befund(e)")
        for satz in liste:
            print("  -", satz)
        fehler += len(liste)
    sys.exit(1 if fehler else 0)
