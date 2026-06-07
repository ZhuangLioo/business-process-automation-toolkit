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


def test_data_quality_metrics_count_invalid_and_missing_values(tmp_path):
    metrics = _run_pipeline(tmp_path)
    # On the canonical sample:
    #   - All 6 dates parse cleanly via the mixed-format router
    #   - Row 1003 has no customer name
    #   - Row 1004 has no quantity
    #   - All quantity / unit_price values are valid numbers
    assert metrics["invalid_order_date_count"] == 0
    assert metrics["missing_customer_name_count"] == 1
    assert metrics["missing_quantity_count"] == 1
    assert metrics["invalid_quantity_count"] == 0
    assert metrics["invalid_unit_price_count"] == 0


def test_invalid_dates_are_counted_in_data_quality_metrics(tmp_path):
    # Replaces the canonical sample with one row that has a bad date —
    # without this test, invalid_order_date_count is only ever proved to
    # produce 0, not to actually increment when the data is dirty.
    bad_dates = (
        "Order ID,order_date,Customer Name,Product,Quantity,unit_price,Total Amount,Status\n"
        "1001,2026-02-01,Acme,Cable Joint,10,12.5,125,Completed\n"
        "1002,not-a-date,Acme,Cable Joint,5,12.5,62.5,Completed\n"
    )
    raw = tmp_path / "orders.csv"
    cleaned = tmp_path / "cleaned.csv"
    summary = tmp_path / "summary.csv"
    raw.write_text(bad_dates)
    clean_order_data(str(raw), str(cleaned))
    generate_basic_report(str(cleaned), str(summary))

    metrics = pd.read_csv(summary).set_index("metric")["value"]
    assert metrics["invalid_order_date_count"] == 1


def test_dirty_numeric_values_are_parsed_or_counted_as_invalid(tmp_path):
    # Real Excel exports contain "$12.50", "1,200", whitespace, and "N/A".
    # Values that can be cleaned must contribute to revenue; values that
    # genuinely can't be parsed must be surfaced as invalid_*_count.
    dirty_numbers = (
        "Order ID,order_date,Customer Name,Product,Quantity,unit_price,Total Amount,Status\n"
        "1001,2026-02-01,Acme,A,10,\"$12.50\",125,Completed\n"      # parseable currency
        "1002,2026-02-02,Acme,A,\"1,000\",8,8000,Completed\n"        # comma thousands
        "1003,2026-02-03,Acme,A,abc,8,,Completed\n"                  # invalid quantity
        "1004,2026-02-04,Acme,A,5,xyz,,Completed\n"                  # invalid unit_price
    )
    raw = tmp_path / "orders.csv"
    cleaned = tmp_path / "cleaned.csv"
    summary = tmp_path / "summary.csv"
    raw.write_text(dirty_numbers)
    clean_order_data(str(raw), str(cleaned))
    generate_basic_report(str(cleaned), str(summary))

    metrics = pd.read_csv(summary).set_index("metric")["value"]
    # Row 1001: 10 × 12.50  =  125
    # Row 1002: 1000 × 8    = 8000
    # Rows 1003, 1004:        unparseable operand → contributes 0 to revenue
    # ---------------------------------------------------------------------
    # Total                 = 8125
    assert metrics["completed_revenue"] == 8125.0
    assert metrics["invalid_quantity_count"] == 1
    assert metrics["invalid_unit_price_count"] == 1
