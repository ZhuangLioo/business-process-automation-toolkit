import argparse
from src.data_cleaning import clean_order_data
from src.reporting import generate_basic_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--report",
        default="output/reports/summary.csv",
        help="path for the generated summary report",
    )
    args = parser.parse_args()

    clean_order_data(args.input, args.output)
    generate_basic_report(args.output, args.report)


if __name__ == "__main__":
    main()
