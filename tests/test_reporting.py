"""Tests for src.reporting — KPI summary generation.

Uses the canonical sample dataset documented in README.md so that the
README example and the code stay locked together.
"""
import pandas as pd

from src.data_cleaning import clean_order_data
from src.reporting import generate_basic_report


CANONICAL_SAMPLE = (
    "Order ID,order_date,Customer Name,Product,Quantity,unit_price,Total Amount,Status\n"
    "1001,2026-02-01,Acme Pty Ltd,Cable Joint,10,12.5,125,Completed\n"
    "1002,01/02/2026,Blue Mountain Trading,Heat Shrink Tube,5,8.0,40,Completed\n"
    "1003,2026/02/03,,Heat Shrink Tube,3,8.0,24,Pending\n"
    "1004,2026-02-04,Sydney Wholesale,Cable Joint,,12.5,,Completed\n"
    "1005,04-02-2026,Acme Pty Ltd,Cable Joint,2,12.5,25,Cancelled\n"
    "1006,2026-02-05,North Shore Supplies,Heat Shrink Tube,1,8.0,8,Completed\n"
)


def _run_pipeline(tmp_path):
    raw = tmp_path / "orders.csv"
    cleaned = tmp_path / "cleaned.csv"
    summary = tmp_path / "summary.csv"
    raw.write_text(CANONICAL_SAMPLE)
    clean_order_data(str(raw), str(cleaned))
    generate_basic_report(str(cleaned), str(summary))
    return pd.read_csv(summary).set_index("metric")["value"]


def test_total_orders_counts_every_row_regardless_of_status(tmp_path):
    metrics = _run_pipeline(tmp_path)
    # 6 rows total: 4 Completed, 1 Pending, 1 Cancelled
    assert metrics["total_orders"] == 6


def test_completed_revenue_excludes_pending_and_cancelled(tmp_path):
    metrics = _run_pipeline(tmp_path)
    # Only Completed rows count:
    #   1001: 10 × 12.5 = 125
    #   1002:  5 × 8.0  =  40
    #   1004: (missing qty → 0)
    #   1006:  1 × 8.0  =   8
    # ---------------------------
    # Total:              = 173
    # Pending (1003 → 24) and Cancelled (1005 → 25) are excluded.
    assert metrics["completed_revenue"] == 173.0
