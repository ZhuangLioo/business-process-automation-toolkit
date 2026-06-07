from pathlib import Path
import pandas as pd


def _count_blank(series: pd.Series) -> int:
    """Count rows where the value is NaN or whitespace-only."""
    return int(series.fillna("").astype(str).str.strip().eq("").sum())


def generate_basic_report(input_path: str, output_path: str):
    print("[report] loading cleaned data...")

    df = pd.read_csv(input_path)

    total_orders = len(df)

    status = df["status"].fillna("").astype(str).str.strip().str.lower()
    completed = df[status == "completed"]
    completed_revenue = (completed["quantity"].fillna(0) * completed["unit_price"].fillna(0)).sum()

    # Data quality metrics — surface problems instead of hiding them.
    # Invalid dates were coerced to NaT during cleaning and round-trip to
    # NaN through the CSV, so isna() catches them.
    invalid_order_date_count = int(df["order_date"].isna().sum())
    missing_customer_name_count = (
        _count_blank(df["customer_name"]) if "customer_name" in df.columns else 0
    )
    missing_quantity_count = int(df["quantity"].isna().sum())

    summary = pd.DataFrame({
        "metric": [
            "total_orders",
            "completed_revenue",
            "invalid_order_date_count",
            "missing_customer_name_count",
            "missing_quantity_count",
        ],
        "value": [
            total_orders,
            completed_revenue,
            invalid_order_date_count,
            missing_customer_name_count,
            missing_quantity_count,
        ],
    })

    # Ensure output directory exists before writing
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print("[report] saving summary...")
    summary.to_csv(output_path, index=False)

    print("[report] done")
