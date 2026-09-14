# verbindung-sqlalchemy.py — dieselbe Verbindung für ein lokales Skript
#
# Die Verbindungszeichenkette kommt aus der Umgebungsvariablen DATABASE_URL, wie in
# dash/app.py. Für ein eigenes Konto steht sie in einer Datei .env im aktuellen Ordner
# (dort, wo Sie python3 aufrufen), ohne Anführungszeichen:
#     DATABASE_URL=postgresql+psycopg2://BENUTZER:KENNWORT@supabase.butscher.cloud:5433/postgres
# Die Datei .env steht in .gitignore und kommt nie ins Repository.
# Fehlt die Variable, nimmt das Skript das Demo-Konto studi_daba (öffentlich, nur lesend);
# so läuft es auch ohne .env-Datei. Die Zeichenkette wird nirgends ausgegeben.
#
# Aufruf: python3 verbindung-sqlalchemy.py
# Voraussetzung: pandas, sqlalchemy, psycopg2-binary (notebooks/requirements.txt)
# Stand 09/2026: pandas 3.0, SQLAlchemy 2.0, psycopg2 2.9.

import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

DEMO_KONTO = "postgresql+psycopg2://studi_daba:thws@supabase.butscher.cloud:5433/postgres"


def lade_env(pfad=".env"):
    # Liest NAME=WERT-Zeilen aus der .env-Datei in die Umgebung; schon gesetzte Variablen bleiben
    datei = Path(pfad)
    if not datei.exists():
        return
    for zeile in datei.read_text(encoding="utf-8").splitlines():
        if "=" in zeile and not zeile.startswith("#"):
            name, wert = zeile.split("=", 1)
            os.environ.setdefault(name.strip(), wert.strip())


lade_env()
VERBINDUNG = os.environ.get("DATABASE_URL", DEMO_KONTO)
engine = create_engine(VERBINDUNG)


def lade_sql(sql):
    # Führt eine Abfrage aus und gibt das Ergebnis als DataFrame zurück
    return pd.read_sql(sql, engine)


if __name__ == "__main__":
    # Verbindungsprobe wie in Notebook 00: Rolle und Suchpfad
    print(lade_sql("SELECT current_user, current_setting('search_path') AS suchpfad"))
