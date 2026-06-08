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
- Computes completed-order revenue (`quantity × unit_price` for `status == "Completed"`, with dirty Excel-style values like `$12.50` and `1,200` coerced to numbers before multiplying)
- Surfaces data quality counts — invalid dates, missing customer names, missing quantities, and unparseable numeric values — so problems are visible instead of hidden
- Outputs a clean `summary.csv` for management review

**Data quality issues report** (`src/data_quality.py`)

The summary report answers *"how many problems are in this batch?"*. But the question the data team actually has on Monday morning is *"which rows do I need to go fix?"*. A count of `missing_customer_name_count = 12` doesn't help a data steward triage — they need to know **which 12 orders**.

`data_issues.csv` answers that. Every detected problem is listed on its own row with:

- `row_number` — position of the order in the source file
- `order_id` — the business identifier, so the issue can be matched back to the source system without re-reading the CSV
- `issue_type` — `missing_customer_name`, `invalid_order_date`, `invalid_quantity`, etc.
- `column` — which field the problem is in
- `value` — the raw value that failed (preserved verbatim so you can see *what* the source actually contained)
- `message` — a human-readable description for non-technical readers

The result is a file a BA or data steward can open in Excel, filter by `issue_type`, and immediately start working through — no need to re-run the pipeline or rebuild a pivot table.

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

| metric                       | value |
|------------------------------|-------|
| total_orders                 | 6     |
| completed_revenue            | 173.0 |
| invalid_order_date_count     | 0     |
| missing_customer_name_count  | 1     |
| missing_quantity_count       | 1     |
| invalid_quantity_count       | 0     |
| invalid_unit_price_count     | 0     |

**Per-row data issues** (`output/reports/data_issues.csv`) — what the summary numbers `missing_customer_name_count = 1` and `missing_quantity_count = 1` *actually mean* in terms of which orders need a follow-up:

| row_number | order_id | issue_type             | column         | value | message                    |
|------------|----------|------------------------|----------------|-------|----------------------------|
| 3          | 1003     | missing_customer_name  | customer_name  |       | Customer name is missing   |
| 4          | 1004     | missing_quantity       | quantity       |       | Quantity is missing        |

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
│   ├── reporting.py       # summary metrics
│   └── data_quality.py    # per-row data issues report (triage output)
├── tests/                 # pytest suite for cleaning, reporting, and data quality
├── data/
│   ├── raw/               # sample input
│   └── processed/         # cleaned output
├── output/
│   └── reports/           # summary reports
├── requirements.txt
└── requirements-dev.txt   # adds pytest for running the test suite
```

---

## How to Run

```bash
pip install -r requirements.txt
python -m src.main \
    --input data/raw/orders_sample.csv \
    --output data/processed/orders_cleaned.csv \
    --report output/reports/summary.csv \
    --issues output/reports/data_issues.csv
```

Both `--report` and `--issues` are optional and default to `output/reports/summary.csv` and `output/reports/data_issues.csv` respectively. A single run produces three artifacts: the cleaned dataset, the KPI summary, and the per-row issues file.

---

## Tests

Cleaning, reporting, and data quality rules are covered by a `pytest` suite:

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

The tests lock the documented business rules into executable form — for example, `completed_revenue` is asserted to equal `173.0` on the canonical sample, so a later change that accidentally includes `Pending` or `Cancelled` rows will fail loudly. Likewise, `data_issues.csv` is asserted to list the *specific* `order_id`s (1003, 1004) that need follow-up on the canonical sample, so the per-row triage output can't silently lose rows.

---

## What This Project Demonstrates

- Translating a real operational pain point (manual Excel reconciliation) into a small, focused tool
- Defensive data handling: preserving missing values, normalising inconsistent formats without losing information
- Clear separation of concerns — cleaning, KPI reporting, and data quality output kept in independent modules
- **Output designed for the actual end user**: a BA / data steward gets both summary counts (for management) and a per-row issues file (for triage), not just one or the other
- Business rules captured as tests so regressions are caught automatically
- Reproducible workflow with sanitised sample data so the project can be demoed end-to-end

---

## Roadmap

- Supplier concentration analysis
- Procurement cost breakdown by category
- Abnormal cost pattern detection
- Excel report export with charts (will reintroduce `openpyxl` and `matplotlib` when implemented)
