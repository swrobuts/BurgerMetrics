#!/usr/bin/env python3
"""alle_bauen.py — erzeugt alle Notebooks neu aus ihren Bauskripten (ohne Ausführung).

    PYTHONPATH=notebooks/quellen python3 notebooks/quellen/alle_bauen.py
"""
import runpy
from pathlib import Path

HIER = Path(__file__).resolve().parent
for skript in sorted(HIER.glob("bau_0*.py")):
    print("==", skript.name)
    runpy.run_path(str(skript), run_name="__main__")
