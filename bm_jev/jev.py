"""Eine Rezension an Jev schicken und sechs Wahrscheinlichkeiten zurückbekommen.

Ein Request je Rezension, sechs Noul-Fragen darin, direkt über die HTTP-API von
TypeSafe (docs.typesafe.ai/api). Der Cache (JSONL) hält jede Antwort fest:
Dieselbe Rezension mit denselben Fragen kostet nur einmal Tokens, und
Notebook 09 läuft ohne Schlüssel aus dem Cache.
"""
import hashlib
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path

import requests

from .fragen import FRAGEN

API_URL = "https://api.typesafe.ai/v1/systemone"
# Feste Version statt "jev-latest": Ergebnisse bleiben vergleichbar, und der
# Cache passt nur zu genau diesem Modell.
MODELL = "jev-1.13.0"
# US-Dollar je eine Million Input-Tokens; Output kostet bei Jev nichts
# (docs.typesafe.ai/models, Stand 29.09.2026).
PREIS_INPUT = 0.042


@dataclass
class Antwort:
    """Jevs Urteil zu einer Rezension, ohne jede Entscheidung."""
    wahrscheinlichkeiten: dict   # je Frage die Wahrscheinlichkeit für „ja“
    input_tokens: int | None
    modell: str
    aus_cache: bool = False


class JevFehler(Exception):
    """Jev hat nicht oder unvollständig geantwortet. Die Meldung enthält nie Rezensionstext."""


class KeinCacheTreffer(LookupError):
    """Die Antwort liegt nicht im Cache, und ohne Schlüssel wird Jev nicht gefragt."""


def state(text, produkt):
    """Nur was die Fragen brauchen: Rezensionstext und Produktname."""
    return {"rezension": {"text": text, "produkt": produkt}}


def anfrage(text, produkt, modell=MODELL, fragen=FRAGEN):
    """Der Körper des Requests: State, Modell und die sechs Fragen des gewählten Stands."""
    return {"state": state(text, produkt), "model": modell, "questions": fragen}


def schluessel(koerper):
    """Cache-Schlüssel: Ändert sich Modell, State oder ein Wort einer Frage, entsteht ein neuer."""
    roh = json.dumps(koerper, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(roh.encode("utf-8")).hexdigest()


def api_schluessel():
    """Der Schlüssel aus der Umgebung oder None; er wird nie ausgegeben."""
    wert = os.environ.get("TYPESAFE_API_KEY", "").strip()
    return wert or None


def wahrscheinlichkeit(wert):
    """Eine Zahl von 0 bis 1; alles andere (Text, NaN, 1.2) ist keine gültige Antwort."""
    if isinstance(wert, bool) or not isinstance(wert, (int, float)):
        raise TypeError("keine Zahl")
    if not math.isfinite(wert) or not 0 <= wert <= 1:
        raise ValueError("nicht zwischen 0 und 1")
    return float(wert)


def tokens_lesen(daten):
    """Die Input-Tokens als ganze Zahl; None, wenn die Antwort keine brauchbare Zahl nennt."""
    usage = daten.get("usage")
    wert = usage.get("input_tokens") if isinstance(usage, dict) else None
    if isinstance(wert, bool) or not isinstance(wert, (int, float)) or not math.isfinite(wert):
        return None
    return int(wert)


def antwort_lesen(daten):
    """Liest die sechs Wahrscheinlichkeiten und die Tokens aus der JSON-Antwort."""
    try:
        p = {frage: wahrscheinlichkeit(daten["answers"][frage]["noul"]) for frage in FRAGEN}
    except (KeyError, TypeError, ValueError) as fehler:
        raise JevFehler(f"Antwort unvollständig: {type(fehler).__name__}") from None
    return Antwort(p, tokens_lesen(daten), daten.get("model") or "")


def fragen_stellen(text, produkt, *, api_key, modell=MODELL, zeitlimit=20, senden=requests.post,
                   fragen=FRAGEN):
    """Ein Request an Jev. Wirft JevFehler bei Netzfehler, Zeitüberschreitung, HTTP-Fehler oder kaputter Antwort."""
    try:
        r = senden(API_URL, json=anfrage(text, produkt, modell, fragen), timeout=zeitlimit,
                   headers={"Authorization": f"Bearer {api_key}"})
    except requests.RequestException as fehler:
        raise JevFehler(f"keine Verbindung: {type(fehler).__name__}") from None
    if r.status_code != 200:
        raise JevFehler(f"HTTP {r.status_code}")
    try:
        daten = r.json()
    except ValueError:
        raise JevFehler("Antwort kein JSON") from None
    return antwort_lesen(daten)


class Cache:
    """Antworten als JSONL, eine Zeile {"schluessel": …, "antwort": {…}} je Anfrage."""

    def __init__(self, datei):
        self.datei = Path(datei)
        self.eintraege = {}
        if self.datei.exists():
            for zeile in self.datei.read_text(encoding="utf-8").splitlines():
                if zeile.strip():
                    eintrag = json.loads(zeile)
                    self.eintraege[eintrag["schluessel"]] = eintrag["antwort"]

    def holen(self, schluessel):
        """Die gespeicherte Antwort zu einem Schlüssel oder None."""
        return self.eintraege.get(schluessel)

    def ablegen(self, schluessel, antwort):
        """Hängt eine Antwort an die Datei an; der Rezensionstext kommt nicht hinein."""
        daten = {"wahrscheinlichkeiten": antwort.wahrscheinlichkeiten,
                 "input_tokens": antwort.input_tokens, "modell": antwort.modell}
        self.eintraege[schluessel] = daten
        self.datei.parent.mkdir(parents=True, exist_ok=True)
        with self.datei.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"schluessel": schluessel, "antwort": daten}, ensure_ascii=False) + "\n")


def beurteilen(text, produkt, *, cache, api_key=None, modell=MODELL, senden=requests.post, fragen=FRAGEN):
    """Erst im Cache nachsehen, dann mit Schlüssel Jev fragen und die Antwort ablegen."""
    s = schluessel(anfrage(text, produkt, modell, fragen))
    gespeichert = cache.holen(s)
    if gespeichert is not None:
        return Antwort(**gespeichert, aus_cache=True)
    if not api_key:
        raise KeinCacheTreffer(s[:12])
    antwort = fragen_stellen(text, produkt, api_key=api_key, modell=modell, senden=senden, fragen=fragen)
    cache.ablegen(s, antwort)
    return antwort
