#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""materialisieren.py — die Sichten der Semantikschicht als Tabellen ablegen.

Warum das noetig wurde: Einzeln braucht keine Sicht mehr als eine Sekunde. Das
Dashboard fragt aber 33 auf einmal ab, und die Rolle anon hat eine Zeitgrenze
von drei Sekunden. Unter der Parallellast saettigen sich die Kerne der Maschine,
jede Abfrage wartet auf die anderen, und zwei laufen in die Grenze. Lokal fiel
das nicht auf — dort war der Server derselbe, aber die Latenz kleiner und die
Anfragen kamen weniger dicht.

Materialisiert dauert dieselbe Abfrage rund 20 Millisekunden, weil sie eine
kleine Tabelle liest statt Millionen Zeilen zu aggregieren. Genau dafuer ist
eine Mart-Schicht da: Die Sicht ist die Definition, die materialisierte Fassung
ist das Ergebnis.

Der Preis: Die Werte sind so alt wie der letzte Lauf. Fuer diesen Bestand ist
das folgenlos — er aendert sich nicht. In einem Betrieb liefe dieses Skript
nach dem naechtlichen Abzug.

    python3 materialisieren.py            # umwandeln und fuellen
    python3 materialisieren.py --neu      # nur auffrischen, ohne Umbau

Die Reihenfolge ergibt sich aus den Abhaengigkeiten, nicht aus einer Liste im
Kopf: v_rfm_segment liest v_rfm_kunde, v_promotion_roi liest v_promotion.
Deshalb wird sie aus pg_depend berechnet.
"""
import argparse
import os
import sys
from pathlib import Path

import psycopg2

SCHEMA = "burgermetrics"


def lade_env():
    """Liest .env im Projektstamm, ohne die Shell zu bemuehen."""
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for zeile in env.read_text().splitlines():
            zeile = zeile.strip()
            if zeile and not zeile.startswith("#") and "=" in zeile:
                k, _, v = zeile.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def verbinde():
    lade_env()
    return psycopg2.connect(
        host=os.environ["PGHOST"], port=os.environ["PGPORT"],
        dbname=os.environ["PGDATABASE"], user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"], connect_timeout=30)


def objekte(cur):
    """Alle Sichten und materialisierten Sichten des Schemas mit ihrer Art."""
    cur.execute("""
        SELECT c.relname, c.relkind
        FROM   pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE  n.nspname = %s AND c.relkind IN ('v', 'm')
        ORDER  BY c.relname""", (SCHEMA,))
    return dict(cur.fetchall())


def abhaengigkeiten(cur, namen):
    """Wer liest wen — als Kantenliste ueber pg_depend."""
    cur.execute("""
        SELECT DISTINCT abh.relname AS kind, quelle.relname AS eltern
        FROM   pg_depend d
        JOIN   pg_rewrite r      ON r.oid = d.objid
        JOIN   pg_class   abh    ON abh.oid = r.ev_class
        JOIN   pg_class   quelle ON quelle.oid = d.refobjid
        JOIN   pg_namespace n1   ON n1.oid = abh.relnamespace
        JOIN   pg_namespace n2   ON n2.oid = quelle.relnamespace
        WHERE  n1.nspname = %s AND n2.nspname = %s
          AND  abh.relname <> quelle.relname
          AND  quelle.relkind IN ('v', 'm')""", (SCHEMA, SCHEMA))
    kanten = [(k, e) for k, e in cur.fetchall() if k in namen and e in namen]
    return kanten


def reihenfolge(namen, kanten):
    """Topologisch: Eltern vor Kindern. Zyklen gibt es hier nicht."""
    offen, fertig = set(namen), []
    eltern_von = {n: set() for n in namen}
    for kind, eltern in kanten:
        eltern_von[kind].add(eltern)
    while offen:
        frei = sorted(n for n in offen if not (eltern_von[n] & offen))
        if not frei:
            sys.exit(f"FEHLER: Abhaengigkeitszyklus bei {sorted(offen)}")
        fertig.extend(frei)
        offen -= set(frei)
    return fertig


def sichern(cur, namen):
    """Definition und Kommentar aller Objekte einsammeln, bevor etwas faellt."""
    stand = {}
    for name in namen:
        cur.execute("SELECT pg_get_viewdef(%s::regclass, true)", (f"{SCHEMA}.{name}",))
        definition = cur.fetchone()[0].rstrip().rstrip(";")
        cur.execute("SELECT obj_description(%s::regclass, 'pg_class')",
                    (f"{SCHEMA}.{name}",))
        stand[name] = (definition, cur.fetchone()[0])
    return stand


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--neu", action="store_true",
                    help="nur auffrischen, nichts umbauen")
    args = ap.parse_args()

    c = verbinde()
    c.autocommit = True
    cur = c.cursor()

    art = objekte(cur)
    namen = sorted(art)
    folge = reihenfolge(namen, abhaengigkeiten(cur, set(namen)))

    if args.neu:
        print(f"  {sum(1 for n in folge if art[n] == 'm')} materialisierte Sichten\n")
        for name in folge:
            if art[name] != "m":
                continue
            cur.execute(f"REFRESH MATERIALIZED VIEW {SCHEMA}.{name}")
            print(f"    {name:<30}aufgefrischt")
    else:
        # Erst alles sichern, dann von den Kindern her abraeumen, dann von den
        # Eltern her neu anlegen. Einzeln geht es nicht: Eine materialisierte
        # Sicht haelt ihre Abhaengigkeit auch dann, wenn ihre Definition
        # eingefroren ist.
        print(f"  {len(folge)} Objekte im Schema {SCHEMA}\n")
        stand = sichern(cur, folge)
        for name in reversed(folge):
            cur.execute(f"DROP {'MATERIALIZED VIEW' if art[name] == 'm' else 'VIEW'} "
                        f"{SCHEMA}.{name}")
        print(f"    {len(folge)} Objekte abgeraeumt")
        for name in folge:
            definition, kommentar = stand[name]
            cur.execute(f"CREATE MATERIALIZED VIEW {SCHEMA}.{name} AS {definition}")
            if kommentar:
                cur.execute(f"COMMENT ON MATERIALIZED VIEW {SCHEMA}.{name} IS %s",
                            (kommentar,))
            cur.execute(f"GRANT SELECT ON {SCHEMA}.{name} TO anon, authenticated")
            print(f"    {name:<30}materialisiert")

    # ANALYZE, damit der Planer die neuen Tabellen kennt.
    cur.execute(f"ANALYZE")
    print("\n  ANALYZE gelaufen.")
    print("  Nicht vergessen: docker compose restart rest — PostgREST liest das")
    print("  Schema nur beim Start (PGRST_DB_CHANNEL_ENABLED=false).")
    c.close()


if __name__ == "__main__":
    main()
