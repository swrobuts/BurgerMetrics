"""Die .env im Projektstamm lesen, ohne Shell und ohne python-dotenv (Muster db/materialisieren.py)."""
import os
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent


def env_laden(datei=WURZEL / ".env"):
    """Übernimmt Schlüssel=Wert-Zeilen in die Umgebung; schon gesetzte Werte gewinnen."""
    datei = Path(datei)
    if not datei.exists():
        return
    for zeile in datei.read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if zeile and not zeile.startswith("#") and "=" in zeile:
            name, _, wert = zeile.partition("=")
            os.environ.setdefault(name.strip(), wert.strip())
