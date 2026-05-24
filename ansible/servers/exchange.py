import requests

# 1. Send a request to the API URL
response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")

# 2. Convert the JSON response into a Python Dictionary
data = response.json()

# 3. Grab the THB rate using dictionary keys
thb_rate = data["rates"]["THB"]
print(f"Current USD to THB rate: {thb_rate}")
