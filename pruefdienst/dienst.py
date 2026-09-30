#!/usr/bin/env python3
"""Prüfdienst: prüft neue Shop-Rezensionen mit Jev und trägt das Ergebnis ein.

Eine Runde alle BM_PRUEF_INTERVALL Sekunden: höchstens BM_PRUEF_STAPEL offene
Rezensionen holen, Muster suchen, Jev fragen, Regeln anwenden, eintragen. Über
BM_JEV_TAGESLIMIT Anfragen am Tag werden neue Rezensionen ohne Jev
zurückgehalten. Das Protokoll nennt Rezensions-ID, Ergebnis, Gründe und Dauer,
nie den Text.
"""
import logging
import os
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bm_jev import datenbank, fragen, jev, muster, regeln  # noqa: E402

log = logging.getLogger("bm-pruefdienst")


@dataclass
class Einstellungen:
    """Die drei Stellschrauben des Dienstes."""
    stapel: int = 20
    intervall: int = 30
    tageslimit: int = 300


def einstellungen_lesen(umgebung=os.environ):
    """Liest BM_PRUEF_STAPEL, BM_PRUEF_INTERVALL und BM_JEV_TAGESLIMIT; fehlende Werte nehmen die Vorgabe."""
    return Einstellungen(stapel=int(umgebung.get("BM_PRUEF_STAPEL", 20)),
                         intervall=int(umgebung.get("BM_PRUEF_INTERVALL", 30)),
                         tageslimit=int(umgebung.get("BM_JEV_TAGESLIMIT", 300)))


def rezension_pruefen(rezension, anfrage):
    """Muster, Jev und Regeln für eine Rezension; liefert die Felder für eintragen()."""
    treffer = muster.treffer(rezension.inhalt)
    felder = {"muster_treffer": treffer, "jev_angefragt": True, "modell": jev.MODELL,
              "fragen_stand": fragen.FRAGEN_STAND, "fragen_fingerabdruck": fragen.fingerabdruck(),
              "regel_version": regeln.REGEL_VERSION}
    try:
        antwort = anfrage(rezension.inhalt, rezension.artikel)
    except jev.JevFehler as fehler:
        return {**felder, "fehler": str(fehler)}
    entscheidung = regeln.entscheiden(antwort.wahrscheinlichkeiten, treffer)
    return {**felder, "ergebnis": entscheidung.ergebnis, "gruende": entscheidung.gruende,
            "qs_fall": entscheidung.qs_fall, "wahrscheinlichkeiten": antwort.wahrscheinlichkeiten,
            "input_tokens": antwort.input_tokens, "modell": antwort.modell or jev.MODELL}


def ohne_jev_zurueckhalten(rezension):
    """Felder für eine Rezension über dem Tageslimit: zurückhalten, ohne Jev zu fragen."""
    return {"ergebnis": "zurueckgehalten", "gruende": ["Tageslimit erreicht"],
            "muster_treffer": muster.treffer(rezension.inhalt), "jev_angefragt": False,
            "regel_version": regeln.REGEL_VERSION}


def als_fehlversuch(felder, fehler):
    """Felder eines Fehlversuchs: ohne Ergebnis und Werte, mit dem Fehlercode der Datenbank."""
    code = getattr(fehler, "pgcode", None) or type(fehler).__name__
    basis = {k: felder[k] for k in ("muster_treffer", "jev_angefragt", "fragen_stand",
                                    "fragen_fingerabdruck", "regel_version") if k in felder}
    return {**basis, "modell": jev.MODELL, "fehler": f"Eintrag abgelehnt {code}"}


def sicher_eintragen(verbindung, db, rezension_id, felder):
    """Trägt ein; lehnt die Datenbank die Werte ab, zählt der Versuch wie ein Fehler von Jev."""
    try:
        return db.eintragen(verbindung, rezension_id, **felder), felder
    except (psycopg2.DataError, psycopg2.IntegrityError, psycopg2.ProgrammingError) as fehler:
        verbindung.rollback()
        felder = als_fehlversuch(felder, fehler)
        return db.eintragen(verbindung, rezension_id, **felder), felder


def eine_runde(verbindung, anfrage, einstellungen, db=datenbank):
    """Prüft einen Stapel offener Rezensionen und liefert die Zahl der Einträge."""
    angefragt = db.heute_angefragt(verbindung)
    eintraege = 0
    for rezension in db.offene_holen(verbindung, einstellungen.stapel):
        beginn = time.monotonic()
        if angefragt >= einstellungen.tageslimit:
            felder = ohne_jev_zurueckhalten(rezension)
        else:
            felder = rezension_pruefen(rezension, anfrage)
            angefragt += 1
        antwort, felder = sicher_eintragen(verbindung, db, rezension.rezension_id, felder)
        eintraege += 1
        log.info("rezension=%s status=%s gruende=%s fehler=%s dauer=%.1fs", rezension.rezension_id,
                 antwort["status"], ",".join(felder.get("gruende", [])) or "-",
                 felder.get("fehler") or "-", time.monotonic() - beginn)
    return eintraege


def warten(sekunden, weiter):
    """Wartet in Sekundenschritten, damit ein Anhalten nicht bis zu 30 Sekunden hängt."""
    for _ in range(sekunden):
        if not weiter():
            return
        time.sleep(1)


def main():
    """Läuft, bis der Container SIGTERM schickt; baut die Verbindung nach Fehlern neu auf."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    einstellungen = einstellungen_lesen()
    api_key = jev.api_schluessel()
    dsn = os.environ.get("DATABASE_URL", "")
    if not api_key or not dsn:
        log.error("TYPESAFE_API_KEY oder DATABASE_URL fehlt; der Dienst startet nicht.")
        return 1
    zustand = {"laufen": True}
    signal.signal(signal.SIGTERM, lambda *_: zustand.update(laufen=False))
    signal.signal(signal.SIGINT, lambda *_: zustand.update(laufen=False))

    def anfrage(text, produkt):
        return jev.fragen_stellen(text, produkt, api_key=api_key)

    log.info("Prüfdienst gestartet: Stapel %s, Intervall %s s, Tageslimit %s",
             einstellungen.stapel, einstellungen.intervall, einstellungen.tageslimit)
    verbindung = None
    while zustand["laufen"]:
        try:
            if verbindung is None or verbindung.closed:
                verbindung = datenbank.verbinden(dsn)
            eine_runde(verbindung, anfrage, einstellungen)
        except psycopg2.Error as fehler:
            log.warning("Datenbank: %s %s", type(fehler).__name__, getattr(fehler, "pgcode", "") or "")
            if verbindung is not None:
                verbindung.close()
            verbindung = None
        warten(einstellungen.intervall, lambda: zustand["laufen"])
    log.info("Prüfdienst beendet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
