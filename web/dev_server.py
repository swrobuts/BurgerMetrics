#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dev_server.py — statischer Server fuer die Entwicklung, ohne Zwischenspeicher.

Warum nicht einfach `python3 -m http.server`: Der sendet keine
Cache-Vorgaben. Chrome wendet dann eine Heuristik an und haelt ES-Module
fest — teils ueber Tabs und Neuladen hinweg. Man aendert eine Datei, laedt
neu, und der Browser fuehrt weiter die alte aus. Bei Modulen faellt das
besonders unangenehm auf: Der Fehler lautet dann "x is not a function",
obwohl die Funktion in der Datei steht.

Genau das ist beim Umbau der Kasse passiert, und es hat eine halbe Stunde
gekostet, bis klar war, dass nicht der Code falsch war, sondern der Browser
eine alte Fassung ausfuehrte.

    python3 web/dev_server.py            # Port 8899
    python3 web/dev_server.py 8080       # anderer Port

Fuer die Veroeffentlichung ist das nicht gedacht — dort sind Cache-Header
erwuenscht, nur eben mit Versionierung.
"""
import http.server
import os
import socketserver
import sys
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8899
WURZEL = Path(__file__).resolve().parent


class OhneZwischenspeicher(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, format, *args):
        # Nur Fehler melden — der Rest rauscht beim Entwickeln nur.
        if not args or not str(args[1]).startswith("2"):
            super().log_message(format, *args)


if __name__ == "__main__":
    os.chdir(WURZEL)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), OhneZwischenspeicher) as srv:
        print(f"  {WURZEL} auf http://localhost:{PORT} — ohne Zwischenspeicher")
        print("  Beenden mit Strg-C")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\n  beendet")
