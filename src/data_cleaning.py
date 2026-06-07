from pathlib import Path
import pandas as pd


REQUIRED_COLUMNS = ("order_date", "status", "quantity", "unit_price")


def _validate_columns(df: pd.DataFrame) -> None:
    missing = sorted(set(REQUIRED_COLUMNS) - set(df.columns))
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(missing)}"
        )


def _parse_order_date(value):
    # Source CSVs mix ISO dates ("2026-02-01") with Australian day-first dates
    # ("01/02/2026", "04-02-2026"). A single `dayfirst` setting cannot serve
    # both — applying dayfirst=True to "2026-02-01" yields Jan 2, not Feb 1.
    # Route per-value: anything starting with a 4-digit year is parsed as ISO;
    # everything else is parsed as day-first.
    if pd.isna(value):
        return pd.NaT
    text = str(value).strip()
    if len(text) >= 4 and text[:4].isdigit():
        return pd.to_datetime(text, errors="coerce")
    return pd.to_datetime(text, errors="coerce", dayfirst=True)


def clean_order_data(input_path: str, output_path: str):
    print(f"[clean] reading: {input_path}")
    df = pd.read_csv(input_path)

    # Standardise column names: lowercase, snake_case, trimmed
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    _validate_columns(df)

    df["order_date"] = df["order_date"].apply(_parse_order_date)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"[clean] writing: {output_path}")
    df.to_csv(output_path, index=False)
    print(f"[clean] done. rows={len(df)}")
