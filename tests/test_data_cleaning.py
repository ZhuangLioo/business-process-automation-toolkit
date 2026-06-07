"""Tests for src.data_cleaning — column normalisation and date parsing."""
import pandas as pd
import pytest

from src.data_cleaning import clean_order_data


SAMPLE_CSV = """Order ID,order_date,Customer Name,Product,Quantity,unit_price,Total Amount,Status
1001,2026-02-01,Acme Pty Ltd,Cable Joint,10,12.5,125,Completed
1002,01/02/2026,Blue Mountain Trading,Heat Shrink Tube,5,8.0,40,Completed
1003,04-02-2026,Sydney Wholesale,Cable Joint,2,12.5,25,Cancelled
"""


def _write_sample(tmp_path):
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "cleaned.csv"
    input_path.write_text(SAMPLE_CSV)
    return input_path, output_path


def test_column_names_are_normalised_to_snake_case(tmp_path):
    input_path, output_path = _write_sample(tmp_path)

    clean_order_data(str(input_path), str(output_path))

    cleaned = pd.read_csv(output_path)
    expected_columns = [
        "order_id",
        "order_date",
        "customer_name",
        "product",
        "quantity",
        "unit_price",
        "total_amount",
        "status",
    ]
    assert list(cleaned.columns) == expected_columns


def test_mixed_date_formats_are_normalised_to_iso(tmp_path):
    input_path, output_path = _write_sample(tmp_path)

    clean_order_data(str(input_path), str(output_path))

    cleaned = pd.read_csv(output_path)
    # All three input rows describe Feb 1–4, 2026 in different formats
    assert cleaned.loc[0, "order_date"] == "2026-02-01"
    assert cleaned.loc[1, "order_date"] == "2026-02-01"
    assert cleaned.loc[2, "order_date"] == "2026-02-04"


def test_missing_required_columns_raises_clear_error(tmp_path):
    # CSV is missing order_date, status, quantity, unit_price — only the
    # ID and customer columns are present, which a real "messy export"
    # might look like before the data team adds the right fields.
    bad_csv = "Order ID,Customer Name\n1001,Acme Pty Ltd\n"
    input_path = tmp_path / "bad.csv"
    output_path = tmp_path / "out.csv"
    input_path.write_text(bad_csv)

    with pytest.raises(ValueError) as excinfo:
        clean_order_data(str(input_path), str(output_path))

    msg = str(excinfo.value)
    # All four missing columns should be listed (alphabetical), not just the first
    assert "order_date" in msg
    assert "status" in msg
    assert "quantity" in msg
    assert "unit_price" in msg
