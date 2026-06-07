# Business Process Automation Toolkit (BPAT)

Python toolkit for procurement and operations reporting, designed around manual Excel workflows commonly found in small-to-medium industrial businesses.

> All data in this repository is sanitised sample data. No internal company information is included.

---

## The Business Problem

In many small industrial businesses, daily operations data — orders, suppliers, costs — lives in Excel files maintained by hand. Common pain points:

- Order records use **inconsistent date formats** (`2026-02-01`, `01/02/2026`, `04-02-2026` all in the same file)
- Column names vary between exports (`Order ID` vs `order_id`, mixed case, trailing spaces)
- Missing values in critical fields (customer name, quantity) go unnoticed until month-end
- Summary reports are rebuilt manually each week, with high risk of formula errors

The operations team ends up spending hours every week reconciling spreadsheets instead of analysing the business.

---

## Before vs After

**Before** — manual workflow:
1. Open the weekly orders export in Excel
2. Manually fix date formats row by row
3. Rename columns to match the reporting template
4. Build a pivot table for totals
5. Copy results into the management report

**After** — BPAT:
```bash
python -m src.main --input data/raw/orders_sample.csv --output data/processed/orders_cleaned.csv
```

One command produces a cleaned dataset and a summary report ready for review.

---

## What the Toolkit Does

**Data cleaning** (`src/data_cleaning.py`)
- Standardises column names (lowercase, snake_case, trimmed)
- Normalises mixed date formats into ISO `YYYY-MM-DD`
- Preserves missing values for downstream visibility (rather than silently filling)

**Reporting** (`src/reporting.py`)
- Computes total order count
- Computes total revenue (`quantity × unit_price`, handling missing values)
- Outputs a clean `summary.csv` for management review

---

## Sample Input / Output

**Input** (`data/raw/orders_sample.csv`):

| Order ID | order_date  | Customer Name        | Product          | Quantity | unit_price | Status    |
|----------|-------------|----------------------|------------------|----------|------------|-----------|
| 1001     | 2026-02-01  | Acme Pty Ltd         | Cable Joint      | 10       | 12.5       | Completed |
| 1002     | 01/02/2026  | Blue Mountain Trading| Heat Shrink Tube | 5        | 8.0        | Completed |
| 1003     | 2026/02/03  |                      | Heat Shrink Tube | 3        | 8.0        | Pending   |
| 1004     | 2026-02-04  | Sydney Wholesale     | Cable Joint      |          | 12.5       | Completed |

**Cleaned output** (`data/processed/orders_cleaned.csv`) — column names normalised, all date formats unified, all rows preserved (missing values kept visible rather than silently dropped or filled):

| order_id | order_date | customer_name        | product          | quantity | unit_price | total_amount | status    |
|----------|------------|----------------------|------------------|----------|------------|--------------|-----------|
| 1001     | 2026-02-01 | Acme Pty Ltd         | Cable Joint      | 10.0     | 12.5       | 125.0        | Completed |
| 1002     | 2026-02-01 | Blue Mountain Trading| Heat Shrink Tube | 5.0      | 8.0        | 40.0         | Completed |
| 1003     | 2026-02-03 |                      | Heat Shrink Tube | 3.0      | 8.0        | 24.0         | Pending   |
| 1004     | 2026-02-04 | Sydney Wholesale     | Cable Joint      |          | 12.5       |              | Completed |
| 1005     | 2026-02-04 | Acme Pty Ltd         | Cable Joint      | 2.0      | 12.5       | 25.0         | Cancelled |
| 1006     | 2026-02-05 | North Shore Supplies | Heat Shrink Tube | 1.0      | 8.0        | 8.0          | Completed |

**Summary report** (`output/reports/summary.csv`):

| metric             | value |
|--------------------|-------|
| total_orders       | 6     |
| completed_revenue  | 173.0 |

---

## Tech Stack

- Python 3
- pandas — data manipulation and date normalisation
- python-dateutil — flexible date parsing (used via pandas)

---

## Project Structure

```
.
├── src/
│   ├── main.py            # CLI entry point
│   ├── data_cleaning.py   # column + date normalisation
│   └── reporting.py       # summary metrics
├── data/
│   ├── raw/               # sample input
│   └── processed/         # cleaned output
├── output/
│   └── reports/           # summary reports
└── requirements.txt
```

---

## How to Run

```bash
pip install -r requirements.txt
python -m src.main \
    --input data/raw/orders_sample.csv \
    --output data/processed/orders_cleaned.csv \
    --report output/reports/summary.csv
```

`--report` is optional and defaults to `output/reports/summary.csv`.

---

## What This Project Demonstrates

- Translating a real operational pain point (manual Excel reconciliation) into a small, focused tool
- Defensive data handling: preserving missing values, normalising inconsistent formats without losing information
- Clear separation of concerns — cleaning, reporting, and CLI entry kept independent
- Reproducible workflow with sanitised sample data so the project can be demoed end-to-end

---

## Roadmap

- Supplier concentration analysis
- Procurement cost breakdown by category
- Abnormal cost pattern detection
- Excel report export with charts (will reintroduce `openpyxl` and `matplotlib` when implemented)
