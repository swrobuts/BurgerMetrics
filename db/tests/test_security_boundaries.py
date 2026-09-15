"""Real PostgreSQL integration tests; ONLY use a disposable local cluster.

BM_SECURITY_TEST_DSN: superuser connection to an empty database named postgres.
BM_SECURITY_TEST_CA: CA for that server, whose certificate names localhost only.
The fixture creates schemas and roles and truncates its synthetic orders.
See db/tests/README.md for setup. No application endpoint is contacted.
"""
import importlib.util
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
import threading

import psycopg2
import pytest

ROOT = Path(__file__).resolve().parents[2]
SIGNATURE = "wawi.bestellung_anlegen(bigint,bigint,text,jsonb,text,text,bigint,bigint,numeric,numeric)"
CALL = "SELECT wawi.bestellung_anlegen(1,1,'Counter','[{\"artikel_id\":1,\"menge\":2}]','shop',%s)"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def cluster():
    dsn = os.environ.get("BM_SECURITY_TEST_DSN")
    ca = os.environ.get("BM_SECURITY_TEST_CA")
    if not dsn or not ca:
        pytest.skip("disposable local PostgreSQL and BM_SECURITY_TEST_CA required")
    params = psycopg2.extensions.parse_dsn(dsn)
    assert params["host"] == "localhost" and params["dbname"] == "postgres"
    con = psycopg2.connect(dsn)
    with con.cursor() as cur:
        cur.execute("SELECT to_regnamespace('wawi'), to_regnamespace('burgermetrics')")
        assert cur.fetchone() == (None, None), "Use an EMPTY disposable cluster"
        cur.execute("CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE studi;")
        cur.execute("CREATE SCHEMA burgermetrics; CREATE TABLE burgermetrics.fact_orders(order_id bigint);")
        cur.execute("CREATE FUNCTION burgermetrics.kurzname(text) RETURNS text LANGUAGE sql AS 'SELECT $1';")
        # Production DDL, with tiny synthetic master data instead of CSV imports.
        ddl = (ROOT / "db/aufbau/0016_wawi_schema.sql").read_text().split("INSERT INTO filialtyp", 1)[0]
        cur.execute(ddl)
        cur.execute("""
            INSERT INTO wawi.filiale(filiale_id,name) VALUES(1,'Test');
            INSERT INTO wawi.zahlungsart(zahlungsart_id,bezeichnung) VALUES(1,'Test');
            INSERT INTO wawi.artikelkategorie(kategorie_id,name) VALUES(1,'Test');
            INSERT INTO wawi.artikelunterkategorie(unterkategorie_id,name,kategorie_id) VALUES(1,'Test',1);
            INSERT INTO wawi.artikel(artikel_id,name,unterkategorie_id,listenpreis) VALUES(1,'Test',1,5);
            CREATE SCHEMA net;
            CREATE TABLE net.http_request_queue(url text);
            CREATE TABLE net._http_response(content text);
        """)
        cur.execute((ROOT / "db/aufbau/0018_wawi_sichten_und_schreiben.sql").read_text())
        cur.execute((ROOT / "db/aufbau/0020_demo_rolle.sql").read_text())
        cur.execute((ROOT / "db/betrieb/studi_daba_lesend.sql").read_text())
    con.commit()
    con.close()
    yield params, ca


@pytest.fixture
def environment(cluster, monkeypatch):
    params, ca = cluster
    for key in ("host", "port", "dbname", "user", "password"):
        monkeypatch.setenv("PGDATABASE" if key == "dbname" else "PG" + key.upper(), params[key])
    monkeypatch.setenv("PGSSLROOTCERT", ca)
    # An insecure ambient setting must NOT override production policy.
    monkeypatch.setenv("PGSSLMODE", "disable")
    monkeypatch.setenv("BM_MCP_READ_USER", "studi_daba")
    monkeypatch.setenv("BM_MCP_READ_PASSWORD", "thws")
    monkeypatch.setenv("BM_MCP_NUR_LESEN", "0")
    return params


@pytest.fixture
def orders(cluster, request):
    con = psycopg2.connect(**cluster[0])
    migration = ROOT / "db/aufbau/0022_bestellquote.sql"
    # Same tests cover fresh setup (0018) and an upgraded installation (0022).
    path = migration if getattr(request, "param", "upgrade") == "upgrade" else ROOT / "db/aufbau/0018_wawi_sichten_und_schreiben.sql"
    with con.cursor() as cur:
        cur.execute(path.read_text())
        cur.execute(path.read_text())  # idempotence
        cur.execute("TRUNCATE wawi.kundenbestellung CASCADE")
    con.commit()
    yield con
    con.close()


def seed(con, n, session=None, source="shop"):
    with con.cursor() as cur:
        cur.execute("""INSERT INTO wawi.kundenbestellung
            (bestelldatum,bestellzeit,filiale_id,zahlungsart_id,bestellkanal,
             artikel_anzahl,brutto_gesamt,netto_gesamt,quelle,sitzung)
            SELECT current_date,localtime,1,1,'Counter',1,5,5,%s,%s FROM generate_series(1,%s)""", (source, session, n))
    con.commit()


def order(con, session, role="anon"):
    with con.cursor() as cur:
        cur.execute(f"SET LOCAL ROLE {role}")
        cur.execute(CALL, (session,))
        result = cur.fetchone()[0]
    con.commit()
    return result


@pytest.mark.parametrize("orders", ["initial", "upgrade"], indirect=True)
@pytest.mark.parametrize("session", [None, "group"])
def test_session_quota_including_null(orders, session):
    seed(orders, 59, session)
    assert order(orders, session)["netto_gesamt"] == 10
    with pytest.raises(psycopg2.errors.ConfigurationLimitExceeded):
        order(orders, session)
    orders.rollback()


@pytest.mark.parametrize("orders", ["initial", "upgrade"], indirect=True)
def test_rotating_sessions_hit_global_limit(orders):
    seed(orders, 599, "other")
    order(orders, "fresh-1")
    with pytest.raises(psycopg2.errors.ConfigurationLimitExceeded):
        order(orders, "fresh-2")
    orders.rollback()


def test_history_excluded_and_invoice_atomic(orders):
    seed(orders, 601, None, "bestand")
    result = order(orders, None, "authenticated")
    with orders.cursor() as cur:
        cur.execute("SELECT menge,positionsbetrag,zahlbetrag FROM wawi.bestellposition JOIN wawi.rechnung USING(bestellung_id) WHERE bestellung_id=%s", (result["bestellung_id"],))
        assert cur.fetchone() == (2, 10, 10)
        cur.execute("SELECT has_function_privilege('studi_daba',%s,'EXECUTE')", (SIGNATURE,))
        assert cur.fetchone()[0] is False


def test_stale_snapshot_rejected(orders):
    orders.set_session(isolation_level="REPEATABLE READ")
    with pytest.raises(psycopg2.errors.InvalidTransactionState):
        order(orders, "fresh")
    orders.rollback()


def test_session_length_bound(orders):
    with pytest.raises(psycopg2.errors.InvalidParameterValue):
        order(orders, "x" * 101)
    orders.rollback()


def test_concurrent_last_slot(cluster, orders):
    seed(orders, 599, "other")
    barrier = threading.Barrier(8)
    def attempt(i):
        con = psycopg2.connect(**cluster[0])
        try:
            barrier.wait(timeout=10)
            order(con, f"parallel-{i}")
            return True
        except psycopg2.errors.ConfigurationLimitExceeded:
            return False
        finally:
            con.close()
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(8))) == 1


@pytest.mark.parametrize("readonly", ["0", "1"])
@pytest.mark.parametrize("sql", [
    "COMMIT; BEGIN READ WRITE; UPDATE burgermetrics.fact_orders SET order_id=42; COMMIT",
    "SET TRANSACTION READ WRITE; UPDATE burgermetrics.fact_orders SET order_id=42",
    "COMMIT; BEGIN READ WRITE; RESET ROLE; CREATE TABLE wawi.forbidden(id integer)",
    "COMMIT; BEGIN READ WRITE; SET ROLE postgres; SELECT 1",
    "COMMIT; BEGIN READ WRITE; SELECT wawi.bestellung_anlegen(1,1,'Counter','[{\"artikel_id\":1,\"menge\":1}]','shop')",
])
def test_mcp_transaction_escape_denied(environment, monkeypatch, readonly, sql):
    monkeypatch.setenv("BM_MCP_NUR_LESEN", readonly)
    module = load_module("mcp/server.py", "bm_mcp")
    result = module.abfragen(sql)
    assert "permission denied" in result, result


def test_mcp_select_and_operator_write(environment):
    module = load_module("mcp/server.py", "bm_mcp")
    assert '"value": 42' in module.abfragen("WITH x AS (SELECT 42 AS value) SELECT * FROM x")
    assert "QUERY PLAN" in module.abfragen("EXPLAIN SELECT * FROM wawi.artikel")
    assert "studi_daba" in module.abfragen("SELECT session_user,current_user")
    assert "bestaetigt" in module.ausfuehren("UPDATE burgermetrics.fact_orders SET order_id=order_id", "Integrationstest")


def test_operator_identity_rejected_for_reads(environment, monkeypatch):
    monkeypatch.setenv("BM_MCP_READ_USER", environment["user"])
    monkeypatch.setenv("BM_MCP_READ_PASSWORD", environment["password"])
    module = load_module("mcp/server.py", "bm_mcp")
    with pytest.raises(ValueError, match="studi_daba"):
        module._verbindung()


@pytest.mark.parametrize("path", ["mcp/server.py", "db/skript_ausfuehren.py", "db/materialisieren.py", "db/lade_csv.py"])
@pytest.mark.parametrize("trusted", [True, False])
def test_connection_requires_verified_tls(environment, monkeypatch, path, trusted):
    if not trusted:
        # Server cert contains localhost only; connecting by IP must fail.
        monkeypatch.setenv("PGHOST", "127.0.0.1")
    if path == "db/lade_csv.py":
        proc = subprocess.run([sys.executable, str(ROOT / path), "--nur", "fact_reviews"], capture_output=True, text=True)
        output = proc.stdout + proc.stderr
        if trusted:
            assert "Tabelle(n) fehlen noch" in output, output  # reached DB catalog, before any import
        else:
            assert "does not match host name" in output, output
    else:
        module = load_module(path, "bm_connection")
        connect = module._verbindung if path.startswith("mcp/") else module.verbinde
        if trusted:
            con = connect()
            try:
                assert con.info.ssl_in_use
            finally:
                con.close()
        else:
            with pytest.raises(psycopg2.OperationalError, match="does not match host name"):
                connect()


def test_existing_acl_regressions(cluster):
    env = dict(os.environ, BM_READONLY_TEST_DSN=psycopg2.extensions.make_dsn(**cluster[0]))
    proc = subprocess.run([sys.executable, "-m", "pytest", str(ROOT / "db/tests/test_studi_daba_lesend.py"), "-q"], env=env, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
