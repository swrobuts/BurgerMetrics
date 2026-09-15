# open-meteo.py — Tageswerte für Würzburg von der Open-Meteo-Archiv-API holen
# und als CSV speichern. Nachbildung von hole_wetter() aus
# notebooks/05_wetter_und_ereignisse.ipynb als eigenständiges Skript (Lab 08).
#
# Voraussetzung: das Paket requests
#   python3 -m pip install requests
# Aufruf:
#   python3 open-meteo.py
# Schreibt wetter_open_meteo.csv im aktuellen Ordner. Kein Schlüssel nötig;
# Stand 09/2026 sind bis 10.000 Aufrufe je Tag kostenfrei (Lizenz CC BY 4.0).
#
# Lizenzpflicht: Wer mit diesen Daten arbeitet, nennt die Quelle —
# "Weather data by Open-Meteo.com" (CC BY 4.0, https://open-meteo.com/en/terms).

import csv
import requests

ADRESSE = "https://archive-api.open-meteo.com/v1/archive"
BREITE = 49.79    # Würzburg, nördliche Breite
LAENGE = 9.95     # Würzburg, östliche Länge


def hole_wetter(start_datum, end_datum):
    # Fragt Tageswerte für einen Zeitraum ab und gibt das Feld "daily" zurück:
    # ein Objekt mit gleich langen Listen, eine je Tag im Zeitraum.
    antwort = requests.get(ADRESSE, timeout=60, params={
        "latitude": BREITE,
        "longitude": LAENGE,
        "start_date": start_datum,
        "end_date": end_datum,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Europe/Berlin",
    })
    antwort.raise_for_status()
    return antwort.json()["daily"]


def schreibe_csv(tage, pfad):
    # Schreibt eine Zeile je Tag; die Listen aus hole_wetter() sind parallel,
    # also gleicher Index, gleicher Tag.
    with open(pfad, "w", encoding="utf-8", newline="") as datei:
        schreiber = csv.writer(datei)
        schreiber.writerow(["tag", "tmax", "tmin", "niederschlag_mm"])
        for i, tag in enumerate(tage["time"]):
            schreiber.writerow([
                tag,
                tage["temperature_2m_max"][i],
                tage["temperature_2m_min"][i],
                tage["precipitation_sum"][i],
            ])


if __name__ == "__main__":
    tage = hole_wetter("2026-01-01", "2026-01-07")
    schreibe_csv(tage, "wetter_open_meteo.csv")
    print(f"{len(tage['time'])} Tage gespeichert in wetter_open_meteo.csv")
    print("Weather data by Open-Meteo.com (CC BY 4.0)")
