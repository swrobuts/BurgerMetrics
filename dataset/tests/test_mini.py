# dataset/tests/test_mini.py
from pathlib import Path

import duckdb
import pytest

BASIS = Path(__file__).resolve().parent.parent
ZIELE = ["dim_product", "dim_branch", "dim_customer", "dim_payment_method", "dim_promotion",
         "dim_date", "fact_orders", "fact_order_items", "fact_reviews"]


@pytest.fixture(scope="module")
def con():
    """Lädt wawi_mini, baut die Sichten, lädt burgermetrics_mini daneben."""
    c = duckdb.connect()
    for datei in ["wawi_mini.sql", "wawi_zu_analytisch.sql", "burgermetrics_mini.sql"]:
        c.execute((BASIS / datei).read_text(encoding="utf-8"))
    return c


def test_zwoelf_rezensionen(con):
    assert con.execute("SELECT count(*) FROM rezension").fetchone()[0] == 12
    assert con.execute("SELECT count(*) FROM fact_reviews").fetchone()[0] == 12


@pytest.mark.parametrize("ziel", ZIELE)
def test_zeilengleich(con, ziel):
    n = con.execute(f"""
        SELECT count(*) FROM (
          (SELECT * FROM {ziel}_neu EXCEPT SELECT * FROM {ziel})
          UNION ALL
          (SELECT * FROM {ziel} EXCEPT SELECT * FROM {ziel}_neu)) t""").fetchone()[0]
    assert n == 0, ziel


def test_rezensionen_haengen_an_mini_bestellungen(con):
    fehlend = con.execute("""
        SELECT count(*) FROM fact_reviews r
        WHERE NOT EXISTS (SELECT 1 FROM fact_orders o WHERE o.order_id = r.order_id)
           OR NOT EXISTS (SELECT 1 FROM dim_product p WHERE p.product_id = r.product_id)
           OR NOT EXISTS (SELECT 1 FROM dim_date d WHERE d.date = r.date)""").fetchone()[0]
    assert fehlend == 0
