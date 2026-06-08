from pathlib import Path
import re

import pandas as pd


REQUIRED_COLUMNS = ("order_date", "status", "quantity", "unit_price")

# Characters that real Excel exports leave in numeric cells: currency symbols,
# thousands separators, and any whitespace (regular space, tab, non-breaking
# space, etc.). Stripped before attempting to parse a number. Shared between
# src.reporting (which coerces for revenue) and src.data_quality (which uses
# the same definition of "noise" to decide what counts as an invalid number),
# so the two modules can never silently diverge on what they accept.
NUMERIC_NOISE_PATTERN = re.compile(r"[$,\s]")


def normalise_columns(df: pd.DataFrame) -> None:
    """Lowercase / snake_case / trim column names in place."""
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")


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

    normalise_columns(df)

    _validate_columns(df)

    df["order_date"] = df["order_date"].apply(_parse_order_date)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"[clean] writing: {output_path}")
    df.to_csv(output_path, index=False)
    print(f"[clean] done. rows={len(df)}")
