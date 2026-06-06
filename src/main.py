import argparse
from src.data_cleaning import clean_order_data
from src.reporting import generate_basic_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    clean_order_data(args.input, args.output)

    generate_basic_report(
        "data/processed/orders_cleaned.csv",
        "output/reports/summary.csv"
    )


if __name__ == "__main__":
    main()
