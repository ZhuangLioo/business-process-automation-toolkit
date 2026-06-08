"""Per-row data quality issues report.

The summary report in reporting.py answers "how many problems are in this
batch?". This module answers the follow-up question a BA / data steward
actually asks: "which rows do I need to go fix?".
"""
from pathlib import Path
import pandas as pd


ISSUES_COLUMNS = ["row_number", "order_id", "issue_type", "column", "value", "message"]


def _is_blank(value) -> bool:
    if pd.isna(value):
        return True
    return str(value).strip() == ""


def _is_invalid_number(value) -> bool:
    # Mirrors src.reporting._to_number: strip currency / thousands separators
    # / whitespace, then try to parse. Anything that still fails is "invalid"
    # (as opposed to "missing", which _is_blank covers).
    if _is_blank(value):
        return False
    cleaned = str(value).replace("$", "").replace(",", "").replace(" ", "")
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


def generate_data_issues_report(input_path: str, output_path: str):
    print("[issues] loading cleaned data...")
    df = pd.read_csv(input_path)

    has_customer_name = "customer_name" in df.columns
    has_order_id = "order_id" in df.columns

    issues = []

    for position, row in df.reset_index(drop=True).iterrows():
        # row_number is 1-indexed counting from the first data row (i.e. matches
        # how a BA user counts orders, not Excel's header-aware row count).
        row_number = position + 1
        order_id = row["order_id"] if has_order_id else ""

        if pd.isna(row["order_date"]):
            issues.append(_issue(
                row_number, order_id, "invalid_order_date",
                "order_date", "",
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
