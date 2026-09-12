#!/usr/bin/env bash
# pruefe_notebooks.sh — führt alle Notebooks gegen die Datenbank aus und speichert die
# Ausgaben im Notebook. Das ist die Abnahme der Phase: Läuft eines nicht durch, bricht
# das Skript ab. Danach prüft pruefe_ausgaben.py jedes Notebook auf Fehlerausgaben.
set -euo pipefail
cd "$(dirname "$0")"
for nb in 0*.ipynb; do
  echo "== $nb"
  jupyter nbconvert --execute --to notebook --inplace --ExecutePreprocessor.timeout=1800 "$nb"
done
python3 quellen/pruefe_ausgaben.py 0*.ipynb
echo "Alle Notebooks ausgeführt und geprüft."
