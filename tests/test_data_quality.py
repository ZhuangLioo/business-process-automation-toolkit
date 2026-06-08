"""Tests for src.data_quality — per-row data issues export."""
import pandas as pd
import pytest

from src.data_cleaning import clean_order_data
from src.data_quality import generate_data_issues_report


CANONICAL_SAMPLE = (
    "Order ID,order_date,Customer Name,Product,Quantity,unit_price,Total Amount,Status\n"
    "1001,2026-02-01,Acme Pty Ltd,Cable Joint,10,12.5,125,Completed\n"
    "1002,01/02/2026,Blue Mountain Trading,Heat Shrink Tube,5,8.0,40,Completed\n"
    "1003,2026/02/03,,Heat Shrink Tube,3,8.0,24,Pending\n"
    "1004,2026-02-04,Sydney Wholesale,Cable Joint,,12.5,,Completed\n"
    "1005,04-02-2026,Acme Pty Ltd,Cable Joint,2,12.5,25,Cancelled\n"
    "1006,2026-02-05,North Shore Supplies,Heat Shrink Tube,1,8.0,8,Completed\n"
)


def _run(tmp_path, raw_csv):
    raw = tmp_path / "orders.csv"
    cleaned = tmp_path / "cleaned.csv"
    issues = tmp_path / "issues.csv"
    raw.write_text(raw_csv)
    clean_order_data(str(raw), str(cleaned))
    generate_data_issues_report(str(raw), str(cleaned), str(issues))
    return pd.read_csv(issues)


def test_canonical_sample_lists_missing_customer_and_missing_quantity(tmp_path):
    issues = _run(tmp_path, CANONICAL_SAMPLE)

    # Row 3 (order 1003) is missing the customer name
    cust = issues[issues["issue_type"] == "missing_customer_name"]
    assert len(cust) == 1
    assert int(cust.iloc[0]["row_number"]) == 3
    assert int(cust.iloc[0]["order_id"]) == 1003

    # Row 4 (order 1004) is missing the quantity
    qty = issues[issues["issue_type"] == "missing_quantity"]
    assert len(qty) == 1
    assert int(qty.iloc[0]["row_number"]) == 4
    assert int(qty.iloc[0]["order_id"]) == 1004


def test_clean_sample_produces_empty_issues_file_with_header(tmp_path):
    clean_csv = (
        "Order ID,order_date,Customer Name,Product,Quantity,unit_price,Status\n"
        "1001,2026-02-01,Acme,Cable,10,12.5,Completed\n"
        "1002,2026-02-02,Acme,Cable,5,8.0,Completed\n"
    )
    issues = _run(tmp_path, clean_csv)
    # No data rows, but the header still has all 6 expected columns
    assert len(issues) == 0
    assert list(issues.columns) == [
        "row_number", "order_id", "issue_type", "column", "value", "message",
    ]


def test_dirty_dates_and_numbers_emit_correct_issue_types(tmp_path):
    # Three orders, three distinct problems: bad date, bad qty, bad price.
    dirty = (
        "Order ID,order_date,Customer Name,Product,Quantity,unit_price,Status\n"
        "1001,not-a-date,Acme,Cable,10,12.5,Completed\n"
        "1002,2026-02-02,Acme,Cable,abc,12.5,Completed\n"
        "1003,2026-02-03,Acme,Cable,5,xyz,Completed\n"
    )
    issues = _run(tmp_path, dirty)
    types = set(issues["issue_type"].tolist())
    assert "invalid_order_date" in types
    assert "invalid_quantity" in types
    assert "invalid_unit_price" in types

    # The unparseable raw value is preserved in the `value` column so the BA
    # user can see exactly what the source data contained.
    bad_qty = issues[issues["issue_type"] == "invalid_quantity"].iloc[0]
    assert bad_qty["value"] == "abc"
    bad_price = issues[issues["issue_type"] == "invalid_unit_price"].iloc[0]
    assert bad_price["value"] == "xyz"


def test_row_count_mismatch_between_raw_and_cleaned_raises_clear_error(tmp_path):
    # Guards against future regressions in clean_order_data: if cleaning ever
    # starts filtering / sorting / deduplicating rows, raw-vs-cleaned position
    # alignment breaks silently and issues would be attached to the wrong row.
    # The function must refuse to run instead of producing a misleading file.
    raw_two_rows = (
        "Order ID,order_date,Customer Name,Product,Quantity,unit_price,Status\n"
        "1001,2026-02-01,Acme,Cable,10,12.5,Completed\n"
        "1002,2026-02-02,Acme,Cable,5,12.5,Completed\n"
    )
    cleaned_one_row = (
        "order_id,order_date,customer_name,product,quantity,unit_price,status\n"
        "1001,2026-02-01,Acme,Cable,10,12.5,Completed\n"
    )
    raw = tmp_path / "raw.csv"
    cleaned = tmp_path / "cleaned.csv"
    issues = tmp_path / "issues.csv"
    raw.write_text(raw_two_rows)
    cleaned.write_text(cleaned_one_row)

    with pytest.raises(ValueError) as excinfo:
        generate_data_issues_report(str(raw), str(cleaned), str(issues))

    msg = str(excinfo.value)
    assert "2" in msg and "1" in msg  # both row counts surfaced in the message


def test_invalid_date_preserves_raw_string_from_source_file(tmp_path):
    # Regression test for a real bug: cleaning converts bad dates to NaT, so
    # the cleaned CSV only has an empty cell where the bad date used to be.
    # If data_quality reads only the cleaned file, the `value` column for an
    # invalid_order_date issue becomes empty — which silently breaks the
    # README's promise that raw failing values are preserved verbatim.
    # data_quality must reach back into the raw input to recover the original
    # string so the steward knows *what* the source actually contained.
    dirty_dates = (
        "Order ID,order_date,Customer Name,Product,Quantity,unit_price,Status\n"
        "1001,2026-02-01,Acme,Cable,10,12.5,Completed\n"
        "1002,31-Feb-2026,Acme,Cable,5,12.5,Completed\n"
        "1003,tba,Acme,Cable,3,12.5,Completed\n"
    )
    issues = _run(tmp_path, dirty_dates)

    date_issues = issues[issues["issue_type"] == "invalid_order_date"]
    raw_values = set(date_issues["value"].tolist())
    # Both unparseable strings must appear verbatim in the issues file
    assert "31-Feb-2026" in raw_values
    assert "tba" in raw_values
