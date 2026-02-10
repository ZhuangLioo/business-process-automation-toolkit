import argparse
from src.data_cleaning import clean_orders


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    clean_orders(args.input, args.output)


if __name__ == "__main__":
    main()
