"""Die drei Dienstfunktionen der Datenbank für den Prüfdienst (Rolle bm_pruefdienst).

Der Dienst liest und schreibt nur über wawi.pruefung_offene_holen(),
wawi.pruefung_eintragen() und wawi.pruefung_heute(); Tabellen sieht er nicht.
Jede Funktion bestätigt ihre eigene Transaktion.
"""
import json
from dataclasses import dataclass

import psycopg2


@dataclass
class OffeneRezension:
    """Eine Shop-Rezension, die auf die Prüfung wartet."""
    rezension_id: int
    artikel: str
    inhalt: str


def verbinden(dsn):
    """Öffnet eine Verbindung mit kurzer Wartezeit und erkennbarem Namen."""
    return psycopg2.connect(dsn, connect_timeout=10, application_name="bm-pruefdienst")


def offene_holen(verbindung, anzahl):
    """Die ältesten offenen Shop-Rezensionen, höchstens anzahl."""
    with verbindung.cursor() as cur:
        cur.execute("SELECT rezension_id, artikel, inhalt FROM wawi.pruefung_offene_holen(%s)", (anzahl,))
        zeilen = cur.fetchall()
    verbindung.commit()
    return [OffeneRezension(*z) for z in zeilen]


def heute_angefragt(verbindung):
    """Zahl der heutigen Anfragen an Jev (Europe/Berlin)."""
    with verbindung.cursor() as cur:
        cur.execute("SELECT wawi.pruefung_heute()")
        anzahl = cur.fetchone()[0]
    verbindung.commit()
    return anzahl


def eintragen(verbindung, rezension_id, *, ergebnis=None, gruende=(), qs_fall=False,
              wahrscheinlichkeiten=None, muster_treffer=(), jev_angefragt=False, modell=None,
              fragen_stand=None, fragen_fingerabdruck=None, regel_version=None, input_tokens=None,
              fehler=None):
    """Trägt ein Prüfergebnis ein und liefert {rezension_id, status, uebersprungen}."""
    with verbindung.cursor() as cur:
        cur.execute(
            """SELECT wawi.pruefung_eintragen(
                 rezension_id => %s, ergebnis => %s, gruende => %s::text[], qs_fall_anlegen => %s,
                 wahrscheinlichkeiten => %s::jsonb, muster_treffer => %s::text[], jev_angefragt => %s,
                 modell => %s, fragen_stand => %s, fragen_fingerabdruck => %s, regel_version => %s,
                 input_tokens => %s, fehler => %s)""",
            (rezension_id, ergebnis, list(gruende), qs_fall,
             None if wahrscheinlichkeiten is None else json.dumps(wahrscheinlichkeiten),
             list(muster_treffer), jev_angefragt, modell, fragen_stand, fragen_fingerabdruck,
             regel_version, input_tokens, fehler))
        antwort = cur.fetchone()[0]
    verbindung.commit()
    return antwort
