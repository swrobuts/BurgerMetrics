"""Fehler während DROP/CREATE oder REFRESH dürfen keinen Teilstand bestätigen."""
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

spec = importlib.util.spec_from_file_location('materialisieren', Path(__file__).parents[1] / 'materialisieren.py')
modul = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modul)


@pytest.mark.parametrize('neu', [False, True])
@pytest.mark.parametrize('scheitert', [False, True])
def test_ein_lauf_ist_eine_transaktion(monkeypatch, neu, scheitert):
    con = MagicMock()
    cur = con.cursor.return_value
    cur.__enter__.return_value = cur
    monkeypatch.setattr(modul, 'verbinde', lambda: con)
    monkeypatch.setattr(modul, 'objekte', lambda _: {'v_a': 'm', 'v_b': 'm'})
    monkeypatch.setattr(modul, 'abhaengigkeiten', lambda *_: [('v_b', 'v_a')])
    monkeypatch.setattr(modul, 'sichern', lambda *_: {'v_a': ('SELECT 1', None), 'v_b': ('SELECT * FROM burgermetrics.v_a', None)})
    monkeypatch.setattr(sys, 'argv', ['materialisieren.py'] + (['--neu'] if neu else []))

    def ausfuehren(sql, *args):
        if scheitert and sql.startswith(('CREATE MATERIALIZED VIEW burgermetrics.v_b',
                                        'REFRESH MATERIALIZED VIEW burgermetrics.v_b')):
            raise RuntimeError('Abbruch beim zweiten Objekt')

    cur.execute.side_effect = ausfuehren
    if scheitert:
        with pytest.raises(RuntimeError, match='zweiten Objekt'):
            modul.main()
        con.rollback.assert_called_once()
        con.commit.assert_not_called()
    else:
        modul.main()
        con.commit.assert_called_once()
        con.rollback.assert_not_called()
    assert con.autocommit is False
    con.close.assert_called_once()
