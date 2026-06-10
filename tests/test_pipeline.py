"""Unit tests for the pipeline's pure transformation helpers.

These run without the warehouse or any file download, so they're fast and CI-friendly.
They cover the parts most likely to break silently: header normalization, type coercion
(especially the float-to-string customer id), and exact-duplicate removal.
"""
import pandas as pd

from pipeline.load import coerce_types, dedupe, normalize_columns


def test_normalize_columns_maps_header_variants():
    df = pd.DataFrame(
        columns=["InvoiceNo", "StockCode", "UnitPrice", "Customer ID", "Quantity", "InvoiceDate", "Country"]
    )
    cols = set(normalize_columns(df).columns)
    assert {"invoice", "stock_code", "price", "customer_id", "quantity", "invoice_date", "country"} <= cols


def test_coerce_types_cleans_customer_id_and_numbers():
    df = pd.DataFrame(
        {
            "invoice": ["536365", "C536379"],
            "stock_code": ["85123A", "71053"],
            "description": ["white hanging heart", "white metal lantern"],
            "country": ["United Kingdom", "France"],
            "quantity": ["6", "-2"],
            "price": ["2.55", "3.0"],
            "invoice_date": ["2010-12-01 08:26:00", "2010-12-01 09:00:00"],
            "customer_id": [17850.0, None],  # float in, clean string / None out
        }
    )
    out = coerce_types(df)
    assert out["customer_id"].iloc[0] == "17850"   # float 17850.0 -> clean "17850"
    assert pd.isna(out["customer_id"].iloc[1])      # missing id -> NA (becomes SQL NULL)
    assert out["quantity"].tolist() == [6, -2]
    assert out["price"].tolist() == [2.55, 3.0]
    assert str(out["invoice_date"].dtype).startswith("datetime")


def test_dedupe_removes_exact_duplicates_only():
    base = {
        "invoice": "1", "stock_code": "A", "quantity": 1, "price": 1.0,
        "invoice_date": "2011-01-01", "customer_id": "5", "description": "d", "country": "UK",
    }
    df = pd.DataFrame([base, dict(base), {**base, "quantity": 2}])
    out = dedupe(df)
    assert len(out) == 2  # the exact dup is dropped, the different-quantity row is kept
