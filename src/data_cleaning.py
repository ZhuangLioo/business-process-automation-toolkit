from pathlib import Path
import pandas as pd


def clean_orders(input_path: str, output_path: str):
    print(f"[clean] reading: {input_path}")
    df = pd.read_csv(input_path)

    # 标准化列名
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # 统一日期
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce", dayfirst=True)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"[clean] writing: {output_path}")
    df.to_csv(output_path, index=False)
    print(f"[clean] done. rows={len(df)}")
