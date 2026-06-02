import requests
import pandas as pd

# 5 Key Schemes
schemes = {
    "SBI_Bluechip": 119551,
    "ICICI_Bluechip": 120503,
    "Nippon_Large_Cap": 118632,
    "Axis_Bluechip": 119092,
    "Kotak_Bluechip": 120841
}

for scheme_name, code in schemes.items():
    url = f"https://api.mfapi.in/mf/{code}"
    response = requests.get(url)
    data = response.json()
    
    nav_data = data['data']
    df = pd.DataFrame(nav_data)
    
    # Save each scheme as separate CSV
    df.to_csv(f'data/raw/{scheme_name}_nav.csv', index=False)
    print(f"✅ {scheme_name} saved with {len(df)} records")

print("\nAll 5 schemes saved successfully!")
extra_schemes = {
    "HDFC_Top100": 125497,
    "Mirae_Large_Cap": 118834,
    "DSP_Top100": 119364
}

for scheme_name, code in extra_schemes.items():
    url = f"https://api.mfapi.in/mf/{code}"
    response = requests.get(url)
    data = response.json()
    nav_data = data['data']
    df = pd.DataFrame(nav_data)
    df.to_csv(f'data/raw/{scheme_name}_nav.csv', index=False)
    print(f"✅ {scheme_name} saved with {len(df)} records")