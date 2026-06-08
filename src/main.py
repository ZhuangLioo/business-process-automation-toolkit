import argparse
from src.data_cleaning import clean_order_data
from src.data_quality import generate_data_issues_report
from src.reporting import generate_basic_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--report",
        default="output/reports/summary.csv",
        help="path for the generated KPI summary report",
    )
    parser.add_argument(
        "--issues",
        default="output/reports/data_issues.csv",
        help="path for the per-row data quality issues file (one row per problem)",
    )
    args = parser.parse_args()

    clean_order_data(args.input, args.output)
    generate_basic_report(args.output, args.report)
    # data_quality needs the raw input too — it reaches back to recover the
    # original date string for any row that failed to parse, so the issues
    # report can show "31-Feb-2026" instead of just an empty cell.
    generate_data_issues_report(args.input, args.output, args.issues)


if __name__ == "__main__":
    main()
