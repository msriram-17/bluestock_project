import requests
import pandas as pd
import os

output_folder = "data/raw/live_nav"

os.makedirs(output_folder, exist_ok=True)

scheme_codes = {
    "HDFC_Top100": 125497,
    "SBI_Bluechip": 119551,
    "ICICI_Bluechip": 120503,
    "Nippon_Large_Cap": 118632,
    "Axis_Bluechip": 119092,
    "Kotak_Bluechip": 120841
}

for fund_name, scheme_code in scheme_codes.items():

    url = f"https://api.mfapi.in/mf/{scheme_code}"

    try:

        response = requests.get(url)

        if response.status_code == 200:

            data = response.json()

            nav_df = pd.DataFrame(data["data"])

            file_name = f"{fund_name}_nav.csv"

            nav_df.to_csv(
                os.path.join(output_folder, file_name),
                index=False
            )

            print(f"{fund_name} saved successfully")

        else:
            print(f"Failed for {fund_name}")

    except Exception as e:
        print(f"Error: {fund_name} -> {e}")

print("\nLive NAV fetching completed.")