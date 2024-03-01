import requests
from datetime import datetime, timedelta
import pandas as pd
import os
import threading

BASE_API_URL = "https://www.nseindia.com/"
OPTIONS = ["Equities"]
OUTPUT_FOLDER = "Output"
BATCH_SIZE = 10


def not_downloaded():
    global total_not_downloaded
    total_not_downloaded = []


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


def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Folder '{folder_path}' created.")


def download_file(url, symbol, from_to, folder_path, request_meta):
    filename = os.path.join(folder_path, f"{symbol}_{from_to[0]}_{from_to[1]}_BRSR.xml")
    try:
        response = request_meta["session"].get(
            url,
            headers=request_meta["headers"],
            cookies=request_meta["cookies"],
            timeout=5,
        )

        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"Downloaded: {filename}")
        else:
            total_not_downloaded.append(filename)

            print(
                f"Failed to download: {filename}, Status code: {response.status_code}"
            )
    except Exception as e:
        total_not_downloaded.append(filename)
        print(f"Failed to download: {filename}, Error: {str(e)}")


def download_batch(data, folder_path, request_meta):
    threads = []
    for row in data.itertuples(index=False):
        url = row.xbrlFile
        symbol = row.symbol
        from_to = (row.fyFrom, row.fyTo)
        thread = threading.Thread(
            target=download_file,
            args=(url, symbol, from_to, folder_path, request_meta),
        )
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()


def download_in_batches(data_df, folder_path, batch_size, request_meta):
    total_rows = len(data_df)
    num_batches = (total_rows + batch_size - 1) // batch_size
    for i in range(num_batches):
        start_index = i * batch_size
        end_index = min((i + 1) * batch_size, total_rows)
        batch_data = data_df.iloc[start_index:end_index]
        download_batch(batch_data, folder_path, request_meta=request_meta)


def main():

    selected_option = get_valid_option("\nEnter the index of the option: ", OPTIONS)
    print("Selected the type of index you want:", selected_option)
    index_option = selected_option.lower()

    today = datetime.today()
    one_year_ago = today - timedelta(days=365)
    print(
        "\n",
        "=====Fetching Business Responsitbility & Sustainability Reports from NSE India====",  # noqa
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

    headers = {
        "User-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",  # noqa
        "Accept-Language": "en,gu;q=0.9,hi;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "*/*",
    }

    session = requests.Session()
    session_response = session.get(BASE_API_URL, headers=headers, timeout=5)
    cookies = dict(session_response.cookies)

    api_url = BASE_API_URL + "api/corporate-bussiness-sustainabilitiy"
    response = session.get(api_url, headers=headers, cookies=cookies, params=params)
    json_data = {}
    if response.status_code == 200:
        print("Reports downloaded successfully!")
        json_data = response.json()
    else:
        print("Failed to download reports. Status code:", response.status_code)
    df = pd.DataFrame()
    if "data" in json_data:  # Check if 'data' key exists
        data = json_data["data"]  # Extract data associated with 'data' key
        df = pd.DataFrame(data)
        create_folder_if_not_exists(OUTPUT_FOLDER)
        folder_name = f"{params['from_date']}~{params['to_date']}"
        folder_path = os.path.join(OUTPUT_FOLDER, folder_name)
        create_folder_if_not_exists(folder_path)
        download_in_batches(
            df,
            folder_path,
            batch_size=BATCH_SIZE,
            request_meta={"session": session, "headers": headers, "cookies": cookies},
        )
        for i, row in df.iterrows():
            xbrl_file_path = os.path.join(
                folder_path, f"{row['symbol']}_{row['fyFrom']}_{row['fyTo']}_BRSR.xml"
            )
            if xbrl_file_path in total_not_downloaded:
                xbrl_file_path = "N/A"
            df.at[i, "xbrlFile"] = xbrl_file_path
        print("Check downloaded data at: ", folder_path)
        df.to_csv(
            f"BRSR_Reports_{params['from_date']}_{params['to_date']}.csv", index=False
        )
        print("Total files downloaded: ", len(df) - len(total_not_downloaded))
        print(
            "Mapped Response csv file:",
            f"BRSR_Reports_{params['from_date']}_{params['to_date']}.csv",
        )

    else:
        print("No data found in the response.")


if __name__ == "__main__":
    not_downloaded()
    main()
