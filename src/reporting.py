from pathlib import Path
import pandas as pd


def generate_basic_report(input_path: str, output_path: str):
    print("[report] loading cleaned data...")

    df = pd.read_csv(input_path)

    total_orders = len(df)
    status = df["status"].fillna("").astype(str).str.strip().str.lower()
    completed = df[status == "completed"]
    completed_revenue = (completed["quantity"].fillna(0) * completed["unit_price"].fillna(0)).sum()

    summary = pd.DataFrame({
        "metric": ["total_orders", "completed_revenue"],
        "value": [total_orders, completed_revenue]
    })

    # Ensure output directory exists before writing
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print("[report] saving summary...")
    summary.to_csv(output_path, index=False)

    print("[report] done")
