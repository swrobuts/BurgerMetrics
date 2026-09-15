"""Der CSV-Import bestätigt nur vollständige Daten und erhält vorhandene Arbeit."""
import importlib.util
import sys
from pathlib import Path

import duckdb
import pytest

spec = importlib.util.spec_from_file_location('load_duckdb', Path(__file__).parents[1] / 'load_duckdb.py')
loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loader)


@pytest.fixture
def datenbank(tmp_path, monkeypatch):
    ziel = tmp_path / 'bestehend.duckdb'
    with duckdb.connect(str(ziel)) as con:
        con.execute('CREATE TABLE dim_branch AS SELECT 42 AS branch_id')
        con.execute("CREATE TABLE notizen AS SELECT 'behalten' AS text")
    (tmp_path / 'dim_branch.csv').write_text('branch_id\n1\n2\n', encoding='utf-8')
    (tmp_path / 'fact_orders.csv').write_text('order_id\n1\n', encoding='utf-8')
    monkeypatch.setattr(loader, 'BASE', tmp_path)
    monkeypatch.setattr(loader, 'TABELLEN', [('dim_branch', 'dim_branch.csv'), ('fact_orders', 'fact_orders.csv')])
    monkeypatch.setattr(loader, 'SOLL', {'dim_branch': 2, 'fact_orders': 1})
    monkeypatch.setattr(sys, 'argv', ['load_duckdb.py', '--lokal', '--ausgabe', str(ziel)])
    return ziel


def test_erfolg_ersetzt_tabellen_und_erhaelt_eigene_arbeit(datenbank):
    loader.main()
    with duckdb.connect(str(datenbank)) as con:
        assert con.execute('SELECT * FROM dim_branch ORDER BY branch_id').fetchall() == [(1,), (2,)]
        assert con.execute('SELECT * FROM notizen').fetchone() == ('behalten',)


def test_falsche_zeilenzahl_bricht_ab_und_rollt_gesamten_import_zurueck(datenbank, monkeypatch):
    monkeypatch.setitem(loader.SOLL, 'fact_orders', 2)
    with pytest.raises(SystemExit, match='fact_orders'):
        loader.main()
    with duckdb.connect(str(datenbank)) as con:
        assert con.execute('SELECT * FROM dim_branch').fetchall() == [(42,)]
        assert con.execute('SELECT * FROM notizen').fetchone() == ('behalten',)


def test_lfs_pointer_wird_vor_dem_import_abgewiesen(datenbank):
    (datenbank.parent / 'fact_orders.csv').write_text('version https://git-lfs.github.com/spec/v1\n')
    with pytest.raises(SystemExit, match='Git-LFS'):
        loader.main()
    with duckdb.connect(str(datenbank)) as con:
        assert con.execute('SELECT * FROM dim_branch').fetchall() == [(42,)]
