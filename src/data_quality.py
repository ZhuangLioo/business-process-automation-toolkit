"""Per-row data quality issues report.

The summary report in reporting.py answers "how many problems are in this
batch?". This module answers the follow-up question a BA / data steward
actually asks: "which rows do I need to go fix?".

It reads *both* the raw input and the cleaned output: the cleaned file
tells it which dates failed to parse (NaT), and the raw file holds the
original string that failed — so the issues report can show the BA user
the exact source value (e.g. "31-Feb-2026") rather than just an empty
cell, which is what they need to understand the underlying mistake.
"""
from pathlib import Path
import pandas as pd

from src.data_cleaning import NUMERIC_NOISE_PATTERN, normalise_columns


ISSUES_COLUMNS = ["row_number", "order_id", "issue_type", "column", "value", "message"]


def _is_blank(value) -> bool:
    if pd.isna(value):
        return True
    return str(value).strip() == ""


def _is_invalid_number(value) -> bool:
    # Mirrors src.reporting._to_number: strip the shared NUMERIC_NOISE_PATTERN
    # (currency / thousands / any whitespace), then try to parse. Anything that
    # still fails is "invalid" (as opposed to "missing", which _is_blank covers).
    if _is_blank(value):
        return False
    cleaned = NUMERIC_NOISE_PATTERN.sub("", str(value))
    try:
        float(cleaned)
    except ValueError:
        return True
    return False


def _issue(row_number, order_id, issue_type, column, value, message):
    return {
        "row_number": row_number,
        "order_id": order_id,
        "issue_type": issue_type,
        "column": column,
        "value": value,
        "message": message,
    }


def _raw_value(raw_df: pd.DataFrame, position: int, column: str) -> str:
    """Look up the original (pre-cleaning) cell value for a given row + column,
    returning an empty string if the column is missing or the cell is NaN."""
    if column not in raw_df.columns or position >= len(raw_df):
        return ""
    value = raw_df.iloc[position][column]
    if pd.isna(value):
        return ""
    return str(value)


def generate_data_issues_report(
    raw_input_path: str,
    cleaned_input_path: str,
    output_path: str,
):
    print("[issues] loading raw + cleaned data...")
    raw_df = pd.read_csv(raw_input_path)
    normalise_columns(raw_df)  # so raw_df["order_date"] works regardless of source casing
    cleaned_df = pd.read_csv(cleaned_input_path).reset_index(drop=True)

    # Position-alignment guard. Raw value lookup uses raw_df.iloc[position]
    # while iterating cleaned_df, which relies on the invariant that cleaning
    # preserves all rows in original order. If a future change to
    # clean_order_data() adds filtering (e.g. drop cancelled), sorting, or
    # deduplication, that invariant breaks silently — the issues file would
    # attach the wrong raw value and order_id to the wrong row. Fail fast
    # here so the bug surfaces at run time, not in a steward's triage queue.
    if len(raw_df) != len(cleaned_df):
        raise ValueError(
            f"Row count mismatch between raw input ({len(raw_df)} rows) and "
            f"cleaned output ({len(cleaned_df)} rows); cannot align raw values "
            f"to cleaned rows for issue reporting."
        )

    has_customer_name = "customer_name" in cleaned_df.columns
    has_order_id = "order_id" in cleaned_df.columns

    issues = []

    for position, row in cleaned_df.iterrows():
        # row_number is 1-indexed counting from the first data row (i.e. matches
        # how a BA user counts orders, not Excel's header-aware row count).
        row_number = position + 1
        order_id = row["order_id"] if has_order_id else ""

        if pd.isna(row["order_date"]):
            # Cleaned column is NaT — the original string was lost in cleaning.
            # Reach back into the raw input so the BA user can see what they
            # actually entered (e.g. "31-Feb-2026" or "tba").
            issues.append(_issue(
                row_number, order_id, "invalid_order_date",
                "order_date", _raw_value(raw_df, position, "order_date"),
                "Order date could not be parsed",
            ))

        if has_customer_name and _is_blank(row["customer_name"]):
            issues.append(_issue(
                row_number, order_id, "missing_customer_name",
                "customer_name", "",
                "Customer name is missing",
            ))

        if _is_blank(row["quantity"]):
            issues.append(_issue(
                row_number, order_id, "missing_quantity",
                "quantity", "",
                "Quantity is missing",
            ))
        elif _is_invalid_number(row["quantity"]):
            issues.append(_issue(
                row_number, order_id, "invalid_quantity",
                "quantity", str(row["quantity"]),
                "Quantity could not be parsed as a number",
            ))

        if _is_blank(row["unit_price"]):
            issues.append(_issue(
                row_number, order_id, "missing_unit_price",
                "unit_price", "",
                "Unit price is missing",
            ))
        elif _is_invalid_number(row["unit_price"]):
            issues.append(_issue(
                row_number, order_id, "invalid_unit_price",
                "unit_price", str(row["unit_price"]),
                "Unit price could not be parsed as a number",
            ))

    issues_df = pd.DataFrame(issues, columns=ISSUES_COLUMNS)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"[issues] writing {len(issues)} issue(s) to {output_path}")
    issues_df.to_csv(output_path, index=False)
    print("[issues] done")
