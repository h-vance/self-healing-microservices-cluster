import csv


def calculate_cost(filename):
    total_cost = 0.0

    try:
        with open(filename, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                total_cost += float(row["hourly_cost"])

        print(f"Total Hourly Fleet Cost: ${total_cost:.2f}")

    except FileNotFoundError:
        print(f"Error: Could not find the file named '{filename}'!")


# This calls your new function and passes in the filename
calculate_cost("servers.csv")
