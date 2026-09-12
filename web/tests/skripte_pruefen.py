#!/usr/bin/env python3
"""skripte_pruefen.py — prüft jeden eingebetteten <script>-Block einer HTML-Datei mit `node --check`.

    python3 web/tests/skripte_pruefen.py                # web/shop.html
    python3 web/tests/skripte_pruefen.py web/pos.html   # eine andere Seite

Der Browser meldet einen Syntaxfehler erst beim Laden der Seite, und dann
fehlt still die ganze Funktion. So fällt er vor dem Commit auf.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def bloecke(html):
    """Liefert (nummer, ist_modul, quelltext) je eingebettetem Skript; externe (src=) werden übersprungen."""
    aus = []
    for nummer, treffer in enumerate(re.finditer(r'<script([^>]*)>(.*?)</script>', html, re.S), 1):
        attribute, code = treffer.group(1), treffer.group(2)
        if 'src=' in attribute or not code.strip():
            continue
        aus.append((nummer, 'type="module"' in attribute, code))
    return aus


def pruefe(datei):
    """Schreibt jeden Block in eine Datei (.mjs für Module), lässt node --check darüber laufen und räumt die Datei weg."""
    fehler = 0
    for nummer, modul, code in bloecke(Path(datei).read_text(encoding='utf-8')):
        with tempfile.NamedTemporaryFile('w', suffix='.mjs' if modul else '.js',
                                         delete=False, encoding='utf-8') as f:
            f.write(code)
            pfad = f.name
        lauf = subprocess.run(['node', '--check', pfad], capture_output=True, text=True)
        Path(pfad).unlink()
        if lauf.returncode:
            fehler += 1
            print(f'FEHLER in Skriptblock {nummer} ({"Modul" if modul else "klassisch"}):\n{lauf.stderr.strip()}')
    print(f'{datei}: {fehler} Block(e) mit Syntaxfehler')
    return fehler


if __name__ == '__main__':
    sys.exit(1 if pruefe(sys.argv[1] if len(sys.argv) > 1 else 'web/shop.html') else 0)
