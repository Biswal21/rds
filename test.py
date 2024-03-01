import requests
from datetime import datetime, timedelta
import pandas as pd

API_URL = "https://www.nseindia.com/api/corporate-business-sustainability"
OPTIONS = ["Equities"]


def get_valid_date(prompt):
    while True:
        date_str = input(prompt)
        if not date_str:
            return None
        try:
            date = datetime.strptime(date_str, "%d-%m-%Y")
            return date
        except ValueError:
            print("Incorrect date format. Please enter date in dd-mm-yyyy format.")


def get_valid_option(prompt, options):
    while True:
        print("Select an Index:")
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        user_input = input(prompt)
        if not user_input:
            print("(Selecting the first option as default.)\n")
            return options[0]
        try:
            index = int(user_input)
            if 1 <= index <= len(options):
                return options[index - 1]
            else:
                print("Invalid option. Please select a valid number.")
        except ValueError:
            print("Invalid option. Please select a valid number.")


def main():

    selected_option = get_valid_option("\nEnter the index of the option: ", OPTIONS)
    print("Selected the type of index you want:", selected_option)
    index_option = selected_option.lower()

    today = datetime.today()
    one_year_ago = today - timedelta(days=365)
    print(
        "\n",
        "=====Fetching Business Responsitbility & Sustainability Reports from NSE India====",
        "\n",
    )

    print(
        f"Please enter the 'From' date (dd-mm-yyyy), or leave empty for default one year ago from today's date ({one_year_ago.strftime('%d-%m-%Y')}):"  # noqa
    )
    from_date = get_valid_date("> ")

    if from_date is None:
        print("Using default 'From' date:", one_year_ago.strftime("%d-%m-%Y"))
        from_date = one_year_ago
    elif from_date > today:
        print("From date cannot be in the future. Setting it to today's date.")
        from_date = today

    print(
        f"\nPlease enter the 'To' date (dd-mm-yyyy), or leave empty for default today ({today.strftime('%d-%m-%y')}):"  # noqa
    )
    to_date = get_valid_date("> ")

    if to_date is None:
        print("Using default 'To' date:", today.strftime("%d-%m-%Y"))
        to_date = today
    elif to_date > today:
        print("To date cannot be in the future. Setting it to today's date.")
        to_date = today

    if to_date < from_date:
        print("To date cannot be before the From date. Setting it to the From date.")
        to_date = from_date

    # Assuming 'abc' is the base URL of the API
    params = {
        "index": index_option,
        "from_date": from_date.strftime("%d-%m-%Y"),
        "to_date": to_date.strftime("%d-%m-%Y"),
    }
    print(params)

    # response = requests.get(API_URL, params=params)

    # if response.status_code == 200:
    #     # Process the response data here
    #     print("Reports downloaded successfully!")
    # else:
    #     print("Failed to download reports. Status code:", response.status_code)


if __name__ == "__main__":
    main()
