#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP-Server fuer die BurgerMetrics-Datenbank - fuer den Betreiber.

WAS ER IST

Ein Fenster auf die beiden Schemata des Projekts: wawi (das operative
Warenwirtschaftsmodell, 3NF, in das Kasse und Shop schreiben) und
burgermetrics (das Galaxy-Schema mit der Semantikschicht, aus dem das
Dashboard liest). Ein Agent kann damit Tabellen auflisten, Spalten und
Fremdschluessel nachsehen, SQL lesen und - als Betreiber - auch
ausfuehren.

WESSEN KONTO

Das des Betreibers, aus der nicht versionierten .env im Wurzelverzeichnis
(PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD) - dasselbe Konto, mit
dem lade_csv.py und materialisieren.py arbeiten. Dieser Server ist NICHT
fuer Studierende gedacht; die haben die Rolle studi_daba
(db/aufbau/0020_demo_rolle.sql) und koennen sich damit einen eigenen
Server bauen. Fehlt die .env, startet der Server nicht.

LESEN UND SCHREIBEN

abfragen() laeuft in einer nur lesenden Transaktion, immer. ausfuehren()
ist der Schreibweg: DDL und DML, eine Transaktion je Aufruf, Commit nur
ohne Fehler. Wer den Server nur lesend betreiben will, setzt in der
Umgebung BM_MCP_NUR_LESEN=1 - dann meldet ausfuehren() sich ab.

EINRICHTUNG

    Eigene Umgebung, damit die allgemeine unberuehrt bleibt:
        bash mcp/einrichten.sh

    Pruefen, bevor irgendein Client ins Spiel kommt:
        mcp/.venv/bin/python mcp/server.py --pruefen

    Claude Desktop, ~/Library/Application Support/Claude/
    claude_desktop_config.json:

        {"mcpServers": {"burgermetrics-db": {
            "command": "<Pfad>/mcp/.venv/bin/python",
            "args": ["<Pfad>/mcp/server.py"]}}}
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
from decimal import Decimal
from typing import Any

import psycopg2
import psycopg2.extras
from mcp.server.mcpserver import MCPServer

# ─────────────────────────────────────────────────────── Zugangsdaten
#
# Aus der .env des Repos, wie lade_csv.py. Nichts davon steht hier im
# Quelltext: Das Konto ist das des Betreibers.
WURZEL = pathlib.Path(__file__).resolve().parent.parent


def _env_laden() -> None:
    """Liest .env nach os.environ, ohne Vorhandenes zu ueberschreiben."""
    datei = WURZEL / ".env"
    if not datei.exists():
        return
    for zeile in datei.read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        schluessel, wert = zeile.split("=", 1)
        os.environ.setdefault(schluessel.strip(), wert.strip())


_env_laden()
HOST = os.environ.get("PGHOST", "")
PORT = int(os.environ.get("PGPORT", "5432") or 5432)
DATENBANK = os.environ.get("PGDATABASE", "postgres")
BENUTZER = os.environ.get("PGUSER", "")
PASSWORT = os.environ.get("PGPASSWORD", "")
NUR_LESEN = os.environ.get("BM_MCP_NUR_LESEN", "") not in ("", "0", "nein", "false")

if not (HOST and BENUTZER and PASSWORT):
    sys.stderr.write(f"burgermetrics-db: PGHOST, PGUSER und PGPASSWORD fehlen. "
                     f"Erwartet in {WURZEL / '.env'} (siehe .env.example).\n")
    raise SystemExit(2)

SCHEMATA = ("wawi", "burgermetrics")
MAX_ZEILEN = 500
MAX_ZEICHEN = 60_000

ERKLAERUNG = {
    "wawi": ("Operatives Warenwirtschaftsmodell, 3NF, deutsche Namen. Kasse "
             "und Shop lesen hier Speisekarte und Filialliste und schreiben "
             "jeden Beleg hinein (kundenbestellung, bestellposition, rechnung). "
             "15 Tabellen, drei Sichten fuer die Anwendungen, drei stg-Sichten "
             "fuer den ETL-Schritt."),
    "burgermetrics": ("Auswertungsmodell: Galaxy-Schema mit zehn dim_-Tabellen, "
                      "fact_orders (Grain Bestellung), fact_order_items (Grain "
                      "Position) und obt_orders. Darueber die Semantikschicht: "
                      "materialisierte Sichten v_*, aus denen das Dashboard "
                      "liest. Wird per ETL aus wawi beladen (0019)."),
}

# ─────────────────────────────────────────── Stand dieses Prozesses
#
# Claude Desktop startet diese Datei als eigenen Prozess und laedt sie
# EINMAL. Wird sie danach geaendert, laeuft der alte Code weiter.
# serverstand() vergleicht den Abdruck von damals mit dem von jetzt.


def _fingerabdruck(pfad: pathlib.Path) -> str:
    return hashlib.sha256(pfad.read_bytes()).hexdigest()[:8]


_DATEI = pathlib.Path(__file__).resolve()
_STAND_BEIM_START = _fingerabdruck(_DATEI)


# ─────────────────────────────────────────────────────── Verbindung
def _verbindung(schreibend: bool = False):
    """Eine frische Verbindung je Aufruf. Lesend heisst: die Datenbank
    selbst weist jede Aenderung ab (SET TRANSACTION READ ONLY), nicht
    dieses Programm. Schreibend: eine Transaktion, Commit durch den Aufrufer."""
    con = psycopg2.connect(host=HOST, port=PORT, dbname=DATENBANK,
                           user=BENUTZER, password=PASSWORT,
                           connect_timeout=10,
                           application_name="burgermetrics-mcp")
    if schreibend:
        con.set_session(readonly=False, autocommit=False)
    else:
        con.set_session(readonly=True, autocommit=True)
        with con.cursor() as cur:
            cur.execute("SET statement_timeout = '120s'")
    return con


def _lesen(sql: str, parameter: tuple = ()) -> list[dict[str, Any]]:
    with _verbindung() as con:
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, parameter)
            if cur.description is None:
                return []
            return [dict(z) for z in cur.fetchall()]


def _json(wert: Any) -> Any:
    if isinstance(wert, Decimal):
        return float(wert)
    return str(wert)


def _ausgabe(zeilen: list[dict[str, Any]], kopf: str) -> str:
    text = kopf + "\n" + json.dumps(zeilen, ensure_ascii=False, indent=1, default=_json)
    if len(text) > MAX_ZEICHEN:
        text = text[:MAX_ZEICHEN] + "\n… abgeschnitten. Enger filtern oder limit senken."
    return text


def _fehler(fehler: Exception) -> str:
    text = str(fehler).strip().splitlines()[0] if str(fehler).strip() else repr(fehler)
    if "read-only transaction" in text:
        return ("Abgelehnt: abfragen() liest nur. Fuer Aenderungen ausfuehren() benutzen. " + text)
    if "statement timeout" in text:
        return ("Abgebrochen (Zeitgrenze). Abfrage einschraenken (WHERE, "
                "LIMIT) oder eine materialisierte Sicht v_* benutzen. " + text)
    return "Datenbank meldet: " + text


def _schema_pruefen(schema: str | None) -> tuple[str, ...]:
    if not schema:
        return SCHEMATA
    if schema not in SCHEMATA:
        raise ValueError(f"Unbekanntes Schema: {schema}. Es gibt {', '.join(SCHEMATA)}.")
    return (schema,)


def _name_aufloesen(name: str) -> tuple[str, str]:
    """'wawi.rechnung' oder 'rechnung' -> (schema, relation). Ohne Praefix
    gilt die Reihenfolge des Suchpfads der Rolle: wawi vor burgermetrics."""
    if "." in name:
        schema, rel = name.split(".", 1)
        _schema_pruefen(schema)
        return schema, rel
    treffer = _lesen(
        "SELECT n.nspname AS schema FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE c.relname = %s AND n.nspname = ANY(%s) AND c.relkind IN ('r','v','m','p')",
        (name, list(SCHEMATA)))
    if not treffer:
        raise ValueError(f"Keine Tabelle oder Sicht namens {name} in {', '.join(SCHEMATA)}.")
    gefunden = {t["schema"] for t in treffer}
    for s in SCHEMATA:
        if s in gefunden:
            return s, name
    raise ValueError(name)


# ─────────────────────────────────────────────────────── Server
server = MCPServer(
    "burgermetrics-db",
    instructions=(
        "Datenbank der Fallstudie BurgerMetrics (THWS), synthetische Daten "
        "einer Schnellrestaurantkette in Wuerzburg. Zwei Schemata: wawi ist "
        "das operative 3NF-Modell (Kasse, Shop), burgermetrics das "
        "Auswertungsmodell mit Galaxy-Schema und materialisierten Sichten "
        "v_* (Dashboard). Erst tabellen_auflisten und tabelle_beschreiben, "
        "dann abfragen. Tabellen IMMER mit Schemapraefix nennen "
        "(wawi.rechnung, burgermetrics.fact_orders); das Konto hat keinen "
        "Suchpfad auf die Projektschemata. Aenderungen nur ueber "
        "ausfuehren(), und nur wenn ausdruecklich verlangt. "
        "Fuer Kennzahlen die Sichten v_* bevorzugen - dort ist jede Kennzahl "
        "genau einmal definiert."),
)


@server.tool()
def serverstand() -> str:
    """Zeigt, womit dieser Prozess verbunden ist, wer er in der Datenbank
    ist, und ob die geladene Fassung von server.py noch die Datei auf der
    Platte ist."""
    zeilen: list[str] = [f"Verbindung: {BENUTZER}@{HOST}:{PORT}/{DATENBANK}"]
    try:
        z = _lesen("SELECT current_user, current_setting('search_path') AS suchpfad, "
                   "current_setting('statement_timeout') AS zeitgrenze, "
                   "current_setting('default_transaction_read_only') AS nur_lesen, "
                   "version() AS version")[0]
        zeilen.append(f"Rolle: {z['current_user']}, Suchpfad {z['suchpfad']}, "
                      f"Zeitgrenze {z['zeitgrenze']}, Schreibweg: {'aus' if NUR_LESEN else 'ausfuehren()'}")
        zeilen.append("Server: " + z["version"].split(" on ")[0])
    except Exception as fehler:                       # noqa: BLE001
        zeilen.append("Verbindung FEHLGESCHLAGEN: " + _fehler(fehler))
    jetzt = _fingerabdruck(_DATEI)
    if jetzt == _STAND_BEIM_START:
        zeilen.append(f"server.py: Stand {jetzt}, entspricht der Datei.")
    else:
        zeilen.append(f"server.py: geladen {_STAND_BEIM_START}, Datei jetzt {jetzt} - "
                      "der Prozess ist VERALTET. Claude Desktop neu starten.")
    return "\n".join(zeilen)


@server.tool()
def schemata_erklaeren() -> str:
    """Erklaert die beiden Schemata und wie sie zusammenhaengen."""
    return "\n\n".join(f"{s}: {t}" for s, t in ERKLAERUNG.items()) + (
        "\n\nDie Kette: Kasse/Shop schreiben nach wawi -> "
        "burgermetrics.uebernahme_aus_wawi() (ETL, nicht automatisch) -> "
        "Galaxy-Schema -> materialisierte Sichten -> Dashboard. "
        "Beide Schemata tragen denselben Bestand: 754.513 Bestellungen, "
        "2.950.082 Positionen.")


@server.tool()
def tabellen_auflisten(schema: str | None = None, sichten: bool = True) -> str:
    """Listet Tabellen und Sichten mit Zeilenzahl (Schaetzung) und Kommentar.

    schema   "wawi", "burgermetrics" oder leer fuer beide.
    sichten  auch Sichten und materialisierte Sichten zeigen.
    """
    try:
        arten = ("r", "p", "v", "m") if sichten else ("r", "p")
        zeilen = _lesen(
            "SELECT n.nspname AS schema, c.relname AS name, "
            "CASE c.relkind WHEN 'v' THEN 'Sicht' WHEN 'm' THEN 'mat. Sicht' ELSE 'Tabelle' END AS art, "
            "CASE WHEN c.relkind IN ('r','p','m') THEN c.reltuples::bigint END AS zeilen_ca, "
            "obj_description(c.oid, 'pg_class') AS kommentar "
            "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = ANY(%s) AND c.relkind = ANY(%s) "
            "ORDER BY n.nspname, c.relkind, c.relname",
            (list(_schema_pruefen(schema)), list(arten)))
    except Exception as fehler:                       # noqa: BLE001
        return _fehler(fehler)
    aus = []
    for z in zeilen:
        n = f"{z['zeilen_ca']:,}".replace(",", ".") if z["zeilen_ca"] is not None and z["zeilen_ca"] >= 0 else ""
        k = f"  — {z['kommentar']}" if z["kommentar"] else ""
        aus.append(f"{z['schema']}.{z['name']:<32} {z['art']:<11} {n:>10}{k}")
    return f"{len(zeilen)} Objekte:\n" + "\n".join(aus)


@server.tool()
def tabelle_beschreiben(name: str) -> str:
    """Spalten, Typen, Schluessel und Fremdschluessel einer Tabelle oder Sicht.

    name  "rechnung", "wawi.rechnung" oder "burgermetrics.fact_orders".
          Ohne Praefix gewinnt wawi; kunde, mitarbeiter, rechnung und
          zahlungsart gibt es nur in wawi, die dim_/fact_-Tabellen nur in
          burgermetrics.
    """
    try:
        schema, rel = _name_aufloesen(name)
        spalten = _lesen(
            "SELECT a.attnum AS nr, a.attname AS spalte, format_type(a.atttypid, a.atttypmod) AS typ, "
            "NOT a.attnotnull AS null_erlaubt, col_description(c.oid, a.attnum) AS kommentar "
            "FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = %s AND c.relname = %s AND a.attnum > 0 AND NOT a.attisdropped "
            "ORDER BY a.attnum", (schema, rel))
        if not spalten:
            return f"Keine Tabelle oder Sicht {schema}.{rel}."
        schluessel = _lesen(
            "SELECT con.contype AS art, pg_get_constraintdef(con.oid) AS definition "
            "FROM pg_constraint con JOIN pg_class c ON c.oid = con.conrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = %s AND c.relname = %s AND con.contype IN ('p','f','u') "
            "ORDER BY con.contype, con.conname", (schema, rel))
        verweise = _lesen(
            "SELECT n2.nspname || '.' || c2.relname AS von, pg_get_constraintdef(con.oid) AS definition "
            "FROM pg_constraint con JOIN pg_class c2 ON c2.oid = con.conrelid "
            "JOIN pg_namespace n2 ON n2.oid = c2.relnamespace "
            "JOIN pg_class c ON c.oid = con.confrelid JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = %s AND c.relname = %s AND con.contype = 'f' ORDER BY 1", (schema, rel))
        kommentar = _lesen(
            "SELECT obj_description(c.oid, 'pg_class') AS k, c.relkind AS art FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relname = %s",
            (schema, rel))[0]
    except Exception as fehler:                       # noqa: BLE001
        return _fehler(fehler)
    art = {"v": "Sicht", "m": "materialisierte Sicht"}.get(kommentar["art"], "Tabelle")
    aus = [f"{schema}.{rel} ({art})" + (f": {kommentar['k']}" if kommentar["k"] else "")]
    aus.append("Spalten:")
    for s in spalten:
        aus.append(f"  {s['spalte']:<28} {s['typ']:<22}{'' if s['null_erlaubt'] else ' NOT NULL'}"
                   + (f"  — {s['kommentar']}" if s["kommentar"] else ""))
    if schluessel:
        aus.append("Schluessel:")
        for k in schluessel:
            bez = {"p": "PRIMARY", "f": "FOREIGN", "u": "UNIQUE"}[k["art"]]
            aus.append(f"  {bez:<8} {k['definition']}")
    if verweise:
        aus.append("Verwiesen von:")
        for v in verweise:
            aus.append(f"  {v['von']:<32} {v['definition']}")
    return "\n".join(aus)


@server.tool()
def beziehungen_auflisten(schema: str = "wawi") -> str:
    """Alle Fremdschluessel eines Schemas: das Datenmodell als Liste.

    schema  "wawi" (15 Tabellen, 3NF) oder "burgermetrics" (Galaxy-Schema).
    """
    try:
        _schema_pruefen(schema)
        zeilen = _lesen(
            "SELECT c.relname AS von, a.attname AS spalte, c2.relname AS nach, a2.attname AS auf "
            "FROM pg_constraint con "
            "JOIN pg_class c ON c.oid = con.conrelid JOIN pg_namespace n ON n.oid = c.relnamespace "
            "JOIN pg_class c2 ON c2.oid = con.confrelid "
            "JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = con.conkey[1] "
            "JOIN pg_attribute a2 ON a2.attrelid = c2.oid AND a2.attnum = con.confkey[1] "
            "WHERE con.contype = 'f' AND n.nspname = %s ORDER BY c.relname, a.attname", (schema,))
    except Exception as fehler:                       # noqa: BLE001
        return _fehler(fehler)
    if not zeilen:
        return f"Keine Fremdschluessel in {schema}."
    return f"{len(zeilen)} Fremdschluessel in {schema}:\n" + "\n".join(
        f"  {z['von']}.{z['spalte']:<20} -> {z['nach']}.{z['auf']}" for z in zeilen)


@server.tool()
def abfragen(sql: str, limit: int = 100) -> str:
    """Fuehrt eine SQL-Abfrage aus und liefert die Zeilen als JSON.

    sql    Eine SELECT-Abfrage (auch WITH, EXPLAIN). Tabellen mit
           Schemapraefix nennen: wawi.rechnung, burgermetrics.fact_orders.
           Die Transaktion ist nur lesend; Aenderungen weist die
           Datenbank ab. Dafuer gibt es ausfuehren().
    limit  Hoechstens 500 Zeilen. Wer mehr braucht, aggregiert.
    """
    limit = max(1, min(int(limit), MAX_ZEILEN))
    sql = sql.strip().rstrip(";")
    if not sql:
        return "Leere Abfrage."
    try:
        with _verbindung() as con:
            with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql)
                if cur.description is None:
                    return "Ausgefuehrt, keine Ergebniszeilen."
                zeilen = [dict(z) for z in cur.fetchmany(limit + 1)]
    except Exception as fehler:                       # noqa: BLE001
        return _fehler(fehler)
    mehr = len(zeilen) > limit
    zeilen = zeilen[:limit]
    if not zeilen:
        return "Keine Zeile trifft zu."
    kopf = f"{len(zeilen)} Zeile(n)" + (f", weitere vorhanden (limit {limit})" if mehr else "") + ":"
    return _ausgabe(zeilen, kopf)


if not NUR_LESEN:
    @server.tool()
    def ausfuehren(sql: str, begruendung: str) -> str:
        """Fuehrt aendernde SQL aus (INSERT, UPDATE, DELETE, DDL, Funktionsaufrufe
        wie SELECT burgermetrics.uebernahme_aus_wawi()). Betreiberwerkzeug.

        Eine Transaktion je Aufruf: mehrere Anweisungen, durch Semikolon
        getrennt, gelten alle oder keine. Commit nur, wenn keine fehlschlaegt.

        sql          Die Anweisung(en).
        begruendung  Ein Satz, warum. Wird nicht gespeichert, zwingt aber
                     den Aufrufer, es zu benennen.
        """
        sql = sql.strip()
        if not sql:
            return "Leere Anweisung."
        if not begruendung.strip():
            return "Ohne Begruendung wird nichts ausgefuehrt."
        try:
            con = _verbindung(schreibend=True)
            try:
                with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(sql)
                    zeilen = [dict(z) for z in cur.fetchmany(MAX_ZEILEN)] if cur.description else []
                    status = cur.statusmessage
                con.commit()
            except Exception:
                con.rollback()
                raise
            finally:
                con.close()
        except Exception as fehler:                   # noqa: BLE001
            return "Zurueckgerollt. " + _fehler(fehler)
        kopf = f"Ausgefuehrt und bestaetigt ({status})."
        if zeilen:
            return _ausgabe(zeilen, kopf + f" {len(zeilen)} Zeile(n):")
        return kopf


# ─────────────────────────────────────────────────────── Selbsttest
def _selbsttest() -> int:
    """Verbindet sich, liest je eine Zeile aus beiden Schemata, prueft,
    dass Schreiben scheitert, zaehlt die Werkzeuge."""
    print(f"Verbindung als {BENUTZER} zu {HOST}:{PORT}/{DATENBANK}")
    try:
        z = _lesen("SELECT current_user, current_setting('search_path') AS sp")[0]
    except Exception as fehler:                       # noqa: BLE001
        print(f"  FEHLER  {_fehler(fehler)}")
        return 1
    print(f"  ok      angemeldet als {z['current_user']}, Suchpfad {z['sp']}")
    for schema, tabelle in (("wawi", "artikel"), ("burgermetrics", "fact_orders")):
        try:
            n = _lesen(f"SELECT count(*) AS n FROM {schema}.{tabelle}")[0]["n"]
            print(f"  ok      {schema}.{tabelle}: {n:,} Zeilen".replace(",", "."))
        except Exception as fehler:                   # noqa: BLE001
            print(f"  FEHLER  {schema}.{tabelle}: {_fehler(fehler)}")
            print("          Stimmen die Zugangsdaten in .env?")
            return 1
    antwort = abfragen("INSERT INTO wawi.zahlungsart SELECT * FROM wawi.zahlungsart LIMIT 0")
    if "liest nur" not in antwort:
        print(f"  FEHLER  abfragen() hat Schreiben nicht abgewiesen: {antwort}")
        return 1
    print("  ok      abfragen() weist Schreiben ab")
    print(f"  ok      Schreibweg ausfuehren(): {'abgeschaltet (BM_MCP_NUR_LESEN)' if NUR_LESEN else 'vorhanden'}")
    import asyncio
    werkzeuge = asyncio.run(server.list_tools())
    print(f"  ok      {len(werkzeuge)} Werkzeuge angemeldet: "
          + ", ".join(w.name for w in werkzeuge))
    return 0


if __name__ == "__main__":
    if "--pruefen" in sys.argv:
        raise SystemExit(_selbsttest())
    server.run("stdio")
