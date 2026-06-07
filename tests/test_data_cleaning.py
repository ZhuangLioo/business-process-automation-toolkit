"""Tests for src.data_cleaning — column normalisation and date parsing."""
import pandas as pd

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
