import argparse
import csv
from pathlib import Path


def calculate_cost(filename):
    total_cost = 0.0

    with Path(filename).open(mode="r", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            total_cost += float(row["hourly_cost"])

    return total_cost


def parse_args():
    parser = argparse.ArgumentParser(description="Calculate hourly fleet cost from a CSV file.")
    parser.add_argument(
        "filename",
        nargs="?",
        default=Path(__file__).with_name("servers.csv"),
        help="CSV file with an hourly_cost column.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        total_cost = calculate_cost(args.filename)
    except FileNotFoundError:
        raise SystemExit(f"Could not find the file named '{args.filename}'.")
    except (KeyError, ValueError) as error:
        raise SystemExit(f"Invalid cost data in '{args.filename}': {error}.")

    print(f"Total Hourly Fleet Cost: ${total_cost:.2f}")


if __name__ == "__main__":
    main()
