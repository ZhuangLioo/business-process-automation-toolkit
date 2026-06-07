from pathlib import Path
import pandas as pd


def _count_blank(series: pd.Series) -> int:
    """Count rows where the value is NaN or whitespace-only."""
    return int(series.fillna("").astype(str).str.strip().eq("").sum())


def _to_number(series: pd.Series) -> pd.Series:
    # Real-world Excel exports contain things like "$12.50", "1,200", "  ", "N/A".
    # Strip currency / thousands separators / whitespace, then coerce; anything
    # still unparseable becomes NaN so the caller can either fill or count it.
    cleaned = series.fillna("").astype(str).str.replace(r"[$,\s]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def _invalid_numeric_count(series: pd.Series) -> int:
    """Count rows that have non-blank content but still can't be parsed as a number."""
    is_blank = series.fillna("").astype(str).str.strip().eq("")
    return int((~is_blank & _to_number(series).isna()).sum())


def generate_basic_report(input_path: str, output_path: str):
    print("[report] loading cleaned data...")

    df = pd.read_csv(input_path)

    total_orders = len(df)

    status = df["status"].fillna("").astype(str).str.strip().str.lower()
    completed = df[status == "completed"]

    # Coerce dirty Excel-style numbers before multiplying. Unparseable values
    # (e.g. "abc") become NaN and are then treated as 0 for the revenue sum
    # but surfaced separately as invalid_*_count below.
    quantity = _to_number(completed["quantity"]).fillna(0)
    unit_price = _to_number(completed["unit_price"]).fillna(0)
    completed_revenue = float((quantity * unit_price).sum())

    # Data quality metrics — surface problems instead of hiding them.
    # Invalid dates were coerced to NaT during cleaning and round-trip to
    # NaN through the CSV, so isna() catches them.
    invalid_order_date_count = int(df["order_date"].isna().sum())
    missing_customer_name_count = (
        _count_blank(df["customer_name"]) if "customer_name" in df.columns else 0
    )
    missing_quantity_count = _count_blank(df["quantity"])
    invalid_quantity_count = _invalid_numeric_count(df["quantity"])
    invalid_unit_price_count = _invalid_numeric_count(df["unit_price"])

    summary = pd.DataFrame({
        "metric": [
            "total_orders",
            "completed_revenue",
            "invalid_order_date_count",
            "missing_customer_name_count",
            "missing_quantity_count",
            "invalid_quantity_count",
            "invalid_unit_price_count",
        ],
        "value": [
            total_orders,
            completed_revenue,
            invalid_order_date_count,
            missing_customer_name_count,
            missing_quantity_count,
            invalid_quantity_count,
            invalid_unit_price_count,
        ],
    })

    # Ensure output directory exists before writing
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print("[report] saving summary...")
    summary.to_csv(output_path, index=False)

    print("[report] done")
