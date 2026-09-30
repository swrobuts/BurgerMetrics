#!/usr/bin/env python3
"""passwort_setzen.py — gibt der Rolle bm_pruefdienst ein neues Passwort und legt es auf dem VPS ab.

Das Passwort entsteht hier und geht zuerst per SSH über stdin nach
/opt/bm-pruefdienst/.env.db (Modus 600), dann als SCRAM-Hash an die Datenbank.
Die Datenbank protokolliert DDL mit; der Klartext erscheint dort deshalb nie.
Ausgegeben wird er auch hier nicht. Ein zweiter Lauf ersetzt das Passwort; der
Dienst braucht danach einen Neustart (deploy.sh).

    python3 pruefdienst/passwort_setzen.py
"""
import secrets
import subprocess
import sys
from pathlib import Path

import psycopg2.extensions

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL / "db"))
from skript_ausfuehren import verbinde  # noqa: E402

ROLLE = "bm_pruefdienst"
ZIEL = "/opt/bm-pruefdienst/.env.db"


def env_zeile(passwort):
    """Die Zeile für .env.db: Verbindung über das interne Docker-Netz."""
    return (f"DATABASE_URL=postgresql://{ROLLE}:{passwort}@supabase-db:5432/postgres"
            "?sslmode=require&application_name=bm-pruefdienst\n")


def ablegen(inhalt):
    """Schreibt die Datei per SSH auf den VPS; der Inhalt geht über stdin, nicht über die Befehlszeile."""
    befehl = f"umask 077 && mkdir -p /opt/bm-pruefdienst && cat > {ZIEL} && chmod 600 {ZIEL}"
    subprocess.run(["ssh", "vps", befehl], input=inhalt, text=True, check=True)


def passwort_setzen(verbindung, passwort):
    """Setzt das Passwort als SCRAM-Hash, berechnet auf dieser Seite."""
    geheim = psycopg2.extensions.encrypt_password(passwort, ROLLE, verbindung, "scram-sha-256")
    with verbindung.cursor() as cur:
        cur.execute(f"ALTER ROLE {ROLLE} PASSWORD %s", (geheim,))
    verbindung.commit()


def main():
    """Neues Passwort erzeugen, auf dem VPS ablegen, in der Datenbank setzen."""
    passwort = secrets.token_urlsafe(32)
    ablegen(env_zeile(passwort))
    verbindung = verbinde()
    try:
        passwort_setzen(verbindung, passwort)
    finally:
        verbindung.close()
    print(f"Passwort für {ROLLE} gesetzt und nach vps:{ZIEL} geschrieben.")


if __name__ == "__main__":
    main()
