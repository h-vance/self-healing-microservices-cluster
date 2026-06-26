import argparse

import requests


def parse_args():
    parser = argparse.ArgumentParser(description="Print a USD exchange rate.")
    parser.add_argument("--currency", default="THB")
    parser.add_argument("--timeout", type=int, default=5)
    return parser.parse_args()


def main():
    args = parse_args()
    response = requests.get(
        "https://api.exchangerate-api.com/v4/latest/USD",
        timeout=args.timeout,
    )
    response.raise_for_status()
    data = response.json()
    rate = data["rates"][args.currency.upper()]
    print(f"Current USD to {args.currency.upper()} rate: {rate}")


if __name__ == "__main__":
    main()
