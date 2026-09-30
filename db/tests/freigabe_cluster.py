"""Baut auf einer lokalen Wegwerf-Instanz eine Datenbank mit wawi bis 0023 auf.

Gebraucht von db/tests/test_rezension_freigabe.py und vom Integrationstest
des Prüfdienstes (Phase D). Nur Schemata, Rollen und wenige Stammdaten;
kein Supabase, keine Anwendungsdaten.
"""
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[2]
AUFBAU = ROOT / "db" / "aufbau"

# Nachbau dessen, was 0023 von Supabase braucht. auth.uid() entspricht der
# Definition auf supabase.butscher.cloud (Stand 30.09.2026).
AUTH = """
CREATE SCHEMA auth;
CREATE TABLE auth.users (id uuid PRIMARY KEY);
CREATE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE AS $$
  SELECT coalesce(
    nullif(current_setting('request.jwt.claim.sub', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
  )::uuid
$$;
"""

# Nur die Spalten, auf die 0018 und 0021 mit Fremdschlüsseln und Sichten zeigen.
BURGERMETRICS = """
CREATE SCHEMA burgermetrics;
CREATE TABLE burgermetrics.dim_date (date_id bigint, date date PRIMARY KEY);
CREATE TABLE burgermetrics.dim_customer (customer_id bigint PRIMARY KEY);
CREATE TABLE burgermetrics.dim_product (product_id bigint PRIMARY KEY, product_name text, category text);
CREATE TABLE burgermetrics.dim_branch (branch_id bigint PRIMARY KEY);
CREATE TABLE burgermetrics.fact_orders (order_id bigint PRIMARY KEY);
CREATE FUNCTION burgermetrics.kurzname(text) RETURNS text LANGUAGE sql AS 'SELECT $1';
CREATE SCHEMA net;
CREATE TABLE net.http_request_queue (url text);
CREATE TABLE net._http_response (content text);
"""

STAMMDATEN = """
INSERT INTO wawi.filiale (filiale_id, name) VALUES (1, 'Test');
INSERT INTO wawi.zahlungsart (zahlungsart_id, bezeichnung) VALUES (1, 'Test');
INSERT INTO wawi.artikelkategorie (kategorie_id, name) VALUES (1, 'Test');
INSERT INTO wawi.artikelunterkategorie (unterkategorie_id, name, kategorie_id) VALUES (1, 'Test', 1);
INSERT INTO wawi.artikel (artikel_id, name, unterkategorie_id, listenpreis) VALUES (1, 'Test', 1, 5);
"""

# Rollen gelten für den ganzen Cluster; die Sicherheitstests legen sie
# vielleicht schon an.
ROLLEN = """
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN CREATE ROLE anon; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN CREATE ROLE authenticated; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'studi') THEN CREATE ROLE studi; END IF;
END $$;
"""


def datenbank_aufbauen(dsn, name):
    """Legt die Datenbank name neu an, spielt 0016 bis 0023 ein und gibt eine offene Verbindung zurück."""
    params = psycopg2.extensions.parse_dsn(dsn)
    assert params["host"] == "localhost", "nur eine lokale Wegwerf-Instanz verwenden"
    verwaltung = psycopg2.connect(dsn)
    verwaltung.autocommit = True
    with verwaltung.cursor() as cur:
        cur.execute(f'DROP DATABASE IF EXISTS "{name}"')
        cur.execute(f'CREATE DATABASE "{name}"')
        cur.execute(ROLLEN)
    verwaltung.close()
    con = psycopg2.connect(**dict(params, dbname=name))
    with con.cursor() as cur:
        cur.execute(AUTH)
        cur.execute(BURGERMETRICS)
        ddl = (AUFBAU / "0016_wawi_schema.sql").read_text().split("INSERT INTO filialtyp", 1)[0]
        cur.execute(ddl)
        cur.execute(STAMMDATEN)
        cur.execute((AUFBAU / "0018_wawi_sichten_und_schreiben.sql").read_text())
        cur.execute((AUFBAU / "0020_demo_rolle.sql").read_text())
        # db/betrieb/studi_daba_lesend.sql läuft nur in der Datenbank postgres
        # (Schutz im Skript) und gehört nicht hierher; 0023 setzt die Rechte
        # seiner Objekte selbst.
        # 0021 legt Funktionen an, deren Tabellen hier fehlen (0019). Ihr Rumpf
        # wird sonst beim Anlegen geprüft; aufgerufen werden sie hier nicht.
        cur.execute("SET check_function_bodies = off")
        cur.execute((AUFBAU / "0021_rezensionen.sql").read_text())
        cur.execute("RESET check_function_bodies")
        migration = (AUFBAU / "0023_rezension_freigabe.sql").read_text()
        cur.execute(migration)
        cur.execute(migration)  # wiederholbar
    con.commit()
    return con
