"""Opt-in integration: BM_READONLY_TEST_DSN must be a superuser DSN.

All DDL, ACL changes and synthetic writes are rolled back, including on error.
No application data or existing sequence values are changed.
"""
import os
from pathlib import Path

import psycopg2
import pytest


MIGRATION = Path(__file__).resolve().parents[1] / "betrieb/studi_daba_lesend.sql"


@pytest.fixture(scope="module")
def repaired():
    dsn = os.environ.get("BM_READONLY_TEST_DSN")
    if not dsn:
        pytest.skip("BM_READONLY_TEST_DSN required (superuser, always rolled back)")
    con = psycopg2.connect(dsn)
    try:
        with con.cursor() as cur:
            # A synthetic sibling path, including column-only grants and OID access.
            cur.execute("""
                CREATE SCHEMA bm_readonly_test;
                GRANT USAGE ON SCHEMA bm_readonly_test TO PUBLIC;
                CREATE TABLE bm_readonly_test.probe(value integer);
                GRANT SELECT, UPDATE(value) ON bm_readonly_test.probe TO PUBLIC;
                CREATE SEQUENCE bm_readonly_test.counter;
                GRANT USAGE, UPDATE ON SEQUENCE bm_readonly_test.counter TO PUBLIC;
                CREATE FUNCTION bm_readonly_test.write_probe() RETURNS void
                  LANGUAGE sql SECURITY DEFINER AS 'UPDATE bm_readonly_test.probe SET value=1';
                GRANT EXECUTE ON FUNCTION bm_readonly_test.write_probe() TO PUBLIC;
                SELECT 'bm_readonly_test.counter'::regclass::oid;
            """)
            seq_oid = cur.fetchone()[0]
            cur.execute("SET LOCAL ROLE studi_daba")
            cur.execute("PREPARE bm_cached_write AS SELECT bm_readonly_test.write_probe()")
            cur.execute("RESET ROLE")
            cur.execute(MIGRATION.read_text(encoding="utf-8"))
            # Re-running must not expand permissions or depend on a fresh session.
            cur.execute(MIGRATION.read_text(encoding="utf-8"))
        yield con, seq_oid
    finally:
        con.rollback()
        con.close()


@pytest.mark.parametrize("statement", [
    "UPDATE net.http_request_queue SET url=url WHERE false",
    "UPDATE net._http_response SET content=content WHERE false",
    "UPDATE burgermetrics.fact_orders SET order_id=order_id WHERE false",
    "SELECT pg_catalog.lo_create(0)",
    "SELECT pg_catalog.lo_from_bytea(0, 'x'::bytea)",
    "CREATE TEMP TABLE bm_forbidden(value integer)",
    "UPDATE bm_readonly_test.probe SET value=value WHERE false",
    "EXECUTE bm_cached_write",
])
def test_write_paths_denied_with_read_write_transaction(repaired, statement):
    con, _ = repaired
    with con.cursor() as cur:
        cur.execute("SAVEPOINT negative_probe")
        try:
            cur.execute("SET LOCAL ROLE studi_daba")
            cur.execute("SET LOCAL default_transaction_read_only=off")
            with pytest.raises(psycopg2.errors.InsufficientPrivilege):
                cur.execute(statement)
        finally:
            cur.execute("ROLLBACK TO SAVEPOINT negative_probe")
            cur.execute("RELEASE SAVEPOINT negative_probe")


def test_sequence_oid_cannot_bypass_schema_permission(repaired):
    con, seq_oid = repaired
    with con.cursor() as cur:
        cur.execute("SAVEPOINT oid_probe")
        try:
            cur.execute("SET LOCAL ROLE studi_daba")
            with pytest.raises(psycopg2.errors.InsufficientPrivilege):
                cur.execute("SELECT nextval(%s::oid::regclass)", (seq_oid,))
        finally:
            cur.execute("ROLLBACK TO SAVEPOINT oid_probe")
            cur.execute("RELEASE SAVEPOINT oid_probe")


def test_all_teaching_objects_remain_readable(repaired):
    con, _ = repaired
    with con.cursor() as cur:
        cur.execute("""SELECT format('%I.%I',n.nspname,c.relname)
            FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname IN ('burgermetrics','wawi') AND c.relkind IN ('r','p','v','m','f')""")
        objects = [r[0] for r in cur.fetchall()]
        assert objects
        cur.execute("SAVEPOINT read_probe")
        try:
            cur.execute("SET LOCAL ROLE studi_daba")
            for name in objects:
                cur.execute(f"SELECT * FROM {name} LIMIT 1")
                cur.fetchall()
            cur.execute("SELECT burgermetrics.kurzname('BurgerMetrics')")
            assert cur.fetchone()[0]
        finally:
            cur.execute("ROLLBACK TO SAVEPOINT read_probe")
            cur.execute("RELEASE SAVEPOINT read_probe")


def test_new_definer_routine_is_not_public(repaired):
    con, _ = repaired
    with con.cursor() as cur:
        cur.execute("""CREATE FUNCTION public.bm_readonly_test_future()
            RETURNS integer LANGUAGE sql SECURITY DEFINER AS 'SELECT 1'""")
        # New routines require explicit grants; the hardening script does not
        # grant future operator routines to every existing application role.
        for role, allowed in [("studi_daba", False), ("anon", False), ("authenticated", False)]:
            cur.execute("SELECT has_function_privilege(%s, 'public.bm_readonly_test_future()', 'EXECUTE')", (role,))
            assert cur.fetchone()[0] is allowed


def test_no_other_database_or_temp_access(repaired):
    con, _ = repaired
    with con.cursor() as cur:
        cur.execute("""SELECT datname FROM pg_database
            WHERE has_database_privilege('studi_daba',oid,'CREATE,TEMPORARY')
               OR (datname <> current_database() AND has_database_privilege('studi_daba',oid,'CONNECT'))""")
        assert cur.fetchall() == []


def test_recreated_operator_routine_remains_operator_only(repaired):
    con, _ = repaired
    with con.cursor() as cur:
        cur.execute("SAVEPOINT operator_probe")
        try:
            cur.execute("SET LOCAL ROLE postgres")
            cur.execute("""CREATE FUNCTION burgermetrics.bm_readonly_test_operator()
                RETURNS integer LANGUAGE sql SECURITY DEFINER AS 'SELECT 1';
                REVOKE EXECUTE ON FUNCTION burgermetrics.bm_readonly_test_operator()
                  FROM PUBLIC, anon, authenticated;""")
            # Same create/revoke lifecycle as 0019 and the ETL recreation in 0021.
            for role in ["studi", "studi_daba", "anon", "authenticated"]:
                cur.execute("SELECT has_function_privilege(%s,'burgermetrics.bm_readonly_test_operator()','EXECUTE')", (role,))
                assert cur.fetchone()[0] is False, role
        finally:
            cur.execute("ROLLBACK TO SAVEPOINT operator_probe")
            cur.execute("RELEASE SAVEPOINT operator_probe")
