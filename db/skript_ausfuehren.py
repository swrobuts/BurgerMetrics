#!/usr/bin/env python3
"""skript_ausfuehren.py — führt eine SQL-Datei aus db/aufbau/ als postgres aus.

Eine Transaktion: Läuft die Datei fehlerfrei, wird sie bestätigt, sonst wird
alles zurückgerollt. Die NOTICE-Meldungen der Skripte (RAISE NOTICE) erscheinen
auf der Konsole — sie sind die Rückmeldung der Aufbauskripte.

    python3 db/skript_ausfuehren.py db/aufbau/0021_rezensionen.sql

Verbindung aus der nicht versionierten .env im Projektstamm (PGHOST, PGPORT,
PGDATABASE, PGUSER, PGPASSWORD), wie bei lade_csv.py und materialisieren.py.
"""
import os
import sys
from pathlib import Path

import psycopg2


def lade_env():
    """Liest .env im Projektstamm, ohne die Shell zu bemühen."""
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for zeile in env.read_text().splitlines():
            zeile = zeile.strip()
            if zeile and not zeile.startswith("#") and "=" in zeile:
                k, _, v = zeile.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def verbinde():
    """Öffnet die Verbindung mit dem Betreiberkonto aus der .env."""
    lade_env()
    return psycopg2.connect(
        host=os.environ["PGHOST"], port=os.environ["PGPORT"],
        dbname=os.environ["PGDATABASE"], user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"], connect_timeout=30, sslmode="verify-full")


def skript_ausfuehren(pfad):
    """Führt die Datei in einer Transaktion aus und gibt die NOTICE-Zeilen zurück."""
    sql = Path(pfad).read_text(encoding="utf-8")
    con = verbinde()
    try:
        with con.cursor() as cur:
            cur.execute(sql)
        con.commit()
        return [m.strip() for m in con.notices]
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def main():
    """Kommandozeile: genau eine Datei, Meldungen ausgeben, Ergebnis nennen."""
    if len(sys.argv) != 2:
        sys.exit("Aufruf: python3 db/skript_ausfuehren.py <sql-datei>")
    pfad = Path(sys.argv[1])
    if not pfad.exists():
        sys.exit(f"FEHLER: {pfad} gibt es nicht")
    lade_env()
    print(f"Führe {pfad.name} als {os.environ.get('PGUSER', '?')} aus ...")
    try:
        for zeile in skript_ausfuehren(pfad):
            print("  " + zeile)
    except psycopg2.Error as fehler:
        sys.exit(f"Zurückgerollt: {fehler.pgerror or fehler}")
    print("Bestätigt.")


if __name__ == "__main__":
    main()
